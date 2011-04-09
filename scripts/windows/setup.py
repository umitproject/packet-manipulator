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

import re
import sys
import glob
import os, os.path

if os.name == 'nt':
    try:
        import py2exe
        from py2exe.build_exe import py2exe as BuildExe
    except ImportError:
        print "Install py2exe to use setup.py"
        sys.exit(-1)

from distutils.core import setup, Extension
from distutils.command.install import install
from distutils.command.build import build
from umit.pm.core.const import PM_VERSION, PM_SITE

BASE_DOCS_DIR = os.path.join('share', 'doc', 'PacketManipulator-%s' % PM_VERSION)
DOCS_DIR = os.path.join('generated-doc', 'html')

def getoutput(cmd):
    """Return output (stdout or stderr) of executing cmd in a shell."""
    return getstatusoutput(cmd)[1]

def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    if sys.platform == 'win32':
        pipe = os.popen(cmd, 'r')
        text = pipe.read()
        sts = pipe.close() or 0
        if text[-1:] == '\n':
            text = text[:-1]
        return sts, text
    else:
        from commands import getstatusoutput
        return getstatusoutput(cmd)

def pkgc_version_check(name, longname, req_version):
    is_installed = not os.system('pkg-config --exists %s' % name)
    if not is_installed:
        print "Could not find %s" % longname
        return 0

    orig_version = getoutput('pkg-config --modversion %s' % name)
    version = map(int, orig_version.split('.'))
    pkc_version = map(int, req_version.split('.'))

    if version >= pkc_version:
        return 1
    else:
        print "Warning: Too old version of %s" % longname
        print "         Need %s, but %s is installed" % \
              (pkc_version, orig_version)
        self.can_build_ok = 0
        return 0

