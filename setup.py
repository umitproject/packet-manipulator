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

from distutils.core import setup
import glob, os.path

setup(name         = 'PacketManipulator',
      version      = '0.1',
      description  = 'Packet manipulation made easy',
      author       = 'Francesco Piccinno',
      author_email = 'stack.box@gmail.com',
      url          = 'http://trac.umitproject.org/wiki/PacketManipulator/FrontEnd',
      license      = 'GNU GPL 2',
      requires     = ['gtk'],
      platforms    = ['Platform Indipendent'],
      packages     = ['PM',
                      'PM.Backend',
                      'PM.Backend.Abstract',
                      'PM.Backend.Abstract.BaseContext',
                      'PM.Backend.Abstract.Context',
                      'PM.Backend.Scapy',
                      'PM.Backend.Scapy.Context',
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
      data_files   = [('share/pixmaps/umit', glob.glob("PM/share/pixmaps/umit/*"))],
      scripts      = ['PM/PacketManipulator']
)
