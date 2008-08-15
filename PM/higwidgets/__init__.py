#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
#         Cleber Rodrigues <cleber.gnu@gmail.com>
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
higwidgets/__init__.py

This module implements GTK Widgets that try their best to adhere to the
GNOME Human Interface Guidelines (aka HIG).

This is mostly implemented by subclassing from the GTK classes, and
providing defaults that better match the HIG specifications/recomendations.
"""

from gtkutils import *
from higboxes import *
from higbuttons import *
from higdialogs import *
from higentries import *
from higexpanders import *
from higlabels import *
from higlogindialogs import *
from higprogressbars import *
from higscrollers import *
from higspinner import *
from higtables import *
from higtextviewers import *
from higwindows import *