def pkc_get_include_dirs(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --cflags-only-I %s' % name)
        retval.extend(output.replace('-I', '').split())
    return retval

def pkc_get_libraries(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --libs-only-l %s' % name)
        retval.extend(output.replace('-l', '').split())
    return retval

def pkc_get_library_dirs(names):
    if type(names) != tuple:
        names = (names,)
    retval = []
    for name in names:
        output = getoutput('pkg-config --libs-only-L %s' % name)
        retval.extend(output.replace('-L', '').split())
    return retval

modules = []

if os.getenv('PM_DOCKING', False):
    print "OMG you're brave enough to give a try :O"

    if os.name != 'nt':
        os.chdir("umit/pm/moo")
        os.system("make")
        os.system("make moo-pygtk.c")
        os.chdir("../..")

        moo = Extension(
            'umit.pm.gui.moo_stub',
            [
                'umit/pm/moo/moopane.c',
                'umit/pm/moo/moopaned.c',
                'umit/pm/moo/moobigpaned.c',
                'umit/pm/moo/moomarshals.c',
                'umit/pm/moo/moo-pygtk.c',
                'umit/pm/moo/moo-stub.c',
            ],
            include_dirs=pkc_get_include_dirs('gtk+-2.0 pygtk-2.0'),
            libraries=pkc_get_libraries('gtk+-2.0 pygtk-2.0'),
            library_dirs=pkc_get_library_dirs('gtk+-2.0 pygtk-2.0'),
        )
    else:
        gtk = "C:\\Python26\\Lib\\site-packages\\gtk-2.0\\runtime"
        inc = "%s\\include" % gtk
        lib = "%s\\lib" % gtk
        
        moo = Extension(
            'umit.pm.gui.moo_stub',
            [
                'umit/pm/moo/moopane.c',
                'umit/pm/moo/moopaned.c',
                'umit/pm/moo/moobigpaned.c',
                'umit/pm/moo/moomarshals.c',
                'umit/pm/moo/moo-pygtk.c',
                'umit/pm/moo/moo-stub.c',
            ],
            include_dirs=[
                "%s\\gtk-2.0" % inc, "%s\\glib-2.0" % inc,
                "%s\\atk-1.0" % inc, "%s\\pango-1.0" % inc,
                "%s\\gdk-pixbuf-2.0" % inc, "%s\\cairo" % inc,
                "%s\\gtk-2.0\\include" % lib, "%s\\glib-2.0\\include" % lib,
                "C:\\Python26\\include\\pycairo", "C:\\Python26\\include\\pygtk-2.0"
                ],
            library_dirs=[lib],
            libraries=["gtk-win32-2.0", "gthread-2.0", "glib-2.0", "gobject-2.0", "gdk-win32-2.0", "gdk_pixbuf-2.0"]
        )

    modules = [moo]

mo_files = []

for filepath in glob.glob("umit/pm/share/locale/*/LC_MESSAGES/*.mo"):
    lang = filepath[len("umit/pm/share/locale/"):]
    targetpath = os.path.dirname(os.path.join("share/locale",lang))
    mo_files.append((targetpath, [filepath]))

class pm_build(build):
    def build_html_doc(self):
        """Build the html documentation."""

        try:
            import sphinx
        except ImportError:
            self.warn("sphinx not found, documentation won't be build.")
            return

        sphinx_ver = sphinx.__version__
        def digits(x):
            res = re.match('\d+', x)
            if res is None:
                return 0
            else:
                return int(res.group())
        if map(digits, sphinx_ver.split('.')) < [0, 5, 1]:
            self.warn("Sphinx's version is too old (%s, expected at least "
                      "0.5.1, documentation won't be build." % sphinx_ver)
            return

        # Build the documentation just like it is done through the Makefile
        sphinx.main([__file__,
            "-b", "html",
            "-d", os.path.join("umit", "pm", "share", "doc", "doctrees"),
            os.path.join("umit", "pm", "share", "doc", "src"), DOCS_DIR])

    def run(self):
        self.build_html_doc()
        build.run(self)

class pm_install(BuildExe):
    def run(self):
        print
        print "#" * 80
        print "# Creating EXE"
        print "#" * 80
        print

        BuildExe.run(self)
        self.build_plugins()
        self.build_audits()

        print
        print "#" * 80
        print "# Packet manipulator is now installed"
        print "#" * 80
        print

    def build_audits(self):
        print
        print "#" * 80
        print "# Generating audits plugins"
        print "#" * 80
        print

        # Use dist_dir on windows
        dir = self.dist_dir
        dirs = ['share', 'PacketManipulator', 'audits']

        while dirs:
            dir = os.path.join(dir, dirs.pop(0))

            if not os.path.exists(dir):
                os.mkdir(dir)

        dest_dir = dir
        old_cd = os.getcwd()
        pm_dir = os.path.abspath(os.path.dirname(os.sys.argv[0]))
        plugins_dir = os.path.join(pm_dir, 'audits')
        os.chdir(plugins_dir)

        if os.name =="nt":
            os.system("C:\\python26\\python.exe setup-autogen.py passive")
            os.system("C:\\python26\\python.exe setup-autogen.py active")
        else:
            os.system("python setup-autogen.py passive")
            os.system("python setup-autogen.py active")

        print
        print "#" * 80
        print "# Building plugins"
        print "#" * 80
        print

        if os.name =="nt":
            os.system("C:\\python26\\python.exe setup-autogen.py "
                      "-o %s -b passive" % dest_dir)
            os.system("C:\\python26\\python.exe setup-autogen.py "
                      "-o %s -b active" % dest_dir)
        else:
            os.system("python setup-autogen.py -o %s -b passive" % dest_dir)
            os.system("python setup-autogen.py -o %s -b active" % dest_dir)

        os.chdir(old_cd)

    def build_plugins(self):
        print
        print "#" * 80
        print "# Building plugins"
        print "#" * 80
        print

        # Use dist_dir on windows
        dir = self.dist_dir
        dirs = ['share', 'PacketManipulator', 'plugins']

        while dirs:
            dir = os.path.join(dir, dirs.pop(0))

            if not os.path.exists(dir):
                os.mkdir(dir)

        # Ok now dir is our destination so we should make plugins

        dest_dir = dir
        old_cd = os.getcwd()
        pm_dir = os.path.abspath(os.path.dirname(os.sys.argv[0]))
        plugins_dir = os.path.join(pm_dir, 'plugins')

        os.putenv('PYTHONPATH',
                  '%s%s%s' % (pm_dir, os.pathsep, os.getenv('PYTHONPATH', '')))

        for dir_entry in os.listdir(plugins_dir):
            dir_entry = os.path.join(plugins_dir, dir_entry)

            if not os.path.isdir(dir_entry) or \
               not os.path.exists(os.path.join(dir_entry, "setup.py")):
                continue

            self.build_plugin(plugins_dir, dir_entry, dest_dir)

        os.chdir(old_cd)

    def build_plugin(self, plugins_dir, dir_entry, dest_dir):
        os.chdir(os.path.join(plugins_dir, dir_entry))

        if os.name =="nt":
            os.system("C:\\python26\\python.exe setup.py build_ext -c mingw32 install")
        else:
            os.system("python setup.py install")

        for plugin in glob.glob("*.ump"):
            dest = os.path.join(dest_dir, os.path.basename(plugin))
            os.rename(plugin, dest)

uac_manifest = \
"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"> 
 <assemblyIdentity version="1.0.0.0" processorArchitecture="X86" name="IsUserAdmin" type="win32"/> 
 <description>Packet Manipulator</description> 
 <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
  <security>
   <requestedPrivileges>
    <requestedExecutionLevel level="requireAdministrator" uiAccess="false" />
   </requestedPrivileges>
  </security>
 </trustInfo>
</assembly>"""

setup(name         = 'PacketManipulator',
      version      = PM_VERSION,
      description  = 'Packet manipulation made easy',
      author       = 'Francesco Piccinno',
      author_email = 'stack.box@gmail.com',
      url          = PM_SITE,
      license      = 'GNU GPL 2',
      requires     = ['gtk'],
      platforms    = ['Platform Independent'],
      packages     = ['umit',
                      'umit.pm',
                      'umit.pm.backend',
                      'umit.pm.backend.abstract',
                      'umit.pm.backend.abstract.basecontext',
                      'umit.pm.backend.abstract.context',
                      'umit.pm.backend.scapy',
                      'umit.pm.backend.scapy.context',
                      'umit.pm.backend.umpa',
                      'umit.pm.backend.umpa.context',
                      'umit.pm.manager',
                      'umit.pm.core',
                      'umit.pm.gui',
                      'umit.pm.gui.core',
                      'umit.pm.gui.tabs',
                      'umit.pm.gui.pages',
                      'umit.pm.gui.sessions',
                      'umit.pm.gui.dialogs',
                      'umit.pm.gui.widgets',
                      'umit.pm.gui.plugins',
                      'umit.pm.higwidgets'
                     ],
      data_files   = [
                      (os.path.join('share', 'pixmaps', 'pm'),
                       glob.glob(os.path.join('umit', 'pm', 'share', 'pixmaps',
                                              'pm', '*'))),
                      (BASE_DOCS_DIR,
                          glob.glob(os.path.join(DOCS_DIR, '*.html')) + \
                          glob.glob(os.path.join(DOCS_DIR, '*.js')) +   \
                          glob.glob(os.path.join(DOCS_DIR, '*.inv'))),
                      (os.path.join(BASE_DOCS_DIR, '_images'),
                          glob.glob(os.path.join(DOCS_DIR, '_images', '*'))),
                      (os.path.join(BASE_DOCS_DIR, '_sources'),
                          glob.glob(os.path.join(DOCS_DIR, '_sources', '*'))),
                      (os.path.join(BASE_DOCS_DIR, '_static'),
                          glob.glob(os.path.join(DOCS_DIR, '_static', '*'))),
                     ] + mo_files,
      scripts      = [os.path.join('umit', 'pm', 'PacketManipulator')],
      windows      = [{'script' : r'umit\pm\PacketManipulator',
                       'icon_resources' : [(1, r'umit\pm\share\pixmaps\pm\pm-icon48.ico')],
					   'uac_info' : 'requireAdministrator',
                      # 'other_resources' : [(24, 1, uac_manifest)]}],
                      }],
      options      = {'py2exe' : {
                          'compressed' : 1,
                          'packages' : 'encodings,scapy',
						  'excludes' : 'psyco,Crypto',
                          'includes' : 'umit.pm.gui.moo_stub,gtk.keysyms,gtk,pango,atk,gobject,encodings,encodings.*,cairo,pangocairo,atk,gtkhex,gio,glib,gobject'},
                      'build': {'compiler' : 'mingw32'}},
      ext_modules  = modules,
      cmdclass     = {'py2exe' : pm_install,
                      'build' : pm_build}
)
