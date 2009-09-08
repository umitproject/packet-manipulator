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

from __future__ import with_statement

from datetime import datetime
from threading import Thread, Lock

from umit.pm.core.i18n import _
from umit.pm.backend.scapy import *

def register_sniff_context(BaseSniffContext):
    class SniffContext(BaseSniffContext):
        """
        A sniff context for controlling various options.
        """
        has_stop = False
        has_pause = False
        has_restart = False

        def __init__(self, *args, **kwargs):
            BaseSniffContext.__init__(self, *args, **kwargs)

            self.title = _('%s capture') % self.iface

        def get_percentage(self):
            return 100.0

        def _start(self):
            self.summary = _('Sniff is not avaiable with this backend')
            return False

    return SniffContext
