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

import os
import os.path

from fnmatch import fnmatch
from zipfile import ZipFile, BadZipfile, ZIP_DEFLATED
from xml.dom.minidom import parseString, getDOMImplementation
from tempfile import mktemp

# Needs testing
from PM.Gui.Core.Icons import get_pixbuf
from PM.Gui.Plugins.Atoms import StringFile
from PM.Gui.Plugins.Parser import Parser

from PM.Core.Const import PM_PLUGINS_TEMP_DIR

from PM.Core.Logger import log

# For setup functionality
from distutils.dist import Distribution

from distutils.core import setup as dist_setup
from distutils.core import setup_keywords, extension_keywords

from distutils.command.install import install as installcmd
from distutils.command.install_lib import install_lib as install_libcmd

try:
    from distutils.command.install_egg_info import install_egg_info as install_egginfocmd

    class PlugEggInstaller(install_egginfocmd):
        def run(self):
            pass
except ImportError:
    pass

# For removing directory trees we need
import shutil

# FIXME: add others fields
FIELDS = (
    "url",
    "conflicts",
    "provides",
    "needs",
    "type",
    "start_file",
    "name",
    "version", # only a convenient field
    "description",
    "author",
    "license",
    "artist",
    "copyright",
    "update"
)

SIGNATURE = "UmitPlugin"

class BadPlugin(Exception):
    "Used to track exceptions while loading Plugin"
    pass

class PluginReader(object):
    def __init__(self, file):
        self.path = file
        self.enabled = False
        self.hasprefs = False
        self.parser = None

        try:
            self.file = ZipFile(file, "r")
        except BadZipfile:
            raise BadPlugin("Not a valid umit plugin format")
        
        if not self.parse_manifest():
            raise BadPlugin("Not a valid umit plugin manifest")
        
        if not self.check_validity():
            raise BadPlugin("Validation phase not passed")

        # Needs some testing
        self.parse_preferences()

    def parse_manifest(self):
        """
        Parse the Manifest.xml inside the zip file and set the fields
        
        @return
                False if the Manifest is not in the proper format
                True if everything is ok
        """
        
        try:
            data = self.file.read("Manifest.xml")
            doc = parseString(data)
        except Exception:
            return False
        
        if doc.documentElement.tagName != SIGNATURE:
            return False
        
        for field in FIELDS:
            setattr(self, field, "")
        
        for node in doc.documentElement.childNodes:
            if node.nodeName in FIELDS and node.firstChild:
                if node.nodeName in ('needs', 'provides', 'conflicts'):
                    # Convert to list
                    data = node.firstChild.data
                    setattr(self, node.nodeName, \
                            data.replace(" ", "").split(","))
                else:
                    setattr(self, node.nodeName, node.firstChild.data)
        
        return True

    def parse_preferences(self):
        try:
            data = self.file.read('data/preferences.xml')

            self.parser = Parser()
            self.parser.parse_string(data)
        except Exception, err:
            return
    
    def check_validity(self):
        """
        Checks the fields presents and validity
        
        @return True if it's ok
        """
        # TODO: implement me!
        
        return True
    
    def __repr__(self):
        #FIXME: that
        return "[%s::Plugin]" % self.name

    def get_logo(self, w=64, h=64):
        "@return a gtk.dk.Pixbuf"

        import gtk

        try:
            # TODO: eliminate the mktemp workaround
            
            name = mktemp('.png')
            f = open(name, 'wb')
            f.write(self.file.read('data/logo.png'))
            f.close()

            p = gtk.gdk.pixbuf_new_from_file_at_size(name, w, h)
            
            os.remove(name)

            return p
        except Exception, err:
            log.critical("PluginReader.get_logo(): %s" % err)
            return get_pixbuf('extension_normal', w, h)

    def get_path(self):
        return self.path

    def extract_file(self, zip_path):
        plug_subdir = os.path.join(PM_PLUGINS_TEMP_DIR, self.name)

        log.debug("Extracting %s into %s " % (zip_path, plug_subdir))

        if not os.path.exists(plug_subdir):
            os.mkdir(plug_subdir)

        name = os.path.join(plug_subdir,
                            os.path.basename(zip_path))

        f = open(name, 'wb')
        f.write(self.file.read(zip_path))
        f.close()

        return name

    # Code ripped from gettext
    def expand_lang(self, locale):
        from locale import normalize
        locale = normalize(locale)
        COMPONENT_CODESET   = 1 << 0
        COMPONENT_TERRITORY = 1 << 1
        COMPONENT_MODIFIER  = 1 << 2
        # split up the locale into its base components
        mask = 0
        pos = locale.find('@')
        if pos >= 0:
            modifier = locale[pos:]
            locale = locale[:pos]
            mask |= COMPONENT_MODIFIER
        else:
            modifier = ''
        pos = locale.find('.')
        if pos >= 0:
            codeset = locale[pos:]
            locale = locale[:pos]
            mask |= COMPONENT_CODESET
        else:
            codeset = ''
        pos = locale.find('_')
        if pos >= 0:
            territory = locale[pos:]
            locale = locale[:pos]
            mask |= COMPONENT_TERRITORY
        else:
            territory = ''
        language = locale
        ret = []
        for i in range(mask+1):
            if not (i & ~mask):  # if all components for this combo exist ...
                val = language
                if i & COMPONENT_TERRITORY: val += territory
                if i & COMPONENT_CODESET:   val += codeset
                if i & COMPONENT_MODIFIER:  val += modifier
                ret.append(val)
        ret.reverse()
        return ret

    def bind_translation(self, mofile):
        """
        @return a catalog on success or None
        """
        
        # We foreach inside locale dir and find a proper dir
        
        try:
            import gettext
            import locale
            LC_ALL = locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            return None

        LANG, ENC = locale.getdefaultlocale()

        if ENC is None:
            ENC = "utf8"
        if LANG is None:
            LANG = "en_US"
        
        # FIXME: is the '/' os indipendent?
        dir_lst = filter( \
            lambda x: x.startswith("locale/") and x.endswith("%s.mo" % mofile), \
            self.file.namelist() \
        )
        dir_lst.sort()

        avaiable_langs = []
        
        for dirname in dir_lst:
            t = dirname.split("/")

            if len(t) < 3:
                continue
            
            avaiable_langs.append(t[-2])

        request = self.expand_lang(".".join([LANG, ENC]))

        for req in request:
            if req in avaiable_langs:
                # Ok getted! Lucky day :)

                return gettext.GNUTranslations(StringFile( \
                    self.file.read("locale/%s/%s.mo" % (req, mofile)) \
                ))
            
        return None

