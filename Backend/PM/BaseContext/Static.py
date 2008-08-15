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

from Backend.PM.Context import register_static_context

class BaseStaticContext(object):
    NOT_SAVED, SAVED = range(2)

    def __init__(self, title, fname=None):
        self._data = []
        self._title = title
        self._status = self.NOT_SAVED

        if fname:
            self._summary = fname
            self._cap_file = fname
        else:
            self._summary = ''
            self._cap_file = None

        self.title_callback = None

    def load(self):
        self.status = self.SAVED
    def save(self):
        self.status = self.SAVED

    def get_summary(self):
        return self._summary
    def set_summary(self, val):
        self._summary = val

    def get_data(self):
        return self._data
    def set_data(self, val):
        self._data = val

    def get_title(self):
        return self._title
    def set_title(self, val):
        self._title = val

        if self.title_callback:
            self.title_callback()

    def get_status(self):
        return self._status
    def set_status(self, val):
        self._status = val

    def get_cap_file(self):
        return self._cap_file
    def set_cap_file(self, val):
        self._cap_file = val

    data = property(get_data, set_data)
    title = property(get_title, set_title)
    summary = property(get_summary, set_summary)
    status = property(get_status, set_status)
    cap_file = property(get_cap_file, set_cap_file)

StaticContext = register_static_context(BaseStaticContext)
