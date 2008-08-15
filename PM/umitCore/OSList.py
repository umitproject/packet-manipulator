#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import cPickle
from umitCore.OSListDump import os_dump_file

def load_dumped_os():
    of = open(os_dump_file, "rb")
    osd = cPickle.load(of)
    of.close()
    return osd


class OSList(object):
    def __init__(self):
        self.os = load_dumped_os()

    def get_match_list(self, osclass):
        if osclass in self.os.keys():
            return self.os[osclass]
        return None

    def get_class_list(self):
        return self.os.keys()
    
if __name__ == "__main__":
    o = OSList()

    from pprint import pprint
    pprint (o.os)
