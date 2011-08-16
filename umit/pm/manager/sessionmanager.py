#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010 Adriano Monteiro Marques
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

import time

from umit.pm.core.logger import log
from umit.pm.core.atoms import Singleton, defaultdict
from umit.pm.core.netconst import *

class DissectIdent(object):
    magic = None

    def __init__(self, l3src, l3dst, l4src, l4dst):
        self.l3_src = l3src
        self.l3_dst = l3dst
        self.l4_src = l4src
        self.l4_dst = l4dst

    def __eq__(self, other):
        if self.magic != other.magic:
            return False

        if self.l3_src == other.l3_src and \
           self.l3_dst == other.l3_dst and \
           self.l4_src == other.l4_src and \
           self.l4_dst == other.l4_dst:
            return True

        if self.l3_src == other.l3_dst and \
           self.l3_dst == other.l3_src and \
           self.l4_src == other.l4_dst and \
           self.l4_dst == other.l4_src:
            return True

        return False

    @classmethod
    def mkhash(self, ident):
        return hash(ident.l3_src) ^ hash(ident.l3_dst) ^ \
               ident.l4_src ^ ident.l4_dst

    @classmethod
    def create(self, mpkt):
        return TCPIdent(mpkt.l3_src, mpkt.l3_dst,
                        mpkt.l4_src, mpkt.l4_dst)

class TCPIdent(DissectIdent):
    magic = NL_TYPE_TCP

INJ_FIN = 1
INJ_FWD = 2

class TCPStatus(object):
    def __init__(self):
        self.last_seq = 0
        self.last_ack = 0
        self.seq_adj = 0
        self.injectable = 0

STATELESS_IP_MAGIC = 0x0304e77e

class IPIdent(object):
    magic = LL_TYPE_IP

    def __init__(self, l3src):
        self.l3_src = l3src

    def __eq__(self, other):
        if self.magic == other.magic and \
           self.l3_src == other.l3_src:
            return True
        return False

    @classmethod
    def create(self, mpkt):
        return IPIdent(mpkt.l3_src)

    @classmethod
    def mkhash(self, ident):
        return hash(ident.l3_src)

class IPStatus(object):
    def __init__(self):
        self.last_id = 0
        self.id_adj = 0

class Session(object):
    def __init__(self, ident):
        self.ident = ident
        self.data = None
        self.prev = None

    def __str__(self):
        return "%s -> %s" % (str(self.prev), str(self.ident))

class SessionManager(Singleton):
    """
    The session manager is a singleton class.
    """

    def __init__(self):
        self._sessions = defaultdict(dict)

    # Dissectors methods

    def create_session_on_sack(self, mpkt, ports, dissector):
        """
        Check for SYN/ACK on mpkt and create a session
        @param mpkt a MetaPacket object
        @param ports a tuple of ports supported by the dissector
        @param dissector_name the dissector name
        """

        tcpflags = mpkt.l4_flags

        if tcpflags & TH_SYN != 0 and tcpflags & TH_ACK != 0 and \
           mpkt.l4_src in ports:

            log.debug('Creating sessions for dissector %s' % dissector)
            ident = self.create_dissect_ident(mpkt, dissector)

            sess = Session(ident)
            self.put_session(sess)

            return sess

        return None

    def create_dissect_ident(self, mpkt, magic):
        """
        Create a session object starting from a mpkt instance
        """
        ident = DissectIdent.create(mpkt)
        ident.magic = magic

        return ident

    def lookup_session(self, mpkt, ports, decoder, create_on_fail=False):
        ident = self.create_dissect_ident(mpkt, decoder)
        sess = self.get_session(ident)

        if create_on_fail and not sess:
            sess = Session(ident)
            self.put_session(sess)

        return sess

    def is_first_pkt_from_server(self, mpkt, ports, decoder):
        if mpkt.l4_src in ports and \
           mpkt.l4_flags & TH_PSH != 0:

            return self.get_session(self.create_dissect_ident(mpkt, decoder))

    # Standard methods

    def put_session(self, sess):
        """
        Put the session inside the manager
        @param sess a Session object
        """
        hv = sess.ident.mkhash(sess.ident)
        sessions = self._sessions[sess.ident.magic]

        try:
            sessions[hv].append(sess)
        except:
            sessions[hv] = [sess]

    def delete_session(self, sess):
        """
        Delete the session
        """
        hv = sess.ident.mkhash(sess.ident)
        sessions = self._sessions[sess.ident.magic]

        sessions[hv].remove(sess)

        if not sessions[hv]:
            del sessions[hv]

    def get_session(self, ident):
        hv = ident.mkhash(ident)

        try:
            sessions = self._sessions[ident.magic][hv]

            for sess in sessions:
                if sess.ident == ident:
                    return sess
        except:
            return None

