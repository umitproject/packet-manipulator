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
# Configurations
###############################################################################

class Configuration(object):
    def __init__(self, name):
        self._name = name
        self._dict = {}

    def register_option(self, opt_name, def_value, opt_type):
        assert isinstance(opt_type, type), "opt_type should be a type"
        assert isinstance(opt_name, basestring), "opt_name should be a string"
        assert isinstance(def_value, opt_type), "def_value and should be of " \
                                                 "the same type"

        self._dict[opt_name] = (def_value, def_value, opt_type)

    def __getitem__(self, x):
        return self._dict[x][0]

    def __setitem__(self, x, value):
        tup = self._dict[x]

        if isinstance(value, tup[2]):
            self._dict[x] = (value, tup[1], tup[2])
        else:
            raise Exception('value has different type')

    def get_name(self): return self._name

    name = property(get_name)
###############################################################################
# Implementation
###############################################################################

class AttackManager(Singleton):
    """
    This is a singleton classes that is used to track decoders/dissectors etc.
    It's a singleton class that is used to dispatch packets.
    """
    def __init__(self):
        self._output = None
        # It seems that specifying {} * n doesn't create a new object
        # but instead only create a new pointer to the same object.
        # Here we need separated dict so we should declare them all
        self._decoders = ({}, {}, {}, {}, {})

        self._configurations = {}

        self._global_conf = self.register_configuration('global')
        self._global_conf.register_option('debug', False, bool)

    # Configurations stuff

    def register_configuration(self, conf_name):
        """
        Register a configuration
        @param conf_name a str for configuration root element
        """
        if conf_name in self._configurations:
            raise Exception('Configuration named %s already exists' % conf_name)

        conf = Configuration(conf_name)
        self._configurations[conf_name] = conf

        log.debug('Configuration %s registered.' % conf_name)

        return conf

    def get_configuration(self, conf_name):
        return self._configurations[conf_name]

    def user_msg(self, msg, severity=5, facility=None):
        """
        @param msg the message to show to the user
        @param severity 0 for emerg
                        1 for alert
                        2 for crit
                        3 for err
                        4 for warning
                        5 for notice
                        6 for info
                        7 for debug
                        8 for none
        @param facility a str representing a facility
        """
        trans = ('emerg', 'alert', 'crit', 'err', 'warn', 'notice', 'info',
                 'debug', 'none')

        if facility:
            out = '%s.%s %s' % (facility, trans[severity], msg)
        else:
            out = '%s %s' % (trans[severity], msg)

        if self._global_conf['debug']:
            print out
        else:
            if not self._output:
                import PM.Gui.Core.App
                tab = PM.Gui.Core.App.PMApp().main_window.get_tab('StatusTab')
                self._output = tab.status
            else:
                self._output.info(out)

    # Decoders stuff

    def add_decoder(self, level, type, decoder):
        """
        Add a decoder for the given level
        @param level the level where the decoder works on
        @param type the type of decoder
        @param decoder a callable object
        """
        log.debug("Registering dissector %s for level %s with type %s" % \
                  (decoder, level, type))
        self._decoders[level][type] = (decoder, [], [])

    def add_decoder_hook(self, level, type, decoder_hook, post=0):
        self._decoders[level][type][post + 1].append(decoder_hook)

    def get_decoder(self, level, type):
        try:
            return self._decoders[level][type]
        except:
            log.debug("No decoder registered for level %s type %s" % (level,
                                                                      type))
            return None, None, None

    def run_decoder(self, level, type, metapkt):
        while level and type:
            decoder, pre, post = self.get_decoder(level, type)

            if not decoder:
                return

            log.debug("Running decoder %s" % decoder)

            for pre_hook in pre:
                pre_hook(metapkt)

            ret = decoder(metapkt)

            for post_hook in post:
                post_hook(metapkt)

            if ret:
                # Infinite loop over there :)
                level, type = ret
            else:
                return

    def add_dissector(self):
        pass

    def add_filter(self):
        pass

    def add_injector(self):
        pass

    # Properties

    def get_global_conf(self): return self._global_conf

    global_conf = property(get_global_conf)

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

        #assert isinstance(metapkt, Backend.MetaPacket)
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
    def register_options(self): pass
    def register_hooks(self): pass
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
        import PM.Backend

        self.dispatcher = AttackDispatcher()
        self.ctx = PM.Backend.SniffContext(None, capfile=pcapfile, capmethod=1,
                                           callback=self.dispatcher.feed,
                                           attacks=False)

    def start(self):
        log.debug('Starting context for test')
        self.ctx.start()

    def join(self):
        log.debug('Waiting for test thread termination')
        # We have to use that for the moment since join in SniffContext is dummy
        self.ctx.thread.join()