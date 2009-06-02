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
This module is responsable for attack testing purpose
"""

import os
import sys
import optparse

from PM.Core.Atoms import generate_traceback
from PM.Manager.AttackManager import *

class Tester(object):
    def __init__(self, options, args):
        tester = AttackTester(args[0])

        modules = []
        filters = []

        if options.offline:
            filters = options.offline.replace(' ', '').split(',')

        if options.online:
            filters += options.online.replace(' ', '').split(',')

        for offline in filters:
            print 'Loading plugin: %s ...' % offline,

            path = os.path.join(os.getcwd(), 'offline', offline, 'sources')
            sys.path.insert(0, os.path.abspath(path))

            try:
                mod = __import__('main')
                modules.append(mod)

                for kplug in getattr(mod, '__plugins__', []):
                    plug_inst = kplug()
                    plug_inst.start(None)
                    plug_inst.register_decoders()

                print "OK"
            except Exception, err:
                print "FAILED"
                print generate_traceback()
            finally:
                sys.path.remove(os.path.abspath(path))
                del sys.modules['main']

        tester.dispatcher.main_decoder = AttackManager().get_decoder(LINK_LAYER, IL_TYPE_ETH)
        tester.start()
        tester.join()

if __name__ == "__main__":
    parser = optparse.OptionParser(usage='%s [options] FILE' % sys.argv[0])

    parser.add_option('-f', '--offline', action='store', dest='offline',
                      help='Comma separated list of offline plugins to use')
    parser.add_option('-n', '--online', action='store', dest='online',
                      help='Comma separated list of online plugins to use')

    Tester(*parser.parse_args())