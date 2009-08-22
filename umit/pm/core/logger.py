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
Logger module

Use PM_LOGLEVEL to set the loglevel and
    PM_LOGEXCLUDE to exclude certain log records
"""

import os
import re

from logging import Logger, StreamHandler, Formatter, addLevelName
from logging import __status__ as STATUS

# Avoid coloring the terminal if PM_NOCOLORTERM is setted
if os.name == 'posix' and not os.getenv('PM_NOCOLORTERM', ''):
    reset = "\033[1;0m"
    yellow = "\033[1;33m"
    green = "\033[1;32m"
    brown = "\033[0;33m"
    red = "\033[1;31m"
else:
    reset = yellow = green = brown = red = ''

if os.getenv('PM_HAPPY', ''):
    addLevelName(10, '%s boring stuff: -.- %s' % (brown, reset))
    addLevelName(20, '%s blah blah :> %s' % (green, reset))
    addLevelName(30, '%s what the hell? :( %s' % (yellow, reset))
    addLevelName(40, '%s wtf?! :o %s' % (red, reset))
    addLevelName(50, '%s OMFADG! :oo %s' % (red, reset))
else:
    addLevelName(10, '%sDBG%s' % (brown, reset))
    addLevelName(20, '%sINF%s' % (green, reset))
    addLevelName(30, '%sWRN%s' % (yellow, reset))
    addLevelName(40, '%sERR%s' % (red, reset))
    addLevelName(50, '%sCRI%s' % (red, reset))

class PMLogHandler(StreamHandler):
    def __init__(self):
        regex = os.getenv('PM_LOGEXCLUDE', '')

        if regex:
            try:
                rex = re.compile(regex)
                print "Using %s to filter logging" % regex
                self.rex = rex
            except:
                print "Error while compiling except regex %s" % regex
                self.rex = None
        else:
            self.rex = None

        StreamHandler.__init__(self)

    def emit(self, record):
        if self.rex and self.rex.findall(self.format(record)):
            return

        StreamHandler.emit(self, record)

class PMLogger(Logger, object):
    def __init__(self, name, level):
        Logger.__init__(self, name, level)
        self.formatter = self.format

        self.handler = PMLogHandler()
        self.handler.setFormatter(self.formatter)

        self.addHandler(self.handler)

    def get_formatter(self):
        return self.__formatter

    def set_formatter(self, fmt):
        self.__formatter = Formatter(fmt)

    format = "(%(levelname)s) %(threadName)s:%(msecs)dms at %(filename)s:" \
             "%(lineno)d $(): %(message)s".replace("$",
        (STATUS != "beta") and ("%(funcName)s") or ("")
    )

    formatter = property(get_formatter, set_formatter, doc="")
    __formatter = Formatter(format)

try:
    level = 30 # default value
    level = int(os.getenv('PM_LOGLEVEL', '30'))
finally:
    log = PMLogger("PM", level)
