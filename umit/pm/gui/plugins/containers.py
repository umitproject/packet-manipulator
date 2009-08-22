#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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
import sys

import datetime

from fnmatch import fnmatch
from zipfile import ZipFile, BadZipfile, ZIP_DEFLATED

from StringIO import StringIO

from xml.sax import handler, make_parser
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from tempfile import mktemp

from umit.pm.gui.plugins.parser import Parser
from umit.pm.gui.plugins.atoms import StringFile

from umit.pm.core.const import PM_PLUGINS_TEMP_DIR

from umit.pm.core.logger import log

# For setup functionality
from distutils.dist import Distribution

from distutils.core import setup as dist_setup
from distutils.core import setup_keywords, extension_keywords

from distutils.command.install import install as installcmd
from distutils.command.install_lib import install_lib as install_libcmd

try:
    from distutils.command.install_egg_info import install_egg_info as \
         install_egginfocmd

    class PlugEggInstaller(install_egginfocmd):
        def run(self):
            pass

except ImportError:
    pass

# For removing directory trees we need
import shutil

SIGNATURE = "UmitPlugin"

PASSIVE_AUDIT_TYPE = 0
ACTIVE_AUDIT_TYPE  = 1

class ManifestObject(object):
    def __init__(self):

        # Ok here we're using list object because py2.5 seems to not support
        # index() for tuple. Stupid 2.5 :)

        self.elements = [
            ['name', 'version', 'description', 'url'],
            ['start_file', 'update'],
            ['provide', 'need', 'conflict'],
            ['license', 'copyright', 'author',
             'contributor', 'translator', 'artist'],
            [], # From here fields are for active/passive audits
            ['configuration', 'bool', 'int', 'float', 'str'],
            ['protocol'],
            ['vulnerability', 'description', 'classes', 'class', 'systems',
             'versions', 'affected', 'notaffected', 'credits', 'pubblished',
             'discovered', 'references', 'url', 'platforms', 'platform'],
        ]

        self.containers = [SIGNATURE, 'runtime', 'deptree', 'credits', 'audit',
                           'configurations', 'protocols', 'vulnerabilities']

        self.name = ''
        self.version = ''
        self.description = ''
        self.url = ''

        self.start_file = ''
        self.update = []

        self.provide = []
        self.need = []
        self.conflict = []

        self.license = []
        self.copyright = []
        self.author = []
        self.contributor = []
        self.translator = []
        self.artist = []

        # -1 for standard plugin
        self.audit_type = -1

        # (('configuration_name', {'option_id' : (value, 'description') })
        self.configurations = []

        # (('tcp', 22), ('http', 80))
        self.protocols = []

        # (('vuln_name',
        #  {'description' : 'desc',
        #   'classes'     : ('bof', 'design error'),
        #   'systems'     : (('affected', 'system'), ('not', 'affected')),
        #   'versions'    : (('affected', 'system'), ('not', 'affected')),
        #   'credits'     : (date, ('author1', 'author2')
        #   'references'  : (('solution', 'href'), ('CVE-234', 'href')),
        #   'platforms'   : (('macos', 'ppc'), )), )
        self.vulnerabilities = []

        self.attr_type = ''

    def check_validity(self, use_print=False):
        """
        Checks the fields presents and validity

        @return True if it's ok
        """

        # This fields should be present and not null
        fields = ('name', 'version', 'description', 'url', 'start_file',
                  'license', 'copyright', 'author')

        for element in fields:
            if not getattr(self, element, None):
                txt = 'Element named %s should not be null.' % (element)

                if use_print:
                    print txt
                else:
                    log.warning(txt)

                return False

        return True

    def get_provides(self): return self.provide
    def get_conflicts(self): return self.conflict
    def get_needs(self): return self.need

    provides = property(get_provides)
    conflicts = property(get_conflicts)
    needs = property(get_needs)

