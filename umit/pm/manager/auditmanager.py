#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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
Audit manager module
"""

import sys
import os.path

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus
from umit.pm.core.auditutils import AuditOperation
from umit.pm.manager.sessionmanager import ConnectionManager
from umit.pm.core.atoms import Singleton, defaultdict, generate_traceback
from umit.pm.core.const import PM_TYPE_STR, PM_TYPE_INT, PM_TYPE_INSTANCE,\
                               PM_HOME
from umit.pm.core.netconst import *

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
        #    if plug.audit_type == -1:
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
    def revupdate(self, new_dict):
        new_dict.update(self._dict)
        self._dict = new_dict

    def __repr__(self):
        return 'Conf: %s -> %s' % (self._name, self._dict)

    name = property(get_name)

###############################################################################
# Implementation
###############################################################################

class AuditManager(Singleton):
    """
    This is a singleton classes that is used to track decoders/dissectors etc.
    It's a singleton class that is used to dispatch packets.
    """
    def __init__(self):
        self._output = None
        # It seems that specifying {} * n doesn't create a new object
        # but instead only create a new pointer to the same object.
        # Here we need separated dict so we should declare them all
        self._decoders = ({}, {}, {}, {}, {}, {}, {}, {})
        self._injectors = ({}, {}, {}, {}, {}, {}, {}, {})
        self._hooks = {
            'pm::received'    : [],
            'pm::handled'     : [],
            'pm::decoded'     : [],
            'pm::filter'      : [],
            'pm::pre-forward' : [],
            'pm::dispatcher'  : [],
        }
        self._configurations = {}

        self.load_configurations()

        self._global_conf = self.register_configuration('global', {
            'debug' : [False, 'Turn out debugging'],
        })

        self._global_cfields = self.register_configuration('global.cfields', {
            'username' : [PM_TYPE_STR, 'Account username'],
            'password' : [PM_TYPE_STR, 'Account password'],
            'banner'   : [PM_TYPE_STR, 'Service banner'],

            'good_checksum' : [PM_TYPE_STR, 'Hex string representation of the '
                               'good checksum for the packet. Set if the packet'
                               ' has a wrong checksum'],
            'reassembled_payload' : [PM_TYPE_STR, 'Used by audits that can '
                                     'treassemble fragments of packets'],
        })

        self.add_decoder(APP_LAYER, PL_DEFAULT, self.__run_dissectors)

    def __run_dissectors(self, mpkt):
        if mpkt.flags & MPKT_DONT_DISSECT:
            return

        # TODO: Here we should add a callback to unset MPKT_IGNORE
        # if the packet is directed to TARGET1 or TARGET2

        self.run_hook_point('pm::handled', mpkt)

        if mpkt.flags & MPKT_IGNORE:
            return

        if mpkt.l4_proto == NL_TYPE_TCP:
            ret = APP_LAYER_TCP
        elif mpkt.l4_proto == NL_TYPE_UDP:
            ret = APP_LAYER_UDP
        else:
            ret = None

        if ret is not None:
            self.run_decoder(ret, mpkt.l4_src, mpkt)
            self.run_decoder(ret, mpkt.l4_dst, mpkt)

        self.run_hook_point('pm::decoded', mpkt)

        mtu = mpkt.context and mpkt.context.get_mtu() or 1500
        max_len = mtu - (mpkt.l2_len + mpkt.l3_len + mpkt.l4_len)

        #log.debug('Max length for the payload is %d' % max_len)

        if mpkt.data_len > max_len:
            mpkt.inject = mpkt.data[max_len:]
            mpkt.inject_len = mpkt.data_len - max_len
            mpkt.inj_delta -= mpkt.data_len - max_len
            mpkt.data_len = max_len

        self.run_hook_point('pm::filter', mpkt)

    # Configurations stuff

    def load_configurations(self):
        log.debug('Loading configurations from audits-conf.xml')

        try:
            handler = ConfigurationsLoader()
            parser = make_parser()
            parser.setContentHandler(handler)
            parser.parse(os.path.join(PM_HOME, 'audits-conf.xml'))

            self._configurations.update(handler.opt_dict)
        except Exception, err:
            log.warning('Error while loading audits-conf.xml. ' \
                        'Using default options')

    def write_configurations(self):
        log.debug('Writing configurations to audits-conf.xml')

        writer = ConfigurationsWriter(os.path.join(PM_HOME, 'audits-conf.xml'),
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
            conf.revupdate(conf_dict)

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
                import umit.pm.gui.core.app
                tab = umit.pm.gui.core.app.PMApp().\
                      main_window.get_tab('StatusTab')
                self._output = tab.status
            self._output.info(out)

    ############################################################################
    # General hooks
    ############################################################################

    def register_hook_point(self, name):
        """
        Register a hook point
        @param name the hook point name
        @return bool True if registered correctly
        """
        if name in self._hooks:
            return False

        self._hooks[name] = []
        return True

    def deregister_hook_point(self, name):
        try:
            del self._hooks[name]
            return True
        except:
            return False

    def add_to_hook_point(self, name, callback, to=-1):
        try:
            if to < 0:
                self._hooks[name].append(callback)
            else:
                self._hooks[name].insert(to, callback)
            return True
        except:
            return False

    def remove_from_hook_point(self, name, callback):
        try:
            self._hooks[name].remove(callback)
            return True
        except:
            return False

    def run_hook_point(self, name, *args, **kwargs):
        idx = 0
        log.debug('Starting hook cascade for %s' % name)
        while name in self._hooks and idx < len(self._hooks[name]):
            callback = self._hooks[name][idx]
            log.debug('Callback %d is %s' % (idx, callback))
            callback(*args, **kwargs)
            idx += 1

    ############################################################################
    # Injectors
    ############################################################################

    def add_injector(self, level, type, injector):
        """
        Add a injector for the given level
        @param level the level where the injector works on
        @param type the type of injector
        @param injector a callable object
        """
        log.debug("Registering injector %s for level %s with type %s" % \
                  (injector, level, type))
        self._injectors[level][type] = injector

    def remove_injector(self, level, type, injector):
        """
        Remove a injector for the given level
        @param level the level where the injector works on
        @param type the type of injector
        @param injector a callable object
        """

        assert self._injectors[level][type], injector
        del self._injectors[level][type]
        return True

    def get_injector(self, level, type):
        try:
            return self._injectors[level][type]
        except:
            return None

    ############################################################################
    # Decoders stuff
    ############################################################################

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

    def remove_decoder(self, level, type, decoder, force=True):
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

    def remove_decoder_hook(self, level, type, decoder_hook, post=0):
        if type not in self._decoders[level]:
            return False

        self._decoders[level][type][post + 1].remove(decoder_hook)
        return True

    def get_decoder(self, level, type):
        try:
            return self._decoders[level][type]
        except:
            #log.debug("No decoder registered for level %s type %s" % (level,
            #                                                          type))
            return None, None, None

    def run_decoder(self, level, type, metapkt):
        ret = None
        while level is not None and type is not None:
            decoder, pre, post = self.get_decoder(level, type)


            if not decoder and not pre and not post:
                return

            #log.debug("Running decoder %s" % decoder)

            for pre_hook in pre:
                pre_hook(metapkt)

            if decoder:
                ret = decoder(metapkt)

            for post_hook in post:
                post_hook(metapkt)

            if decoder and isinstance(ret, tuple):
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
        assert layer in (APP_LAYER_TCP, APP_LAYER_UDP)
        # The dissector is only a special case of a decoder.
        self.add_decoder(layer, port, dissector)

    def remove_dissector(self, layer, port, dissector):
        assert layer in (APP_LAYER_TCP, APP_LAYER_UDP)
        # The dissector is only a special case of a decoder.
        self.remove_decoder(layer, port, dissector)

    # Properties

    def get_global_conf(self): return self._global_conf

    global_conf = property(get_global_conf)

class AuditDispatcher(object):
    def __init__(self, datalink=IL_TYPE_ETH, context=None):
        """
        Create an audit manager to use in conjunction with a PacketProducer
        that feeds the instance with feed() method @see AuditManager.feed.

        @param datalink the datalink to be used. As default we use IL_TYPE_ETH.
                        For more information on that @see pcap_datalink manpage
        @param context an AuditContext or None
        """

        self._datalink = datalink
        self._context = context
        self._conn_manager = ConnectionManager()
        self._main_decoder = AuditManager().get_decoder(LINK_LAYER,
                                                        self._datalink)

    def feed(self, mpkt, *args):
        """
        General purpose procedure.
        Will be used the main_decoder created in the constructor. So if you need
        to have another main_dissector you could change it with the correct
        property.

        @param metapkt a MetaPacket object or None
        """
        if not mpkt:# or not self._main_decoder:
            return

        manager = AuditManager()
        manager.run_hook_point('pm::received', mpkt)

        if not self._context:
            manager.run_decoder(LINK_LAYER, self.datalink, mpkt)
            return

        # Same code of run_decoder.
        # Only executed when there's a context so we can have more granularity
        # over various callbacks

        level = LINK_LAYER
        type = self.datalink
        mpkt.context = self._context

        while level is not None and type is not None:
            decoder, pre, post = manager.get_decoder(level, type)

            if not decoder and not pre and not post:
                break

            #log.debug("Running decoder %s" % decoder)

            for pre_hook in pre:
                pre_hook(mpkt)

            if decoder:
                ret = decoder(mpkt)

            for post_hook in post:
                post_hook(mpkt)

            if decoder and isinstance(ret, tuple):
                # Infinite loop over there :)
                level, type = ret
            else:
                break

        if not mpkt.flags & MPKT_FORWARDED:
            self._conn_manager.parse(mpkt)

            if mpkt.flags & MPKT_FORWARDABLE:
                manager.run_hook_point('pm::pre-forward', mpkt)
                self._context.forward(mpkt)

        mpkt.context = None
        mpkt.data = ''


    def get_main_decoder(self): return self._main_decoder
    def set_main_decoder(self, dec): self._main_decoder = dec

    def get_datalink(self): return self._datalink
    def get_connection_manager(self): return self._conn_manager

    main_decoder = property(get_main_decoder, set_main_decoder)
    datalink = property(get_datalink)

###############################################################################
# Plugin related classes
###############################################################################

class AuditPlugin(object):
    def register_hooks(self): pass
    def register_decoders(self): pass
    def register_dissectors(self): pass
    def register_filters(self): pass

class PassiveAudit(AuditPlugin):
    # TODO: passive related methods goes here
    pass

# TODO: the code related to gtk and PMApp should be moved outside this module
class ActiveAudit(AuditPlugin):
    """
    ActiveAudits could require user inputs.
    The dialog to introduce inputs is created automatically by PacketManipulator
    starting by the inputs element contained in Manifest.xml file.

    On load the plugin could user add_menu_entry() function to create a menu
    entry under Audits menu in MainWindow. If the user will click on that
    entry PM will create an input dialog and if the user press OK the inputs
    will be passed as dict in execute_audit() callback that the plugin should
    overload.

    About executing the audit you could use an Operation if the audit should
    run in a continuous mode or is long job.

    If your plugin doesn't need any type of inputs you could set __inputs__ to
    an empty tuple ().

    __inputs__ = (
      ('gateway', ('127.0.0.1', 'The Gateway IP address or hostname')),
      ('port', (80, 'The HTTP port')),
    )
    """

    __inputs__ = ()

    def remove_menu_entry(self, item):
        import umit.pm.gui.core.app

        return umit.pm.gui.core.app.PMApp().main_window.deregister_audit_item(
            item
        )

    def remove_mitm_attack(self, item):
        import umit.pm.gui.core.app

        return umit.pm.gui.core.app.PMApp().main_window.\
               deregister_audit_mitm_item(item)

    def add_menu_entry(self, name, lbl, tooltip, stock):
        """
        Add a MenuEntry to the MainWindow of PM.
        @param name the name for the gtk.Action
        @param label the label to use
        @param tooltip a tooltip for the menuitem
        @param stock a stock-id to use
        """

        log.debug('Creating a new menu entry with \'%s\' as label' % lbl)

        import umit.pm.gui.core.app

        return umit.pm.gui.core.app.PMApp().main_window.register_audit_item(
            name, lbl, tooltip, stock, self.on_input_request
        )

    def add_mitm_attack(self, name, lbl, tooltip, stock):
        log.debug('Registering new MITM menu entry for \'%s\' attack' % lbl)

        import umit.pm.gui.core.app

        return umit.pm.gui.core.app.PMApp().main_window.\
               register_audit_mitm_item(name, lbl, tooltip, stock,
                                        self.on_input_request)

    def execute_audit(self, audit_sess, input_dct=None):
        """
        Overload me.
        @param audit_sess an AuditSession object.
        @param input_dict a dict containing audit inputs.
        @return a bool with True if the audit is executed or False
        """
        raise Exception('This method must be overloaded.')

    def on_input_request(self, action):
        import gtk
        import umit.pm.gui.core.app

        if not self.__inputs__:
            audit_sess = ServiceBus().call('pm.sessions',
                                           'get_current_session')

            self.__start_audit(audit_sess, {})
            return

        dialog = gtk.Dialog(_('Inputs for %s - PacketManipulator') % \
                            self.__class__.__name__,
                            umit.pm.gui.core.app.PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                             gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        tbl = gtk.Table(2, 1, False)

        tbl.set_border_width(4)
        tbl.set_col_spacings(4)
        tbl.set_row_spacings(4)

        dialog.vbox.pack_start(tbl)

        idx = 0

        for txt, (opt_val, desc) in self.__inputs__:
            lbl = gtk.Label('')
            lbl.set_alignment(.0, .5)
            lbl.set_markup('<b>%s:</b>' % txt.capitalize())

            if isinstance(opt_val, bool):
                widget = gtk.ToggleButton('')
                widget.set_active(opt_val)

                widget.get_child().set_text(widget.get_active() \
                                            and _('Enabled') \
                                            or _('Disabled'))

                widget.connect('toggled', lambda w: w.get_child().set_text( \
                    w.get_active() and _('Enabled') or _('Disabled')))

            elif isinstance(opt_val, str):
                widget = gtk.Entry()
                widget.set_text(opt_val)

            elif isinstance(opt_val, int):
                widget = gtk.SpinButton(gtk.Adjustment(opt_val, -sys.maxint,
                                                       sys.maxint, 1, 10),
                                        digits=0)

            elif isinstance(opt_val, float):
                widget = gtk.SpinButton(gtk.Adjustment(opt_val, -sys.maxint,
                                                       sys.maxint, 1, 10),
                                        digits=4)

            lbl.props.has_tooltip = True
            widget.props.has_tooltip = True

            lbl.set_tooltip_markup(desc)
            widget.set_tooltip_markup(desc)
            widget.set_name(txt)

            tbl.attach(lbl, 0, 1, idx, idx + 1, gtk.FILL, gtk.FILL)
            tbl.attach(widget, 1, 2, idx, idx + 1, yoptions=gtk.FILL)
            idx += 1

        tbl.show_all()
        dialog.connect('response', self.__on_dialog_response)
        dialog.show()

    def __start_audit(self, audit_sess, inp_dict):
        ret = self.execute_audit(audit_sess, inp_dict)

        if isinstance(ret, AuditOperation):
            log.debug('Nice. This audit implements AuditOperation')
            audit_sess.audit_page.tree.append_operation(ret)

    def __on_dialog_response(self, dialog, rid):
        import gtk
        import umit.pm.gui.core.app

        if rid != gtk.RESPONSE_ACCEPT:
            dialog.hide()
            dialog.destroy()
            return

        table = dialog.vbox.get_children()[0]

        assert isinstance(table, gtk.Table)

        inp_dict = {}

        for widget in table:
            if isinstance(widget, gtk.Label):
                continue

            if isinstance(widget, gtk.SpinButton):
                if widget.get_digits() == 0:
                    value = widget.get_value_as_int()
                else:
                    value = widget.get_value()

            elif isinstance(widget, gtk.ToggleButton):
                value = widget.get_active()
            else:
                value = widget.get_text()

            inp_dict[widget.get_name()] = value

        dialog.hide()
        dialog.destroy()

        audit_sess = ServiceBus().call('pm.sessions', 'get_current_session')

        self.__start_audit(audit_sess, inp_dict)

###############################################################################
# Testing classes
###############################################################################

class AuditTester(object):
    """
    Simple test class to test your decoders/dissectors.
    Simple use:
        test = AuditTester('my-dump.pcap')
        test.manager.add_decoder(...)
        test.start() # Threaded
        test.join()
    """
    def __init__(self, pcapfile, datalink=IL_TYPE_ETH):
        """
        Launch an audit manager against a pcap file using the selected backend
        """
        import umit.pm.backend

        self.dispatcher = AuditDispatcher(datalink)
        self.ctx = umit.pm.backend.SniffContext(None, capfile=pcapfile, capmethod=1,
                                                callback=self.dispatcher.feed,
                                                audits=False)

    def start(self):
        log.debug('Starting context for test')
        self.ctx.start()

    def join(self):
        log.debug('Waiting for test thread termination')
        # We have to use that for the moment since join in SniffContext is dummy
        self.ctx.thread.join()
