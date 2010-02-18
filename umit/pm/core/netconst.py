#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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

###############################################################################
# Layers
###############################################################################

IFACE_LAYER   = 1
LINK_LAYER    = 2
NET_LAYER     = 3
PROTO_LAYER   = 4

# Here goes dissectors
APP_LAYER     = 5
APP_LAYER_TCP = 6
APP_LAYER_UDP = 7

###############################################################################
# Layer types
###############################################################################

# IFACE_LAYER types
IL_TYPE_ETH   = 0x01 # ethernet
IL_TYPE_TR    = 0x06 # token ring
IL_TYPE_PPP   = 0x09
IL_TYPE_FDDI  = 0x0a # fiber distributed data interface
IL_TYPE_RAWIP = 0x0c # raw ip dump file
IL_TYPE_WIFI  = 0x69 # wireless
IL_TYPE_COOK  = 0x71 # linux cooked
IL_TYPE_PRISM = 0x77 # prism2 header for wifi dumps

# LINK_LAYER types
LL_TYPE_IP   = 0x0800
LL_TYPE_IP6  = 0x86DD
LL_TYPE_ARP  = 0x0806
LL_TYPE_PPP  = 0x880B
LL_TYPE_VLAN = 0x8100

# NET_LAYER types
NL_TYPE_ICMP  = 0x01
NL_TYPE_ICMP6 = 0x3a
NL_TYPE_TCP   = 0x06
NL_TYPE_UDP   = 0x11
NL_TYPE_GRE   = 0x2f
NL_TYPE_OSPF  = 0x59
NL_TYPE_VRRP  = 0x70

# PROTO_LAYER types
PL_DEFAULT  = 0x0000

###############################################################################
# TCP headers flags
###############################################################################

TH_FIN = 0x01
TH_SYN = 0x02
TH_RST = 0x04
TH_PSH = 0x08
TH_ACK = 0x10
TH_URG = 0x20

###############################################################################
# ICMP types & codes
###############################################################################

ICMP_TYPE_ECHOREPLY     = 0
ICMP_TYPE_DEST_UNREACH  = 3
ICMP_TYPE_REDIRECT      = 5
ICMP_TYPE_ECHO          = 8
ICMP_TYPE_TIME_EXCEEDED = 11

ICMP_CODE_NET_UNREACH   = 0
ICMP_CODE_HOST_UNREACH  = 1

###############################################################################
# Reassembler
###############################################################################

REAS_SKIP_PACKET   = 0 # Useless packet skip it
REAS_COLLECT_DATA  = 1 # Data collection
REAS_COLLECT_STATS = 2 # Drop data collect only number of bytes

###############################################################################
# Metapacket constants
###############################################################################

MPKT_IGNORE       = 1
MPKT_DONT_DISSECT = 1 << 1
MPKT_FORWARDABLE  = 1 << 2
MPKT_FORWARDED    = 1 << 3
MPKT_FROMIFACE    = 1 << 4
MPKT_FROMBRIDGE   = 1 << 5
MPKT_MODIFIED     = 1 << 6
MPKT_DROPPED      = 1 << 7

###############################################################################
# Connection tracking constants
###############################################################################

CONN_UNDEFINED        = -1
CONN_JUST_ESTABLISHED = 0
CONN_DATA             = 1
CONN_RESET            = 2
CONN_CLOSE            = 3
CONN_TIMED_OUT        = 4

CN_IDLE      = 0
CN_OPENING   = 1
CN_OPEN      = 2
CN_ACTIVE    = 3
CN_CLOSING   = 4
CN_CLOSED    = 5
CN_KILLED    = 6

CN_INJECTED  = 1
CN_MODIFIED  = 2
CN_VIEWING   = 4
