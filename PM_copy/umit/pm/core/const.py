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

"""
This module contains constants used by PM

All constants related to PacketManipulator
should be prefixed with 'PM_'
"""

import sys
import os, os.path

from logger import log

try:
    PM_SVN_REVISION = """$Revision$"""
    PM_SVN_REVISION = PM_SVN_REVISION.split(" ")[1]
except:
    PM_SVN_REVISION = 'N/A'

PM_SITE = 'http://manipulator.umitproject.org'
PM_VERSION = '0.3'
PM_CODENAME = 'sneaky whisper'
PM_SLOGANS = ['Audaces fortuna adiuvat', 'Intelligenti pauca']
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
    main_dir = os.path.join(main_dir, "pm")
elif hasattr(sys, "frozen"):
    main_dir = os.path.dirname(sys.executable)

LOCALE_DIR = os.path.join(main_dir, "share", "locale")
PIXMAPS_DIR = os.path.join(main_dir, "share", "pixmaps", "pm")
PLUGINS_DIR = os.path.join(main_dir, "share", "PacketManipulator", "plugins")
AUDITS_DIR = os.path.join(main_dir, "share", "PacketManipulator", "audits")

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

# Enumeration of types supported by audit plugins
# Used as the value of <int id="configuration_id" description="desc">ENUM</int>
# to expose cfields setted by various audits to the GUI of PM.

PM_TYPE_NULL,      \
PM_TYPE_BOOLEAN,   \
PM_TYPE_INT,       \
PM_TYPE_FLOAT,     \
PM_TYPE_STR,       \
PM_TYPE_TUPLE,     \
PM_TYPE_LIST,      \
PM_TYPE_SET,       \
PM_TYPE_FROZENSET, \
PM_TYPE_DICT,      \
PM_TYPE_CLASS,     \
PM_TYPE_INSTANCE,  \
PM_TYPE_CALLABLE = range(13)

################################################################################
# Used by AttackManager. See also user_msg
################################################################################

STATUS_EMERG,   \
STATUS_ALERT,   \
STATUS_CRIT,    \
STATUS_ERR,     \
STATUS_WARNING, \
STATUS_NOTICE,  \
STATUS_INFO,    \
STATUS_DEBUG,   \
STATUS_NONE = range(9)
