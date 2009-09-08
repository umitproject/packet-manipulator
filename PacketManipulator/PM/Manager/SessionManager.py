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
Session manager module.
"""

from socket import inet_aton

from PM.Core.Logger import log
from PM.Core.Atoms import Singleton, defaultdict
from PM.Core.NetConst import TH_ACK, TH_SYN, TH_PSH

class DissectIdent(object):
    magic = None

    def __init__(self, sip=None, dip=None, sport=None, dport=None, proto=None):
        self.sip = sip
        self.dip = dip
        self.sport = sport
        self.dport = dport
        self.proto = proto

    def __eq__(self, other):
        if self.magic == other.magic and \
           self.proto == other.proto and \
           self.sport == other.sport and \
           self.dport == other.dport and \
           self.sip == other.sip and     \
           self.dip == other.dip:
            return True
        return False

class Session(object):
    def __init__(self, data=None, ident=None, prev=None):
        self.data = data
        self.ident = ident
        self.prev = prev

class SessionManager(Singleton):
    """
    The session manager is a singleton class.
    """

    def __init__(self):
        # The sessions are saved with ident magic as key
        # and collision are handled by an overflow list
        self._sessions = defaultdict(list)

    def create_session(self, mpkt, ports, dissector):
        """
        Check for SYN/ACK on mpkt and create a session
        @param mpkt a MetaPacket object
        @param ports a tuple of ports supported by the dissector
        @param dissector_name the dissector name
        """

        tcpflags = mpkt.get_field('tcp.flags')

        if tcpflags & TH_SYN != 0 and tcpflags & TH_ACK != 0:
            srcport = mpkt.get_field('tcp.sport')

            if srcport in ports:
                log.debug('Creating sessions for dissector %s' % dissector)
                ident = self.create_ident_from_mpkt(mpkt, hash(dissector))

                sess = Session(ident=ident)
                self.put_session(sess)

                return sess

        return None

    def create_ident_from_mpkt(self, mpkt, hashval):
        """
        Create a session object starting from a mpkt instance
        """
        # CHECKME: inet_aton or ascii transformation?
        # we prefer less space allocated so inet_aton
        ident = DissectIdent(inet_aton(mpkt.get_field('ip.src')),
                             inet_aton(mpkt.get_field('ip.dst')),
                             mpkt.get_field('tcp.sport'),
                             mpkt.get_field('tcp.dport'),
                             mpkt.get_field('ip.proto'))
        ident.magic = hashval

        return ident

    def put_session(self, sess):
        """
        Put the session inside the manager
        @param sess a Session object
        """

        self._sessions[sess.ident.magic].append(sess)

    def delete_session(self, sess):
        """
        Delete the session
        """
        self._sessions[sess.ident.magic].remove(sess)

    def get_session(self, ident):
        for sess in self._sessions[ident.magic]:
            if sess.ident == ident:
                return sess

    def lookup_session(self, mpkt, ports, decoder, create_on_fail=False):
        ident = self.create_ident_from_mpkt(mpkt, hash(decoder))
        sess = self.get_session(ident)

        if create_on_fail and not sess:
            sess = Session(ident=ident)
            self.put_session(sess)

        return sess

    # Useful functions

    def is_first_mpkt_from_server(self, mpkt, ports, decoder):
        if mpkt.get_field('tcp.sport') in ports and \
           mpkt.get_field('tcp.flags') & TH_PSH != 0:

            ident = self.create_ident_from_mpkt(mpkt, hash(decoder))
            return self.get_session(ident)