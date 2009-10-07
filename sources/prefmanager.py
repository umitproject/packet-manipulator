#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Abhiram Kasina <abhiram.casina@gmail.com>
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
This module contains various class to load and store preferences to
XML file using SAX parser provided by python
"""

import sys, os, os.path

from umit.pm.gui.core.app import PMApp
from umit.pm.core.i18n import _

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from umit.pm.core.logger import log
from umit.pm.core.const import PM_HOME, PM_PLUGINS_DIR, PLUGINS_DIR, AUDITS_DIR
from umit.pm.core.atoms import Singleton


TYPES = {
    str        : 'str',
    bool       : 'bool',
    dict       : 'dict',
    float      : 'float',
    int        : 'int',
    list       : 'list',
    tuple      : 'tuple'
}

class Option(object):
    def __init__(self, value, default=None):
        self.type = 'str'
        self.converter = str
        self.cbs = []

        for k, v in TYPES.items():
            if isinstance(value, k):
                self.type = v
                self.converter = k
                break

        self._value = self.converter(value)

    def connect(self, callback, call=True):
        self.cbs.append(callback)

        if call:
            callback(self.value)

    def disconnect(self, callback):
        if callback in self.cbs:
            self.cbs.remove(callback)

    def get_value(self):
        assert isinstance(self._value, self.converter)
        return self._value

    def set_value(self, val):
        # Check type?
        if not isinstance(val, self.converter):
            val = self.converter(val)

        for cb in self.cbs:
            # Lock if a callback returns True
            if cb(val):
                log.debug("Ignoring change")
                return

        log.debug("%s = %s" % (self, val))
        self._value = val

    def __repr__(self):
        return "(%s)" % self._value

    value = property(get_value, set_value)

class PreferenceLoader(handler.ContentHandler):
    def __init__(self, outfile):
        self.outfile = outfile
        self.options = {}

    def startElement(self, name, attrs):
        if name in ('bool', 'int', 'float', \
                    'str', 'list', 'tuple'):

            opt_name = None
            opt_value = None

            for attr in attrs.keys():
                if attr == 'id':
                    opt_name = attrs.get(attr)
                if attr == 'value':
                    opt_value = attrs.get(attr)

            try:
                if name == 'bool':
                    if opt_value.lower() == 'true' or opt_value == '1':
                        opt_value = True
                    else:
                        opt_value = False
                elif name == 'int':
                    opt_value = int(opt_value)
                elif name == 'float':
                    opt_value = float(opt_value)
                elif name == 'list':
                    opt_value = opt_value.split(",")
                    opt_value = filter(None, opt_value)
                elif name == 'tuple':
                    opt_value = opt_value.split(",")
                    opt_value = filter(None, opt_value)
                    opt_value = tuple(opt_value)
            except:
                return

            if opt_name != None and opt_value != None:
                self.options[opt_name] = Option(opt_value)

class PreferenceWriter:
    def startElement(self, names, attrs):
        self.depth_idx += 1
        self.writer.characters('  ' * self.depth_idx)
        self.writer.startElement(names, attrs)

    def endElement(self, name):
        self.writer.endElement(name)
        self.writer.characters('\n')
        self.depth_idx -= 1

    def __init__(self, fname, options):
        output = open(fname, 'w')
        self.depth_idx = -1
        self.writer = XMLGenerator(output, 'utf-8')
        self.writer.startDocument()

        self.startElement('PacketManipulator', {}),
        self.writer.characters('\n')

        items = options.items()
        items.sort()

        for key, option in items:

            attr_vals = {
                'id' : key,
                'value' : str(option.value)
            }

            attrs = AttributesImpl(attr_vals)

            self.startElement(str(option.type), attrs)
            self.endElement(str(option.type))

        self.endElement('PacketManipulator')
        self.writer.endDocument()
        output.close()



class MSCPrefManager(Singleton):
    options = {}

    def __init__(self):
        self.fname = os.path.join(PM_HOME, 'msc-prefs.xml')

        try:
            opts = self.load_options()
            self.options.update(self.load_options())
        except Exception, err:
            log.warning('Error reading msc-prefs.xml. Loading default options')

        diff_dict = {}
        for name, opt in self.options.items():
            if not isinstance(opt, Option):
                diff_dict[name] = Option(opt)

        self.options.update(diff_dict)

    def load_options(self):
        handler = PreferenceLoader(sys.stdout)
        parser = make_parser()
        parser.setContentHandler(handler)
        parser.parse(self.fname)

        return handler.options

    def write_options(self):
        writer = PreferenceWriter(self.fname, self.options)

    def __getitem__(self, x):
        return self.options[x]

        