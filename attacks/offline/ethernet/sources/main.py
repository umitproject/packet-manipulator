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
Ethernet protocol decoder
"""

from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *
from PM.Core.NetConst import *

@coroutine
def eth_decoder():
    try:
        while True:
            mpkt = (yield)
            AttackManager().run_decoder(NET_LAYER, mpkt.get_field('eth.type'),
                                        mpkt)
    except GeneratorExit:
        pass

class EthDecoder(Plugin, OfflineAttack):
    def start(self, reader):
        self._decoder = eth_decoder()

    def stop(self):
        pass

    def register_decoders(self):
        AttackManager().add_decoder(LINK_LAYER, IL_TYPE_ETH, self._decoder)

__plugins__ = [EthDecoder]