class ManifestLoader(handler.ContentHandler, ManifestObject):
    def __init__(self):
        ManifestObject.__init__(self)

        self.element_idx = 0
        self.parsing_pass = -1
        self.current_element = None
        self.data = None

        self.opt_trans = {
            1 : lambda x: x == '1',
            2 : int,
            3 : float,
            4 : str,
        }

        # id / description / transformer
        self.current_option = [None, None, None]

        # conf_id / conf_dict
        self.current_configuration = ['', {}]

        self.current_vuln = ['', {}]

    def startElement(self, name, attrs):
        try:
            self.element_idx = self.elements[self.parsing_pass].index(name)
            self.current_element = \
                self.elements[self.parsing_pass][self.element_idx]

            # <configurations>
            if self.parsing_pass == 5:
                if self.element_idx == 0:
                    self.current_configuration[0] = attrs.get('name')

                elif self.element_idx in range(1, 5, 1):

                    desc = attrs.get('description')
                    opid = attrs.get('id')

                    if not id:
                        log.error('Option without an id')

                    self.current_option[0] = opid

                    if desc:
                        self.current_option[1] = desc

                    self.current_option[2] = self.opt_trans[self.element_idx]

                    log.debug('Allocating new option \'%s\' (type: %s)' % \
                              (opid, name))

                    self.data = None

            # <protocols>
            elif self.parsing_pass == 6 and self.element_idx == 0:
                proto_name = attrs.get('name')
                proto_port = attrs.get('port') or None

                if proto_port and proto_port.isdigit():
                    try:
                        proto_port = int(proto_port)
                    except:
                        proto_port = None

                if proto_name:
                    log.debug('Adding new protocol %s:%s' % (proto_name,
                                                             proto_port))

                    self.protocols.append((proto_name, proto_port))

            elif self.parsing_pass == 7:
                if self.element_idx == 0:
                    self.current_vuln[0] = attrs.get('name')
                elif self.element_idx == 4: # systems
                    self.in_systems = 1
                elif self.element_idx == 5: # versions
                    self.in_systems = 0
                elif self.element_idx in (1, 3, 6, 7, 9, 10):
                    # If we have description, class, affected or notaffected we
                    # need to get the text element
                    self.data = None
                elif self.element_idx == 12:
                    rtype = attrs.get('type')
                    rhref = attrs.get('href')

                    if not rhref:
                        raise Exception('href attribute of url element cannot '
                                        'be null')

                    if 'references' not in self.current_vuln[1]:
                        self.current_vuln[1]['references'] = []

                    self.current_vuln[1]['references'].append((rtype, rhref))
                elif self.element_idx == 14:
                    name, arch = attrs.get('name'), attrs.get('arch')

                    if not name or not arch:
                        raise Exception('name and arch attribute are required '
                                        'inside platform element')

                    if 'platforms' not in self.current_vuln[1]:
                        self.current_vuln[1]['platforms'] = []

                    self.current_vuln[1]['platforms'].append((name, arch))

        except IndexError:

            log.debug('Element named `%s` is not in %s' % \
                      (name, self.elements[self.parsing_pass]))

        except ValueError:
            try:
                idx = self.containers.index(name)

                if self.parsing_pass < idx:
                    self.parsing_pass = idx
                    self.element_idx = 0
                else:
                    log.warning('Element `%s` is not valid at this point. ' \
                                'Should compare before %s' % (name,
                                            self.containers[self.parsing_pass]))

                if self.parsing_pass == 0: # SIGNATURE
                    if type in attrs.keys():
                        self.attr_type = attrs.get('type')
                    else:
                        self.attr_type = 'ui'

                elif self.parsing_pass == 4: # <audit>
                    self.audit_type = attrs.get('type') == 'active' and 1 or 0
                    log.debug("Audit type is %d" % self.audit_type)

            except ValueError:
                log.warning('Element named `%s` not excepted.' % name)

    def characters(self, ch):
        if not self.current_element:
            return

        if not self.data:
            self.data = ch
        else:
            self.data += ch

    def endElement(self, name):
        if self.parsing_pass == 5:
            if name == 'configuration' and self.current_configuration[0] and \
               self.current_configuration[1]:

                log.debug('Adding configuration named %s with %d options' \
                          % (self.current_configuration[0],
                             len(self.current_configuration[1])))

                self.configurations.append(self.current_configuration)
                self.current_configuration = ['', {}]

            elif any(self.current_option) and self.element_idx in (1, 2, 3, 4):

                id, val, desc = self.current_option[0], \
                                self.current_option[2](self.data), \
                                self.current_option[1]

                self.current_configuration[1][id] = [val, desc]
                self.current_option = [None, None, None]

                log.debug('Adding new option with id \'%s\' to \'%s\'.' \
                          % (id, self.current_configuration[0]))

        elif self.parsing_pass == 7:
            if name == 'vulnerability':

                if not self.current_vuln[0]:
                    raise Exception('vulnerability element must have name '
                                    'attribute set')

                log.debug('Adding new vulnerability %s' % self.current_vuln[0])

                self.vulnerabilities.append(self.current_vuln)
                self.current_vuln = ['', {}]

            elif name == 'description':
                self.current_vuln[1]['description'] = self.data
                log.debug('Vuln description for %s is %s...' % \
                          (self.current_vuln[0],
                           self.data[:min(20, len(self.data))]))

            elif name == 'class':
                if 'classes' not in self.current_vuln:
                    self.current_vuln[1]['classes'] = []

                self.current_vuln[1]['classes'].append(self.data)

                log.debug('Adding new class \'%s\' (%d total)' \
                          % (self.data, len(self.current_vuln[1]['classes'])))

            elif name == 'affected' or name == 'notaffected':
                if self.in_systems:
                    if 'systems' not in self.current_vuln[1]:
                        dct = self.current_vuln[1]['systems'] = [[], []]
                    else:
                        dct = self.current_vuln[1]['systems']
                elif self.in_systems == 0:
                    if 'versions' not in self.current_vuln[1]:
                        dct = self.current_vuln[1]['versions'] = [[], []]
                    else:
                        dct = self.current_vuln[1]['versions']
                else:
                    raise Exception('Not valid manifest')

                dct[name[0] == 'a' and 0 or 1].append(self.data)

                log.debug('Adding %s as %s (system: %d)' % (self.data, name,
                                                            self.in_systems))

            elif name == 'pubblished':
                if 'credits' not in self.current_vuln[1]:
                    self.current_vuln[1]['credits'] = ['', []]

                date_tup = self.data.split('-', 2)

                if len(date_tup) != 3:
                    raise Exception('Not a valid date format')

                try:
                    date_tup = map(int, date_tup)
                except:
                    raise Exception('Not a valid date format')

                try:
                    self.current_vuln[1]['credits'][0] = \
                        datetime.datetime(year=date_tup[0],
                                          month=date_tup[1],
                                          day=date_tup[2])
                except:
                    raise Exception('Not a valid date')

            elif name == 'discovered':
                if 'credits' not in self.current_vuln[1]:
                    raise Exception('pubblished element must be present '
                                    'inside credits element')

                log.debug('Adding new discovered %s' % self.data)
                self.current_vuln[1]['credits'][1].append(self.data)

        if self.current_element == name:

            if self.parsing_pass < 5:
                try:
                    attr = getattr(self, name)

                    if isinstance(attr, basestring):
                        setattr(self, name, self.data)
                    elif isinstance(attr, list):
                        attr.append(self.data)
                except:
                    pass

            self.current_element = None
            self.data = None

