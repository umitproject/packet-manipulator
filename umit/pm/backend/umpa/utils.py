#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Luís A. Bastião Silva <luis.kop@gmail.com>
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

from umit.umpa.sniffing import get_available_devices
from umit.pm.backend import VirtualIFace

def find_all_devs(capmethod=0):
    """
    @param capmethod 0 for standard method, 1 for virtual interface,
                     2 for tcpdump/windump, 3 for dumpcap helper.
    @return a list containing VirtualIFace objects
    """

    ifaces = []

    for iface in get_available_devices():
        # XXX Implement something to get IP and MAC of interface (@UMPA)
        ip = "0.0.0.0"
        hw = "00:00:00:00:00:00"
        ifaces.append(VirtualIFace(iface, hw, ip))



    return ifaces


