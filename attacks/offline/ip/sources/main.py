#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

"""
IP protocol decoder.

These are only doctest strings:

>>> from PM.Core.AttackUtils import attack_unittest
>>> attack_unittest('-f ethernet,ip', 'wrong-checksum.pcap')
decoder.ip.notice Invalid IP packet from 127.0.0.1 to 127.0.0.1 : wrong checksum 0xdead instead of 0x7bce

Fragmentation tests.

>>> attack_unittest('-f ethernet,ip -sdecoder.ip.reassemble_max_fragments=1', 'fragmented-ping.pcap')
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
>>> attack_unittest('-f ethernet,ip -sdecoder.ip.reassemble_max_fragments=2', 'fragmented-ping.pcap')
decoder.ip.debug Dropping out the sequence with ID: 14300 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14301 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14302 due reassemble_max_fragments
decoder.ip.debug Dropping out the sequence with ID: 14303 due reassemble_max_fragments
"""

from time import time

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import AttackManager, OfflineAttack
from PM.Core.NetConst import PROTO_LAYER, NET_LAYER, LL_TYPE_IP
from PM.Core.AttackUtils import checksum

def ip_decoder():
    manager = AttackManager()

    conf = manager.get_configuration('decoder.ip')
    checksum_check, reassemble, max_len, max_frags = \
        conf['checksum_check'], conf['reassemble'], \
        conf['reassemble_max_fraglist'], conf['reassemble_max_fragments']

    reas_dict = {}

    def internal(mpkt):
        ipraw = mpkt.get_field('ip')
        iplen = min(20, len(ipraw))

        if mpkt.get_field('ip.len') > len(ipraw):
            # Probably we are capturing with low snaplen
            # so the packets are not fully captured. Avoid
            # further calculation.
            return PROTO_LAYER, mpkt.get_field('ip.proto')

        if checksum_check:
            pkt = ipraw[:10] + '\x00\x00' + ipraw[12:iplen]

            chksum = checksum(pkt)

            # Probably here it's better to set also a cfield
            # and to turn False the checksum_check default value
            if mpkt.get_field('ip.chksum') != chksum:
                mpkt.set_cfield('good_checksum', hex(chksum))
                manager.user_msg(_("Invalid IP packet from %s to %s : " \
                                   "wrong checksum %s instead of %s") %  \
                                 (mpkt.get_field('ip.src'),          \
                                  mpkt.get_field('ip.dst'),          \
                                  hex(mpkt.get_field('ip.chksum')),  \
                                  hex(chksum)),
                                 5, 'decoder.ip')
            elif reassemble:
                # Here we have to check for fragmentation
                # by creating a dict to holds id of ip packets
                # and set mpkt.lock() on it if mpkg is MF
                # until the resegmentation is done.
                # If it's a fragment we have to return None
                # to break the chain.

                # TODO: check ip.flags standard name in UMPA
                ts = time()
                mf = mpkt.get_field('ip.flags') & 1
                frag_off = mpkt.get_field('ip.frag') * 8

                if not mf and frag_off == 0:
                    return PROTO_LAYER, mpkt.get_field('ip.proto')

                ipid = mpkt.get_field('ip.id')

                if ipid in reas_dict:
                    plist = reas_dict[ipid]

                    if len(plist) >= max_frags:
                        del reas_dict[ipid]
                        manager.user_msg(_('Dropping out the sequence with ID: '
                                           '%s due reassemble_max_fragments') %
                                         ipid, 7, 'decoder.ip')

                        return PROTO_LAYER, mpkt.get_field('ip.proto')

                    ret = 0
                    idx = 0
                    inserted = False

                    while idx < len(plist):
                        ts2, frag_off2, mpkt2 = plist[idx]

                        if frag_off2 == frag_off:
                            plist[idx] = (ts, frag_off, mpkt.copy())
                            break
                        elif frag_off2 < frag_off:
                            ret += frag_off2
                            idx += 1
                            continue

                        inserted = True
                        plist.insert(idx, (ts, frag_off, mpkt.copy()))
                        break

                    if not inserted:
                        plist.append((ts, frag_off, mpkt.copy()))

                    # Now let's get the last packet and see if MF = 0
                    # EVASION!
                    if plist[-1][-1].get_field('ip.flags') & 1 == 0:

                        if idx == len(plist) -1:
                            ret = frag_off - ret
                        else:
                            while idx < len(plist) - 1:
                                ts2, frag_off2, mpkt2 = plist[idx]
                                ret += frag_off2
                                idx += 1

                                ret = plist[-1][1] - ret

                        if ret == 0:
                            log.debug('Reassembling sequence with ID: %s' % \
                                      ipid)

                            reas_payload = ''

                            for ts2, frag_off2, mpkt2 in plist:
                                try:
                                    ihl = mpkt2.get_field('ip.ihl') * 4
                                    reas_payload += mpkt2.get_field('ip')[ihl:]
                                except:
                                    pass

                            # Ok check that we have a complete payload
                            ihl = mpkt.get_field('ip.ihl') * 4
                            p_len = frag_off + mpkt.get_field('ip.len') - ihl

                            if len(reas_payload) != p_len:
                                mpkt.set_cfield('reassemble_payload', None)
                                manager.user_msg(_('Reassemble of IP packet ' \
                                                   'from %s to %sfailed') % \
                                                 (mpkt.get_field('ip.src'),
                                                  mpkt.get_field('ip.dst')),
                                                 4, 'decoder.ip')

                            # Nice drop out everythin!
                            del reas_dict[ipid]

                            mpkt.set_cfield('reassemble_payload', reas_payload)
                else:
                    if len(reas_dict) >= max_len:
                        # Ok just drop the list with the minor ts (the oldest)
                        min_k = min([(v, k) for k, v in reas_dict.items()])[1]
                        del reas_dict[min_k]

                        # Debug
                        manager.user_msg(_('Dropping out the oldest sequence '
                                           'with ID: %s') % min_k,
                                         7, 'decoder.ip')

                    log.debug('First packet of the sequence with ID: %s' % ipid)
                    reas_dict[ipid] = [(ts, frag_off, mpkt)]

        return PROTO_LAYER, mpkt.get_field('ip.proto')

    return internal

class IPDecoder(Plugin, OfflineAttack):
    def register_options(self):
        conf = AttackManager().register_configuration('decoder.ip')
        conf.register_option('checksum_check', True, bool)
        conf.register_option('reassemble', True, bool)
        conf.register_option('reassemble_max_fraglist', 30, int)
        conf.register_option('reassemble_max_fragments', 10, int)

    def register_decoders(self):
        AttackManager().add_decoder(NET_LAYER, LL_TYPE_IP, ip_decoder())

__plugins__ = [IPDecoder]
__plugins_deps__ = [('IPDecoder', [], [], [])]
