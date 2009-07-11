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
This module contains constants used by PM

All constants related to PacketManipulator
should be prefixed with 'PM_'
"""

import sys
import os, os.path

from Logger import log

try:
    PM_SVN_REVISION = """$Revision$"""
    PM_SVN_REVISION = PM_SVN_REVISION.split(" ")[1]
except:
    PM_SVN_REVISION = 'N/A'

PM_SITE = 'http://manipulator.umitproject.org'
PM_VERSION = '0.2'
PM_DEVELOPMENT = os.environ.get('PM_DEVELOPMENT', False)

PLATFORM = sys.platform
HOME = os.path.expanduser("~")
CURRENT_DIR = os.getcwd()
PM_HOME = os.path.join(HOME, '.PacketManipulator')

PM_PLUGINS_DIR = os.path.join(PM_HOME, 'plugins')
PM_PLUGINS_TEMP_DIR = os.path.join(PM_PLUGINS_DIR, 'plugins-temp')
PM_PLUGINS_DOWNLOAD_DIR = os.path.join(PM_PLUGINS_DIR, 'plugins-download')

main_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
main_dir = os.path.dirname(main_dir)

if PM_DEVELOPMENT:
    main_dir = os.path.join(main_dir, "PM")
elif hasattr(sys, "frozen"):
    main_dir = os.path.dirname(sys.executable)

LOCALE_DIR = os.path.join(main_dir, "share", "locale")
PIXMAPS_DIR = os.path.join(main_dir, "share", "pixmaps", "pm")
PLUGINS_DIR = os.path.join(main_dir, "share", "PacketManipulator", "plugins")

def create_dir(path):
    if os.path.exists(HOME) and \
       os.access(HOME, os.R_OK and os.W_OK) and \
       not os.path.exists(path):
        log.debug("Creating new directory under %s" % path)
        os.mkdir(path)

for new_dir in (PM_HOME,
                PM_PLUGINS_DIR,
                PM_PLUGINS_TEMP_DIR,
                PM_PLUGINS_DOWNLOAD_DIR):

    create_dir(new_dir)
