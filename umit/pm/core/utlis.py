#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2010 Adriano Monteiro Marques
#
# Author: Gunjan Bansal <gunjanbansal000@gmail.com>
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


import os,imp
#list of modules that must be present to test presence of Btsniffer
#backed/bt_sniffer is a package

class BTSniffer_Available():

    def __init__(self):
        modules = ['umit/pm/backend/abstract/basecontext/btsniff',
                   'umit/pm/backend/bt_sniffer',
                   'umit/pm/backend/bt_sniffer/crack',
                   'umit/pm/backend/bt_sniffer/handlers',
                   'umit/pm/backend/bt_sniffer/sniffcommon',
                   'umit/pm/backend/bt_sniffer/tagger',
                   'umit/pm/backend/bt_sniffer/btsniff',
                   'umit/pm/backend/bt_sniffer/packet',
                   'umit/pm/backend/bt_sniffer/btlayers',
                   'umit/pm/backend/bt_sniffer/sniffer',
                   'umit/pm/backend/bt_sniffer/harness',
                   'umit/pm/backend/bt_sniffer/btsniff_fileio',
                   'umit/pm/backend/bt_sniffer/_crack',
                   'umit/pm/gui/sessions/btsniffsession',
                   'umit/pm/gui/dialogs/btinterface',
                   'umit/pm/gui/pages/btpacketpage',
                   'umit/pm/gui/pages/btsniffpage']
        self.flag_bt_check=True
        try:
            if os.name=='posix' :
                #find_module don't work with . notations.
                for module_name in modules:
                    if imp.find_module(module_name) is None:
                        self.flag_bt_check=False
                        break
            else:
                self.flag_bt_check=False
                #There are many more files which must be present for BTSniffer to work
                #These are the minimum files requried in the PM code(BTSniffer and PM together)
                #to precent crashes from happening(till btsniff is not invoked)
        except ImportError:
            self.flag_bt_check=False
    
    def Check(self):
        """
        Return True if BTsniffer is installed    
        """
        return self.flag_bt_check
