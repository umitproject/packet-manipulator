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

import os.path

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from PM.Core.Logger import log
from PM.Core.Atoms import Singleton, defaultdict, generate_traceback
from PM.Core.Const import PM_TYPE_STR, PM_HOME
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

class ConfigurationsLoader(handler.ContentHandler):
    def __init__(self):
        self.data = ''
        self.parse_pass = -1

        self.opt_id = None
        self.opt_desc = None
        self.configuration = None
        self.opt_dict = {}

        self.trans = {
            'bool'  : lambda x: x == '1',
            'int'   : int,
            'float' : float,
            'str'   : str,
        }

    def startElement(self, name, attrs):
        if name == 'configurations' and self.parse_pass == -1:
            self.parse_pass = 0
        elif name == 'configuration' and self.parse_pass == 0:
            self.parse_pass = 1
            name = attrs.get('name')

            if name:
                self.configuration = Configuration(name)

        elif name in ('bool', 'str', 'int', 'float') and self.parse_pass == 1:
            self.opt_id = attrs.get('id')
            self.opt_desc = attrs.get('description') or None

            self.parse_pass = 2
            self.data = ''

    def characters(self, ch):
        if self.parse_pass == 2:
            self.data += ch

    def endElement(self, name):
        if name == 'configurations' and self.parse_pass == 0:
            self.parse_pass = -1
        elif name == 'configuration' and self.parse_pass == 1:
            if self.configuration:
                self.opt_dict[self.configuration.get_name()] = \
                    self.configuration
                self.configuration = None

            self.parse_pass = 0
        elif name in ('bool', 'str', 'int', 'float') and self.parse_pass == 2:
            try:
                if self.configuration:
                    self.configuration.update({self.opt_id : [
                        self.trans[name](self.data),
                        self.opt_desc]}
                    )
            finally:
                self.data = ''
                self.opt_id = None
                self.opt_desc = None
                self.parse_pass = 1

class ConfigurationsWriter(object):
    def startElement(self, names, attrs):
        self.depth_idx += 1
        self.writer.characters('  ' * self.depth_idx)
        self.writer.startElement(names, attrs)

    def endElement(self, name):
        self.writer.endElement(name)
        self.writer.characters('\n')
        self.depth_idx -= 1

    def __init__(self, fname, options):
        # The commented code here is to enable write to file options with
        # value same as the default. IMHO it's useless so I've commented it

        #from PM.Gui.Plugins.Engine import PluginEngine

        #orig_dict = {}

        #for plug in PluginEngine().available_plugins:
        #    if plug.attack_type == -1:
        #        continue

        #    for conf_name, conf_dict in plug.configurations:
        #        orig_dict[conf_name] = conf_dict

        output = open(fname, 'w')
        self.depth_idx = -1
        self.writer = XMLGenerator(output, 'utf-8')
        self.writer.startDocument()

        self.startElement('configurations', {}),
        self.writer.characters('\n')

        items = options.keys()
        items.sort()

        trans = {
            bool  : 'bool',
            int   : 'int',
            float : 'float',
            str   : 'str'
        }

        for key in items:
            self.startElement('configuration', AttributesImpl({'name' : key}))
            self.writer.characters('\n')

            opts = options[key].items()
            opts.sort()

            for opt_id, (opt_val, opt_desc) in opts:
                #if key in orig_dict and opt_id in orig_dict[key] and \
                #   orig_dict[key][opt_id][0] == opt_val:
                #    continue

                try:
                    self.startElement(trans[type(opt_val)],
                                      AttributesImpl({
                                          'id' : opt_id,
                                          'description' : opt_desc
                                      }))

                    if isinstance(opt_val, bool):
                        self.writer.characters(opt_val and '1' or '0')
                    else:
                        self.writer.characters(str(opt_val))

                    self.endElement(trans[type(opt_val)])
                except:
                    continue

            self.writer.characters('  ' * self.depth_idx)
            self.endElement('configuration')

        self.endElement('configurations')
        self.writer.endDocument()
        output.close()

