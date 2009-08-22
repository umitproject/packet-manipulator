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
This module contains perspectives called also Pages:
    - PacketPage
    - SniffPage
    - SequencePage
"""

from sniffpage import SniffPage
from packetpage import PacketPage
from sequencepage import SequencePage

class PerspectiveType:
    PACKET_PERSPECTIVE, \
    SNIFF_PERSPECTIVE,  \
    SEQUENCE_PERSPECTIVE = range(3)

    types = {
        PacketPage   : 0,
        SniffPage    : 1,
        SequencePage : 2,

        0 : PacketPage,
        1 : SniffPage,
        2 : SequencePage
    }
