#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from os.path import exists
from ConfigParser import ConfigParser, DEFAULTSECT
from ConfigParser import NoOptionError, NoSectionError
from umitCore.UmitLogging import log

class UmitConfigParser(ConfigParser):
    filenames = None
    fp = None
    
    def __init__(self, *args):
        ConfigParser.__init__(self, *args)

    def set(self, section, option, value):
        if not self.has_section(section):
            self.add_section(section)
        
        ConfigParser.set(self, section, option, value)
        self.save_changes()

    def read(self, filename):
        log.debug(">>> Trying to parse: %s" % filename)

        self.filenames = ConfigParser.read(self, filename)
        return self.filenames

    def readfp(self, fp, filename=None):
        ConfigParser.readfp(self, fp, filename)
        self.fp = fp
        self.filenames = filename

    def save_changes(self):
        if self.filenames:
            filename = None
            if isinstance(self.filenames, basestring):
                filename = self.filenames
            elif isinstance(self.filenames, list) and len(self.filenames) == 1:
                filename = self.filenames[0]
            else:
                raise Exception("Wrong filename %s" % self.filenames)
            self.write(open(filename, 'w'))
        elif self.fp:
            self.write(self.fp)

    def write(self, fp):
        '''Write alphabetically sorted config files'''
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            
            items = self._defaults.items()
            items.sort()
            
            for (key, value) in items:
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")

        sects = self._sections.keys()
        sects.sort()
        
        for section in sects:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                if key != "__name__":
                    fp.write("%s = %s\n" %
                             (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")

def test_umit_conf_content(filename):
    parser = ConfigParser()
    parser.read(filename)

    # Paths section
    section = "paths"
    assert exists(get_or_false(parser, section, "config_file") or "")
    assert exists(get_or_false(parser, section, "umit_icon") or "")
    assert exists(get_or_false(parser, section, "locale_dir") or "")
    assert exists(get_or_false(parser, section, "misc_dir") or "")
    assert exists(get_or_false(parser, section, "icons_dir") or "")
    assert exists(get_or_false(parser, section, "pixmaps_dir") or "")
    assert exists(get_or_false(parser, section, "config_dir") or "")
    assert exists(get_or_false(parser, section, "docs_dir") or "")
    assert get_or_false(parser, section, "nmap_command_path")


def get_or_false(parser, section, option):
    try:
        result = parser.get(section, option)
        return result
    except NoOptionError:
        return False
    except NoSectionError:
        return False
