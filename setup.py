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

import os
import os.path
import shutil

from distutils.core import setup, Extension
from distutils.command.install import install
from distutils.command.build import build
from umit.pm.core.const import PM_VERSION, PM_SITE

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DOCS_DIR = os.path.join('share', 'doc',
                             'PacketManipulator-%s' % PM_VERSION)
DOCS_DIR = os.path.join(ROOT_DIR, 'generated-doc', 'html')

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

    os.chdir("umit/pm/moo")
    os.system("make")
    os.system("make moo-pygtk.c")
    os.chdir("../..")

    moo = Extension(
        'umit.pm.gui.moo_stub',
        [
            os.path.join(ROOT_DIR, 'umit/pm/moo/moopane.c'),
            os.path.join(ROOT_DIR, 'umit/pm/moo/moopaned.c'),
            os.path.join(ROOT_DIR, 'umit/pm/moo/moobigpaned.c'),
            os.path.join(ROOT_DIR, 'umit/pm/moo/moomarshals.c'),
            os.path.join(ROOT_DIR, 'umit/pm/moo/moo-pygtk.c'),
            os.path.join(ROOT_DIR, 'umit/pm/moo/moo-stub.c'),
        ],
        include_dirs=pkc_get_include_dirs('gtk+-2.0 pygtk-2.0'),
        libraries=pkc_get_libraries('gtk+-2.0 pygtk-2.0'),
        library_dirs=pkc_get_library_dirs('gtk+-2.0 pygtk-2.0'),
    )

    modules = [moo]

mo_files = []

for filepath in glob.glob(os.path.join(ROOT_DIR, "umit/pm/share/locale/"
                                                 "*/LC_MESSAGES/*.mo")):
    lang = filepath[len(ROOT_DIR) + len("umit/pm/share/locale/"):]
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
            "-d", os.path.join(ROOT_DIR, "umit", "pm",
                               "share", "doc", "doctrees"),
            os.path.join(ROOT_DIR, "umit", "pm", "share",
                         "doc", "src"), DOCS_DIR])

    def run(self):
        self.build_html_doc()
        build.run(self)

class pm_install(install):
    def run(self):
        print
        print "#" * 80
        print "# Installing PacketManipulator"
        print "#" * 80
        print

        install.run(self)
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

        dir = os.path.join(ROOT_DIR, self.install_data, 'share',
                           'PacketManipulator', 'audits')

        if not os.path.exists(dir):
            os.makedirs(dir)

        dest_dir = dir
        old_cd = os.getcwd()
        plugins_dir = os.path.join(ROOT_DIR, 'audits')
        os.chdir(plugins_dir)

        if os.name =="nt":
            os.system("C:\\python25\\python.exe setup-autogen.py passive")
            os.system("C:\\python25\\python.exe setup-autogen.py active")
        else:
            os.system("python setup-autogen.py passive")
            os.system("python setup-autogen.py active")

        print
        print "#" * 80
        print "# Building plugins"
        print "#" * 80
        print

        if os.name =="nt":
            os.system("C:\\python25\\python.exe setup-autogen.py "
                      "-o %s -b passive" % dest_dir)
            os.system("C:\\python25\\python.exe setup-autogen.py "
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

        dir = os.path.join(ROOT_DIR, self.install_data, 'share',
                           'PacketManipulator', 'plugins')

        if not os.path.exists(dir):
            os.makedirs(dir)

        # Ok now dir is our destination so we should make plugins

        dest_dir = dir
        old_cd = os.getcwd()
        plugins_dir = os.path.join(ROOT_DIR, 'plugins')

        os.putenv('PYTHONPATH',
                  '%s%s%s' % (ROOT_DIR, os.pathsep,
                              os.getenv('PYTHONPATH', '')))

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
            os.system("C:\\python25\\python.exe setup.py "
                      "build_ext -c mingw32 install")
        else:
            os.system("python setup.py install")

        for plugin in glob.glob("*.ump"):
            dest = os.path.join(dest_dir, os.path.basename(plugin))
            shutil.move(plugin, dest)




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
      package_dir  = {'umit' : os.path.join(ROOT_DIR, 'umit')},
      data_files   = [
                      (os.path.join('share', 'pixmaps', 'pm'),
                       glob.glob(os.path.join(ROOT_DIR, 'umit', 'pm', 'share',
                                              'pixmaps', 'pm', '*'))),
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
      scripts      = [os.path.join(ROOT_DIR, 'umit', 'pm',
                                   'PacketManipulator')],
      ext_modules  = modules,
      cmdclass     = {'install' : pm_install,
                      'build' : pm_build}
)