class ManifestWriter(object):
    def startElement(self, names, attrs):
        self.depth_idx += 1
        self.writer.characters('  ' * self.depth_idx)
        self.writer.startElement(names, attrs)

    def endElement(self, name):
        self.writer.endElement(name)
        self.writer.characters('\n')
        self.depth_idx -= 1

    def __init__(self, manifest):
        assert isinstance(manifest, ManifestObject)

        self.output = StringIO()
        self.depth_idx = -1
        self.manifest = manifest
        self.writer = XMLGenerator(self.output, 'utf-8')
        self.writer.startDocument()

        attr_vals = {
            'xmlns' : 'http://www.umitproject.org',
            'xsi:schemaLocation' : 'http://www.umitproject.org UmitPlugins.xsd',
            'xmlns:xsi' : 'http://www.w3.org/2001/XMLSchema-instance',
            'type' : manifest.attr_type or 'ui'
        }

        self.startElement('UmitPlugin', AttributesImpl(attr_vals)),
        self.writer.characters('\n')

        # First phase saving
        for elem in manifest.elements[0]:
            self.add_element(elem)

        # Runtime block
        self.startElement('runtime', {})
        self.writer.characters('\n')

        self.add_element('start_file')
        self.add_element('update')

        self.writer.characters('  ' * self.depth_idx)
        self.endElement('runtime')

        # Deptree block
        if manifest.provide or manifest.need or manifest.conflict:
            self.startElement('deptree', {})
            self.writer.characters('\n')

            self.add_element('provide')
            self.add_element('need')
            self.add_element('conflict')

            self.writer.characters('  ' * self.depth_idx)
            self.endElement('deptree')

        # Credits block
        self.startElement('credits', {})
        self.writer.characters('\n')

        for elem in manifest.elements[3]:
            self.add_element(elem)

        self.writer.characters('  ' * self.depth_idx)
        self.endElement('credits')

        if self.manifest.audit_type == PASSIVE_AUDIT_TYPE:
            self.dump_passive_audit()
        elif self.manifest.audit_type == ACTIVE_AUDIT_TYPE:
            self.dump_passive_audit(True)

        self.endElement('UmitPlugin')
        self.writer.endDocument()

    def add_element(self, name):
        value = getattr(self.manifest, name, None)

        if not value:
            return

        if isinstance(value, basestring):
            self.startElement(name, {})
            self.writer.characters(value)
            self.endElement(name)
        elif isinstance(value, list):
            for item in value:
                self.startElement(name, {})
                self.writer.characters(item)
                self.endElement(name)

    def dump_passive_audit(self, active=False):
        trans = {
            bool : 'bool',
            float : 'float',
            int : 'int',
            str : 'str',
        }

        self.startElement('audit', AttributesImpl(
            {'type' : (active and 'active' or 'passive')}
        ))
        self.writer.characters('\n')

        if self.manifest.configurations:
            self.startElement('configurations', {})
            self.writer.characters('\n')

            # Let's dump configurations
            for conf_name, options_dict in self.manifest.configurations:
                self.startElement('configuration',
                                  AttributesImpl({'name' : conf_name}))
                self.writer.characters('\n')

                for k, (val, desc) in options_dict.items():
                    attrs = {'id' : str(k)}

                    if isinstance(val, bool):
                        value = val and '1' or '0'
                    else:
                        value = str(val)

                    if desc:
                        attrs['description'] = desc

                    self.startElement(trans[type(val)],
                                      AttributesImpl(attrs))
                    self.writer.characters(value)
                    self.endElement(trans[type(val)])

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('configuration')

            self.writer.characters('  ' * self.depth_idx)
            self.endElement('configurations')

        if not self.manifest.protocols:
            raise Exception('protocols element cannot be null')

        self.startElement('protocols', {})
        self.writer.characters('\n')

        # Protocols
        for name, port in self.manifest.protocols:
            attrs = {'name' : name}

            if port:
                attrs['port'] = str(port)

            self.startElement('protocol', AttributesImpl(attrs))
            self.endElement('protocol')

        self.writer.characters('  ' * self.depth_idx)
        self.endElement('protocols')

        if not self.manifest.vulnerabilities:
            self.writer.characters('  ' * self.depth_idx)
            self.endElement('audit')
            return

        self.startElement('vulnerabilities', {})
        self.writer.characters('\n')

        for vuln_name, vuln_dict in self.manifest.vulnerabilities:
            self.startElement('vulnerability',
                              AttributesImpl({'name' : vuln_name}))
            self.writer.characters('\n')

            elem = vuln_dict.get('description', None)

            if elem:
                self.startElement('description', {})
                self.writer.characters(elem)
                self.endElement('description')

            elem = vuln_dict.get('classes', None)

            if elem:
                self.startElement('classes', {})
                self.writer.characters('\n')

                for vuln_class in elem:
                    self.startElement('class', {})
                    self.writer.characters(vuln_class)
                    self.endElement('class')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('classes')

            elem = vuln_dict.get('systems', None)

            if elem:
                self.startElement('systems', {})
                self.writer.characters('\n')

                for affected in elem[0]:
                    self.startElement('affected', {})
                    self.writer.characters(affected)
                    self.endElement('affected')

                for notaffected in elem[1]:
                    self.startElement('notaffected', {})
                    self.writer.characters(notaffected)
                    self.endElement('notaffected')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('systems')

            elem = vuln_dict.get('versions', None)

            if elem:
                self.startElement('versions', {})
                self.writer.characters('\n')

                for affected in elem[0]:
                    self.startElement('affected', {})
                    self.writer.characters(affected)
                    self.endElement('affected')

                for notaffected in elem[1]:
                    self.startElement('notaffected', {})
                    self.writer.characters(notaffected)
                    self.endElement('notaffected')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('versions')

            elem = vuln_dict.get('credits', None)

            if elem:
                self.startElement('credits', {})
                self.writer.characters(elem)

                for pdate, authors in elem:
                    self.startElement('pubblished', {})
                    self.writer.characters(pdate)
                    self.endElement('pubblished')

                    for author in authors:
                        self.startElement('discovered', {})
                        self.writer.characters(author)
                        self.endElement('discovered')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('credits')

            elem = vuln_dict.get('references', None)

            if elem:
                self.startElement('references', {})
                self.writer.characters('\n')

                for rtype, rhref in elem:

                    attrs = {'href' : rhref}

                    if rtype:
                        attrs['type'] = rtype

                    self.startElement('url', AttributesImpl(attrs))
                    self.endElement('url')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('references')

            elem = vuln_dict.get('platforms', None)

            if elem:
                self.startElement('platforms', {})
                self.writer.characters('\n')

                for name, arch in elem:
                    self.startElement('platform',
                                      AttributesImpl({'name' : name,
                                                      'arch': arch}))
                    self.endElement('platform')

                self.writer.characters('  ' * self.depth_idx)
                self.endElement('platforms')

            self.writer.characters('  ' * self.depth_idx)
            self.endElement('vulnerability')

        self.writer.characters('  ' * self.depth_idx)
        self.endElement('vulnerabilities')

        self.writer.characters('  ' * self.depth_idx)
        self.endElement('audit')

    def get_output(self):
        return self.output.getvalue()

