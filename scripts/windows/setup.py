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

import sys
import glob
import os, os.path

if os.name == 'nt':
    try:
        import py2exe
    except ImportError:
        print "Install py2exe to use setup.py"
        sys.exit(-1)


from distutils.core import setup, Extension
from PM.Core.Const import PM_VERSION

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
        os.chdir("PM/moo")
        os.system("make")
        os.system("make moo-pygtk.c")
        os.chdir("../..")
    
        moo = Extension(
            'PM.Gui.moo_stub',
            [
                'PM/moo/moopane.c',
                'PM/moo/moopaned.c',
                'PM/moo/moobigpaned.c',
                'PM/moo/moomarshals.c',
                'PM/moo/moo-pygtk.c',
                'PM/moo/moo-stub.c',
            ],
            include_dirs=pkc_get_include_dirs('gtk+-2.0 pygtk-2.0'),
            libraries=pkc_get_libraries('gtk+-2.0 pygtk-2.0'),
            library_dirs=pkc_get_library_dirs('gtk+-2.0 pygtk-2.0'),
        )
    else:
        moo = Extension(
            'PM.Gui.moo_stub',
            [
                'PM/moo/moopane.c',
                'PM/moo/moopaned.c',
                'PM/moo/moobigpaned.c',
                'PM/moo/moomarshals.c',
                'PM/moo/moo-pygtk.c',
                'PM/moo/moo-stub.c',
            ],
            include_dirs=[
                "C:\\GTK\\include\\gtk-2.0", "C:\\GTK\\include\\glib-2.0",
                "C:\\GTK\\include\\atk-1.0", "C:\\GTK\\include\\pango-1.0",
                "C:\\GTK\\include\\cairo",
                "C:\\GTK\\lib\\gtk-2.0\\include", "C:\\GTK\\lib\\glib-2.0\\include",
                "C:\\Python25\\include\\pycairo", "C:\\Python25\\include\\pygtk-2.0"
                ],
            library_dirs=["C:\\GTK\\lib"],
            libraries=["gtk-win32-2.0", "gthread-2.0", "glib-2.0", "gobject-2.0", "gdk-win32-2.0", "gdk_pixbuf-2.0"]
        )

    modules = [moo]

mo_files = []

for filepath in glob.glob("PM/share/locale/*/LC_MESSAGES/*.mo"):
    lang = filepath[len("PM/share/locale/"):]
    targetpath = os.path.dirname(os.path.join("share/locale",lang))
    mo_files.append((targetpath, [filepath]))

setup(name         = 'PacketManipulator',
      version      = PM_VERSION,
      description  = 'Packet manipulation made easy',
      author       = 'Francesco Piccinno',
      author_email = 'stack.box@gmail.com',
      url          = 'http://trac.umitproject.org/wiki/PacketManipulator/FrontEnd',
      license      = 'GNU GPL 2',
      requires     = ['gtk'],
      platforms    = ['Platform Independent'],
      packages     = ['PM',
                      'PM.Backend',
                      'PM.Backend.Abstract',
                      'PM.Backend.Abstract.BaseContext',
                      'PM.Backend.Abstract.Context',
                      'PM.Backend.Scapy',
                      'PM.Backend.Scapy.Context',
                      'PM.Backend.UMPA',
                      'PM.Backend.UMPA.Context',
                      'PM.Manager',
                      'PM.Core',
                      'PM.Gui',
                      'PM.Gui.Core',
                      'PM.Gui.Tabs',
                      'PM.Gui.Pages',
                      'PM.Gui.Dialogs',
                      'PM.Gui.Widgets',
                      'PM.higwidgets'
                     ],
      data_files   = [('share/pixmaps/umit', glob.glob("PM/share/pixmaps/umit/*"))] + mo_files, 
      scripts      = ['PM/PacketManipulator'],
      windows      = [{'script' : 'PM/PacketManipulator',
                       'icon_resources' : [(1, 'PM/share/pixmaps/umit/pm-icon48.ico')]}],
      options      = {'py2exe' : {
                          'compressed' : 1,
                          'packages' : 'encodings, scapy',
                          'includes' : 'gtk,pango,atk,gobject,encodings,encodings.*,cairo,pangocairo,atk'},
                      'build': {'compiler' : 'mingw32'}},
      ext_modules=modules
)
