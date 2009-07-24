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

import socket

from threading import Thread

from PM.Core.I18N import _
from PM.Core.Logger import log

from PM.Backend.Scapy import *

def register_attack_context(BaseAttackContext):
    class AttackContext(BaseAttackContext):
        def __init__(self, dev1, dev2=None, bpf_filter=None, capmethod=0):
            BaseAttackContext.__init__(self, dev1, dev2, bpf_filter, capmethod)

            self.internal = False
            self.thread1 = None
            self.thread2 = None

            if dev2:
                self.title = _('Attack on %s:%s' % (dev1, dev2))
            else:
                self.title = _('Attack on %s' % dev1)


            log.debug('Creating send sockets')

            try:
                # Here we create L2 and L3 sockets used to send packets
                self._l2_socket = conf.L2socket(iface=dev1)
                self._l3_socket = conf.L3socket(iface=dev1)

                if dev2:
                    self._lb_socket = conf.L2socket(iface=dev2)

                if capmethod == 0:
                    log.debug('Creating listen sockets')

                    self._listen_dev1 = conf.L2listen(iface=dev1,
                                                      filter=bpf_filter)

                    if dev2:
                        self._listen_dev2 = conf.L2listen(iface=dev2,
                                                          filter=bpf_filter)
                else:
                    log.debug('Creating helper processes')

                    self._listen_dev1 = run_helper(self.capmethod - 1, dev1,
                                                   bpf_filter)

                    if dev2:
                        self._listen_dev2 = run_helper(self.capmethod - 1, dev2,
                                                       bpf_filter)

            except socket.error, (errno, err):
                self.summary = str(err)
                return

            except Exception, err:
                self.summary = str(err)

        def _start(self):
            if self.internal:
                log.error('Attack is already running')
                return False

            if not self._listen_dev1:
                log.error('We\'ve got an error in __init__. No listen socket')
                return False

            self.internal = True

            log.debug('Spawning capture threads')

            func = (self.capmethod == 0 and \
                    self.__sniff_thread or \
                    self.__helper_thread)

            self.thread1 = Thread(None, func, 'ATK1', (self._listen_dev1, ))
            self.thread1.setDaemon(True)
            self.thread1.start()

            if self._listen_dev2:
                self.thread2 = Thread(None, func, 'ATK2', (self._listen_dev2, ))
                self.thread2.setDaemon(True)
                self.thread2.start()

            return True

        def __helper_thread(self, obj):
            errstr = _('Attack finished')

            try:
                for reader in bind_reader(obj[0], obj[1]):
                    if not self.internal:
                        break

                    if reader:
                        reader, outfile_size, position = reader
            except OSError, err:
                errstr = err.strerror
                self.internal = False
            except Exception, err:
                errstr = str(err)
                self.internal = False

            log.debug('Entering in the helper mainloop')

            reported_packets = 0

            while self.internal:
                report_idx = get_n_packets(obj[0])

                if report_idx < reported_packets:
                    continue

                while reported_packets < report_idx:
                    r = reader.read_packet()

                    if not r:
                        break

                    mpkt = MetaPacket(r)

                    # HERE GOES THE CODE
                    print mpkt.summary()

                    reported_packets += 1

                report_idx = reported_packets

            self.summary = errstr

        def __sniff_thread(self, obj):
            errstr = _('Attack finished')

            log.debug('Entering in the native mainloop')

            while self.internal:
                r = None

                try:
                    if WINDOWS:
                        try:
                            r = obj.recv(MTU)
                        except PcapTimeoutElapsed:
                            continue
                    else:
                        inmask = [obj]
                        inp, out, err = select(inmask, inmask, inmask, None)

                        if obj in inp:
                            r = obj.recv(MTU)

                    if r is None:
                        continue

                    mpkt = MetaPacket(r)

                    # HERE GOES THE CODE
                    print mpkt.summary()

                except Exception, err:
                    if self.internal:
                        errstr = str(err)

                    self.internal = False
                    break

            self.summary = errstr

    return AttackContext
