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
Attack manager module
"""

import PM.Backend as Backend

from PM.Core.Logger import log
from PM.Core.Atoms import Singleton, defaultdict
from PM.Core.NetConst import *

###############################################################################
# Decorators
###############################################################################

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

###############################################################################
# Implementation
###############################################################################

class Decoder(object):
    """
    Decoder objects should respect this scheme and use this as a model.
    If you prefer more speed up you could use directly a coroutine with yield.

    @see
    """
    def send(self, metapkt):
        raise Exception("Not implemented")

class AttackManager(Singleton):
    """
    This is a singleton classes that is used to track decoders/dissectors etc.
    It's a singleton class that is used to dispatch packets.
    """
    def __init__(self):
        self._decoders = ({}, ) * 5

    # Decoders stuff

    def add_decoder(self, level, type, decoder):
        """
        Add a decoder for the given level
        @param level the level where the decoder works on
        @param type the type of decoder
        @param decoder a Decoder object
        """
        log.debug("Registering dissector %s for level %s with type %s" % \
                  (decoder, level, type))
        self._decoders[level][type] = decoder

    def get_decoder(self, level, type):
        try:
            return self._decoders[level][type]
        except:
            log.debug("No decoder registered for level %s type %s" % (level,
                                                                      type))
            return None

    def run_decoder(self, level, type, metapkt):
        decoder = self.get_decoder(level, type)

        if decoder:
            log.debug("Running decoder %s" % decoder)
            decoder.send(metapkt)

    def add_dissector(self):
        pass

    def add_filter(self):
        pass

    def add_injector(self):
        pass

class AttackDispatcher(object):
    def __init__(self, datalink=IL_TYPE_ETH):
        """
        Create an attack manager to use in conjunction with a PacketProducer
        that feeds the instance with feed() method @see AttackManager.feed.

        @param datalink the datalink to be used. As default we use IL_TYPE_ETH.
                        For more information on that @see pcap_datalink manpage
        """
        self._datalink = datalink
        self._main_decoder = AttackManager().get_decoder(LINK_LAYER,
                                                         self._datalink)

    def feed(self, metapkt, *args):
        """
        General purpose procedure.
        Will be used the main_decoder created in the constructor. So if you need
        to have another main_dissector you could change it with the correct
        property.

        @param metapkt a MetaPacket object or None
        """
        if not metapkt or not self._main_decoder:
            return

        assert isinstance(metapkt, Backend.MetaPacket)
        AttackManager().run_decoder(LINK_LAYER, metapkt.get_datalink(), metapkt)

    def get_main_decoder(self): return self._main_decoder
    def set_main_decoder(self, dec): self._main_decoder = dec

    def get_datalink(self): return self._datalink

    main_decoder = property(get_main_decoder, set_main_decoder)
    datalink = property(get_datalink)

###############################################################################
# Plugin related classes
###############################################################################

class AttackPlugin(object):
    def register_decoders(self): pass
    def register_dissectors(self): pass
    def register_filters(self): pass

class OfflineAttack(AttackPlugin):
    # TODO: offline related methods goes here
    pass

class OnlineAttack(AttackPlugin):
    # TODO: online related methods goes here
    pass

###############################################################################
# Testing classes
###############################################################################

class AttackTester(object):
    """
    Simple test class to test your decoders/dissectors.
    Simple use:
        test = AttackTester('my-dump.pcap')
        test.manager.add_decoder(...)
        test.start() # Threaded
        test.join()
    """
    def __init__(self, pcapfile):
        """
        Launch an attack manager against a pcap file using the selected backend
        """
        self.dispatcher = AttackDispatcher()
        self.ctx = Backend.SniffContext(None, capfile=pcapfile, capmethod=1,
                                        callback=self.dispatcher.feed)

    def start(self):
        log.debug('Starting context for test')
        self.ctx.start()

    def join(self):
        log.debug('Waiting for test thread termination')
        # We have to use that for the moment since join in SniffContext is dummy
        self.ctx.thread.join()