class BadPlugin(Exception):
    "Used to track exceptions while loading Plugin"
    pass

class PluginReader(ManifestLoader):
    def __init__(self, file):
        ManifestLoader.__init__(self)

        self.path = file
        self.enabled = False
        self.hasprefs = False
        self.parser = None

        try:
            self.file = ZipFile(file, "r")
        except:
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
            # TODO: add validation of the manifest

            # Py2.5 doesn't have open on ZipFile object
            fileobj = StringIO(self.file.read('Manifest.xml'))

            parser = make_parser()
            parser.setContentHandler(self)

            parser.parse(fileobj)
        except Exception, err:
            log.debug('Exception in parse_manifest(): %s' % str(err))
            return False

        return True

    def parse_preferences(self):
        try:
            data = self.file.read('data/preferences.xml')

            self.parser = Parser()
            self.parser.parse_string(data)
        except Exception, err:
            return

    def __repr__(self):
        #FIXME: that
        return "[%s::Plugin]" % self.name

    def get_logo(self, w=64, h=64):
        "@return a gtk.dk.Pixbuf"

        try:
            # TODO: eliminate the mktemp workaround

            name = mktemp('.png')
            f = open(name, 'wb')
            f.write(self.file.read('data/logo.png'))
            f.close()

            import gtk

            p = gtk.gdk.pixbuf_new_from_file_at_size(name, w, h)

            os.remove(name)

            return p
        except Exception, err:

            from umit.pm.gui.core.icons import get_pixbuf

            if self.audit_type == 0:
                return get_pixbuf('sniff_normal', w, h)
            elif self.audit_type == 1:
                return get_pixbuf('packet_normal', w, h)
            else:
                return get_pixbuf('extension_normal', w, h)

    def get_path(self):
        return self.path

    def extract_dir(self, zip_path, maxdepth=0):
        """
        Extract a dir full recursive.
        @param zip_path the directory to extract (for example data/test/)
        @param maxdepth the max depth. Set 0 for fully recursive extraction.
        @return a list containing extracted files or []
        """
        ret = []
        if zip_path[-1] != '/':
            zip_path += '/'
        if zip_path[0] == '/':
            zip_path = zip_path[1:]

        sep_len = zip_path.count('/')

        log.debug("Extracting files contained in %s" % zip_path)

        for i in self.file.namelist():
            if i.startswith(zip_path):
                if maxdepth > 0 and \
                   i.count('/') - sep_len - maxdepth + 1 != 0:

                    log.debug("Skipping %s for maxdepth %d" % (i, maxdepth))
                    continue

                p = self.extract_file(i, keep_path=True)

                if p: ret.append(p)

        return ret

    def extract_file(self, zip_path, keep_path=False):
        if zip_path not in self.file.namelist():
            log.debug("The file %s seems to not exists in the zip file" % \
                      zip_path)
            return None

        plug_subdir = os.path.join(PM_PLUGINS_TEMP_DIR, self.name)

        if not os.path.exists(plug_subdir):
            os.mkdir(plug_subdir)

        if keep_path:
            # Recursive reconstruct the entire path
            full_path = os.path.join(plug_subdir, os.path.dirname(zip_path))
            if not os.path.isdir(full_path):
                os.makedirs(full_path)
            plug_subdir = full_path

        log.debug("Extracting %s into %s " % (zip_path, plug_subdir))

        name = os.path.join(plug_subdir,
                            os.path.basename(zip_path))

        f = open(name, 'wb+')
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

class PluginWriter(ManifestObject):
    def __init__(self, **fields):
        ManifestObject.__init__(self)

        # Set to None and filter out the unused fields

        FIELDS = ('name', 'version', 'description', 'url', 'start_file',
                  'update', 'provide', 'need', 'conflict', 'license',
                  'copyright', 'author', 'contributor', 'translator', 'artist',
                  'audit_type', 'configurations', 'protocols',
                  'vulnerabilities')

        # Filter out fields that are not related to the schema

        for i in fields:
            if i in FIELDS:
                setattr(self, i, fields[i])

        if not self.check_validity(use_print=True):
            print "!! Manifest could not be created."
            sys.exit(-1)

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

        writer = ManifestWriter(self)
        self.file.writestr('Manifest.xml', writer.get_output())
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

if __name__ == "__main__":
    parser = make_parser()
    loader = ManifestLoader()
    parser.setContentHandler(loader)
    parser.parse(open('test.xml'))
    loader.dump()