class PluginWriter(object):
    def __init__(self, **fields):
        # Set to None and filter out the unused fields
        
        for i in FIELDS:
            setattr(self, i, "")
        
        for i in fields:
            if i in FIELDS:
                setattr(self, i, fields[i])
        
        for i in FIELDS:
            print "Field %s setted to %s" % (i, getattr(self, i))
        
        dirs = {
            'bin'  : '*',
            'data' : '*',
            'lib'  : '*',
            'locale' : '*'
        }
        
        self.file = ZipFile(fields['output'], "w", ZIP_DEFLATED)

        os.chdir("output")

        for i in dirs:
            self.dir_foreach(i, dirs[i])

        os.chdir("..")
        
        self.file.writestr("Manifest.xml", self.create_manifest())
        self.file.close()
        
        print ">> Plugin %s created." % fields['output']
    
    def dir_foreach(self, dir, pattern):
        "Add files contained in dir and that pass the pattern validation phase."

        for path, dirs, files in os.walk(dir):
            if not files:
                continue
            
            for file in files:
                if not fnmatch(file, pattern):
                    continue

                print "Adding file %s %s %s" % (path, file, dir)
                
                self.file.write(os.path.join(path, file),
                                os.path.join(path, file))
    
    def create_manifest(self):
        """
        Create a Manifest.xml file
        
        @return an xml manifest as string
        """
        doc = getDOMImplementation().createDocument(None, SIGNATURE, None)
        
        for field in FIELDS:
            node = doc.createElement(field)
            node.appendChild(doc.createTextNode(getattr(self, field)))
            doc.documentElement.appendChild(node)
        
        print "Manifest.xml created"
        return doc.toxml()


#
# distutils related class

class PlugLibInstaller(install_libcmd):
    def finalize_options(self):
        self.install_dir = 'output/lib'
        install_libcmd.finalize_options(self)

class PlugInstaller(installcmd):
    def finalize_options(self):
        self.home = 'output'
        installcmd.finalize_options(self)

    def run(self):
        installcmd.run(self)

class PlugDistribution(Distribution):
    def __init__(self, *attrs):
        Distribution.__init__(self, *attrs)
        self.cmdclass['install'] = PlugInstaller
        self.cmdclass['install_lib'] = PlugLibInstaller
        self.cmdclass['install_egg_info'] = PlugEggInstaller


def setup(**attrs):
    "Called to create a plugin like the dist-tools setup function"

    setup_d = {}

    # We need to filter out some fields
    # to avoid
    for attr in attrs:
        if attr not in setup_keywords and \
           attr not in extension_keywords:
            setup_d[attr] = attrs[attr]

    print ">> Running setup()"

    import warnings
    warnings.filterwarnings('ignore', r".*", UserWarning)

    setup_d['distclass'] = PlugDistribution
    dist_setup(**setup_d)

    print ">> Creating plugin"
    PluginWriter(**attrs)

    print ">> Cleaning up"
    shutil.rmtree('build')
    shutil.rmtree('output')