class ConnectionManager(object):
    """
    This class will track connections
    """
    def __init__(self, conn_idle=5, conn_timeout=300):
        self.conn_list = []
        self.connections = defaultdict(list)
        self.conn_idle = conn_idle
        self.conn_timeout = conn_timeout

    def parse(self, mpkt):
        if not mpkt.l4_src or not mpkt.l4_dst:
            return

        log.debug("Parsing new mpkt")
        hv, conn = self.search(mpkt)

        if conn:
            self.update(conn, mpkt)
        else:
            self.add(mpkt, hv)

    @classmethod
    def mkhash(cls, mpkt):
        return hash(mpkt.l3_src) ^ hash(mpkt.l3_dst) ^ \
               hash(mpkt.l4_src ^ mpkt.l4_dst)       ^ \
               hash(mpkt.l4_proto)

    def search(self, mpkt):
        hv = self.mkhash(mpkt)
        for conn in self.connections.get(hv, []):
            if conn.match(mpkt):
                return hv, conn
        return hv, None

    def add(self, mpkt, hv):
        conn = Connection(mpkt)

        log.debug("Adding new connection %s" % conn)

        self.connections[hv].append(conn)
        self.update(conn, mpkt)
        self.conn_list.append(conn)

    def update(self, conn, mpkt):
        log.debug("Updating connection %s" % conn)

        conn.ts = time.time()

        if mpkt.l4_flags & TH_SYN:
            conn.status = CN_OPENING
        elif mpkt.l4_flags & TH_FIN:
            conn.status = CN_CLOSING
        elif mpkt.l4_flags & TH_ACK:
            if conn.status == CN_OPENING:
                conn.status = CN_OPEN
            elif conn.status == CN_CLOSING:
                conn.status = CN_CLOSED

        if mpkt.l4_flags & TH_PSH:
            conn.status = CN_ACTIVE

        if mpkt.l4_flags & TH_RST:
            conn.status = CN_KILLED

        conn.add_buf(mpkt)

        if mpkt.l4_proto == NL_TYPE_UDP:
            conn.status = CN_ACTIVE

        if mpkt.flags & MPKT_MODIFIED or mpkt.flags & MPKT_DROPPED:
            conn.flags |= CN_MODIFIED

    def cleaner(self):
        """
        Start this function in a external thread every tot sec
        to collect garbage.
        """

        ts = time.time()

        idx = 0
        while idx < len(self.conn_list):
            conn = self.conn_list[idx]

            if conn.flags & CN_VIEWING:
                continue

            diff = ts - conn.ts

            if conn.status == CN_ACTIVE and \
               diff >= self.conn_idle:

                conn.status = CN_IDLE

            if diff >= self.conn_timeout:
                self.delete(conn)
                continue

            idx += 1

    def delete(self, conn):
        self.conn_list.remove(conn)
        self.connections[Connection.mkhash(conn)].remove(conn)

class Connection(object):
    def __init__(self, mpkt):
        self.l2_addr1 = mpkt.l2_src
        self.l2_addr2 = mpkt.l2_dst

        self.l3_addr1 = mpkt.l3_src
        self.l3_addr2 = mpkt.l3_dst

        self.l4_addr1 = mpkt.l4_src
        self.l4_addr2 = mpkt.l4_dst
        self.l4_proto = mpkt.l4_proto

        self.buffers = []
        self.xferred = 0
        self.flags = 0
        self.status = 0
        self.ts = 0

    @classmethod
    def mkhash(cls, obj):
        return hash(obj.l3_addr1) ^ hash(obj.l3_addr2) ^ \
               hash(obj.l4_addr1 ^ obj.l4_addr2)       ^ \
               hash(obj.l4_proto)

    def match(self, mpkt):
        if mpkt.l4_proto != self.l4_proto:
            return False

        if self.l3_addr1 == mpkt.l3_src and \
           self.l3_addr2 == mpkt.l3_dst and \
           self.l4_addr1 == mpkt.l4_src and \
           self.l4_addr2 == mpkt.l4_dst:
            return True

        if self.l3_addr1 == mpkt.l3_dst and \
           self.l3_addr2 == mpkt.l3_src and \
           self.l4_addr1 == mpkt.l4_dst and \
           self.l4_addr2 == mpkt.l4_src:
            return True

        return False

    def add_buf(self, mpkt):
        if mpkt.data:
            self.xferred += len(mpkt.data)

            if len(self.buffers) > 40:
                log.debug('Removing old buffers')
                self.buffers = []

            if mpkt.l4_dst == self.l4_addr2:
                self.buffers.append((1, mpkt.data))
            else:
                self.buffers.append((0, mpkt.data))

    def __str__(self):
        return "%d - %s:%d <-> %s:%d" % (
            self.l4_proto,
            self.l3_addr1, self.l4_addr1,
            self.l3_addr2, self.l4_addr2)