class Configuration(object):
    def __init__(self, name, odict=None):
        """
        @param name a string representing the Configuration
        @param odict options dictionary {'key' : [value, 'description' or None]}
        """
        self._name = name

        if not odict:
            self._dict = {}
        else:
            self._dict = odict

    def __getitem__(self, x):
        return self._dict[x][0]

    def __setitem__(self, x, value):
        tup = self._dict[x]

        if isinstance(value, type(tup[0])):
            self._dict[x] = (value, tup[1])
        else:
            raise Exception('value has different type')

    def get_name(self): return self._name
    def get_option(self, x):
        """
        @return a tuple (opt_value, opt_desc)
        """
        return self._dict[x]

    def get_description(self, x):
        return self._dict[x][1]

    def keys(self): return self._dict.keys()
    def items(self): return self._dict.items()
    def update(self, new_dict): self._dict.update(new_dict)

    def __repr__(self):
        return 'Conf: %s -> %s' % (self._name, self._dict)

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
        self._decoders = ({}, {}, {}, {}, {}, {}, {})
        self._configurations = {}

        self.load_configurations()

        self._global_conf = self.register_configuration('global', {
            'debug' : [False, 'Turn out debugging']
        })

        self._global_cfields = self.register_configuration('global.cfields', {
            'username' : (PM_TYPE_STR, 'Account username'),
            'password' : (PM_TYPE_STR, 'Account password'),
            'banner'   : (PM_TYPE_STR, 'Service banner'),

            'good_checksum' : (PM_TYPE_STR, 'Hex string representation of the '
                               'good checksum for the packet. Set if the packet'
                               ' has a wrong checksum'),
            'reassembled_payload' : (PM_TYPE_STR, 'Used by attacks that can '
                                     'treassemble fragments of packets'),
        })

    # Configurations stuff

    def load_configurations(self):
        log.debug('Loading configurations from attacks-conf.xml')

        try:
            handler = ConfigurationsLoader()
            parser = make_parser()
            parser.setContentHandler(handler)
            parser.parse(os.path.join(PM_HOME, 'attacks-conf.xml'))

            self._configurations.update(handler.opt_dict)
        except Exception, err:
            log.warning('Error while loading attacks-conf.xml')
            log.warning(generate_traceback())

    def write_configurations(self):
        log.debug('Writing configurations to attacks-conf.xml')

        writer = ConfigurationsWriter(os.path.join(PM_HOME, 'attacks-conf.xml'),
                                      self._configurations)

    def register_configuration(self, conf_name, conf_dict):
        """
        Register a configuration
        @param conf_name a str for configuration root element
        @param conf_dict a dictionary
        @see Configuration()
        """

        if conf_name not in self._configurations:
            conf = Configuration(conf_name, conf_dict)
            self._configurations[conf_name] = conf

            log.debug('Configuration %s registered.' % conf_name)
        else:
            conf = self._configurations[conf_name]
            conf.update(conf_dict)

            log.debug('Configuration %s updated.' % conf_name)

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

    def remove_decoder(self, level, type, decoder, force=False):
        """
        Remove a decoder for the given level
        @param level the level where the decoder works on
        @param type the type of decoder
        @param decoder a callable object
        @param force if force is True and post or pre hooks are set
               remove anyway
        """

        tup = self._decoders[level][type]

        if any(tup[1:]) and not force:
                return False

        del self._decoders[level][type]
        return True

    def add_decoder_hook(self, level, type, decoder_hook, post=0):
        if type not in self._decoders[level]:
            self._decoders[level][type] = (None, [], [])

        self._decoders[level][type][post + 1].append(decoder_hook)

    def get_decoder(self, level, type):
        try:
            return self._decoders[level][type]
        except:
            #log.debug("No decoder registered for level %s type %s" % (level,
            #                                                          type))
            return None, None, None

    def run_decoder(self, level, type, metapkt):
        while level and type:
            decoder, pre, post = self.get_decoder(level, type)

            if not decoder and not pre and not post:
                return

            #log.debug("Running decoder %s" % decoder)

            for pre_hook in pre:
                pre_hook(metapkt)

            if decoder:
                ret = decoder(metapkt)
            else:
                ret = None

            for post_hook in post:
                post_hook(metapkt)

            if isinstance(ret, tuple) and ret[0] != NEED_FRAGMENT:
                # Infinite loop over there :)
                level, type = ret
            else:
                return ret

    def add_dissector(self, layer, port, dissector):
        """
        Add a dissector to the chain
        @param layer APP_LAYER_TCP or APP_LAYER_UDP
        @param port the remote port
        @param dissector a callable
        """
        # The dissector is only a special case of a decoder.
        self.add_decoder(APP_LAYER_TCP, port, dissector)

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