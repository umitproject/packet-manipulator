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

from umit.pm.backend.scapy.wrapper import *

# Scapy seems to respect wireshark nomenclature for protocol and fields.

global_trans = {
    'eth' : (Ether, None),
    'hdlc' : (HDLC, None),
    'ppp' : (PPP, None),
    'radiotap' : (RadioTap, None),
    'wifi' : (Dot11, None),
    'arp' : (ARP, None),
    'ip' : (IP, None),
    'icmp' : (ICMP, None),
    'tcp' : (TCP, None),
    'udp' : (UDP, None),
        'bootp' : (BOOTP, None),
            'dhcp' : (DHCP, None),
    'raw' : (Raw, None),
}

if "SMBHeader" in globals():
    global_trans_smb = {
        'nbt' : (NBTSession, None),
        'smb' : (SMBHeader, None),

        'smbneg_resp' : (SMBNegociate_Response, None),

        'smbsax_resp' : (SMBSetup_AndX_Response, None),
        'smbsax_resp_as' : (SMBSetup_AndX_Response_Advanced_Security, None),

        'smbsax_req' : (SMBSetup_AndX_Request, None),
        'smbsax_req_as' : (SMBSetup_AndX_Request_Advanced_Security, None),
        'smbtcax_req' : (SMBTree_Connect_AndX_Request, None),

        'dns' : (DNS, None),
        'dnsqr' : (DNSQR, None),
        'dnsrr' : (DNSRR, None),
    }
    global_trans.update(global_trans_smb)

