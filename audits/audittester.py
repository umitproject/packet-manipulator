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
This module is responsable for audit testing purpose
"""

# Psyco importing result in the impossibility to debug threads.
# So commented for the moment

#import psyco
#psyco.full()

import os
import sys
import optparse

from umit.pm.gui.plugins.tree import *
from umit.pm.gui.plugins.engine import *
from umit.pm.manager.auditmanager import *
from umit.pm.core.netconst import IL_TYPE_ETH
from umit.pm.core.atoms import generate_traceback

class Tester(object):
    def __init__(self, options, args):
        if not args or not os.path.exists(args[0]):
            print "I need a pcap file as input to work."
            sys.exit(-1)

        if options.datalink is None:
            datalink = IL_TYPE_ETH
        else:
            datalink = options.datalink

        tester = AuditTester(args[0], datalink)

        modules = []
        filters = []

        if options.passive:
            filters = options.passive.replace(' ', '').split(',')

        if options.active:
            filters += options.active.replace(' ', '').split(',')

        instances = []

        for passive in filters:
            if not options.quiet:
                print 'Loading plugin: %s ...' % passive,

            if os.path.exists(os.path.join(os.getcwd(), 'passive', passive)):
                path = os.path.join(os.getcwd(), 'passive', passive, 'sources')
            else:
                path = os.path.join(os.getcwd(), 'active', passive, 'sources')

            sys.path.insert(0, os.path.abspath(path))

            try:
                mod = __import__('main')
                modules.append(mod)

                pkg = None

                for name, needs, provides, conflicts in \
                    getattr(mod, '__plugins_deps__', []):

                    pkg = Package(name, needs, provides, conflicts)
                    PluginEngine().tree.add_plugin_to_cache(pkg)

                ret = []

                for kplug in getattr(mod, '__plugins__', []):
                    confs = getattr(mod, '__configurations__', [])

                    for conf_name, conf_dict in confs:
                        AuditManager().register_configuration(conf_name, conf_dict)

                    plug_inst = kplug()

                    ret.append(plug_inst)

                instances.extend(ret)

                if pkg:
                    PluginEngine().tree.modules[pkg] = mod
                    PluginEngine().tree.instances[pkg] = ret

                if not options.quiet:
                    print "OK"
            except Exception, err:
                if not options.quiet:
                    print "FAILED"

                print generate_traceback()
            finally:
                sys.path.remove(os.path.abspath(path))
                del sys.modules['main']

        if options.setexp:
            for exp in options.setexp.split(','):
                try:
                    id, val = exp.split('=', 1)

                    g_id, id = id.rsplit('.', 1)
                    conf = AuditManager().get_configuration(g_id)


                    if isinstance(conf[id], bool):
                        if val.upper() == 'TRUE' or val == '1': conf[id] = True
                        else: conf[id] = False
                    elif isinstance(conf[id], int):
                        conf[id] = int(val)
                    else:
                        conf[id] = val
                except Exception, err:
                    if not options.quiet:
                        print "Wrong set expression %s" % exp

        try:
            for plug_inst in instances:
                plug_inst.start(None)

                if isinstance(plug_inst, AuditPlugin):
                    plug_inst.register_decoders()
                    plug_inst.register_hooks()

        except Exception, err:
            if not options.quiet:
                print "Error while starting plugin"
                print generate_traceback()

        AuditManager().global_conf['debug'] = True

        tester.start()
        tester.join()

if __name__ == "__main__":
    parser = optparse.OptionParser(usage='%s [options] FILE' % sys.argv[0])

    parser.add_option('-q', '--quiet', action='store_true', dest='quiet',
                      help='If quiet suppress useless output messages')
    parser.add_option('-f', '--passive', action='store', dest='passive',
                      help='Comma separated list of passive plugins to use')
    parser.add_option('-n', '--active', action='store', dest='active',
                      help='Comma separated list of active plugins to use')
    parser.add_option('-t', '--dltype', action='store', dest='datalink',
                      type='int', help='Type of datalink as integer')
    parser.add_option('-s', None, action='store', dest='setexp',
                      help='Option to set. Ex: -sdecoder.ip.checksum_check=1')
    parser.add_option('-p', '--profile', action='store_true', dest='profile',
                      help='Profile the code')

    options, args = parser.parse_args()

    def main():
        Tester(options, args)

    if options.profile:
        import hotshot, hotshot.stats
        prof = hotshot.Profile("audit.prof")
        prof.runcall(main)
        prof.close()

        stats = hotshot.stats.load("audit.prof")
        #stats.strip_dirs()
        stats.sort_stats('time').print_stats()#100)
        sys.exit(0)
    else:
        main()
