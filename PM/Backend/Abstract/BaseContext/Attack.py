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

from Timed import TimedContext
from PM.Backend.Abstract.Context import register_attack_context

class BaseAttackContext(TimedContext):
    "A context representing an attack"

    has_stop = True
    has_pause = False
    has_restart = False

    def __init__(self, dev1, dev2=None, bpf_filter=None):
        """
        @param dev1 the first interface to sniff on
        @param dev2 the second interface to sniff on (used in bridged sniffing)
               or None
        @param bpf_filter pcap filter to apply to the inputs interfaces
        @return a BaseAttackContext
        """

        self._socket1 = None
        self._socket2 = None

    def _stop(self):
        pass

    def get_socket1(self):
        return self._socket1

    def get_socket2(self):
        return self._socket2

    socket1 = property(get_socket1)
    socket2 = property(get_socket2)

AttackContext = register_attack_context(BaseAttackContext)