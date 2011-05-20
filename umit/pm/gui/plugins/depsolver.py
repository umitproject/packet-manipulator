#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009, 2011 Adriano Monteiro Marques
#
# Author: Francesco Piccinno <stack.box@gmail.com>
#         Guilherme Rezende <guilhermebr@gmail.com>
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
Module for managing dependencies among plugins
"""

from collections import deque
from umit.pm.core.logger import log
from umit.pm.gui.plugins.atoms import Version

class Graph():
    """
    A class for storage plugin information and resolve dependencies.

    >>> graph = Graph()
    >>> graph.append(
    ...       Node('SMBDissector', ['=vnc-1.0', '>mysql-1.0'], ['>tcp-1.0', '<udp-2.0'], [])
    ... )
    >>> graph.append(
    ...       Node('MySQLDissector', [], [], ['=mysql-1.1'])
    ...  )
    >>> graph.append(
    ...       Node('TCPDecoder', [], ['>ip-1.0'], ['=tcp-1.1'])
    ... )
    >>> graph.append(
    ...       Node('ShinyTCP', ['=eth-1.7'], ['>ip-1.0'], ['=tcp-1.6'])
    ... )
    >>> graph.append(
    ...       Node('UDPDecoder', [], ['>ip-1.0'], ['=udp-1.5'])
    ... )
    >>> graph.append(
    ...       Node('IPDecoder', [], ['>eth-1.0'], ['=ip-1.5'])
    ... )
    >>> graph.append(
    ...       Node('EthDecoder', [], [], ['=eth-1.7'])
    ... )
    >>> graph._list
    [Node: SMBDissector [], Node: MySQLDissector [('mysql', '=', 1.1.0)], Node: TCPDecoder [('tcp', '=', 1.1.0)], Node: ShinyTCP [('tcp', '=', 1.6.0)], Node: UDPDecoder [('udp', '=', 1.5.0)], Node: IPDecoder [('ip', '=', 1.5.0)], Node: EthDecoder [('eth', '=', 1.7.0)]]
    >>>
    >>> graph.get_dep_for("SMBDissector")
    [Node: SMBDissector [], Node: TCPDecoder [('tcp', '=', 1.1.0)], Node: UDPDecoder [('udp', '=', 1.5.0)], Node: IPDecoder [('ip', '=', 1.5.0)], Node: EthDecoder [('eth', '=', 1.7.0)]]
    >>>
    >>> graph._list
    [Node: SMBDissector [], Node: TCPDecoder [('tcp', '=', 1.1.0)], Node: ShinyTCP [('tcp', '=', 1.6.0)], Node: UDPDecoder [('udp', '=', 1.5.0)], Node: IPDecoder [('ip', '=', 1.5.0)], Node: EthDecoder [('eth', '=', 1.7.0)]]
    >>>
    >>> graph.remove("TCPDecoder")
    >>>
    >>> graph.get_dep_for("SMBDissector")
    []
    >>>
    >>> graph._list
    [Node: SMBDissector [], Node: ShinyTCP [('tcp', '=', 1.6.0)], Node: UDPDecoder [('udp', '=', 1.5.0)], Node: IPDecoder [('ip', '=', 1.5.0)]]
    """

    def __init__(self, lst=[]):
        self._list = lst

    def clone(self):
        return Graph(self._list[:])

    def append(self, node):
        log.debug("Appending %s to the dep-graph" % str(node))
        self._list.append(node)

    def remove(self, name):
        node = self.get_by_name(name)
        self._list.remove(node)

    def get_by_name(self, value):
        for node in self._list:
            if node.name == value:
                return node

    def _check_validity(self, provide, need):
        if provide[0] != need[0]:
            return False

        need_str, need_op, need_ver = need
        prov_str, prov_op, prov_ver = provide

        return need_op(prov_ver, need_ver)

    def _has_conflicts(self, load_list, target):
        for conf in target.conflicts:
            conf_str, conf_op, conf_ver = conf

            for node in load_list:
                for provide in node.provides:
                    prov_str, prov_op, prov_ver = provide

                    if conf_str != prov_str:
                        continue

                    if conf_op(prov_ver, conf_ver):
                        return True
        return False

    def remove_conflicts_for(self, target):
        for conf in target.conflicts:
            conf_str, conf_op, conf_ver = conf

            for node in self._list:
                for provide in node.provides:
                    prov_str, prov_op, prov_ver = provide

                    if conf_str != prov_str:
                        continue

                    if conf_op(prov_ver, conf_ver):
                        log.info("Removing Conflict Node: %s" % str(node))
                        self._list.remove(node)

    def _add_to_queue(self, target, queue):
        if target not in queue:
            queue.append(target)

    def get_dep_for(self, start, queue=None, load_list=None):
        if queue is None:
            node = self.get_by_name(start)
            queue = deque()
            queue.append(node)

        if load_list is None:
            load_list = []

        while queue:
            node = queue.popleft()

            self.remove_conflicts_for(node)

            for need in node.needs:
                first_stage = []

                for target in self._list:
                    for provide in target.provides:
                        if self._check_validity(provide, need):
                            first_stage.append(target)
                            continue

                if not first_stage:
                    log.info("No dep matching your needs %s" % str(need))
                    return []

                elif len(first_stage) == 1:
                    self._add_to_queue(first_stage[0], queue)

                elif len(first_stage) > 1:
                    def check_major_version(node1, node2):
                        return Version.__cmp__(node1.provides[0][2], node2.provides[0][2])

                    first_stage.sort(check_major_version)
                    first_stage.reverse()
                    log.info("First_stage sorted: %s" % str(first_stage))

                    for target in first_stage:
                        fake_graph = Graph(lst=list(self._list))
                        fake_graph.remove_conflicts_for(target)
                        part_list = fake_graph.get_dep_for(target.name)

                        if not part_list:
                            continue

                        self._add_to_queue(target, queue)
                        break

            if node not in load_list:
                load_list.append(node)
        return load_list

class Node(object):
    def __init__(self, name, conflicts, needs, provides):
        """
        @param name an identification string for the plugin
        @param conflicts a list of conflict VersionString ['=ftp-lib-1.0', ..]
        @param needs a list of need VersionString
        @param provides a list of provide VersionString
        """
        self.name = name
        self.conflicts = [Version.extract_version(item) for item in conflicts]
        self.provides  = [Version.extract_version(item) for item in provides]
        self.needs   = [Version.extract_version(item) for item in needs]

    def __repr__(self):
        return "Node: %s %s" % (self.name, str(self.provides))

if __name__ == '__main__':
    import doctest
    doctest.testmod()
