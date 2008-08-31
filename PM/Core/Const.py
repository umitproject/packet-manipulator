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

PM_SVN_REVISION = """$Revision$"""
PM_VERSION = '0.1'
PM_DEVELOPMENT = os.environ.get('PM_DEVELOPMENT', False)

PLATFORM = sys.platform
HOME = os.path.expanduser("~")
CURRENT_DIR = os.getcwd()
PM_HOME = os.path.join(HOME, '.PacketManipulator')

main_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
main_dir = os.path.dirname(main_dir)

if PM_DEVELOPMENT:
    main_dir = os.path.join(main_dir, "PM")
elif hasattr(sys, "frozen"):
    main_dir = os.path.dirname(sys.executable)

LOCALE_DIR = os.path.join(main_dir, "share", "locale")
PIXMAPS_DIR = os.path.join(main_dir, "share", "pixmaps", "umit")

if os.path.exists(HOME) and \
   os.access(HOME, os.R_OK and os.W_OK) and \
   not os.path.exists(PM_HOME):
    log.debug("Creating PM home directory under %s" % PM_HOME)
    os.mkdir(PM_HOME)
