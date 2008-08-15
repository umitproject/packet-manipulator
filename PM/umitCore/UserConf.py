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

import os
import os.path

from umitCore.BasePaths import base_paths
from umitCore.UmitLogging import log


umit_conf_content = '''[diff]
colored_diff = True

[output_highlight]
enable_highlight = True

[diff_colors]
unchanged = [65213, 65535, 38862]
added = [29490, 42662, 54079]
not_present = [58079, 19076, 12703]
modified = [63881, 42182, 13193]
'''

target_list_content = ''' '''

recent_scans_content = ''' '''

scan_profile_content = '''[Quick Scan]
description = 
hint = 
options = Disable reverse DNS resolution,Aggressive,Verbose
command = nmap -T Aggressive -v -n %s
annotation = 

[Intense Scan]
description = 
hint = 
options = Version detection,Operating system detection,Aggressive, Verbose
command = nmap -T Aggressive -A -v %s
annotation = 

[Regular Scan]
description = 
hint = 
options = Verbose
command = nmap -v %s
annotation = 

[Quick and verbose scan]
description = 
hint = 
options = Watch packets,Verbose,Debug,Aggressive,Disable reverse DNS resolution
command = nmap -d -T Aggressive --packet_trace -v -n %s
annotation = 

[Operating System Detection]
description = 
hint = 
options = Operating system detection,Verbose
command = nmap -O -v %s
annotation = 

[Quick Services version detection]
description = 
hint = 
options = Version detection,Aggressive,Verbose
command = nmap -T Aggressive -sV -v %s
annotation = 

[Quick Full version Detection Scan]
description = 
hint = 
options = Aggressive,Version detection,Operating system detection,Disable reverse DNS resolution,Verbose
command = nmap -T Aggressive -sV -n -O -v %s
annotation = 

[Quick Operating System detection]
description = 
hint = 
options = Operating system detection,Aggressive,Verbose
command = nmap -T Aggressive -O -v %s
annotation =  '''

profile_editor_content = '''<?xml version="1.0"?>
<interface>
  <groups>
    <group name="Scan"/>
    <group name="Ping"/>
    <group name="Target"/>
    <group name="Source"/>
    <group name="Other"/>
    <group name="Advanced"/>
  </groups>
  <Scan label="Scan options">
    <option_list label="TCP scan: ">
      <option name="None"/>
      <option name="ACK scan"/>
      <option name="FIN scan"/>
      <option name="Null Scan"/>
      <option name="TCP SYN Scan"/>
      <option name="TCP connect Scan"/>
      <option name="Window Scan"/>
      <option name="Xmas Tree"/>
    </option_list>    
    <option_list label="Special scans: ">
      <option name="None"/>
      <option name="IP protocol Scan"/>
      <option name="List Scan"/>
      <option name="Ping scanning"/>
    </option_list>    
    <option_list label="Timing: ">
      <option name="None"/>
      <option name="Paranoid"/>
      <option name="Sneaky"/>
      <option name="Polite"/>
      <option name="Normal"/>
      <option name="Aggressive"/>
      <option name="Insane"/>
    </option_list>    
    <option_check label="FTP bounce attack" option="FTP bounce attack" arg_type="str"/>
    <option_check label="Idle Scan (Zombie)" option="Idle Scan" arg_type="str"/>
    <option_check label="Services version detection" option="Version detection"/>
    <option_check label="Operating system detection" option="Operating system detection"/>
    <option_check label="Disable reverse DNS resolution" option="Disable reverse DNS resolution"/>
    <option_check label="IPv6 support" option="IPv6 support"/>
    <option_check label="Maximum Retries" option="Max Retries" arg_type="int"/>
  </Scan>
  <Ping label="Ping options">
    <option_check label="Don't ping before scanning" option="Ping after Scan"/>
    <option_check label="ICMP ping" option="ICMP ping"/>
    <option_check label="ICMP timestamp request" option="ICMP timestamp"/>
    <option_check label="ICMP netmask request" option="ICMP netmask"/>
    <option_check label="Default ping type" option="Default ping"/>
    <option_check label="ACK ping" option="TCP ACK" arg_type="str"/>
    <option_check label="SYN ping" option="TCP SYN" arg_type="str"/>
    <option_check label="UDP probes" option="UDP Probe" arg_type="str"/>
  </Ping>
  <Target label="Target options">
    <option_check label="Excluded hosts/networks" option="Excluded hosts/networks" arg_type="str"/>
    <option_check label="Excluded hosts/networks from file" option="Excluded hosts/networks from file" arg_type="path"/>
    <option_check label="Read hosts to be scanned from file" option="Read hosts from file" arg_type="path"/>
    <option_check label="Scan random hosts" option="Scan random hosts" arg_type="int"/>
    <option_check label="Ports to scan" option="Ports to scan" arg_type="str"/>
    <option_check label="Only scan ports listed on services" option="Scan services ports"/>
  </Target>
  <Source label="Source options">
    <option_check label="Use decoys to hide identity" option="Use decoys" arg_type="str"/>
    <option_check label="Set source IP address" option="Set source IP" arg_type="str"/>
    <option_check label="Set source port" option="Set source port" arg_type="str"/>
    <option_check label="Set network interface" option="Set network interface" arg_type="str"/>
  </Source>
  <Other label="Other options">
    <option_check label="Extra options definied by user" option="Extra" arg_type="str"/>
    <option_check label="Set IPv4 time to live (ttl)" option="Set IPv4 ttl" arg_type="str"/>
    <option_check label="Fragment IP packets" option="Fragment IP Packets"/>
    <option_check label="Verbosity level" option="Verbose" arg_type="level"/>
    <option_check label="Debugging level" option="Debug" arg_type="level"/>
    <option_check label="Watch packets" option="Watch packets"/>
    <option_check label="Disable randomizing scanned ports" option="Disable randomizing scanned ports"/>
  </Other>
  <Advanced label="Advanced options">
    <option_check label="Time spent before giving up on an IP" option="Time before give up IP" arg_type="int"/>
    <option_check label="Time spent before retransmitting or timing out" option="Time before retransmitting" arg_type="int"/>
    <option_check label="Minimum timeout time per probe" option="Min timeout per probe" arg_type="int"/>
    <option_check label="Specifies the initial probe timeout" option="Initial probe timeout" arg_type="int"/>
    <option_check label="Maximum number of hosts in parallel" option="Max parallel hosts" arg_type="int"/>
    <option_check label="Minimum number of hosts in parallel" option="Min parallel hosts" arg_type="int"/>
    <option_check label="Maximum number of scans in parallel" option="Max parallel scans" arg_type="int"/>
    <option_check label="Minimum number of scans in parallel" option="Min parallel scans" arg_type="int"/>
    <option_check label="Maximum amount of time between probes" option="Max time between probes" arg_type="int"/>
    <option_check label="Minimum amount of time between probes" option="Min time between probes" arg_type="int"/>
  </Advanced>
</interface>'''

options_content = '''<?xml version="1.0"?>
<nmap_options>
  <option name="FTP bounce attack"
          option="-b %s"
          hint="Try to use a given FTP server as proxy"
          arguments="Host in standard URL notation: username:password@server:port"
          need_root="0"/>
          
  <option name="Max Retries"
          option="--max_retries %s"
          hint="Limit the maximum number of retransmissions the port scan engine should do"
          arguments="The number of retransmissions"
          need_root="0"/>
          
  <option name="ACK scan"
          option="-sA"
          hint="Try to discover firewall rulesets"
          arguments=""
          need_root="1"/>
          
  <option name="FIN scan"
          option="-sF"
          hint="Stealth FIN scan mode"
          arguments=""
          need_root="1"/>
          
  <option name="Idle Scan"
          option="-sI %s"
          hint="Use a zombie host to scan a given target"
          arguments="Zombie host address in the format: host[:probeport]"
          need_root="0"/>
          
  <option name="Null Scan"
          option="-sN"
          hint="Stealth Null Scan"
          arguments=""
          need_root="1"/>
          
  <option name="TCP SYN Scan"
          option="-sS"
          hint="Default TCP Scan for root user"
          arguments=""
          need_root="1"/>
          
  <option name="TCP connect Scan"
          option="-sT"
          hint="Default TCP Scan for non-root users"
          arguments=""
          need_root="0"/>
          
  <option name="Window Scan"
          option="-sW"
          hint="Window Scan"
          arguments=""
          need_root="1"/>
          
  <option name="Xmas Tree"
          option="-sX"
          hint="Stealth Xmas Scan"
          arguments=""
          need_root="1"/>
          
  <option name="IP protocol Scan"
          option="-sO"
          hint="Scan for IP protocols"
          arguments=""
          need_root="1"/>
          
  <option name="IP protocol Scan with number"
          option="-sO -p%"
          hint="Scan for IP protocols"
          arguments=""
          need_root="1"/>
          
  <option name="List Scan"
          option="-sL"
          hint=""
          arguments=""
          need_root="0"/>
          
  <option name="Ping scanning"
          option="-sP"
          hint=""
          arguments=""
          need_root="0"/>
          
  <option name="Paranoid"
          option="-T Paranoid"
          hint="Slowest scan (Avoid IDS detection)"
          arguments=""
          need_root="0"/>
          
  <option name="Sneaky"
          option="-T Sneaky"
          hint="Slower scan"
          arguments=""
          need_root="0"/>
          
  <option name="Polite"
          option="-T Polite"
          hint="Slow scan"
          arguments=""
          need_root="0"/>
          
  <option name="Normal"
          option="-T Normal"
          hint="Default scan"
          arguments=""
          need_root="0"/>
          
  <option name="Aggressive"
          option="-T Aggressive"
          hint="Fast scan"
          arguments=""
          need_root="0"/>
          
  <option name="Insane"
          option="-T Insane"
          hint="Faster scan"
          arguments=""
          need_root="0"/>
          
  <option name="Version detection"
          option="-sV"
          hint="Try to detect version of services on scanned hosts"
          arguments=""
          need_root="0"/>
          
  <option name="Operating system detection"
          option="-O"
          hint="Try to detect running OS on scanned hosts"
          arguments=""
          need_root="1"/>
          
  <option name="Disable reverse DNS resolution"
          option="-n"
          hint=""
          arguments=""
          need_root="1"/>
          
  <option name="Ping after Scan"
          option="-P0"
          hint="Don't ping hosts before scanning"
          arguments=""
          need_root="0"/>
          
  <option name="TCP ACK"
          option="-PA%s"
          hint="TCP ACK ping a host or network"
          arguments="List of tageted ports"
          need_root="0"/>
          
  <option name="TCP SYN"
          option="-PS%s"
          hint="TCP SYN ping a host or network"
          arguments="List of tageted ports"
          need_root="1"/>
          
  <option name="UDP Probe"
          option="-PU%s"
          hint="UDP probes to ping a host or network"
          arguments="List of targeted ports"
          need_root="0"/>
          
  <option name="ICMP ping"
          option="-PE"
          hint="ICMP ping a host or network"
          arguments=""
          need_root="1"/>
          
  <option name="ICMP timestamp"
          option="-PP"
          hint="ICMP timestamp request to ping host or network"
          arguments=""
          need_root="1"/>
          
  <option name="ICMP netmask"
          option="-PM"
          hint="ICMP netmask request to ping host or network"
          arguments=""
          need_root="1"/>
          
  <option name="Default ping"
          option="-PB"
          hint="Default Ping"
          arguments=""
          need_root="0"/>
          
  <option name="IPv6 support"
          option="-6"
          hint="Enable IPv6 support"
          arguments=""
          need_root="1"/>
          
  <option name="Excluded hosts/networks"
          option='--exclude %s'
          hint="Exclude given hosts/networks separated by comma"
          arguments=""
          need_root="0"/>

  <option name="Excluded hosts/networks from file"
          option='--excludefile "%s"'
          hint="Exclude hosts/networks inside given file"
          arguments=""
          need_root="0"/>

  <option name="Read hosts from file"
          option='-iL "%s"'
          hint="Read hosts to be scanned from given file"
          arguments=""
          need_root="0"/>
          
  <option name="Scan random hosts"
          option="-iR %s"
          hint="Nmap will generate a given number of random hosts to be scanned. Use '0' to infinite number of random hosts."
          arguments=""
          need_root="0"/>
          
  <option name="Ports to scan"
          option="-p%s"
          hint="Select ports to be scanned"
          arguments=""
          need_root="0"/>

  <option name="Scan services ports"
          option="-F"
          hint="Only scan ports listed on services file"
          arguments=""
          need_root="0"/>
          
  <option name="Use decoys"
          option="-D %s"
          hint="Use given decoys to hide identity"
          arguments=""
          need_root="1"/>
         
  <option name="Set source IP"
          option="-S %s"
          hint="Set source IP address"
          arguments=""
          need_root="1"/>
          
  <option name="Set source port"
          option="--source_port %s"
          hint="Use given ports as source for scans"
          arguments=""
          need_root="0"/>
          
  <option name="Set network interface"
          option="-e %s"
          hint="Use given network interface to scan"
          arguments=""
          need_root="0"/>
          
  <option name="IP protocol scan"
          option="-sO"
          hint="Scan for IP protocols"
          arguments=""
          need_root="1"/>
          
  <option name="List scan"
          option="-sL"
          hint="Scan for IP protocols"
          arguments=""
          need_root="0"/>
          
  <option name="Ping scanning"
          option="-sP"
          hint="Ping hosts in a given network to figure out which hosts are up"
          arguments=""
          need_root="0"/>
          
  <option name="Fragment IP Packets"
          option="-f"
          hint="Split up TCP headers over several packets."
          arguments=""
          need_root="1"/>
          
  <option name="Set IPv4 ttl"
          option="--ttl %s"
          hint="Set IPv4 time to live (ttl)."
          arguments=""
          need_root="1"/>
          
  <option name="Disable randomizing scanned ports"
          option="-r"
          hint="Avoid random port scan"
          arguments=""
          need_root="0"/>
          
  <option name="Fragment Size"
          option="--mtu %s"
          hint="Specify fragments size"
          arguments="Fragment size"
          need_root="1"/>
          
  <option name="UDP Scan"
          option="-sU"
          hint="Scan for udp services"
          arguments=""
          need_root="1"/>
          
  <option name="Specific Scan"
          option="-p%s"
          hint="Scan for an specific IP Protocol"
          arguments="Number of the protocols to be scaned"
          need_root="1"/>
          
  <option name="Limit OS Detection"
          option="--osscan_limit"
          hint="Only try to discover OS if there is at least one open and one closed TCP port"
          arguments=""
          need_root="1"/>
          
  <option name="Time before give up IP"
          option="--host_timeout %s"
          hint="Time spent before giving up on an IP"
          arguments=""
          need_root="0"/>
          
  <option name="Time before retransmitting"
          option="--max_rtt_timeout %s"
          hint="Time spent before retransmitting or timing out"
          arguments=""
          need_root="0"/>

  <option name="Min timeout per probe"
          option="--min_rtt_timeout %s"
          hint="Minimum amount of timeout time per probe"
          arguments=""
          need_root="0"/>
          
  <option name="Initial probe timeout"
          option="--initial_rtt_timeout %s"
          hint="Initial amount of timeout time per probe"
          arguments=""
          need_root="0"/>
          
  <option name="Max parallel hosts"
          option="--max_hostgroup %s"
          hint="Maximum number of parallel hosts"
          arguments=""
          need_root="0"/>
          
  <option name="Min parallel hosts"
          option="--min_hostgroup %s"
          hint="Minimum number of parallel hosts"
          arguments=""
          need_root="0"/>
          
  <option name="Max parallel scans"
          option="--max_parallelism %s"
          hint="Maximum number of parallel scans"
          arguments=""
          need_root="0"/>
          
  <option name="Min parallel scans"
          option="--min_parallelism %s"
          hint="Minimum number of parallel scans"
          arguments=""
          need_root="0"/>
          
  <option name="Max time between probes"
          option="--scan_delay %s"
          hint="Maximum time between scan probes"
          arguments=""
          need_root="0"/>
          
  <option name="Min time between probes"
          option="--max_scan_delay %s"
          hint="Minimum time between scan probes"
          arguments=""
          need_root="0"/>
          
  <option name="None"
          option=""
          hint=""
          arguments=""
          need_root="0"/>
          
  <option name="Extra"
          option="%s"
          hint=""
          arguments=""
          need_root="0"/>
          
  <option name="Verbose"
          option="-v"
          hint="Raise verbosity level"
          arguments=""
          need_root="0"/>
          
  <option name="Debug"
          option="-d"
          hint="Raise debug level"
          arguments=""
          need_root="0"/>
          
  <option name="Watch packets"
          option="--packet-trace"
          hint="Watch packet while they go through the network"
          arguments=""
          need_root="0"/>
</nmap_options>'''

wizard_content = '''<?xml version="1.0"?>
<interface>
  <groups>
    <group name="Scan"/>
    <group name="Ping"/>
    <group name="Target"/>
    <group name="Source"/>
    <group name="Other"/>
  </groups>
  <Scan label="Choose Scan Type">
    <option_list label="TCP scan">
      <option name="None"/>
      <option name="ACK scan"/>
      <option name="FIN scan"/>
      <option name="Null Scan"/>
      <option name="TCP SYN Scan"/>
      <option name="TCP connect Scan"/>
      <option name="Window Scan"/>
      <option name="Xmas Tree"/>
    </option_list>
    <option_list label="Special scans: ">
      <option name="None"/>
      <option name="IP protocol Scan"/>
      <option name="List Scan"/>
      <option name="Ping scanning"/>
    </option_list>
    <option_list label="Timing: ">
      <option name="None"/>
      <option name="Paranoid"/>
      <option name="Sneaky"/>
      <option name="Polite"/>
      <option name="Normal"/>
      <option name="Aggressive"/>
      <option name="Insane"/>
    </option_list>    
    <option_check label="Services version detection" option="Version detection"/>
    <option_check label="Operating system detection" option="Operating system detection"/>
  </Scan>
  <Ping label="Ping options">
    <option_check label="Don't ping before scanning" option="Ping after Scan"/>
    <option_check label="ICMP ping" option="ICMP ping"/>
    <option_check label="ICMP timestamp request" option="ICMP timestamp"/>
    <option_check label="ICMP netmask request" option="ICMP netmask"/>
    <option_check label="Default ping type" option="Default ping"/>
    <option_check label="ACK ping" option="TCP ACK" arg_type="str"/>
    <option_check label="SYN ping" option="TCP SYN" arg_type="str"/>
    <option_check label="UDP probes" option="UDP Probe" arg_type="str"/>
  </Ping>
  <Target label="Target options">
    <option_check label="Excluded hosts/networks" option="Excluded hosts/networks" arg_type="str"/>
    <option_check label="Ports to scan" option="Ports to scan" arg_type="str"/>
    <option_check label="Only scan ports listed on services" option="Scan services ports"/>
  </Target>
  <Source label="Source options">
    <option_check label="Use decoys to hide identity" option="Use decoys" arg_type="str"/>
    <option_check label="Set source IP address" option="Set source IP" arg_type="str"/>
    <option_check label="Set source port" option="Set source port" arg_type="str"/>
  </Source>
  <Other label="Other options">
    <option_check label="Extra options definied by user" option="Extra" arg_type="str"/>
    <option_check label="Set IPv4 time to live (ttl)" option="Set IPv4 ttl" arg_type="str"/>
    <option_check label="Fragment IP packets" option="Fragment IP Packets"/>
    <option_check label="Verbosity level" option="Verbose" arg_type="level"/>
    <option_check label="Debugging level" option="Debug" arg_type="level"/>
    <option_check label="Watch packets" option="Watch packets"/>
  </Other>
</interface>'''

services_dump_content = """(dp1
S'radmin'
p2
(dp3
S'comment'
p4
S'Radmin (www.radmin.com) remote PC control software'
p5
sS'udp'
p6
I00
sS'ddp'
p7
I00
sS'ports'
p8
(lp9
I4899
asS'tcp'
p10
I01
ssS'zannet'
p11
(dp12
g4
S''
sg6
I01
sg7
I00
sg8
(lp13
I317
asg10
I01
ssS'freeciv'
p14
(dp15
g4
S''
sg6
I00
sg7
I00
sg8
(lp16
I5555
asg10
I01
ssS'dlswpn'
p17
(dp18
g4
S'Data Link Switch Write Port Number'
p19
sg6
I01
sg7
I00
sg8
(lp20
I2067
asg10
I01
ssS'proshare2'
p21
(dp22
g4
S'Proshare Notebook Application'
p23
sg6
I01
sg7
I00
sg8
(lp24
I1460
asg10
I01
ssS'proshare1'
p25
(dp26
g4
S'Proshare Notebook Application'
p27
sg6
I01
sg7
I00
sg8
(lp28
I1459
asg10
I01
ssS'elan'
p29
(dp30
g4
S'Elan License Manager'
p31
sg6
I01
sg7
I00
sg8
(lp32
I1378
asg10
I01
ssS'entomb'
p33
(dp34
g4
S''
sg6
I00
sg7
I00
sg8
(lp35
I775
asg10
I01
ssS'ansatrader'
p36
(dp37
g4
S'ANSA REX Trader'
p38
sg6
I01
sg7
I00
sg8
(lp39
I124
asg10
I01
ssS'krb524'
p40
(dp41
g4
S'Kerberos 5 to 4 ticket xlator'
p42
sg6
I01
sg7
I00
sg8
(lp43
I4444
asg10
I01
ssS'semantix'
p44
(dp45
g4
S''
sg6
I01
sg7
I00
sg8
(lp46
I361
asg10
I01
ssS'datasurfsrv'
p47
(dp48
g4
S''
sg6
I01
sg7
I00
sg8
(lp49
I461
asg10
I01
ssS'mimer'
p50
(dp51
g4
S''
sg6
I01
sg7
I00
sg8
(lp52
I1360
asg10
I01
ssS'cce4x'
p53
(dp54
g4
S'ClearCommerce Engine 4.x (www.clearcommerce.com)'
p55
sg6
I00
sg7
I00
sg8
(lp56
I12000
asg10
I01
ssS'send'
p57
(dp58
g4
S''
sg6
I01
sg7
I00
sg8
(lp59
I169
asg10
I01
ssS'isakmp'
p60
(dp61
g4
S''
sg6
I01
sg7
I00
sg8
(lp62
I500
asg10
I01
ssS'compressnet'
p63
(dp64
g4
S'Management Utility'
p65
sg6
I01
sg7
I00
sg8
(lp66
I2
aI3
asg10
I01
ssS'troff'
p67
(dp68
g4
S''
sg6
I00
sg7
I00
sg8
(lp69
I2014
asg10
I01
ssS'openmath'
p70
(dp71
g4
S''
sg6
I01
sg7
I00
sg8
(lp72
I1473
asg10
I01
ssS'lansource'
p73
(dp74
g4
S''
sg6
I01
sg7
I00
sg8
(lp75
I1485
asg10
I01
ssS'imaps'
p76
(dp77
g4
S'imap4 protocol over TLS/SSL'
p78
sg6
I00
sg7
I00
sg8
(lp79
I993
asg10
I01
ssS'dectalk'
p80
(dp81
g4
S''
sg6
I00
sg7
I00
sg8
(lp82
I2007
asg10
I01
ssS'fax'
p83
(dp84
g4
S'FlexFax FAX transmission service'
p85
sg6
I00
sg7
I00
sg8
(lp86
I4557
asg10
I01
ssS'pdap'
p87
(dp88
g4
S'Prospero Data Access Protocol'
p89
sg6
I01
sg7
I00
sg8
(lp90
I344
asg10
I01
ssS'VeritasBackupExec'
p91
(dp92
g4
S'Backup Exec UNIX and 95/98/ME Aent'
p93
sg6
I00
sg7
I00
sg8
(lp94
I6101
asg10
I01
ssS'krb_prop'
p95
(dp96
g4
S'kerberos/v5 server propagation'
p97
sg6
I00
sg7
I00
sg8
(lp98
I754
asg10
I01
ssS'mpm'
p99
(dp100
g4
S'Message Processing Module [recv]'
p101
sg6
I01
sg7
I00
sg8
(lp102
I45
asg10
I01
ssS'licensedaemon'
p103
(dp104
g4
S'cisco license management'
p105
sg6
I01
sg7
I00
sg8
(lp106
I1986
asg10
I01
ssS'mpp'
p107
(dp108
g4
S'Netix Message Posting Protocol'
p109
sg6
I01
sg7
I00
sg8
(lp110
I218
asg10
I01
ssS'tinyfw'
p111
(dp112
g4
S'tiny personal firewall admin port'
p113
sg6
I00
sg7
I00
sg8
(lp114
I44334
asg10
I01
ssS'hems'
p115
(dp116
g4
S''
sg6
I01
sg7
I00
sg8
(lp117
I151
asg10
I01
ssS'utime'
p118
(dp119
g4
S'unixtime'
p120
sg6
I01
sg7
I00
sg8
(lp121
I519
asg10
I01
ssS'dtspc'
p122
(dp123
g4
S'CDE subprocess control'
p124
sg6
I00
sg7
I00
sg8
(lp125
I6112
asg10
I01
ssS'dbreporter'
p126
(dp127
g4
S'Integrity Solutions'
p128
sg6
I01
sg7
I00
sg8
(lp129
I1379
asg10
I01
ssS'netcp'
p130
(dp131
g4
S'NETscout Control Protocol'
p132
sg6
I01
sg7
I00
sg8
(lp133
I395
aI740
asg10
I01
ssS'fhc'
p134
(dp135
g4
S'Federico Heinz Consultora'
p136
sg6
I01
sg7
I00
sg8
(lp137
I1499
asg10
I01
ssS'phonebook'
p138
(dp139
g4
S'phone'
p140
sg6
I01
sg7
I00
sg8
(lp141
I767
asg10
I01
ssS'srssend'
p142
(dp143
g4
S'SRS Send'
p144
sg6
I01
sg7
I00
sg8
(lp145
I362
asg10
I01
ssS'atex_elmd'
p146
(dp147
g4
S'Atex Publishing License Manager'
p148
sg6
I01
sg7
I00
sg8
(lp149
I1385
asg10
I01
ssS'cvspserver'
p150
(dp151
g4
S'CVS network server'
p152
sg6
I01
sg7
I00
sg8
(lp153
I2401
asg10
I01
ssS'venus'
p154
(dp155
g4
S''
sg6
I01
sg7
I00
sg8
(lp156
I2430
asg10
I01
ssS'cce3x'
p157
(dp158
g4
S'ClearCommerce Engine 3.x ( www.clearcommerce.com)'
p159
sg6
I00
sg7
I00
sg8
(lp160
I1139
asg10
I01
ssS'imap3'
p161
(dp162
g4
S'Interactive Mail Access Protocol v3'
p163
sg6
I01
sg7
I00
sg8
(lp164
I220
asg10
I01
ssS'dis'
p165
(dp166
g4
S'Data Interpretation System'
p167
sg6
I01
sg7
I00
sg8
(lp168
I393
asg10
I01
ssS'rrh'
p169
(dp170
g4
S''
sg6
I01
sg7
I00
sg8
(lp171
I753
asg10
I01
ssS'sns_credit'
p172
(dp173
g4
S'Shared Network Services (SNS) for Canadian credit card authorizations'
p174
sg6
I00
sg7
I00
sg8
(lp175
I1076
asg10
I01
ssS'tnETOS'
p176
(dp177
g4
S'NEC Corporation'
p178
sg6
I01
sg7
I00
sg8
(lp179
I377
asg10
I01
ssS'syslog'
p180
(dp181
g4
S'BSD syslogd(8)'
p182
sg6
I01
sg7
I00
sg8
(lp183
I514
asg10
I00
ssS'scrabble'
p184
(dp185
g4
S''
sg6
I01
sg7
I00
sg8
(lp186
I2026
asg10
I01
ssS'ntalk'
p187
(dp188
g4
S'(talkd)'
p189
sg6
I01
sg7
I00
sg8
(lp190
I518
asg10
I01
ssS'crystalenterprise'
p191
(dp192
g4
S'Seagate Crystal Enterprise'
p193
sg6
I00
sg7
I00
sg8
(lp194
I6401
asg10
I01
ssS'cfs'
p195
(dp196
g4
S'cryptographic file system (nfs) (proposed)'
p197
sg6
I01
sg7
I00
sg8
(lp198
I3049
asg10
I01
ssS'zserv'
p199
(dp200
g4
S'Zebra server'
p201
sg6
I01
sg7
I00
sg8
(lp202
I346
asg10
I01
ssS'amandaidx'
p203
(dp204
g4
S'Amanda indexing'
p205
sg6
I00
sg7
I00
sg8
(lp206
I10082
asg10
I01
ssS'sdxauthd'
p207
(dp208
g4
S'ACE/Server services'
p209
sg6
I01
sg7
I00
sg8
(lp210
I5540
asg10
I00
ssS'is99c'
p211
(dp212
g4
S'TIA/EIA/IS-99 modem client'
p213
sg6
I01
sg7
I00
sg8
(lp214
I379
asg10
I01
ssS'sj3'
p215
(dp216
g4
S'SJ3 (kanji input)'
p217
sg6
I00
sg7
I00
sg8
(lp218
I3086
asg10
I01
ssS'pipes'
p219
(dp220
g4
S'Pipes Platform'
p221
sg6
I01
sg7
I00
sg8
(lp222
I1465
asg10
I01
ssS'DragonIDSConsole'
p223
(dp224
g4
S'Dragon IDS Console '
p225
sg6
I00
sg7
I00
sg8
(lp226
I9111
asg10
I01
ssS'prsvp'
p227
(dp228
g4
S'RSVP Port'
p229
sg6
I01
sg7
I00
sg8
(lp230
I3455
asg10
I01
ssS'netnews'
p231
(dp232
g4
S'readnews'
p233
sg6
I01
sg7
I00
sg8
(lp234
I532
asg10
I01
ssS'ndsauth'
p235
(dp236
g4
S''
sg6
I01
sg7
I00
sg8
(lp237
I353
asg10
I01
ssS'ipcserver'
p238
(dp239
g4
S'Sun IPC server'
p240
sg6
I01
sg7
I00
sg8
(lp241
I600
asg10
I01
ssS'bdp'
p242
(dp243
g4
S'Bundle Discovery Protocol'
p244
sg6
I01
sg7
I00
sg8
(lp245
I581
asg10
I01
ssS'xnmp'
p246
(dp247
g4
S''
sg6
I01
sg7
I00
sg8
(lp248
I1652
asg10
I01
ssS'is99s'
p249
(dp250
g4
S'TIA/EIA/IS-99 modem server'
p251
sg6
I01
sg7
I00
sg8
(lp252
I380
asg10
I01
ssS'mondex'
p253
(dp254
g4
S''
sg6
I01
sg7
I00
sg8
(lp255
I471
asg10
I01
ssS'kerberos_master'
p256
(dp257
g4
S"Kerberos `kadmin' (v4)"
p258
sg6
I01
sg7
I00
sg8
(lp259
I751
asg10
I01
ssS'admd'
p260
(dp261
g4
S'(chili!soft asp admin port) or Yahoo pager'
p262
sg6
I00
sg7
I00
sg8
(lp263
I5100
asg10
I01
ssS'ginad'
p264
(dp265
g4
S''
sg6
I01
sg7
I00
sg8
(lp266
I634
asg10
I01
ssS'docstor'
p267
(dp268
g4
S''
sg6
I01
sg7
I00
sg8
(lp269
I1488
asg10
I01
ssS'quake3'
p270
(dp271
g4
S'Quake 3 Arena Server'
p272
sg6
I01
sg7
I00
sg8
(lp273
I27960
asg10
I00
ssS'quake2'
p274
(dp275
g4
S'Quake 2 game server'
p276
sg6
I01
sg7
I00
sg8
(lp277
I27910
asg10
I00
ssS'shadowserver'
p278
(dp279
g4
S''
sg6
I01
sg7
I00
sg8
(lp280
I2027
asg10
I01
ssS'uarps'
p281
(dp282
g4
S'Unisys ARPs'
p283
sg6
I01
sg7
I00
sg8
(lp284
I219
asg10
I01
ssS'stmf'
p285
(dp286
g4
S''
sg6
I01
sg7
I00
sg8
(lp287
I501
asg10
I01
ssS'tacnews'
p288
(dp289
g4
S'TAC News'
p290
sg6
I01
sg7
I00
sg8
(lp291
I98
asg10
I00
ssS'utmpcd'
p292
(dp293
g4
S''
sg6
I01
sg7
I00
sg8
(lp294
I431
asg10
I01
ssS'acmaint_dbd'
p295
(dp296
g4
S''
sg6
I01
sg7
I00
sg8
(lp297
I774
asg10
I00
ssS'search'
p298
(dp299
g4
S'Or nfr411'
p300
sg6
I00
sg7
I00
sg8
(lp301
I2010
asg10
I01
ssS'omad'
p302
(dp303
g4
S'OpenMosix Autodiscovery Daemon'
p304
sg6
I01
sg7
I00
sg8
(lp305
I32768
asg10
I00
ssS'rds'
p306
(dp307
g4
S''
sg6
I01
sg7
I00
sg8
(lp308
I1540
asg10
I01
ssS'udt_os'
p309
(dp310
g4
S'Unidata UDT OS'
p311
sg6
I01
sg7
I00
sg8
(lp312
I3900
asg10
I01
ssS'checksum'
p313
(dp314
g4
S'CheckSum License Manager'
p315
sg6
I01
sg7
I00
sg8
(lp316
I1386
asg10
I01
ssS'netviewdm1'
p317
(dp318
g4
S'IBM NetView DM/6000 Server/Client'
p319
sg6
I01
sg7
I00
sg8
(lp320
I729
asg10
I01
ssS'cronus'
p321
(dp322
g4
S'CRONUS-SUPPORT'
p323
sg6
I01
sg7
I00
sg8
(lp324
I148
asg10
I01
ssS'submitserver'
p325
(dp326
g4
S''
sg6
I01
sg7
I00
sg8
(lp327
I2028
asg10
I01
ssS'ariel1'
p328
(dp329
g4
S''
sg6
I01
sg7
I00
sg8
(lp330
I419
asg10
I01
ssS'timbuktu'
p331
(dp332
g4
S''
sg6
I01
sg7
I00
sg8
(lp333
I407
asg10
I01
ssS'ctf'
p334
(dp335
g4
S'Common Trace Facility'
p336
sg6
I01
sg7
I00
sg8
(lp337
I84
asg10
I01
ssS'ariel2'
p338
(dp339
g4
S''
sg6
I01
sg7
I00
sg8
(lp340
I421
asg10
I01
ssS'garcon'
p341
(dp342
g4
S''
sg6
I00
sg7
I00
sg8
(lp343
I999
asg10
I01
ssS'dsp3270'
p344
(dp345
g4
S'Display Systems Protocol'
p346
sg6
I01
sg7
I00
sg8
(lp347
I246
asg10
I01
ssS'dhcps'
p348
(dp349
g4
S'DHCP/Bootstrap Protocol Server'
p350
sg6
I01
sg7
I00
sg8
(lp351
I67
asg10
I01
ssS'nlogin'
p352
(dp353
g4
S''
sg6
I01
sg7
I00
sg8
(lp354
I758
asg10
I01
ssS'vid'
p355
(dp356
g4
S''
sg6
I01
sg7
I00
sg8
(lp357
I769
asg10
I01
ssS'objectmanager'
p358
(dp359
g4
S''
sg6
I01
sg7
I00
sg8
(lp360
I2038
asg10
I01
ssS'chshell'
p361
(dp362
g4
S'chcmd'
p363
sg6
I01
sg7
I00
sg8
(lp364
I562
asg10
I01
ssS'dhcpc'
p365
(dp366
g4
S'DHCP/Bootstrap Protocol Client'
p367
sg6
I01
sg7
I00
sg8
(lp368
I68
asg10
I01
ssS'ipp'
p369
(dp370
g4
S'Internet Printing Protocol -- for one implementation see http://www.cups.org (Common UNIX Printing System)'
p371
sg6
I00
sg7
I00
sg8
(lp372
I631
asg10
I01
ssS'wpages'
p373
(dp374
g4
S''
sg6
I01
sg7
I00
sg8
(lp375
I776
asg10
I01
ssS'snagas'
p376
(dp377
g4
S'SNA Gateway Access Server'
p378
sg6
I01
sg7
I00
sg8
(lp379
I108
asg10
I01
ssS'telelpathattack'
p380
(dp381
g4
S''
sg6
I01
sg7
I00
sg8
(lp382
I5011
asg10
I01
ssS'ipx'
p383
(dp384
g4
S''
sg6
I01
sg7
I00
sg8
(lp385
I213
asg10
I01
ssS'deos'
p386
(dp387
g4
S'Distributed External Object Store'
p388
sg6
I01
sg7
I00
sg8
(lp389
I76
asg10
I01
ssS'wdbrpc'
p390
(dp391
g4
S'vxWorks WDB remote debugging ONCRPC'
p392
sg6
I01
sg7
I00
sg8
(lp393
I17185
asg10
I00
ssS'softpc'
p394
(dp395
g4
S'Insignia Solutions'
p396
sg6
I01
sg7
I00
sg8
(lp397
I215
asg10
I01
ssS'sstats'
p398
(dp399
g4
S''
sg6
I00
sg7
I00
sg8
(lp400
I486
asg10
I01
ssS'msp'
p401
(dp402
g4
S'Message Send Protocol'
p403
sg6
I01
sg7
I00
sg8
(lp404
I18
asg10
I01
ssS'emce'
p405
(dp406
g4
S'CCWS mm conf'
p407
sg6
I01
sg7
I00
sg8
(lp408
I2004
asg10
I00
ssS'https'
p409
(dp410
g4
S'secure http (SSL)'
p411
sg6
I01
sg7
I00
sg8
(lp412
I443
asg10
I01
ssS'ohimsrv'
p413
(dp414
g4
S''
sg6
I01
sg7
I00
sg8
(lp415
I506
asg10
I01
ssS'pop3s'
p416
(dp417
g4
S'POP3 protocol over TLS/SSL'
p418
sg6
I00
sg7
I00
sg8
(lp419
I995
asg10
I01
ssS'xdsxdm'
p420
(dp421
g4
S''
sg6
I01
sg7
I00
sg8
(lp422
I6558
asg10
I01
ssS'nessus'
p423
(dp424
g4
S'Nessus or remote message server'
p425
sg6
I00
sg7
I00
sg8
(lp426
I1241
asg10
I01
ssS'infoseek'
p427
(dp428
g4
S''
sg6
I01
sg7
I00
sg8
(lp429
I414
asg10
I01
ssS'cacp'
p430
(dp431
g4
S'Gateway Access Control Protocol'
p432
sg6
I01
sg7
I00
sg8
(lp433
I190
asg10
I00
ssS'kauth'
p434
(dp435
g4
S'Remote kauth'
p436
sg6
I00
sg7
I00
sg8
(lp437
I2120
asg10
I01
ssS'vmodem'
p438
(dp439
g4
S''
sg6
I01
sg7
I00
sg8
(lp440
I3141
asg10
I01
ssS'phone'
p441
(dp442
g4
S'conference calling'
p443
sg6
I01
sg7
I00
sg8
(lp444
I1167
asg10
I00
ssS'ocbinder'
p445
(dp446
g4
S''
sg6
I01
sg7
I00
sg8
(lp447
I183
asg10
I01
ssS'netgw'
p448
(dp449
g4
S''
sg6
I01
sg7
I00
sg8
(lp450
I741
asg10
I01
ssS'doom'
p451
(dp452
g4
S'doom Id Software'
p453
sg6
I01
sg7
I00
sg8
(lp454
I666
asg10
I01
ssS'acmaint_transd'
p455
(dp456
g4
S''
sg6
I01
sg7
I00
sg8
(lp457
I775
asg10
I00
ssS'gdomap'
p458
(dp459
g4
S''
sg6
I01
sg7
I00
sg8
(lp460
I538
asg10
I01
ssS'tacacs'
p461
(dp462
g4
S'Login Host Protocol (TACACS)'
p463
sg6
I01
sg7
I00
sg8
(lp464
I49
asg10
I01
ssS'ulp'
p465
(dp466
g4
S''
sg6
I01
sg7
I00
sg8
(lp467
I522
asg10
I01
ssS'sygatefw'
p468
(dp469
g4
S'Sygate Firewall management port version 3.0 build 521 and above'
p470
sg6
I01
sg7
I00
sg8
(lp471
I39213
asg10
I00
ssS'tpip'
p472
(dp473
g4
S''
sg6
I01
sg7
I00
sg8
(lp474
I594
asg10
I01
ssS'vmnet'
p475
(dp476
g4
S''
sg6
I01
sg7
I00
sg8
(lp477
I175
asg10
I01
ssS'halflife'
p478
(dp479
g4
S'Half-life game server'
p480
sg6
I01
sg7
I00
sg8
(lp481
I27015
asg10
I00
ssS'cal'
p482
(dp483
g4
S''
sg6
I01
sg7
I00
sg8
(lp484
I588
asg10
I01
ssS'iafserver'
p485
(dp486
g4
S''
sg6
I01
sg7
I00
sg8
(lp487
I479
asg10
I01
ssS'webster'
p488
(dp489
g4
S''
sg6
I01
sg7
I00
sg8
(lp490
I765
aI2627
asg10
I01
ssS'quakeworld'
p491
(dp492
g4
S'Quake world'
p493
sg6
I01
sg7
I00
sg8
(lp494
I27500
asg10
I00
ssS'vettcp'
p495
(dp496
g4
S''
sg6
I01
sg7
I00
sg8
(lp497
I78
asg10
I01
ssS'lockd'
p498
(dp499
g4
S''
sg6
I01
sg7
I00
sg8
(lp500
I4045
asg10
I01
ssS'corbaloc'
p501
(dp502
g4
S'Corba'
p503
sg6
I00
sg7
I00
sg8
(lp504
I2809
asg10
I01
ssS'openport'
p505
(dp506
g4
S''
sg6
I01
sg7
I00
sg8
(lp507
I260
asg10
I01
ssS'kpasswd'
p508
(dp509
g4
S'kpwd Kerberos (v4) "passwd"'
p510
sg6
I00
sg7
I00
sg8
(lp511
I761
asg10
I01
ssS'interbase'
p512
(dp513
g4
S''
sg6
I01
sg7
I00
sg8
(lp514
I2041
asg10
I01
ssS'smtp'
p515
(dp516
g4
S'Simple Mail Transfer'
p517
sg6
I01
sg7
I00
sg8
(lp518
I25
asg10
I01
ssS'globalcatLDAP'
p519
(dp520
g4
S'Global Catalog LDAP'
p521
sg6
I00
sg7
I00
sg8
(lp522
I3268
asg10
I01
ssS'intecourier'
p523
(dp524
g4
S''
sg6
I01
sg7
I00
sg8
(lp525
I495
asg10
I01
ssS'swgps'
p526
(dp527
g4
S'Nortel Java S/WGPS Global Payment Solutions for US credit card authorizations'
p528
sg6
I00
sg7
I00
sg8
(lp529
I15126
asg10
I01
ssS'xtell'
p530
(dp531
g4
S'Xtell messenging server'
p532
sg6
I00
sg7
I00
sg8
(lp533
I4224
asg10
I01
ssS'tam'
p534
(dp535
g4
S'Trivial Authenticated Mail Protocol'
p536
sg6
I01
sg7
I00
sg8
(lp537
I209
asg10
I01
ssS'callbook'
p538
(dp539
g4
S''
sg6
I01
sg7
I00
sg8
(lp540
I2000
asg10
I01
ssS'interhdl_elmd'
p541
(dp542
g4
S'interHDL License Manager'
p543
sg6
I01
sg7
I00
sg8
(lp544
I1454
asg10
I01
ssS'sip'
p545
(dp546
g4
S'Session Initiation Protocol (SIP)'
p547
sg6
I01
sg7
I00
sg8
(lp548
I5060
asg10
I01
ssS'vslmp'
p549
(dp550
g4
S''
sg6
I01
sg7
I00
sg8
(lp551
I312
asg10
I01
ssS'nmsp'
p552
(dp553
g4
S'Networked Media Streaming Protocol'
p554
sg6
I01
sg7
I00
sg8
(lp555
I537
asg10
I01
ssS'globalcatLDAPssl'
p556
(dp557
g4
S'Global Catalog LDAP over ssl'
p558
sg6
I00
sg7
I00
sg8
(lp559
I3269
asg10
I01
ssS'telnets'
p560
(dp561
g4
S'telnet protocol over TLS/SSL'
p562
sg6
I00
sg7
I00
sg8
(lp563
I992
asg10
I01
ssS'smsd'
p564
(dp565
g4
S''
sg6
I01
sg7
I00
sg8
(lp566
I596
asg10
I01
ssS'lotusnotes'
p567
(dp568
g4
S'Lotus Note'
p569
sg6
I01
sg7
I00
sg8
(lp570
I1352
asg10
I01
ssS'mmcc'
p571
(dp572
g4
S'multimedia conference control tool'
p573
sg6
I01
sg7
I00
sg8
(lp574
I5050
asg10
I01
ssS'flexlm9'
p575
(dp576
g4
S'FlexLM license manager additional ports'
p577
sg6
I00
sg7
I00
sg8
(lp578
I27009
asg10
I01
ssS'cycleserv'
p579
(dp580
g4
S''
sg6
I01
sg7
I00
sg8
(lp581
I763
asg10
I01
ssS'dwf'
p582
(dp583
g4
S'Tandem Distributed Workbench Facility'
p584
sg6
I01
sg7
I00
sg8
(lp585
I1450
asg10
I01
ssS'mumps'
p586
(dp587
g4
S"Plus Five's MUMPS"
p588
sg6
I01
sg7
I00
sg8
(lp589
I188
asg10
I01
ssS'flexlm3'
p590
(dp591
g4
S'FlexLM license manager additional ports'
p592
sg6
I00
sg7
I00
sg8
(lp593
I27003
asg10
I01
ssS'smsp'
p594
(dp595
g4
S''
sg6
I01
sg7
I00
sg8
(lp596
I413
asg10
I01
ssS'mdbs_daemon'
p597
(dp598
g4
S''
sg6
I01
sg7
I00
sg8
(lp599
I800
asg10
I01
ssS'flexlm0'
p600
(dp601
g4
S'FlexLM license manager additional ports'
p602
sg6
I00
sg7
I00
sg8
(lp603
I27000
asg10
I01
ssS'flexlm7'
p604
(dp605
g4
S'FlexLM license manager additional ports'
p606
sg6
I00
sg7
I00
sg8
(lp607
I27007
asg10
I01
ssS'flexlm6'
p608
(dp609
g4
S'FlexLM license manager additional ports'
p610
sg6
I00
sg7
I00
sg8
(lp611
I27006
asg10
I01
ssS'flexlm5'
p612
(dp613
g4
S'FlexLM license manager additional ports'
p614
sg6
I00
sg7
I00
sg8
(lp615
I27005
asg10
I01
ssS'afs'
p616
(dp617
g4
S'AFS License Manager'
p618
sg6
I01
sg7
I00
sg8
(lp619
I1483
asg10
I01
ssS'deviceshare'
p620
(dp621
g4
S''
sg6
I01
sg7
I00
sg8
(lp622
I552
asg10
I01
ssS'lam'
p623
(dp624
g4
S''
sg6
I01
sg7
I00
sg8
(lp625
I2040
asg10
I01
ssS'quicktime'
p626
(dp627
g4
S'Apple Darwin and QuickTime Streaming Administration Servers'
p628
sg6
I00
sg7
I00
sg8
(lp629
I1220
asg10
I01
ssS'csdmbase'
p630
(dp631
g4
S''
sg6
I01
sg7
I00
sg8
(lp632
I1467
aI1471
asg10
I01
ssS'idfp'
p633
(dp634
g4
S''
sg6
I01
sg7
I00
sg8
(lp635
I549
asg10
I01
ssS'connlcli'
p636
(dp637
g4
S''
sg6
I01
sg7
I00
sg8
(lp638
I1358
asg10
I01
ssS'aol'
p639
(dp640
g4
S'America-Online.  Also can be used by ICQ'
p641
sg6
I01
sg7
I00
sg8
(lp642
I5190
asg10
I01
ssS'hpnpd'
p643
(dp644
g4
S'Hewlett-Packard Network Printer daemon'
p645
sg6
I01
sg7
I00
sg8
(lp646
I22370
asg10
I01
ssS'netcheque'
p647
(dp648
g4
S'NetCheque accounting'
p649
sg6
I01
sg7
I00
sg8
(lp650
I4008
asg10
I01
ssS'advocentkvm'
p651
(dp652
g4
S'Advocent KVM Server'
p653
sg6
I00
sg7
I00
sg8
(lp654
I2068
asg10
I01
ssS'X11'
p655
(dp656
g4
S'X Window server'
p657
sg6
I00
sg7
I00
sg8
(lp658
I6000
asg10
I01
ssS'kpasswd5'
p659
(dp660
g4
S'Kerberos (v5)'
p661
sg6
I01
sg7
I00
sg8
(lp662
I464
asg10
I01
ssS'scoi2odialog'
p663
(dp664
g4
S''
sg6
I01
sg7
I00
sg8
(lp665
I360
asg10
I01
ssS'npp'
p666
(dp667
g4
S'Network Printing Protocol'
p668
sg6
I01
sg7
I00
sg8
(lp669
I92
asg10
I01
ssS'CarbonCopy'
p670
(dp671
g4
S''
sg6
I00
sg7
I00
sg8
(lp672
I1680
asg10
I01
ssS'whois'
p673
(dp674
g4
S'nicname'
p675
sg6
I01
sg7
I00
sg8
(lp676
I43
asg10
I01
ssS'issd'
p677
(dp678
g4
S''
sg6
I01
sg7
I00
sg8
(lp679
I1600
asg10
I01
ssS'omid'
p680
(dp681
g4
S'OpenMosix Info Dissemination'
p682
sg6
I01
sg7
I00
sg8
(lp683
I5428
asg10
I00
ssS'rellpack'
p684
(dp685
g4
S''
sg6
I01
sg7
I00
sg8
(lp686
I2018
asg10
I00
ssS'smakynet'
p687
(dp688
g4
S''
sg6
I01
sg7
I00
sg8
(lp689
I122
asg10
I01
ssS'ocserver'
p690
(dp691
g4
S''
sg6
I01
sg7
I00
sg8
(lp692
I184
asg10
I01
ssS'bftp'
p693
(dp694
g4
S'Background File Transfer Program'
p695
sg6
I01
sg7
I00
sg8
(lp696
I152
asg10
I01
ssS'wins'
p697
(dp698
g4
S"Microsoft's Windows Internet Name Service"
p699
sg6
I01
sg7
I00
sg8
(lp700
I1512
asg10
I01
ssS'flexlm2'
p701
(dp702
g4
S'FlexLM license manager additional ports'
p703
sg6
I00
sg7
I00
sg8
(lp704
I27002
asg10
I01
ssS'kryptolan'
p705
(dp706
g4
S''
sg6
I01
sg7
I00
sg8
(lp707
I398
asg10
I01
ssS'cadlock'
p708
(dp709
g4
S''
sg6
I01
sg7
I00
sg8
(lp710
I770
aI1000
asg10
I01
ssS'cfdptkt'
p711
(dp712
g4
S''
sg6
I01
sg7
I00
sg8
(lp713
I120
asg10
I01
ssS'wincim'
p714
(dp715
g4
S'pc windows compuserve.com protocol'
p716
sg6
I00
sg7
I00
sg8
(lp717
I4144
asg10
I01
ssS'eyelink'
p718
(dp719
g4
S''
sg6
I01
sg7
I00
sg8
(lp720
I589
asg10
I01
ssS'uaac'
p721
(dp722
g4
S'UAAC Protocol'
p723
sg6
I01
sg7
I00
sg8
(lp724
I145
asg10
I01
ssS'vmpwscs'
p725
(dp726
g4
S''
sg6
I01
sg7
I00
sg8
(lp727
I214
asg10
I01
ssS'bootserver'
p728
(dp729
g4
S''
sg6
I01
sg7
I00
sg8
(lp730
I2016
asg10
I01
ssS'talk'
p731
(dp732
g4
S'like tenex link, but across'
p733
sg6
I01
sg7
I00
sg8
(lp734
I517
asg10
I01
ssS'sd'
p735
(dp736
g4
S'Session Director'
p737
sg6
I01
sg7
I00
sg8
(lp738
I9876
asg10
I01
ssS'jetdirect'
p739
(dp740
g4
S'HP JetDirect card'
p741
sg6
I00
sg7
I00
sg8
(lp742
I9100
asg10
I01
ssS'xtreelic'
p743
(dp744
g4
S'XTREE License Server'
p745
sg6
I00
sg7
I00
sg8
(lp746
I996
asg10
I01
ssS'flexlm8'
p747
(dp748
g4
S'FlexLM license manager additional ports'
p749
sg6
I00
sg7
I00
sg8
(lp750
I27008
asg10
I01
ssS'meter'
p751
(dp752
g4
S'demon'
p753
sg6
I01
sg7
I00
sg8
(lp754
I570
asg10
I01
ssS'glogger'
p755
(dp756
g4
S''
sg6
I01
sg7
I00
sg8
(lp757
I2033
asg10
I01
ssS'creativepartnr'
p758
(dp759
g4
S''
sg6
I01
sg7
I00
sg8
(lp760
I455
asg10
I01
ssS'qmqp'
p761
(dp762
g4
S'Qmail Quick Mail Queueing'
p763
sg6
I00
sg7
I00
sg8
(lp764
I628
asg10
I01
ssS'quake'
p765
(dp766
g4
S'Quake game server'
p767
sg6
I01
sg7
I00
sg8
(lp768
I26000
asg10
I00
ssS'xdmcp'
p769
(dp770
g4
S'X Display Mgr. Control Proto'
p771
sg6
I01
sg7
I00
sg8
(lp772
I177
asg10
I01
ssS'appleqtc'
p773
(dp774
g4
S'apple quick time'
p775
sg6
I01
sg7
I00
sg8
(lp776
I458
asg10
I01
ssS'Trinoo_Register'
p777
(dp778
g4
S'Trinoo distributed attack tool Bcast Daemon registration port'
p779
sg6
I01
sg7
I00
sg8
(lp780
I31335
asg10
I00
ssS'qbikgdp'
p781
(dp782
g4
S''
sg6
I01
sg7
I00
sg8
(lp783
I368
asg10
I01
ssS'scoremgr'
p784
(dp785
g4
S''
sg6
I01
sg7
I00
sg8
(lp786
I2034
asg10
I01
ssS'monitor'
p787
(dp788
g4
S''
sg6
I01
sg7
I00
sg8
(lp789
I561
asg10
I01
ssS'ellpack'
p790
(dp791
g4
S''
sg6
I00
sg7
I00
sg8
(lp792
I2025
asg10
I01
ssS'hylafax'
p793
(dp794
g4
S'HylaFAX client-server protocol'
p795
sg6
I00
sg7
I00
sg8
(lp796
I4559
asg10
I01
ssS'rsvd'
p797
(dp798
g4
S''
sg6
I01
sg7
I00
sg8
(lp799
I168
asg10
I01
ssS'decap'
p800
(dp801
g4
S''
sg6
I01
sg7
I00
sg8
(lp802
I403
asg10
I01
ssS'maybeveritas'
p803
(dp804
g4
S''
sg6
I00
sg7
I00
sg8
(lp805
I4987
aI4998
asg10
I01
ssS'uaiact'
p806
(dp807
g4
S'Universal Analytics'
p808
sg6
I01
sg7
I00
sg8
(lp809
I1470
asg10
I01
ssS'pcm'
p810
(dp811
g4
S'PCM Agent (AutoSecure Policy Compliance Manager'
p812
sg6
I00
sg7
I00
sg8
(lp813
I1827
asg10
I01
ssS'kshell'
p814
(dp815
g4
S'krcmd Kerberos (v4/v5)'
p816
sg6
I01
sg7
I00
sg8
(lp817
I544
asg10
I01
ssS'rwhois'
p818
(dp819
g4
S'Remote Who Is'
p820
sg6
I01
sg7
I00
sg8
(lp821
I4321
asg10
I01
ssS'dmdocbroker'
p822
(dp823
g4
S''
sg6
I01
sg7
I00
sg8
(lp824
I1489
asg10
I01
ssS'rgtp'
p825
(dp826
g4
S'Reverse Gossip Transport'
p827
sg6
I01
sg7
I00
sg8
(lp828
I1431
asg10
I01
ssS'postgres'
p829
(dp830
g4
S'postgres database server'
p831
sg6
I00
sg7
I00
sg8
(lp832
I5432
asg10
I01
ssS'pptp'
p833
(dp834
g4
S'Point-to-point tunnelling protocol'
p835
sg6
I00
sg7
I00
sg8
(lp836
I1723
asg10
I01
ssS'eklogin'
p837
(dp838
g4
S'Kerberos (v4) encrypted rlogin'
p839
sg6
I01
sg7
I00
sg8
(lp840
I2105
asg10
I01
ssS'rndc'
p841
(dp842
g4
S'RNDC is used by BIND 9 (& probably other NS)'
p843
sg6
I00
sg7
I00
sg8
(lp844
I953
asg10
I01
ssS'mloadd'
p845
(dp846
g4
S'mloadd monitoring tool'
p847
sg6
I01
sg7
I00
sg8
(lp848
I1427
asg10
I01
ssS'auth'
p849
(dp850
g4
S'ident, tap, Authentication Service'
p851
sg6
I01
sg7
I00
sg8
(lp852
I113
asg10
I01
ssS'dlip'
p853
(dp854
g4
S''
sg6
I01
sg7
I00
sg8
(lp855
I7201
asg10
I01
ssS'mcidas'
p856
(dp857
g4
S'McIDAS Data Transmission Protocol'
p858
sg6
I01
sg7
I00
sg8
(lp859
I112
asg10
I01
ssS'wnn6_Kr'
p860
(dp861
g4
S'Wnn6 (Korean input)'
p862
sg6
I00
sg7
I00
sg8
(lp863
I22305
asg10
I01
ssS'rww'
p864
(dp865
g4
S'Microsoft Remote Web Workplace on Small Business Server'
p866
sg6
I00
sg7
I00
sg8
(lp867
I4125
asg10
I01
ssS'saft'
p868
(dp869
g4
S'saft Simple Asynchronous File Transfer'
p870
sg6
I01
sg7
I00
sg8
(lp871
I487
asg10
I01
ssS'contentserver'
p872
(dp873
g4
S''
sg6
I01
sg7
I00
sg8
(lp874
I454
asg10
I01
ssS'nucleus'
p875
(dp876
g4
S''
sg6
I01
sg7
I00
sg8
(lp877
I1463
asg10
I01
ssS'peerenabler'
p878
(dp879
g4
S'P2PNetworking/PeerEnabler protocol'
p880
sg6
I01
sg7
I00
sg8
(lp881
I3531
asg10
I01
ssS'smartsdp'
p882
(dp883
g4
S''
sg6
I01
sg7
I00
sg8
(lp884
I426
asg10
I01
ssS'symplex'
p885
(dp886
g4
S''
sg6
I01
sg7
I00
sg8
(lp887
I1507
asg10
I01
ssS'nfa'
p888
(dp889
g4
S'Network File Access'
p890
sg6
I01
sg7
I00
sg8
(lp891
I1155
asg10
I01
ssS'prospero'
p892
(dp893
g4
S'Prospero Directory Service'
p894
sg6
I01
sg7
I00
sg8
(lp895
I191
asg10
I01
ssS'opsec_sam'
p896
(dp897
g4
S'Check Point OPSEC'
p898
sg6
I00
sg7
I00
sg8
(lp899
I18183
asg10
I01
ssS'namp'
p900
(dp901
g4
S''
sg6
I01
sg7
I00
sg8
(lp902
I167
asg10
I01
ssS'metagram'
p903
(dp904
g4
S'Metagram Relay'
p905
sg6
I01
sg7
I00
sg8
(lp906
I99
asg10
I01
ssS'snews'
p907
(dp908
g4
S''
sg6
I01
sg7
I00
sg8
(lp909
I563
asg10
I01
ssS'shivasound'
p910
(dp911
g4
S'Shiva Sound'
p912
sg6
I01
sg7
I00
sg8
(lp913
I1549
asg10
I00
ssS'man'
p914
(dp915
g4
S''
sg6
I01
sg7
I00
sg8
(lp916
I9535
asg10
I01
ssS'scohelp'
p917
(dp918
g4
S''
sg6
I01
sg7
I00
sg8
(lp919
I457
asg10
I01
ssS'flexlm4'
p920
(dp921
g4
S'FlexLM license manager additional ports'
p922
sg6
I00
sg7
I00
sg8
(lp923
I27004
asg10
I01
ssS'profile'
p924
(dp925
g4
S'PROFILE Naming System'
p926
sg6
I01
sg7
I00
sg8
(lp927
I136
asg10
I01
ssS'domain'
p928
(dp929
g4
S'Domain Name Server'
p930
sg6
I01
sg7
I00
sg8
(lp931
I53
asg10
I01
ssS'dixie'
p932
(dp933
g4
S'DIXIE Protocol Specification'
p934
sg6
I01
sg7
I00
sg8
(lp935
I96
asg10
I01
ssS'teedtap'
p936
(dp937
g4
S''
sg6
I01
sg7
I00
sg8
(lp938
I559
asg10
I01
ssS'heretic2'
p939
(dp940
g4
S'Heretic 2 game server'
p941
sg6
I01
sg7
I00
sg8
(lp942
I28910
asg10
I00
ssS'ospfd'
p943
(dp944
g4
S'OSPFd vty'
p945
sg6
I00
sg7
I00
sg8
(lp946
I2604
asg10
I01
ssS'globe'
p947
(dp948
g4
S''
sg6
I01
sg7
I00
sg8
(lp949
I2002
asg10
I01
ssS'cichlid'
p950
(dp951
g4
S'Cichlid License Manager'
p952
sg6
I01
sg7
I00
sg8
(lp953
I1377
asg10
I01
ssS'wnn6_Tw'
p954
(dp955
g4
S'Wnn6 (Taiwanse input)'
p956
sg6
I00
sg7
I00
sg8
(lp957
I22321
asg10
I01
ssS'zebra'
p958
(dp959
g4
S'zebra vty'
p960
sg6
I00
sg7
I00
sg8
(lp961
I2601
asg10
I01
ssS'iasd'
p962
(dp963
g4
S''
sg6
I01
sg7
I00
sg8
(lp964
I432
asg10
I01
ssS'opsec_omi'
p965
(dp966
g4
S'Check Point OPSEC'
p967
sg6
I00
sg7
I00
sg8
(lp968
I18185
asg10
I01
ssS'ftp'
p969
(dp970
g4
S'File Transfer [Control]'
p971
sg6
I01
sg7
I00
sg8
(lp972
I21
asg10
I01
ssS'puparp'
p973
(dp974
g4
S''
sg6
I01
sg7
I00
sg8
(lp975
I998
asg10
I00
ssS'msl_lmd'
p976
(dp977
g4
S'MSL License Manager'
p978
sg6
I01
sg7
I00
sg8
(lp979
I1464
asg10
I01
ssS'skkserv'
p980
(dp981
g4
S'SKK (kanji input)'
p982
sg6
I00
sg7
I00
sg8
(lp983
I1178
asg10
I01
ssS'busboy'
p984
(dp985
g4
S''
sg6
I00
sg7
I00
sg8
(lp986
I998
asg10
I01
ssS'netinfo'
p987
(dp988
g4
S'Netinfo is apparently on many OS X boxes.'
p989
sg6
I00
sg7
I00
sg8
(lp990
I1033
asg10
I01
ssS'dsp'
p991
(dp992
g4
S'Display Support Protocol'
p993
sg6
I01
sg7
I00
sg8
(lp994
I33
asg10
I01
ssS'coauthor'
p995
(dp996
g4
S'oracle'
p997
sg6
I01
sg7
I00
sg8
(lp998
I1529
asg10
I00
ssS'dsf'
p999
(dp1000
g4
S''
sg6
I01
sg7
I00
sg8
(lp1001
I555
asg10
I01
ssS'krbupdate'
p1002
(dp1003
g4
S'kreg Kerberos (v4) registration'
p1004
sg6
I00
sg7
I00
sg8
(lp1005
I760
asg10
I01
ssS'custix'
p1006
(dp1007
g4
S'Customer IXChange'
p1008
sg6
I01
sg7
I00
sg8
(lp1009
I528
asg10
I01
ssS'rtelnet'
p1010
(dp1011
g4
S'Remote Telnet'
p1012
sg6
I01
sg7
I00
sg8
(lp1013
I107
asg10
I01
ssS'kip'
p1014
(dp1015
g4
S'IP over kerberos'
p1016
sg6
I00
sg7
I00
sg8
(lp1017
I2112
asg10
I01
ssS'utcd'
p1018
(dp1019
g4
S'Universal Time daemon (utcd)'
p1020
sg6
I01
sg7
I00
sg8
(lp1021
I1506
asg10
I01
ssS'pciarray'
p1022
(dp1023
g4
S''
sg6
I01
sg7
I00
sg8
(lp1024
I1552
asg10
I01
ssS'ntp'
p1025
(dp1026
g4
S'Network Time Protocol'
p1027
sg6
I01
sg7
I00
sg8
(lp1028
I123
asg10
I01
ssS'secureidprop'
p1029
(dp1030
g4
S'ACE/Server services'
p1031
sg6
I00
sg7
I00
sg8
(lp1032
I5510
asg10
I01
ssS'tempo'
p1033
(dp1034
g4
S'newdate'
p1035
sg6
I01
sg7
I00
sg8
(lp1036
I526
asg10
I01
ssS'netviewdm3'
p1037
(dp1038
g4
S'IBM NetView DM/6000 receive/tcp'
p1039
sg6
I01
sg7
I00
sg8
(lp1040
I731
asg10
I01
ssS'netviewdm2'
p1041
(dp1042
g4
S'IBM NetView DM/6000 send/tcp'
p1043
sg6
I01
sg7
I00
sg8
(lp1044
I730
asg10
I01
ssS'asa'
p1045
(dp1046
g4
S'ASA Message Router Object Def.'
p1047
sg6
I01
sg7
I00
sg8
(lp1048
I386
asg10
I01
ssS'miroconnect'
p1049
(dp1050
g4
S''
sg6
I01
sg7
I00
sg8
(lp1051
I1532
asg10
I01
ssS'hermes'
p1052
(dp1053
g4
S''
sg6
I01
sg7
I00
sg8
(lp1054
I1248
asg10
I01
ssS'rlp'
p1055
(dp1056
g4
S'Resource Location Protocol'
p1057
sg6
I01
sg7
I00
sg8
(lp1058
I39
asg10
I01
ssS'flexlm1'
p1059
(dp1060
g4
S'FlexLM license manager additional ports'
p1061
sg6
I00
sg7
I00
sg8
(lp1062
I27001
asg10
I01
ssS'objcall'
p1063
(dp1064
g4
S'Tivoli Object Dispatcher'
p1065
sg6
I01
sg7
I00
sg8
(lp1066
I94
asg10
I01
ssS'pythonds'
p1067
(dp1068
g4
S'Python Documentation Server'
p1069
sg6
I00
sg7
I00
sg8
(lp1070
I7464
asg10
I01
ssS'ufsd'
p1071
(dp1072
g4
S'ufsd\t\t# UFS-aware server'
p1073
sg6
I01
sg7
I00
sg8
(lp1074
I1008
asg10
I01
ssS'route'
p1075
(dp1076
g4
S'router routed -- RIP'
p1077
sg6
I01
sg7
I00
sg8
(lp1078
I520
asg10
I00
ssS'covia'
p1079
(dp1080
g4
S'Communications Integrator (CI)'
p1081
sg6
I01
sg7
I00
sg8
(lp1082
I64
asg10
I01
ssS'ups'
p1083
(dp1084
g4
S'Uninterruptible Power Supply'
p1085
sg6
I01
sg7
I00
sg8
(lp1086
I401
asg10
I01
ssS'servserv'
p1087
(dp1088
g4
S''
sg6
I01
sg7
I00
sg8
(lp1089
I2011
asg10
I00
ssS'ats'
p1090
(dp1091
g4
S'Advanced Training System Program'
p1092
sg6
I01
sg7
I00
sg8
(lp1093
I2201
asg10
I01
ssS'timed'
p1094
(dp1095
g4
S'timeserver'
p1096
sg6
I01
sg7
I00
sg8
(lp1097
I525
asg10
I01
ssS'seosload'
p1098
(dp1099
g4
S'From the new Computer Associates eTrust ACX'
p1100
sg6
I00
sg7
I00
sg8
(lp1101
I8892
asg10
I01
ssS'essbase'
p1102
(dp1103
g4
S'Essbase Arbor Software'
p1104
sg6
I01
sg7
I00
sg8
(lp1105
I1423
asg10
I01
ssS'ptcnameservice'
p1106
(dp1107
g4
S'PTC Name Service'
p1108
sg6
I01
sg7
I00
sg8
(lp1109
I597
asg10
I01
ssS'rtsp'
p1110
(dp1111
g4
S'Real Time Stream Control Protocol'
p1112
sg6
I01
sg7
I00
sg8
(lp1113
I554
asg10
I01
ssS'terminaldb'
p1114
(dp1115
g4
S''
sg6
I01
sg7
I00
sg8
(lp1116
I2008
aI2018
asg10
I01
ssS'echo'
p1117
(dp1118
g4
S''
sg6
I01
sg7
I00
sg8
(lp1119
I7
asg10
I01
ssS'rpcbind'
p1120
(dp1121
g4
S'portmapper, rpcbind'
p1122
sg6
I01
sg7
I00
sg8
(lp1123
I111
asg10
I01
ssS'notify'
p1124
(dp1125
g4
S''
sg6
I01
sg7
I00
sg8
(lp1126
I773
asg10
I00
ssS'csdm'
p1127
(dp1128
g4
S''
sg6
I01
sg7
I00
sg8
(lp1129
I1468
aI1472
asg10
I01
ssS'proshareaudio'
p1130
(dp1131
g4
S'proshare conf audio'
p1132
sg6
I01
sg7
I00
sg8
(lp1133
I5713
asg10
I01
ssS'bh611'
p1134
(dp1135
g4
S''
sg6
I01
sg7
I00
sg8
(lp1136
I354
asg10
I01
ssS'shivadiscovery'
p1137
(dp1138
g4
S'Shiva'
p1139
sg6
I01
sg7
I00
sg8
(lp1140
I1502
asg10
I01
ssS'gkrellmd'
p1141
(dp1142
g4
S'GKrellM remote system activity meter daemon'
p1143
sg6
I00
sg7
I00
sg8
(lp1144
I19150
asg10
I01
ssS'bwnfs'
p1145
(dp1146
g4
S'BW-NFS DOS Authentication'
p1147
sg6
I01
sg7
I00
sg8
(lp1148
I650
asg10
I00
ssS'ivsd'
p1149
(dp1150
g4
S'IVS Daemon'
p1151
sg6
I01
sg7
I00
sg8
(lp1152
I2241
asg10
I01
ssS'rplay'
p1153
(dp1154
g4
S''
sg6
I01
sg7
I00
sg8
(lp1155
I5555
asg10
I00
ssS'creativeserver'
p1156
(dp1157
g4
S''
sg6
I01
sg7
I00
sg8
(lp1158
I453
asg10
I01
ssS'airs'
p1159
(dp1160
g4
S''
sg6
I01
sg7
I00
sg8
(lp1161
I1481
asg10
I01
ssS'odmr'
p1162
(dp1163
g4
S''
sg6
I01
sg7
I00
sg8
(lp1164
I366
asg10
I01
ssS'amidxtape'
p1165
(dp1166
g4
S'Amanda tape indexing'
p1167
sg6
I00
sg7
I00
sg8
(lp1168
I10083
asg10
I01
ssS'siam'
p1169
(dp1170
g4
S''
sg6
I01
sg7
I00
sg8
(lp1171
I498
asg10
I01
ssS'dnsix'
p1172
(dp1173
g4
S'DNSIX Securit Attribute Token Map'
p1174
sg6
I01
sg7
I00
sg8
(lp1175
I90
asg10
I01
ssS'UPnP'
p1176
(dp1177
g4
S'Universal PnP'
p1178
sg6
I01
sg7
I00
sg8
(lp1179
I1900
aI5000
asg10
I01
ssS'listen'
p1180
(dp1181
g4
S'System V listener port'
p1182
sg6
I00
sg7
I00
sg8
(lp1183
I2766
asg10
I01
ssS'dbstar'
p1184
(dp1185
g4
S''
sg6
I01
sg7
I00
sg8
(lp1186
I1415
asg10
I01
ssS'shell'
p1187
(dp1188
g4
S'BSD rshd(8)'
p1189
sg6
I00
sg7
I00
sg8
(lp1190
I514
asg10
I01
ssS'wizard'
p1191
(dp1192
g4
S'curry'
p1193
sg6
I01
sg7
I00
sg8
(lp1194
I2001
asg10
I00
ssS'courier'
p1195
(dp1196
g4
S'rpc'
p1197
sg6
I01
sg7
I00
sg8
(lp1198
I530
asg10
I01
ssS'bootclient'
p1199
(dp1200
g4
S''
sg6
I01
sg7
I00
sg8
(lp1201
I2017
asg10
I00
ssS'ncp'
p1202
(dp1203
g4
S''
sg6
I01
sg7
I00
sg8
(lp1204
I524
asg10
I01
ssS'direct'
p1205
(dp1206
g4
S''
sg6
I01
sg7
I00
sg8
(lp1207
I242
asg10
I01
ssS'decladebug'
p1208
(dp1209
g4
S'DECLadebug Remote Debug Protocol'
p1210
sg6
I01
sg7
I00
sg8
(lp1211
I410
asg10
I01
ssS'issa'
p1212
(dp1213
g4
S'ISS System Scanner Agent'
p1214
sg6
I00
sg7
I00
sg8
(lp1215
I9991
asg10
I01
ssS'dtk'
p1216
(dp1217
g4
S'Deception Tool Kit (www.all.net) '
p1218
sg6
I01
sg7
I00
sg8
(lp1219
I365
asg10
I01
ssS'cuillamartin'
p1220
(dp1221
g4
S'CuillaMartin Company'
p1222
sg6
I01
sg7
I00
sg8
(lp1223
I1356
asg10
I01
ssS'issc'
p1224
(dp1225
g4
S'ISS System Scanner Console'
p1226
sg6
I00
sg7
I00
sg8
(lp1227
I9992
asg10
I01
ssS'pcduo'
p1228
(dp1229
g4
S'RemCon PC-Duo - new port'
p1230
sg6
I00
sg7
I00
sg8
(lp1231
I5405
asg10
I01
ssS'napster'
p1232
(dp1233
g4
S'Napster File (MP3) sharing  software'
p1234
sg6
I00
sg7
I00
sg8
(lp1235
I6699
asg10
I01
ssS'anynetgateway'
p1236
(dp1237
g4
S''
sg6
I01
sg7
I00
sg8
(lp1238
I1491
asg10
I01
ssS'timeflies'
p1239
(dp1240
g4
S''
sg6
I01
sg7
I00
sg8
(lp1241
I1362
asg10
I01
ssS'stx'
p1242
(dp1243
g4
S'Stock IXChange'
p1244
sg6
I01
sg7
I00
sg8
(lp1245
I527
asg10
I01
ssS'telelpathstart'
p1246
(dp1247
g4
S''
sg6
I01
sg7
I00
sg8
(lp1248
I5010
asg10
I01
ssS'nqs'
p1249
(dp1250
g4
S''
sg6
I01
sg7
I00
sg8
(lp1251
I607
asg10
I01
ssS'nsrexecd'
p1252
(dp1253
g4
S'Legato NetWorker'
p1254
sg6
I00
sg7
I00
sg8
(lp1255
I7937
asg10
I01
ssS'bnet'
p1256
(dp1257
g4
S''
sg6
I01
sg7
I00
sg8
(lp1258
I415
asg10
I01
ssS'dasp'
p1259
(dp1260
g4
S''
sg6
I01
sg7
I00
sg8
(lp1261
I439
asg10
I01
ssS'softcm'
p1262
(dp1263
g4
S'HP SoftBench CM'
p1264
sg6
I01
sg7
I00
sg8
(lp1265
I6110
asg10
I01
ssS'instl_boots'
p1266
(dp1267
g4
S'Installation Bootstrap Proto. Serv.'
p1268
sg6
I01
sg7
I00
sg8
(lp1269
I1067
asg10
I01
ssS'erpc'
p1270
(dp1271
g4
S'Encore Expedited Remote Pro.Call'
p1272
sg6
I01
sg7
I00
sg8
(lp1273
I121
asg10
I01
ssS'rap'
p1274
(dp1275
g4
S'Route Access Protocol'
p1276
sg6
I01
sg7
I00
sg8
(lp1277
I38
aI256
asg10
I01
ssS'vpvd'
p1278
(dp1279
g4
S'Virtual Places Video data'
p1280
sg6
I01
sg7
I00
sg8
(lp1281
I1518
asg10
I01
ssS'omfs'
p1282
(dp1283
g4
S'OpenMosix File System'
p1284
sg6
I00
sg7
I00
sg8
(lp1285
I723
asg10
I01
ssS'vpvc'
p1286
(dp1287
g4
S'Virtual Places Video control'
p1288
sg6
I01
sg7
I00
sg8
(lp1289
I1519
asg10
I01
ssS'entrusttime'
p1290
(dp1291
g4
S''
sg6
I01
sg7
I00
sg8
(lp1292
I309
asg10
I01
ssS'efs'
p1293
(dp1294
g4
S'extended file name server'
p1295
sg6
I00
sg7
I00
sg8
(lp1296
I520
asg10
I01
ssS'imsldoc'
p1297
(dp1298
g4
S''
sg6
I01
sg7
I00
sg8
(lp1299
I2035
asg10
I01
ssS'rpasswd'
p1300
(dp1301
g4
S''
sg6
I00
sg7
I00
sg8
(lp1302
I774
asg10
I01
ssS'linuxconf'
p1303
(dp1304
g4
S'linuxconf'
p1305
sg6
I00
sg7
I00
sg8
(lp1306
I98
asg10
I01
ssS'analogx'
p1307
(dp1308
g4
S'AnalogX HTTP proxy port'
p1309
sg6
I00
sg7
I00
sg8
(lp1310
I6588
asg10
I01
ssS'sdadmind'
p1311
(dp1312
g4
S'ACE/Server services'
p1313
sg6
I00
sg7
I00
sg8
(lp1314
I5550
asg10
I01
ssS'relief'
p1315
(dp1316
g4
S'Relief Consulting'
p1317
sg6
I01
sg7
I00
sg8
(lp1318
I1353
asg10
I01
ssS'fcp'
p1319
(dp1320
g4
S'FirstClass Protocol'
p1321
sg6
I01
sg7
I00
sg8
(lp1322
I510
asg10
I01
ssS'stel'
p1323
(dp1324
g4
S'Secure telnet'
p1325
sg6
I00
sg7
I00
sg8
(lp1326
I10005
asg10
I01
ssS'printer'
p1327
(dp1328
g4
S'spooler (lpd)'
p1329
sg6
I01
sg7
I00
sg8
(lp1330
I515
asg10
I01
ssS'dsETOS'
p1331
(dp1332
g4
S'NEC Corporation'
p1333
sg6
I01
sg7
I00
sg8
(lp1334
I378
asg10
I01
ssS'crystalreports'
p1335
(dp1336
g4
S'Seagate Crystal Reports'
p1337
sg6
I00
sg7
I00
sg8
(lp1338
I6400
asg10
I01
ssS'exec'
p1339
(dp1340
g4
S'BSD rexecd(8)'
p1341
sg6
I00
sg7
I00
sg8
(lp1342
I512
asg10
I01
ssS'track'
p1343
(dp1344
g4
S'software distribution'
p1345
sg6
I00
sg7
I00
sg8
(lp1346
I3462
asg10
I01
ssS'controlit'
p1347
(dp1348
g4
S'Remotely possible'
p1349
sg6
I00
sg7
I00
sg8
(lp1350
I799
asg10
I01
ssS'pcanywheredata'
p1351
(dp1352
g4
S''
sg6
I00
sg7
I00
sg8
(lp1353
I5631
asg10
I01
ssS'who'
p1354
(dp1355
g4
S'BSD rwhod(8)'
p1356
sg6
I01
sg7
I00
sg8
(lp1357
I513
asg10
I00
ssS'tpdu'
p1358
(dp1359
g4
S'Hypercom TPDU'
p1360
sg6
I01
sg7
I00
sg8
(lp1361
I1430
asg10
I01
ssS'gppitnp'
p1362
(dp1363
g4
S'Genesis Point-to-Point Trans Net, or x400 ISO Email'
p1364
sg6
I01
sg7
I00
sg8
(lp1365
I103
asg10
I01
ssS'device'
p1366
(dp1367
g4
S''
sg6
I01
sg7
I00
sg8
(lp1368
I801
asg10
I01
ssS'ibm_wrless_lan'
p1369
(dp1370
g4
S'IBM Wireless LAN'
p1371
sg6
I01
sg7
I00
sg8
(lp1372
I1461
asg10
I01
ssS'orasrv'
p1373
(dp1374
g4
S'oracle or Prospero Directory Service non-priv'
p1375
sg6
I01
sg7
I00
sg8
(lp1376
I1525
asg10
I01
ssS'codasrv'
p1377
(dp1378
g4
S''
sg6
I01
sg7
I00
sg8
(lp1379
I2432
asg10
I01
ssS'urm'
p1380
(dp1381
g4
S'Cray Unified Resource Manager'
p1382
sg6
I01
sg7
I00
sg8
(lp1383
I606
asg10
I01
ssS'datasurfsrvsec'
p1384
(dp1385
g4
S''
sg6
I01
sg7
I00
sg8
(lp1386
I462
asg10
I01
ssS'rkinit'
p1387
(dp1388
g4
S'Kerberos (v4) remote initialization'
p1389
sg6
I01
sg7
I00
sg8
(lp1390
I2108
asg10
I01
ssS'con'
p1391
(dp1392
g4
S''
sg6
I01
sg7
I00
sg8
(lp1393
I759
asg10
I01
ssS'rendezvous'
p1394
(dp1395
g4
S'Rendezvous Zeroconf (used by Apple)'
p1396
sg6
I00
sg7
I00
sg8
(lp1397
I3689
asg10
I01
ssS'admeng'
p1398
(dp1399
g4
S'(chili!soft asp)'
p1400
sg6
I00
sg7
I00
sg8
(lp1401
I5102
asg10
I01
ssS'kx'
p1402
(dp1403
g4
S'X over kerberos'
p1404
sg6
I00
sg7
I00
sg8
(lp1405
I2111
asg10
I01
ssS'sgcp'
p1406
(dp1407
g4
S''
sg6
I01
sg7
I00
sg8
(lp1408
I440
asg10
I01
ssS'iafdbase'
p1409
(dp1410
g4
S''
sg6
I01
sg7
I00
sg8
(lp1411
I480
asg10
I00
ssS'cdc'
p1412
(dp1413
g4
S'Certificate Distribution Center'
p1414
sg6
I01
sg7
I00
sg8
(lp1415
I223
asg10
I01
ssS'compaqdiag'
p1416
(dp1417
g4
S'Compaq remote diagnostic/management'
p1418
sg6
I00
sg7
I00
sg8
(lp1419
I2301
aI49400
asg10
I01
ssS'innosys'
p1420
(dp1421
g4
S''
sg6
I01
sg7
I00
sg8
(lp1422
I1412
asg10
I01
ssS'ftps'
p1423
(dp1424
g4
S'ftp protocol, control, over TLS/SSL'
p1425
sg6
I00
sg7
I00
sg8
(lp1426
I990
asg10
I01
ssS'bhfhs'
p1427
(dp1428
g4
S''
sg6
I01
sg7
I00
sg8
(lp1429
I248
asg10
I01
ssS'msql'
p1430
(dp1431
g4
S'mini-sql server'
p1432
sg6
I00
sg7
I00
sg8
(lp1433
I1112
aI4333
asg10
I01
ssS'systat'
p1434
(dp1435
g4
S'Active Users'
p1436
sg6
I01
sg7
I00
sg8
(lp1437
I11
asg10
I01
ssS'dls'
p1438
(dp1439
g4
S'Directory Location Service'
p1440
sg6
I01
sg7
I00
sg8
(lp1441
I197
aI2047
asg10
I01
ssS'ock'
p1442
(dp1443
g4
S''
sg6
I01
sg7
I00
sg8
(lp1444
I1000
asg10
I00
ssS'newacct'
p1445
(dp1446
g4
S'[unauthorized use]'
p1447
sg6
I00
sg7
I00
sg8
(lp1448
I100
asg10
I01
ssS'xribs'
p1449
(dp1450
g4
S''
sg6
I01
sg7
I00
sg8
(lp1451
I2025
asg10
I00
ssS'dict'
p1452
(dp1453
g4
S'Dictionary service (RFC2229)'
p1454
sg6
I00
sg7
I00
sg8
(lp1455
I2628
asg10
I01
ssS'ldap'
p1456
(dp1457
g4
S'Lightweight Directory Access Protocol'
p1458
sg6
I01
sg7
I00
sg8
(lp1459
I389
asg10
I01
ssS'bgmp'
p1460
(dp1461
g4
S''
sg6
I00
sg7
I00
sg8
(lp1462
I264
asg10
I01
ssS'iiop'
p1463
(dp1464
g4
S''
sg6
I01
sg7
I00
sg8
(lp1465
I535
asg10
I01
ssS'hiq'
p1466
(dp1467
g4
S'HiQ License Manager'
p1468
sg6
I01
sg7
I00
sg8
(lp1469
I1410
asg10
I01
ssS'telefinder'
p1470
(dp1471
g4
S''
sg6
I01
sg7
I00
sg8
(lp1472
I1474
asg10
I01
ssS'smux'
p1473
(dp1474
g4
S'SNMP Unix Multiplexer'
p1475
sg6
I01
sg7
I00
sg8
(lp1476
I199
asg10
I01
ssS'dc'
p1477
(dp1478
g4
S'or nfr20 web queries'
p1479
sg6
I00
sg7
I00
sg8
(lp1480
I2001
asg10
I01
ssS'peport'
p1481
(dp1482
g4
S''
sg6
I01
sg7
I00
sg8
(lp1483
I1449
asg10
I01
ssS'zebrasrv'
p1484
(dp1485
g4
S'zebra service'
p1486
sg6
I00
sg7
I00
sg8
(lp1487
I2600
asg10
I01
ssS'pop3'
p1488
(dp1489
g4
S'PostOffice V.3'
p1490
sg6
I01
sg7
I00
sg8
(lp1491
I110
asg10
I01
ssS'pop2'
p1492
(dp1493
g4
S'PostOffice V.2'
p1494
sg6
I01
sg7
I00
sg8
(lp1495
I109
asg10
I01
ssS'wnn6_Cn'
p1496
(dp1497
g4
S'Wnn6 (Chinese input)'
p1498
sg6
I00
sg7
I00
sg8
(lp1499
I22289
asg10
I01
ssS'silc'
p1500
(dp1501
g4
S'Secure Internet Live Conferencing -- http://silcnet.org'
p1502
sg6
I00
sg7
I00
sg8
(lp1503
I706
asg10
I01
ssS'ssh'
p1504
(dp1505
g4
S'Secure Shell Login'
p1506
sg6
I01
sg7
I00
sg8
(lp1507
I22
asg10
I01
ssS'prosharerequest'
p1508
(dp1509
g4
S'proshare conf request'
p1510
sg6
I01
sg7
I00
sg8
(lp1511
I5716
asg10
I01
ssS'xfer'
p1512
(dp1513
g4
S'XFER Utility'
p1514
sg6
I01
sg7
I00
sg8
(lp1515
I82
asg10
I01
ssS'ircs'
p1516
(dp1517
g4
S'irc protocol over TLS/SSL'
p1518
sg6
I00
sg7
I00
sg8
(lp1519
I994
asg10
I01
ssS'qotd'
p1520
(dp1521
g4
S'Quote of the Day'
p1522
sg6
I01
sg7
I00
sg8
(lp1523
I17
asg10
I01
ssS'crs'
p1524
(dp1525
g4
S''
sg6
I01
sg7
I00
sg8
(lp1526
I507
asg10
I01
ssS'irc'
p1527
(dp1528
g4
S'Internet Relay Chat'
p1529
sg6
I01
sg7
I00
sg8
(lp1530
I194
aI6667
aI6668
asg10
I01
ssS'bhevent'
p1531
(dp1532
g4
S''
sg6
I01
sg7
I00
sg8
(lp1533
I357
asg10
I01
ssS'bytex'
p1534
(dp1535
g4
S''
sg6
I01
sg7
I00
sg8
(lp1536
I1375
asg10
I01
ssS'nimreg'
p1537
(dp1538
g4
S''
sg6
I01
sg7
I00
sg8
(lp1539
I1059
asg10
I01
ssS'PowerChutePLUS'
p1540
(dp1541
g4
S''
sg6
I01
sg7
I00
sg8
(lp1542
I6547
aI6548
aI6549
asg10
I01
ssS'dantz'
p1543
(dp1544
g4
S''
sg6
I01
sg7
I00
sg8
(lp1545
I497
asg10
I01
ssS'sdlog'
p1546
(dp1547
g4
S'ACE/Server services'
p1548
sg6
I00
sg7
I00
sg8
(lp1549
I5520
asg10
I01
ssS'supfiledbg'
p1550
(dp1551
g4
S'SUP debugging'
p1552
sg6
I00
sg7
I00
sg8
(lp1553
I1127
asg10
I01
ssS'rfe'
p1554
(dp1555
g4
S'Radio Free Ethernet'
p1556
sg6
I01
sg7
I00
sg8
(lp1557
I5002
asg10
I01
ssS'sonar'
p1558
(dp1559
g4
S''
sg6
I01
sg7
I00
sg8
(lp1560
I572
asg10
I01
ssS'shiva_confsrvr'
p1561
(dp1562
g4
S''
sg6
I01
sg7
I00
sg8
(lp1563
I1651
asg10
I01
ssS'amanda'
p1564
(dp1565
g4
S'Amanda Backup Util'
p1566
sg6
I01
sg7
I00
sg8
(lp1567
I10080
asg10
I00
ssS'whoami'
p1568
(dp1569
g4
S''
sg6
I01
sg7
I00
sg8
(lp1570
I565
asg10
I01
ssS'resvc'
p1571
(dp1572
g4
S'The Microsoft Exchange 2000 Server Routing Service          '
p1573
sg6
I00
sg7
I00
sg8
(lp1574
I691
asg10
I01
ssS'ocs_cmu'
p1575
(dp1576
g4
S''
sg6
I01
sg7
I00
sg8
(lp1577
I428
asg10
I01
ssS'set'
p1578
(dp1579
g4
S'secure electronic transaction'
p1580
sg6
I01
sg7
I00
sg8
(lp1581
I257
asg10
I00
ssS'concert'
p1582
(dp1583
g4
S''
sg6
I01
sg7
I00
sg8
(lp1584
I786
asg10
I01
ssS'rmt'
p1585
(dp1586
g4
S'Remote MT Protocol'
p1587
sg6
I01
sg7
I00
sg8
(lp1588
I411
asg10
I01
ssS'msrpc'
p1589
(dp1590
g4
S'Microsoft RPC services'
p1591
sg6
I01
sg7
I00
sg8
(lp1592
I135
asg10
I01
ssS'atls'
p1593
(dp1594
g4
S'Access Technology License Server'
p1595
sg6
I01
sg7
I00
sg8
(lp1596
I216
asg10
I01
ssS'auditd'
p1597
(dp1598
g4
S'Digital Audit Daemon'
p1599
sg6
I01
sg7
I00
sg8
(lp1600
I48
asg10
I01
ssS'securid'
p1601
(dp1602
g4
S'SecurID'
p1603
sg6
I01
sg7
I00
sg8
(lp1604
I5500
asg10
I00
ssS'molly'
p1605
(dp1606
g4
S'EPI Software Systems'
p1607
sg6
I01
sg7
I00
sg8
(lp1608
I1374
asg10
I01
ssS'radius'
p1609
(dp1610
g4
S'radius authentication'
p1611
sg6
I01
sg7
I00
sg8
(lp1612
I1645
aI1812
asg10
I00
ssS'rtmp'
p1613
(dp1614
g4
S'Macromedia FlasComm Server'
p1615
sg6
I00
sg7
I00
sg8
(lp1616
I1935
asg10
I01
ssS'dpsi'
p1617
(dp1618
g4
S''
sg6
I01
sg7
I00
sg8
(lp1619
I315
asg10
I01
ssS'opsec_ufp'
p1620
(dp1621
g4
S'Check Point OPSEC'
p1622
sg6
I00
sg7
I00
sg8
(lp1623
I18182
asg10
I01
ssS'ingreslock'
p1624
(dp1625
g4
S'ingres'
p1626
sg6
I01
sg7
I00
sg8
(lp1627
I1524
asg10
I01
ssS'bhmds'
p1628
(dp1629
g4
S''
sg6
I01
sg7
I00
sg8
(lp1630
I310
asg10
I01
ssS'imsp'
p1631
(dp1632
g4
S'Interactive Mail Support Protocol'
p1633
sg6
I01
sg7
I00
sg8
(lp1634
I406
asg10
I01
ssS'xinuexpansion1'
p1635
(dp1636
g4
S''
sg6
I01
sg7
I00
sg8
(lp1637
I2021
asg10
I00
ssS'xinuexpansion3'
p1638
(dp1639
g4
S''
sg6
I01
sg7
I00
sg8
(lp1640
I2023
asg10
I01
ssS'xinuexpansion2'
p1641
(dp1642
g4
S''
sg6
I01
sg7
I00
sg8
(lp1643
I2022
asg10
I00
ssS'xinuexpansion4'
p1644
(dp1645
g4
S''
sg6
I01
sg7
I00
sg8
(lp1646
I2024
asg10
I01
ssS'comscm'
p1647
(dp1648
g4
S''
sg6
I01
sg7
I00
sg8
(lp1649
I437
asg10
I01
ssS'tabula'
p1650
(dp1651
g4
S''
sg6
I01
sg7
I00
sg8
(lp1652
I1437
asg10
I01
ssS'finger'
p1653
(dp1654
g4
S''
sg6
I01
sg7
I00
sg8
(lp1655
I79
asg10
I01
ssS'ripng'
p1656
(dp1657
g4
S''
sg6
I01
sg7
I00
sg8
(lp1658
I521
asg10
I01
ssS'remotefs'
p1659
(dp1660
g4
S'rfs, rfs_server, Brunhoff remote filesystem'
p1661
sg6
I01
sg7
I00
sg8
(lp1662
I556
asg10
I01
ssS'nntp'
p1663
(dp1664
g4
S'Network News Transfer Protocol'
p1665
sg6
I01
sg7
I00
sg8
(lp1666
I119
asg10
I01
ssS'fodms'
p1667
(dp1668
g4
S'FODMS FLIP'
p1669
sg6
I01
sg7
I00
sg8
(lp1670
I7200
asg10
I01
ssS'pcnfs'
p1671
(dp1672
g4
S'PC-NFS DOS Authentication'
p1673
sg6
I01
sg7
I00
sg8
(lp1674
I640
asg10
I00
ssS'appleqtcsrvr'
p1675
(dp1676
g4
S''
sg6
I01
sg7
I00
sg8
(lp1677
I545
asg10
I00
ssS'padl2sim'
p1678
(dp1679
g4
S''
sg6
I01
sg7
I00
sg8
(lp1680
I5236
asg10
I01
ssS'snpp'
p1681
(dp1682
g4
S'Simple Network Paging Protocol'
p1683
sg6
I01
sg7
I00
sg8
(lp1684
I444
asg10
I01
ssS'lupa'
p1685
(dp1686
g4
S''
sg6
I01
sg7
I00
sg8
(lp1687
I1212
asg10
I01
ssS'tenebris_nts'
p1688
(dp1689
g4
S'Tenebris Network Trace Service'
p1690
sg6
I01
sg7
I00
sg8
(lp1691
I359
asg10
I01
ssS'mailbox'
p1692
(dp1693
g4
S''
sg6
I00
sg7
I00
sg8
(lp1694
I2004
asg10
I01
ssS'xinupageserver'
p1695
(dp1696
g4
S''
sg6
I01
sg7
I00
sg8
(lp1697
I2020
asg10
I01
ssS'remoteanything'
p1698
(dp1699
g4
S'neoworx remote-anything slave daemon'
p1700
sg6
I01
sg7
I00
sg8
(lp1701
I3996
aI3997
aI3998
aI3999
aI4000
asg10
I01
ssS'news'
p1702
(dp1703
g4
S'NewS window system'
p1704
sg6
I01
sg7
I00
sg8
(lp1705
I144
aI2009
asg10
I01
ssS'ciscopop'
p1706
(dp1707
g4
S'Cisco Postoffice Protocol for Cisco Secure IDS'
p1708
sg6
I01
sg7
I00
sg8
(lp1709
I45000
asg10
I00
ssS'keyserver'
p1710
(dp1711
g4
S''
sg6
I01
sg7
I00
sg8
(lp1712
I584
asg10
I01
ssS'rtsserv'
p1713
(dp1714
g4
S'Resource Tracking system server'
p1715
sg6
I01
sg7
I00
sg8
(lp1716
I2500
asg10
I01
ssS'diagmond'
p1717
(dp1718
g4
S''
sg6
I01
sg7
I00
sg8
(lp1719
I1508
asg10
I01
ssS'aurp'
p1720
(dp1721
g4
S'Appletalk Update-Based Routing Pro.'
p1722
sg6
I01
sg7
I00
sg8
(lp1723
I387
asg10
I01
ssS'VeritasNetbackup'
p1724
(dp1725
g4
S'vmd           server'
p1726
sg6
I00
sg7
I00
sg8
(lp1727
I13701
aI13702
aI13705
aI13706
aI13708
aI13709
aI13710
aI13711
aI13712
aI13713
aI13714
aI13715
aI13716
aI13717
aI13718
aI13720
aI13721
aI13722
aI13782
aI13783
asg10
I01
ssS'qft'
p1728
(dp1729
g4
S'Queued File Transport'
p1730
sg6
I01
sg7
I00
sg8
(lp1731
I189
asg10
I01
ssS'nnsp'
p1732
(dp1733
g4
S'Usenet, Network News Transfer'
p1734
sg6
I01
sg7
I00
sg8
(lp1735
I433
asg10
I01
ssS'decbsrv'
p1736
(dp1737
g4
S''
sg6
I01
sg7
I00
sg8
(lp1738
I579
asg10
I01
ssS'utmpsd'
p1739
(dp1740
g4
S''
sg6
I01
sg7
I00
sg8
(lp1741
I430
asg10
I01
ssS'sbook'
p1742
(dp1743
g4
S'Registration Network Protocol'
p1744
sg6
I01
sg7
I00
sg8
(lp1745
I1349
asg10
I01
ssS'msdtc'
p1746
(dp1747
g4
S'MS distributed transaction coordinator'
p1748
sg6
I00
sg7
I00
sg8
(lp1749
I3372
asg10
I01
ssS'aspeclmd'
p1750
(dp1751
g4
S''
sg6
I01
sg7
I00
sg8
(lp1752
I1544
asg10
I01
ssS'whosockami'
p1753
(dp1754
g4
S''
sg6
I01
sg7
I00
sg8
(lp1755
I2009
aI2019
asg10
I01
ssS'nameserver'
p1756
(dp1757
g4
S'Host Name Server'
p1758
sg6
I01
sg7
I00
sg8
(lp1759
I42
asg10
I01
ssS'powerburst'
p1760
(dp1761
g4
S'Air Soft Power Burst'
p1762
sg6
I01
sg7
I00
sg8
(lp1763
I485
asg10
I01
ssS'fasttrack'
p1764
(dp1765
g4
S'Kazaa File Sharing'
p1766
sg6
I01
sg7
I00
sg8
(lp1767
I1214
asg10
I01
ssS'instl_bootc'
p1768
(dp1769
g4
S'Installation Bootstrap Proto. Cli.'
p1770
sg6
I01
sg7
I00
sg8
(lp1771
I1068
asg10
I01
ssS'gopher'
p1772
(dp1773
g4
S''
sg6
I01
sg7
I00
sg8
(lp1774
I70
asg10
I01
ssS'xvttp'
p1775
(dp1776
g4
S''
sg6
I01
sg7
I00
sg8
(lp1777
I508
asg10
I01
ssS'unicall'
p1778
(dp1779
g4
S''
sg6
I01
sg7
I00
sg8
(lp1780
I4343
asg10
I01
ssS'chromagrafx'
p1781
(dp1782
g4
S''
sg6
I01
sg7
I00
sg8
(lp1783
I1373
asg10
I01
ssS'gwha'
p1784
(dp1785
g4
S'GW Hannaway Network License Manager'
p1786
sg6
I01
sg7
I00
sg8
(lp1787
I1383
asg10
I01
ssS'conference'
p1788
(dp1789
g4
S'chat'
p1790
sg6
I01
sg7
I00
sg8
(lp1791
I531
asg10
I01
ssS'pipe_server'
p1792
(dp1793
g4
S'Also used by NFR'
p1794
sg6
I01
sg7
I00
sg8
(lp1795
I2010
asg10
I00
ssS'afpovertcp'
p1796
(dp1797
g4
S'AFP over TCP'
p1798
sg6
I01
sg7
I00
sg8
(lp1799
I548
asg10
I01
ssS'equationbuilder'
p1800
(dp1801
g4
S'Digital Tool Works (MIT)'
p1802
sg6
I01
sg7
I00
sg8
(lp1803
I1351
asg10
I01
ssS'filemaker'
p1804
(dp1805
g4
S'Filemaker Server - http://www.filemaker.com/ti/104289.html'
p1806
sg6
I01
sg7
I00
sg8
(lp1807
I5003
asg10
I01
ssS'laplink'
p1808
(dp1809
g4
S''
sg6
I01
sg7
I00
sg8
(lp1810
I1547
asg10
I01
ssS'nessusd'
p1811
(dp1812
g4
S'Nessus Security Scanner (www.nessus.org) Daemon or chili!soft asp'
p1813
sg6
I00
sg7
I00
sg8
(lp1814
I3001
asg10
I01
ssS'ph'
p1815
(dp1816
g4
S''
sg6
I01
sg7
I00
sg8
(lp1817
I481
asg10
I00
ssS'waste'
p1818
(dp1819
g4
S'Nullsoft WASTE encrypted P2P app'
p1820
sg6
I00
sg7
I00
sg8
(lp1821
I1337
asg10
I01
ssS'Elite'
p1822
(dp1823
g4
S'Sometimes interesting stuff can be found here'
p1824
sg6
I00
sg7
I00
sg8
(lp1825
I31337
asg10
I01
ssS'citadel'
p1826
(dp1827
g4
S''
sg6
I01
sg7
I00
sg8
(lp1828
I504
asg10
I01
ssS'ftsrv'
p1829
(dp1830
g4
S''
sg6
I01
sg7
I00
sg8
(lp1831
I1359
asg10
I01
ssS'avian'
p1832
(dp1833
g4
S''
sg6
I01
sg7
I00
sg8
(lp1834
I486
asg10
I00
ssS'silverplatter'
p1835
(dp1836
g4
S''
sg6
I01
sg7
I00
sg8
(lp1837
I416
asg10
I01
ssS'pcanywherestat'
p1838
(dp1839
g4
S''
sg6
I01
sg7
I00
sg8
(lp1840
I5632
asg10
I01
ssS'cypress'
p1841
(dp1842
g4
S''
sg6
I00
sg7
I00
sg8
(lp1843
I2015
asg10
I01
ssS'kerberos'
p1844
(dp1845
g4
S'kdc Kerberos (v4)'
p1846
sg6
I01
sg7
I00
sg8
(lp1847
I750
asg10
I01
ssS'telnet'
p1848
(dp1849
g4
S''
sg6
I01
sg7
I00
sg8
(lp1850
I23
asg10
I01
ssS'hexen2'
p1851
(dp1852
g4
S'Hexen 2 game server'
p1853
sg6
I01
sg7
I00
sg8
(lp1854
I26900
asg10
I00
ssS'9pfs'
p1855
(dp1856
g4
S'plan 9 file service'
p1857
sg6
I01
sg7
I00
sg8
(lp1858
I564
asg10
I01
ssS'ripngd'
p1859
(dp1860
g4
S'RIPngd vty'
p1861
sg6
I00
sg7
I00
sg8
(lp1862
I2603
asg10
I01
ssS'graphics'
p1863
(dp1864
g4
S''
sg6
I01
sg7
I00
sg8
(lp1865
I41
asg10
I01
ssS'lanserver'
p1866
(dp1867
g4
S''
sg6
I01
sg7
I00
sg8
(lp1868
I637
asg10
I01
ssS'sdnskmp'
p1869
(dp1870
g4
S''
sg6
I01
sg7
I00
sg8
(lp1871
I558
asg10
I01
ssS'imap'
p1872
(dp1873
g4
S'Interim Mail Access Protocol v2'
p1874
sg6
I01
sg7
I00
sg8
(lp1875
I143
asg10
I01
ssS'rimsl'
p1876
(dp1877
g4
S''
sg6
I01
sg7
I00
sg8
(lp1878
I2044
asg10
I01
ssS'commerce'
p1879
(dp1880
g4
S''
sg6
I01
sg7
I00
sg8
(lp1881
I542
asg10
I01
ssS'pwdgen'
p1882
(dp1883
g4
S'Password Generator Protocol'
p1884
sg6
I01
sg7
I00
sg8
(lp1885
I129
asg10
I01
ssS'unify'
p1886
(dp1887
g4
S''
sg6
I01
sg7
I00
sg8
(lp1888
I181
asg10
I01
ssS'pksd'
p1889
(dp1890
g4
S'PGP Public Key Server'
p1891
sg6
I00
sg7
I00
sg8
(lp1892
I11371
asg10
I01
ssS'arcserve'
p1893
(dp1894
g4
S'ARCserve agent'
p1895
sg6
I00
sg7
I00
sg8
(lp1896
I6050
asg10
I01
ssS'mount'
p1897
(dp1898
g4
S'NFS Mount Service'
p1899
sg6
I01
sg7
I00
sg8
(lp1900
I635
asg10
I00
ssS'sdserv'
p1901
(dp1902
g4
S'ACE/Server services'
p1903
sg6
I00
sg7
I00
sg8
(lp1904
I5530
asg10
I01
ssS'uis'
p1905
(dp1906
g4
S''
sg6
I01
sg7
I00
sg8
(lp1907
I390
asg10
I01
ssS'gnutella'
p1908
(dp1909
g4
S'Gnutella file sharing protocol'
p1910
sg6
I00
sg7
I00
sg8
(lp1911
I6346
asg10
I01
ssS'btx'
p1912
(dp1913
g4
S"xcept4 (Interacts with German Telekom's CEPT videotext service)"
p1914
sg6
I00
sg7
I00
sg8
(lp1915
I20005
asg10
I01
ssS'nextstep'
p1916
(dp1917
g4
S'NextStep Window Server'
p1918
sg6
I01
sg7
I00
sg8
(lp1919
I178
asg10
I01
ssS'cfengine'
p1920
(dp1921
g4
S''
sg6
I01
sg7
I00
sg8
(lp1922
I5308
asg10
I01
ssS'login'
p1923
(dp1924
g4
S'BSD rlogind(8)'
p1925
sg6
I00
sg7
I00
sg8
(lp1926
I513
asg10
I01
ssS'clearcase'
p1927
(dp1928
g4
S''
sg6
I01
sg7
I00
sg8
(lp1929
I371
asg10
I01
ssS'spc'
p1930
(dp1931
g4
S'HP SoftBench Sub-Process Control'
p1932
sg6
I01
sg7
I00
sg8
(lp1933
I6111
asg10
I01
ssS'cvc'
p1934
(dp1935
g4
S''
sg6
I01
sg7
I00
sg8
(lp1936
I1495
asg10
I01
ssS'flexlm'
p1937
(dp1938
g4
S'Flexible License Manager'
p1939
sg6
I01
sg7
I00
sg8
(lp1940
I744
asg10
I01
ssS'unitary'
p1941
(dp1942
g4
S'Unisys Unitary Login'
p1943
sg6
I01
sg7
I00
sg8
(lp1944
I126
asg10
I01
ssS'localinfosrvr'
p1945
(dp1946
g4
S''
sg6
I01
sg7
I00
sg8
(lp1947
I1487
asg10
I01
ssS'ripd'
p1948
(dp1949
g4
S'RIPd vty'
p1950
sg6
I00
sg7
I00
sg8
(lp1951
I2602
asg10
I01
ssS'xlog'
p1952
(dp1953
g4
S''
sg6
I01
sg7
I00
sg8
(lp1954
I482
asg10
I00
ssS'Trinoo_Master'
p1955
(dp1956
g4
S'Trinoo distributed attack tool Master server control port'
p1957
sg6
I00
sg7
I00
sg8
(lp1958
I27665
asg10
I01
ssS'ris'
p1959
(dp1960
g4
S'Intergraph'
p1961
sg6
I01
sg7
I00
sg8
(lp1962
I180
asg10
I01
ssS'shivahose'
p1963
(dp1964
g4
S'Shiva Hose'
p1965
sg6
I00
sg7
I00
sg8
(lp1966
I1549
asg10
I01
ssS'abbaccuray'
p1967
(dp1968
g4
S''
sg6
I01
sg7
I00
sg8
(lp1969
I1546
asg10
I01
ssS'conf'
p1970
(dp1971
g4
S''
sg6
I00
sg7
I00
sg8
(lp1972
I2008
asg10
I01
ssS'supfilesrv'
p1973
(dp1974
g4
S'SUP server'
p1975
sg6
I00
sg7
I00
sg8
(lp1976
I871
asg10
I01
ssS'rtip'
p1977
(dp1978
g4
S''
sg6
I01
sg7
I00
sg8
(lp1979
I771
asg10
I01
ssS'rmonitor_secure'
p1980
(dp1981
g4
S''
sg6
I01
sg7
I00
sg8
(lp1982
I5145
asg10
I01
ssS'arcisdms'
p1983
(dp1984
g4
S''
sg6
I01
sg7
I00
sg8
(lp1985
I262
asg10
I01
ssS'kuang2'
p1986
(dp1987
g4
S'Kuang2 backdoor'
p1988
sg6
I00
sg7
I00
sg8
(lp1989
I17300
asg10
I01
ssS'tserver'
p1990
(dp1991
g4
S''
sg6
I01
sg7
I00
sg8
(lp1992
I450
asg10
I01
ssS'BackOrifice'
p1993
(dp1994
g4
S'cDc Back Orifice remote admin tool'
p1995
sg6
I01
sg7
I00
sg8
(lp1996
I31337
asg10
I00
ssS'ncld'
p1997
(dp1998
g4
S''
sg6
I01
sg7
I00
sg8
(lp1999
I405
asg10
I01
ssS'gacp'
p2000
(dp2001
g4
S'Gateway Access Control Protocol'
p2002
sg6
I00
sg7
I00
sg8
(lp2003
I190
asg10
I01
ssS'hostname'
p2004
(dp2005
g4
S'hostnames NIC Host Name Server'
p2006
sg6
I01
sg7
I00
sg8
(lp2007
I101
asg10
I01
ssS'ariel3'
p2008
(dp2009
g4
S''
sg6
I01
sg7
I00
sg8
(lp2010
I422
asg10
I01
ssS'qaz'
p2011
(dp2012
g4
S'Quaz trojan worm'
p2013
sg6
I00
sg7
I00
sg8
(lp2014
I7597
asg10
I01
ssS'netvenuechat'
p2015
(dp2016
g4
S'Nortel NetVenue Notification, Chat, Intercom'
p2017
sg6
I00
sg7
I00
sg8
(lp2018
I1023
asg10
I01
ssS'dayna'
p2019
(dp2020
g4
S''
sg6
I01
sg7
I00
sg8
(lp2021
I244
asg10
I01
ssS'mciautoreg'
p2022
(dp2023
g4
S''
sg6
I01
sg7
I00
sg8
(lp2024
I1528
asg10
I01
ssS'pacerforum'
p2025
(dp2026
g4
S''
sg6
I01
sg7
I00
sg8
(lp2027
I1480
asg10
I01
ssS'http'
p2028
(dp2029
g4
S'World Wide Web HTTP'
p2030
sg6
I01
sg7
I00
sg8
(lp2031
I80
asg10
I01
ssS'lgtomapper'
p2032
(dp2033
g4
S'Legato portmapper'
p2034
sg6
I00
sg7
I00
sg8
(lp2035
I7938
asg10
I01
ssS'nim'
p2036
(dp2037
g4
S''
sg6
I01
sg7
I00
sg8
(lp2038
I1058
asg10
I01
ssS'kis'
p2039
(dp2040
g4
S'KIS Protocol'
p2041
sg6
I01
sg7
I00
sg8
(lp2042
I186
asg10
I01
ssS'netsaint'
p2043
(dp2044
g4
S'Netsaint status daemon'
p2045
sg6
I00
sg7
I00
sg8
(lp2046
I1040
asg10
I01
ssS'ekshell'
p2047
(dp2048
g4
S'Kerberos encrypted remote shell -kfall'
p2049
sg6
I01
sg7
I00
sg8
(lp2050
I545
aI2106
asg10
I01
ssS'infoman'
p2051
(dp2052
g4
S'IBM Information Management'
p2053
sg6
I01
sg7
I00
sg8
(lp2054
I1451
asg10
I01
ssS'sdfunc'
p2055
(dp2056
g4
S''
sg6
I01
sg7
I00
sg8
(lp2057
I2046
asg10
I01
ssS'distccd'
p2058
(dp2059
g4
S'Distributed compiler daemon'
p2060
sg6
I00
sg7
I00
sg8
(lp2061
I3632
asg10
I01
ssS'rds2'
p2062
(dp2063
g4
S''
sg6
I01
sg7
I00
sg8
(lp2064
I1541
asg10
I01
ssS'nip'
p2065
(dp2066
g4
S'Amiga Envoy Network Inquiry Proto'
p2067
sg6
I01
sg7
I00
sg8
(lp2068
I376
asg10
I01
ssS'flexlm10'
p2069
(dp2070
g4
S'FlexLM license manager additional ports'
p2071
sg6
I00
sg7
I00
sg8
(lp2072
I27010
asg10
I01
ssS'ansanotify'
p2073
(dp2074
g4
S'ANSA REX Notify'
p2075
sg6
I01
sg7
I00
sg8
(lp2076
I116
asg10
I01
ssS'tftp'
p2077
(dp2078
g4
S'Trivial File Transfer'
p2079
sg6
I01
sg7
I00
sg8
(lp2080
I69
asg10
I01
ssS'rfa'
p2081
(dp2082
g4
S'remote file access server'
p2083
sg6
I01
sg7
I00
sg8
(lp2084
I4672
asg10
I01
ssS'audit'
p2085
(dp2086
g4
S'Unisys Audit SITP'
p2087
sg6
I01
sg7
I00
sg8
(lp2088
I182
asg10
I01
ssS'supdup'
p2089
(dp2090
g4
S'BSD supdupd(8)'
p2091
sg6
I01
sg7
I00
sg8
(lp2092
I95
asg10
I01
ssS'invokator'
p2093
(dp2094
g4
S''
sg6
I00
sg7
I00
sg8
(lp2095
I2006
asg10
I01
ssS'cybercash'
p2096
(dp2097
g4
S''
sg6
I01
sg7
I00
sg8
(lp2098
I551
asg10
I01
ssS'chargen'
p2099
(dp2100
g4
S'ttytst source Character Generator'
p2101
sg6
I01
sg7
I00
sg8
(lp2102
I19
asg10
I01
ssS'ccmail'
p2103
(dp2104
g4
S'cc:mail/lotus'
p2105
sg6
I01
sg7
I00
sg8
(lp2106
I3264
asg10
I01
ssS'genie'
p2107
(dp2108
g4
S'Genie Protocol'
p2109
sg6
I01
sg7
I00
sg8
(lp2110
I402
asg10
I01
ssS'nced'
p2111
(dp2112
g4
S''
sg6
I01
sg7
I00
sg8
(lp2113
I404
asg10
I01
ssS'tcpmux'
p2114
(dp2115
g4
S'TCP Port Service Multiplexer [rfc-1078]'
p2116
sg6
I01
sg7
I00
sg8
(lp2117
I1
asg10
I01
ssS'kpop'
p2118
(dp2119
g4
S'Pop with Kerberos'
p2120
sg6
I00
sg7
I00
sg8
(lp2121
I1109
asg10
I01
ssS'mnotes'
p2122
(dp2123
g4
S'CommonTime Mnotes PDA Synchronization'
p2124
sg6
I00
sg7
I00
sg8
(lp2125
I603
asg10
I01
ssS'knetd'
p2126
(dp2127
g4
S''
sg6
I00
sg7
I00
sg8
(lp2128
I2053
asg10
I01
ssS'sdreport'
p2129
(dp2130
g4
S'ACE/Server services'
p2131
sg6
I00
sg7
I00
sg8
(lp2132
I5540
asg10
I01
ssS'spamassassin'
p2133
(dp2134
g4
S'Apache SpamAssassin spamd'
p2135
sg6
I00
sg7
I00
sg8
(lp2136
I783
asg10
I01
ssS'multiplex'
p2137
(dp2138
g4
S'Network Innovations Multiplex'
p2139
sg6
I01
sg7
I00
sg8
(lp2140
I171
asg10
I01
ssS'mysql'
p2141
(dp2142
g4
S'mySQL'
p2143
sg6
I00
sg7
I00
sg8
(lp2144
I3306
asg10
I01
ssS'applix'
p2145
(dp2146
g4
S'Applix ac'
p2147
sg6
I01
sg7
I00
sg8
(lp2148
I999
asg10
I00
ssS'alpes'
p2149
(dp2150
g4
S''
sg6
I01
sg7
I00
sg8
(lp2151
I463
asg10
I01
ssS'streettalk'
p2152
(dp2153
g4
S''
sg6
I00
sg7
I00
sg8
(lp2154
I566
asg10
I01
ssS'snmp'
p2155
(dp2156
g4
S''
sg6
I01
sg7
I00
sg8
(lp2157
I161
asg10
I01
ssS'bigbrother'
p2158
(dp2159
g4
S'Big Brother monitoring server - www.bb4.com'
p2160
sg6
I00
sg7
I00
sg8
(lp2161
I1984
asg10
I01
ssS'cfingerd'
p2162
(dp2163
g4
S'GNU finger'
p2164
sg6
I00
sg7
I00
sg8
(lp2165
I2003
asg10
I01
ssS'prosharevideo'
p2166
(dp2167
g4
S'proshare conf video'
p2168
sg6
I01
sg7
I00
sg8
(lp2169
I5714
asg10
I01
ssS'ipdd'
p2170
(dp2171
g4
S''
sg6
I01
sg7
I00
sg8
(lp2172
I578
asg10
I01
ssS'smpte'
p2173
(dp2174
g4
S''
sg6
I01
sg7
I00
sg8
(lp2175
I420
asg10
I01
ssS'wms'
p2176
(dp2177
g4
S'Windows media service'
p2178
sg6
I00
sg7
I00
sg8
(lp2179
I1755
asg10
I01
ssS'dlsrpn'
p2180
(dp2181
g4
S'Data Link Switch Read Port Number'
p2182
sg6
I01
sg7
I00
sg8
(lp2183
I2065
asg10
I01
ssS'pawserv'
p2184
(dp2185
g4
S'Perf Analysis Workbench'
p2186
sg6
I01
sg7
I00
sg8
(lp2187
I345
asg10
I01
ssS'editbench'
p2188
(dp2189
g4
S'Registration Network Protocol'
p2190
sg6
I01
sg7
I00
sg8
(lp2191
I1350
asg10
I01
ssS'openmanage'
p2192
(dp2193
g4
S'Dell OpenManage'
p2194
sg6
I00
sg7
I00
sg8
(lp2195
I7273
asg10
I01
ssS'bo2k'
p2196
(dp2197
g4
S'Back Orifice 2K Default Port'
p2198
sg6
I01
sg7
I00
sg8
(lp2199
I54320
aI54321
asg10
I01
ssS'blackjack'
p2200
(dp2201
g4
S'network blackjack'
p2202
sg6
I01
sg7
I00
sg8
(lp2203
I1025
asg10
I00
ssS'dbase'
p2204
(dp2205
g4
S'dBASE Unix'
p2206
sg6
I01
sg7
I00
sg8
(lp2207
I217
asg10
I01
ssS'snare'
p2208
(dp2209
g4
S''
sg6
I01
sg7
I00
sg8
(lp2210
I509
asg10
I01
ssS'submission'
p2211
(dp2212
g4
S''
sg6
I01
sg7
I00
sg8
(lp2213
I587
asg10
I01
ssS'rtsclient'
p2214
(dp2215
g4
S'Resource Tracking system client'
p2216
sg6
I01
sg7
I00
sg8
(lp2217
I2501
asg10
I01
ssS'intrinsa'
p2218
(dp2219
g4
S''
sg6
I01
sg7
I00
sg8
(lp2220
I503
asg10
I01
ssS'mftp'
p2221
(dp2222
g4
S''
sg6
I01
sg7
I00
sg8
(lp2223
I349
asg10
I01
ssS'opsec_cvp'
p2224
(dp2225
g4
S'Check Point OPSEC'
p2226
sg6
I00
sg7
I00
sg8
(lp2227
I18181
asg10
I01
ssS'shrinkwrap'
p2228
(dp2229
g4
S''
sg6
I01
sg7
I00
sg8
(lp2230
I358
asg10
I01
ssS'NetBus'
p2231
(dp2232
g4
S'NetBus backdoor trojan or Trend Micro Office Scan'
p2233
sg6
I00
sg7
I00
sg8
(lp2234
I12345
aI12346
asg10
I01
ssS'ocs_amu'
p2235
(dp2236
g4
S''
sg6
I01
sg7
I00
sg8
(lp2237
I429
asg10
I01
ssS'kdm'
p2238
(dp2239
g4
S'K Display Manager (KDE version of xdm)'
p2240
sg6
I00
sg7
I00
sg8
(lp2241
I1024
asg10
I01
ssS'dberegister'
p2242
(dp2243
g4
S''
sg6
I01
sg7
I00
sg8
(lp2244
I1479
asg10
I01
ssS'elcsd'
p2245
(dp2246
g4
S'errlog copy/server daemon'
p2247
sg6
I01
sg7
I00
sg8
(lp2248
I704
asg10
I01
ssS'acmsoda'
p2249
(dp2250
g4
S''
sg6
I01
sg7
I00
sg8
(lp2251
I6969
asg10
I01
ssS'biff'
p2252
(dp2253
g4
S'comsat'
p2254
sg6
I01
sg7
I00
sg8
(lp2255
I512
asg10
I00
ssS'acas'
p2256
(dp2257
g4
S'ACA Services'
p2258
sg6
I01
sg7
I00
sg8
(lp2259
I62
asg10
I01
ssS'decauth'
p2260
(dp2261
g4
S''
sg6
I01
sg7
I00
sg8
(lp2262
I316
asg10
I01
ssS'acap'
p2263
(dp2264
g4
S'ACAP server of Communigate (www.stalker.com)'
p2265
sg6
I00
sg7
I00
sg8
(lp2266
I674
asg10
I01
ssS'vnc'
p2267
(dp2268
g4
S'Virtual Network Computer display 0'
p2269
sg6
I00
sg7
I00
sg8
(lp2270
I5900
asg10
I01
ssS'rightbrain'
p2271
(dp2272
g4
S'RightBrain Software'
p2273
sg6
I01
sg7
I00
sg8
(lp2274
I1354
asg10
I01
ssS'subseven'
p2275
(dp2276
g4
S'Subseven trojan'
p2277
sg6
I00
sg7
I00
sg8
(lp2278
I16959
aI27374
asg10
I01
ssS'extensisportfolio'
p2279
(dp2280
g4
S'Portfolio Server by Extensis Product Group'
p2281
sg6
I00
sg7
I00
sg8
(lp2282
I2903
asg10
I01
ssS'rsync'
p2283
(dp2284
g4
S'Rsync server ( http://rsync.samba.org )'
p2285
sg6
I00
sg7
I00
sg8
(lp2286
I873
asg10
I01
ssS'icb'
p2287
(dp2288
g4
S"Internet Citizen's Band"
p2289
sg6
I00
sg7
I00
sg8
(lp2290
I7326
asg10
I01
ssS'daytime'
p2291
(dp2292
g4
S''
sg6
I01
sg7
I00
sg8
(lp2293
I13
asg10
I01
ssS'netwall'
p2294
(dp2295
g4
S'for emergency broadcasts'
p2296
sg6
I01
sg7
I00
sg8
(lp2297
I533
asg10
I01
ssS'screencast'
p2298
(dp2299
g4
S''
sg6
I01
sg7
I00
sg8
(lp2300
I1368
asg10
I01
ssS'novastorbakcup'
p2301
(dp2302
g4
S'novastor backup'
p2303
sg6
I01
sg7
I00
sg8
(lp2304
I308
asg10
I01
ssS'maitrd'
p2305
(dp2306
g4
S''
sg6
I01
sg7
I00
sg8
(lp2307
I997
asg10
I01
ssS'blackboard'
p2308
(dp2309
g4
S''
sg6
I01
sg7
I00
sg8
(lp2310
I2032
asg10
I01
ssS'nfs'
p2311
(dp2312
g4
S'networked file system'
p2313
sg6
I01
sg7
I00
sg8
(lp2314
I2049
asg10
I01
ssS'icq'
p2315
(dp2316
g4
S'AOL ICQ instant messaging clent-server communication'
p2317
sg6
I01
sg7
I00
sg8
(lp2318
I4000
asg10
I00
ssS'rpc2portmap'
p2319
(dp2320
g4
S''
sg6
I01
sg7
I00
sg8
(lp2321
I369
asg10
I01
ssS'deslogin'
p2322
(dp2323
g4
S'encrypted symmetric telnet/login'
p2324
sg6
I00
sg7
I00
sg8
(lp2325
I2005
aI3005
asg10
I01
ssS'pegboard'
p2326
(dp2327
g4
S'Electronic PegBoard'
p2328
sg6
I01
sg7
I00
sg8
(lp2329
I1357
asg10
I01
ssS'ulistserv'
p2330
(dp2331
g4
S'Unix Listserv'
p2332
sg6
I01
sg7
I00
sg8
(lp2333
I372
asg10
I01
ssS'nms'
p2334
(dp2335
g4
S'Hypercom NMS'
p2336
sg6
I01
sg7
I00
sg8
(lp2337
I1429
asg10
I01
ssS'biimenu'
p2338
(dp2339
g4
S'Beckman Instruments, Inc.'
p2340
sg6
I01
sg7
I00
sg8
(lp2341
I18000
asg10
I01
ssS'Trinoo_Bcast'
p2342
(dp2343
g4
S'Trinoo distributed attack tool Master'
p2344
sg6
I01
sg7
I00
sg8
(lp2345
I27444
asg10
I00
ssS'confluent'
p2346
(dp2347
g4
S'Confluent License Manager'
p2348
sg6
I01
sg7
I00
sg8
(lp2349
I1484
asg10
I01
ssS'netrcs'
p2350
(dp2351
g4
S'Network based Rev. Cont. Sys.'
p2352
sg6
I01
sg7
I00
sg8
(lp2353
I742
asg10
I01
ssS'audionews'
p2354
(dp2355
g4
S'Audio News Multicast'
p2356
sg6
I01
sg7
I00
sg8
(lp2357
I114
asg10
I01
ssS'dca'
p2358
(dp2359
g4
S''
sg6
I01
sg7
I00
sg8
(lp2360
I1456
asg10
I01
ssS'photuris'
p2361
(dp2362
g4
S'Photuris Key Management'
p2363
sg6
I01
sg7
I00
sg8
(lp2364
I468
asg10
I01
ssS'meetingmaker'
p2365
(dp2366
g4
S'Meeting maker time management software'
p2367
sg6
I00
sg7
I00
sg8
(lp2368
I3292
asg10
I01
ssS'skronk'
p2369
(dp2370
g4
S''
sg6
I01
sg7
I00
sg8
(lp2371
I460
asg10
I01
ssS'fatserv'
p2372
(dp2373
g4
S'Fatmen Server'
p2374
sg6
I01
sg7
I00
sg8
(lp2375
I347
asg10
I01
ssS'canna'
p2376
(dp2377
g4
S'Canna (Japanese Input)'
p2378
sg6
I00
sg7
I00
sg8
(lp2379
I5680
asg10
I01
ssS'dcs'
p2380
(dp2381
g4
S''
sg6
I01
sg7
I00
sg8
(lp2382
I1367
asg10
I01
ssS'dcp'
p2383
(dp2384
g4
S'Device Control Protocol'
p2385
sg6
I01
sg7
I00
sg8
(lp2386
I93
asg10
I01
ssS'videotex'
p2387
(dp2388
g4
S''
sg6
I01
sg7
I00
sg8
(lp2389
I516
asg10
I01
ssS'src'
p2390
(dp2391
g4
S'IBM System Resource Controller'
p2392
sg6
I01
sg7
I00
sg8
(lp2393
I200
asg10
I01
ssS'about'
p2394
(dp2395
g4
S''
sg6
I01
sg7
I00
sg8
(lp2396
I2019
asg10
I00
ssS'dbbrowse'
p2397
(dp2398
g4
S'Databeam Corporation'
p2399
sg6
I01
sg7
I00
sg8
(lp2400
I47557
asg10
I01
ssS'ajp13'
p2401
(dp2402
g4
S'Apache JServ Protocol 1.3'
p2403
sg6
I00
sg7
I00
sg8
(lp2404
I8009
asg10
I01
ssS'ajp12'
p2405
(dp2406
g4
S'Apache JServ Protocol 1.x'
p2407
sg6
I00
sg7
I00
sg8
(lp2408
I8007
asg10
I01
ssS'aci'
p2409
(dp2410
g4
S'Application Communication Interface'
p2411
sg6
I01
sg7
I00
sg8
(lp2412
I187
asg10
I01
ssS'sqlsrv'
p2413
(dp2414
g4
S'SQL Service'
p2415
sg6
I01
sg7
I00
sg8
(lp2416
I156
asg10
I01
ssS'smtps'
p2417
(dp2418
g4
S'smtp protocol over TLS/SSL (was ssmtp)'
p2419
sg6
I01
sg7
I00
sg8
(lp2420
I465
asg10
I01
ssS'bgp'
p2421
(dp2422
g4
S'Border Gateway Protocol'
p2423
sg6
I01
sg7
I00
sg8
(lp2424
I179
asg10
I01
ssS'svrloc'
p2425
(dp2426
g4
S'Server Location'
p2427
sg6
I01
sg7
I00
sg8
(lp2428
I427
asg10
I01
ssS'opsec_lea'
p2429
(dp2430
g4
S'Check Point OPSEC'
p2431
sg6
I00
sg7
I00
sg8
(lp2432
I18184
asg10
I01
ssS'acp'
p2433
(dp2434
g4
S'Aeolon Core Protocol'
p2435
sg6
I01
sg7
I00
sg8
(lp2436
I599
asg10
I01
ssS'nsiiops'
p2437
(dp2438
g4
S'iiop name service over tls/ssl'
p2439
sg6
I01
sg7
I00
sg8
(lp2440
I261
asg10
I01
ssS'radacct'
p2441
(dp2442
g4
S'radius accounting'
p2443
sg6
I01
sg7
I00
sg8
(lp2444
I1646
aI1813
asg10
I00
ssS'vnas'
p2445
(dp2446
g4
S''
sg6
I01
sg7
I00
sg8
(lp2447
I577
asg10
I01
ssS'discard'
p2448
(dp2449
g4
S'sink null'
p2450
sg6
I01
sg7
I00
sg8
(lp2451
I9
asg10
I01
ssS'prosharedata'
p2452
(dp2453
g4
S'proshare conf data'
p2454
sg6
I01
sg7
I00
sg8
(lp2455
I5715
asg10
I01
ssS'spsc'
p2456
(dp2457
g4
S''
sg6
I01
sg7
I00
sg8
(lp2458
I478
asg10
I01
ssS'cvc_hostd'
p2459
(dp2460
g4
S''
sg6
I01
sg7
I00
sg8
(lp2461
I442
asg10
I01
ssS'L2TP'
p2462
(dp2463
g4
S''
sg6
I01
sg7
I00
sg8
(lp2464
I1701
asg10
I00
ssS'mosmig'
p2465
(dp2466
g4
S'OpenMOSix MIGrates local processes'
p2467
sg6
I00
sg7
I00
sg8
(lp2468
I4660
asg10
I01
ssS'qrh'
p2469
(dp2470
g4
S''
sg6
I01
sg7
I00
sg8
(lp2471
I752
asg10
I01
ssS'prosharenotify'
p2472
(dp2473
g4
S'proshare conf notify'
p2474
sg6
I01
sg7
I00
sg8
(lp2475
I5717
asg10
I01
ssS'socks'
p2476
(dp2477
g4
S''
sg6
I01
sg7
I00
sg8
(lp2478
I1080
asg10
I01
ssS'down'
p2479
(dp2480
g4
S''
sg6
I00
sg7
I00
sg8
(lp2481
I2022
asg10
I01
ssS'snmptrap'
p2482
(dp2483
g4
S'snmp-trap'
p2484
sg6
I01
sg7
I00
sg8
(lp2485
I162
asg10
I01
ssS'ppp'
p2486
(dp2487
g4
S'User-level ppp daemon, or chili!soft asp'
p2488
sg6
I00
sg7
I00
sg8
(lp2489
I3000
asg10
I01
ssS'hotline'
p2490
(dp2491
g4
S''
sg6
I00
sg7
I00
sg8
(lp2492
I1234
asg10
I01
ssS'rsvp_tunnel'
p2493
(dp2494
g4
S''
sg6
I01
sg7
I00
sg8
(lp2495
I363
asg10
I01
ssS'nuts_bootp'
p2496
(dp2497
g4
S'NUTS Bootp Server'
p2498
sg6
I01
sg7
I00
sg8
(lp2499
I4133
asg10
I01
ssS'funkproxy'
p2500
(dp2501
g4
S'Funk Software, Inc.'
p2502
sg6
I01
sg7
I00
sg8
(lp2503
I1505
asg10
I01
ssS'support'
p2504
(dp2505
g4
S'prmsd gnatsd\t# cygnus bug tracker'
p2506
sg6
I00
sg7
I00
sg8
(lp2507
I1529
asg10
I01
ssS'rcp'
p2508
(dp2509
g4
S'Radio Control Protocol'
p2510
sg6
I01
sg7
I00
sg8
(lp2511
I469
asg10
I01
ssS'submit'
p2512
(dp2513
g4
S''
sg6
I00
sg7
I00
sg8
(lp2514
I773
asg10
I01
ssS'device2'
p2515
(dp2516
g4
S''
sg6
I01
sg7
I00
sg8
(lp2517
I2030
asg10
I01
ssS'dsfgw'
p2518
(dp2519
g4
S''
sg6
I01
sg7
I00
sg8
(lp2520
I438
asg10
I01
ssS'iiimsf'
p2521
(dp2522
g4
S'Internet/Intranet Input Method Server Framework'
p2523
sg6
I00
sg7
I00
sg8
(lp2524
I50000
aI50002
asg10
I01
ssS'vat'
p2525
(dp2526
g4
S'VAT default data'
p2527
sg6
I00
sg7
I00
sg8
(lp2528
I3456
asg10
I01
ssS'statsrv'
p2529
(dp2530
g4
S'Statistics Service'
p2531
sg6
I01
sg7
I00
sg8
(lp2532
I133
asg10
I01
ssS'linx'
p2533
(dp2534
g4
S''
sg6
I01
sg7
I00
sg8
(lp2535
I1361
asg10
I01
ssS'codaauth2'
p2536
(dp2537
g4
S''
sg6
I01
sg7
I00
sg8
(lp2538
I370
asg10
I01
ssS'ttyinfo'
p2539
(dp2540
g4
S''
sg6
I00
sg7
I00
sg8
(lp2541
I2012
asg10
I01
ssS'sqlserv'
p2542
(dp2543
g4
S'SQL Services'
p2544
sg6
I01
sg7
I00
sg8
(lp2545
I118
asg10
I01
ssS'rje'
p2546
(dp2547
g4
S'Remote Job Entry'
p2548
sg6
I01
sg7
I00
sg8
(lp2549
I5
asg10
I01
ssS'link'
p2550
(dp2551
g4
S''
sg6
I01
sg7
I00
sg8
(lp2552
I245
asg10
I01
ssS'cycleserv2'
p2553
(dp2554
g4
S''
sg6
I01
sg7
I00
sg8
(lp2555
I772
asg10
I01
ssS'mptn'
p2556
(dp2557
g4
S'Multi Protocol Trans. Net.'
p2558
sg6
I01
sg7
I00
sg8
(lp2559
I397
asg10
I01
ssS'tcpnethaspsrv'
p2560
(dp2561
g4
S''
sg6
I01
sg7
I00
sg8
(lp2562
I475
asg10
I01
ssS'quotad'
p2563
(dp2564
g4
S''
sg6
I01
sg7
I00
sg8
(lp2565
I762
asg10
I01
ssS'arns'
p2566
(dp2567
g4
S'A Remote Network Server System'
p2568
sg6
I01
sg7
I00
sg8
(lp2569
I384
asg10
I01
ssS'isis'
p2570
(dp2571
g4
S''
sg6
I01
sg7
I00
sg8
(lp2572
I2042
asg10
I01
ssS'nuts_dem'
p2573
(dp2574
g4
S'NUTS Daemon'
p2575
sg6
I01
sg7
I00
sg8
(lp2576
I4132
asg10
I01
ssS'rmonitor'
p2577
(dp2578
g4
S'rmonitord'
p2579
sg6
I01
sg7
I00
sg8
(lp2580
I560
asg10
I01
ssS'vsinet'
p2581
(dp2582
g4
S''
sg6
I01
sg7
I00
sg8
(lp2583
I996
asg10
I00
ssS'sgmp'
p2584
(dp2585
g4
S''
sg6
I01
sg7
I00
sg8
(lp2586
I153
asg10
I01
ssS'klogin'
p2587
(dp2588
g4
S'Kerberos (v4/v5)'
p2589
sg6
I01
sg7
I00
sg8
(lp2590
I543
asg10
I01
ssS'anet'
p2591
(dp2592
g4
S'ATEXSSTR'
p2593
sg6
I01
sg7
I00
sg8
(lp2594
I212
asg10
I01
ssS'hassle'
p2595
(dp2596
g4
S''
sg6
I01
sg7
I00
sg8
(lp2597
I375
asg10
I01
ssS'isqlplus'
p2598
(dp2599
g4
S'Oracle web enabled SQL interface (version 10g+)'
p2600
sg6
I00
sg7
I00
sg8
(lp2601
I5560
asg10
I01
ssS'pirp'
p2602
(dp2603
g4
S''
sg6
I01
sg7
I00
sg8
(lp2604
I553
asg10
I01
ssS'admdog'
p2605
(dp2606
g4
S'(chili!soft asp)'
p2607
sg6
I00
sg7
I00
sg8
(lp2608
I5101
asg10
I01
ssS'cdfunc'
p2609
(dp2610
g4
S''
sg6
I01
sg7
I00
sg8
(lp2611
I2045
asg10
I01
ssS'isdninfo'
p2612
(dp2613
g4
S'isdninfo'
p2614
sg6
I00
sg7
I00
sg8
(lp2615
I6105
aI6106
asg10
I01
ssS'mailq'
p2616
(dp2617
g4
S''
sg6
I01
sg7
I00
sg8
(lp2618
I174
asg10
I01
ssS'netstat'
p2619
(dp2620
g4
S''
sg6
I00
sg7
I00
sg8
(lp2621
I15
asg10
I01
ssS'af'
p2622
(dp2623
g4
S'AudioFile'
p2624
sg6
I01
sg7
I00
sg8
(lp2625
I1411
asg10
I01
ssS'deslogind'
p2626
(dp2627
g4
S''
sg6
I00
sg7
I00
sg8
(lp2628
I3006
asg10
I01
ssS'lsnr'
p2629
(dp2630
g4
S'Oracle DB listener'
p2631
sg6
I00
sg7
I00
sg8
(lp2632
I1158
asg10
I01
ssS'ldapssl'
p2633
(dp2634
g4
S'LDAP over SSL'
p2635
sg6
I00
sg7
I00
sg8
(lp2636
I636
asg10
I01
ssS'nerv'
p2637
(dp2638
g4
S'SNI R&D network'
p2639
sg6
I01
sg7
I00
sg8
(lp2640
I1222
asg10
I01
ssS'umeter'
p2641
(dp2642
g4
S'udemon'
p2643
sg6
I01
sg7
I00
sg8
(lp2644
I571
asg10
I01
ssS'pip'
p2645
(dp2646
g4
S''
sg6
I01
sg7
I00
sg8
(lp2647
I321
asg10
I01
ssS'nkd'
p2648
(dp2649
g4
S''
sg6
I01
sg7
I00
sg8
(lp2650
I1650
asg10
I01
ssS'tlisrv'
p2651
(dp2652
g4
S'oracle'
p2653
sg6
I01
sg7
I00
sg8
(lp2654
I1527
asg10
I01
ssS'wnn6'
p2655
(dp2656
g4
S'Wnn6 (Japanese input)'
p2657
sg6
I00
sg7
I00
sg8
(lp2658
I22273
asg10
I01
ssS'abyss'
p2659
(dp2660
g4
S'Abyss web server remote web management interface'
p2661
sg6
I00
sg7
I00
sg8
(lp2662
I9999
asg10
I01
ssS'vpac'
p2663
(dp2664
g4
S'Virtual Places Audio control'
p2665
sg6
I01
sg7
I00
sg8
(lp2666
I1517
asg10
I01
ssS'uucp'
p2667
(dp2668
g4
S'uucpd'
p2669
sg6
I01
sg7
I00
sg8
(lp2670
I540
asg10
I01
ssS'vpad'
p2671
(dp2672
g4
S'Virtual Places Audio data'
p2673
sg6
I01
sg7
I00
sg8
(lp2674
I1516
asg10
I01
ssS'ss7ns'
p2675
(dp2676
g4
S''
sg6
I01
sg7
I00
sg8
(lp2677
I477
asg10
I01
ssS'hybrid'
p2678
(dp2679
g4
S'Hybrid Encryption Protocol'
p2680
sg6
I01
sg7
I00
sg8
(lp2681
I1424
asg10
I01
ssS'srmp'
p2682
(dp2683
g4
S'Spider Remote Monitoring Protocol'
p2684
sg6
I01
sg7
I00
sg8
(lp2685
I193
asg10
I01
ssS'sybase'
p2686
(dp2687
g4
S'Sybase database'
p2688
sg6
I00
sg7
I00
sg8
(lp2689
I2638
asg10
I01
ssS'pehelp'
p2690
(dp2691
g4
S''
sg6
I01
sg7
I00
sg8
(lp2692
I2307
asg10
I01
ssS'passgo'
p2693
(dp2694
g4
S''
sg6
I01
sg7
I00
sg8
(lp2695
I511
asg10
I01
ssS'bmap'
p2696
(dp2697
g4
S'Bull Apprise portmapper'
p2698
sg6
I01
sg7
I00
sg8
(lp2699
I3421
asg10
I01
ssS'subntbcst_tftp'
p2700
(dp2701
g4
S''
sg6
I01
sg7
I00
sg8
(lp2702
I247
asg10
I01
ssS'mortgageware'
p2703
(dp2704
g4
S''
sg6
I01
sg7
I00
sg8
(lp2705
I367
asg10
I01
ssS'ns'
p2706
(dp2707
g4
S''
sg6
I01
sg7
I00
sg8
(lp2708
I760
asg10
I00
ssS'ulpnet'
p2709
(dp2710
g4
S''
sg6
I01
sg7
I00
sg8
(lp2711
I483
asg10
I01
ssS'xaudio'
p2712
(dp2713
g4
S'Xaserver\t# X Audio Server'
p2714
sg6
I00
sg7
I00
sg8
(lp2715
I1103
asg10
I01
ssS'omserv'
p2716
(dp2717
g4
S''
sg6
I01
sg7
I00
sg8
(lp2718
I764
asg10
I01
ssS'iad2'
p2719
(dp2720
g4
S'BBN IAD'
p2721
sg6
I01
sg7
I00
sg8
(lp2722
I1031
asg10
I01
ssS'iad3'
p2723
(dp2724
g4
S'BBN IAD'
p2725
sg6
I01
sg7
I00
sg8
(lp2726
I1032
asg10
I01
ssS'iad1'
p2727
(dp2728
g4
S'BBN IAD'
p2729
sg6
I01
sg7
I00
sg8
(lp2730
I1030
asg10
I01
ssS'opsec_ela'
p2731
(dp2732
g4
S'Check Point OPSEC'
p2733
sg6
I00
sg7
I00
sg8
(lp2734
I18187
asg10
I01
ssS'mfcobol'
p2735
(dp2736
g4
S'Micro Focus Cobol'
p2737
sg6
I01
sg7
I00
sg8
(lp2738
I86
asg10
I01
ssS'servexec'
p2739
(dp2740
g4
S''
sg6
I00
sg7
I00
sg8
(lp2741
I2021
asg10
I01
ssS'activesync'
p2742
(dp2743
g4
S'Microsoft ActiveSync PDY synchronization'
p2744
sg6
I00
sg7
I00
sg8
(lp2745
I5679
asg10
I01
ssS'accessbuilder'
p2746
(dp2747
g4
S'or Audio CD Database'
p2748
sg6
I01
sg7
I00
sg8
(lp2749
I888
asg10
I01
ssS'entrustmanager'
p2750
(dp2751
g4
S'EntrustManager - NorTel DES auth network see 389/tcp'
p2752
sg6
I01
sg7
I00
sg8
(lp2753
I709
asg10
I01
ssS'pop3pw'
p2754
(dp2755
g4
S'Eudora compatible PW changer'
p2756
sg6
I00
sg7
I00
sg8
(lp2757
I106
asg10
I01
ssS'onmux'
p2758
(dp2759
g4
S'Meeting maker'
p2760
sg6
I01
sg7
I00
sg8
(lp2761
I417
asg10
I01
ssS'loadsrv'
p2762
(dp2763
g4
S''
sg6
I00
sg7
I00
sg8
(lp2764
I480
asg10
I01
ssS'wnn6_DS'
p2765
(dp2766
g4
S'Wnn6 (Dserver)'
p2767
sg6
I00
sg7
I00
sg8
(lp2768
I26208
asg10
I01
ssS'vemmi'
p2769
(dp2770
g4
S''
sg6
I01
sg7
I00
sg8
(lp2771
I575
asg10
I01
ssS'netmap_lm'
p2772
(dp2773
g4
S''
sg6
I01
sg7
I00
sg8
(lp2774
I1493
asg10
I01
ssS'nms_topo_serv'
p2775
(dp2776
g4
S''
sg6
I01
sg7
I00
sg8
(lp2777
I1486
asg10
I01
ssS'ipcd'
p2778
(dp2779
g4
S''
sg6
I01
sg7
I00
sg8
(lp2780
I576
asg10
I01
ssS'hdap'
p2781
(dp2782
g4
S''
sg6
I01
sg7
I00
sg8
(lp2783
I263
asg10
I01
ssS'rxe'
p2784
(dp2785
g4
S''
sg6
I01
sg7
I00
sg8
(lp2786
I761
asg10
I00
ssS'sftp'
p2787
(dp2788
g4
S'Simple File Transfer Protocol'
p2789
sg6
I01
sg7
I00
sg8
(lp2790
I115
asg10
I01
ssS'time'
p2791
(dp2792
g4
S'timserver'
p2793
sg6
I01
sg7
I00
sg8
(lp2794
I37
asg10
I01
ssS'oracle'
p2795
(dp2796
g4
S'Oracle Database'
p2797
sg6
I01
sg7
I00
sg8
(lp2798
I1521
aI2005
asg10
I01
ssS'bgpd'
p2799
(dp2800
g4
S'BGPd vty'
p2801
sg6
I00
sg7
I00
sg8
(lp2802
I2605
asg10
I01
ssS'dvs'
p2803
(dp2804
g4
S''
sg6
I00
sg7
I00
sg8
(lp2805
I481
asg10
I01
ssS'wpgs'
p2806
(dp2807
g4
S''
sg6
I01
sg7
I00
sg8
(lp2808
I780
asg10
I01
ss."""

os_classification_content = """(lp1
(S''
S'Nothing in this list matches'
tp2
a(S'2Wire|embedded||WAP'
S'2Wire embedded WAP'
tp3
a(S'3Com|ComOS||terminal server'
S'3Com ComOS terminal server'
tp4
a(S'3Com|embedded||broadband router'
S'3Com embedded broadband router'
tp5
a(S'3Com|embedded||PBX'
S'3Com embedded PBX'
tp6
a(S'3Com|embedded||router'
S'3Com embedded router'
tp7
a(S'3Com|embedded||switch'
S'3Com embedded switch'
tp8
a(S'3Com|embedded||telecom-misc'
S'3Com embedded telecom-misc'
tp9
a(S'3Com|embedded||terminal server'
S'3Com embedded terminal server'
tp10
a(S'3Com|embedded||WAP'
S'3Com embedded WAP'
tp11
a(S'ACC|embedded||router'
S'ACC embedded router'
tp12
a(S'Acorn|RISC OS||general purpose'
S'Acorn RISC OS general purpose'
tp13
a(S'Actiontec|embedded||broadband router'
S'Actiontec embedded broadband router'
tp14
a(S'Adtran|embedded||telecom-misc'
S'Adtran embedded telecom-misc'
tp15
a(S'Aethra|embedded||webcam'
S'Aethra embedded webcam'
tp16
a(S'Aironet|embedded||bridge'
S'Aironet embedded bridge'
tp17
a(S'Aironet|embedded||WAP'
S'Aironet embedded WAP'
tp18
a(S'Alcatel|embedded||broadband router'
S'Alcatel embedded broadband router'
tp19
a(S'Alcatel|embedded||switch'
S'Alcatel embedded switch'
tp20
a(S'Alcatel|embedded||telecom-misc'
S'Alcatel embedded telecom-misc'
tp21
a(S'Alcatel|embedded||VoIP phone'
S'Alcatel embedded VoIP phone'
tp22
a(S'Allied Telesyn|embedded||hub'
S'Allied Telesyn embedded hub'
tp23
a(S'Allied Telesyn|embedded||switch'
S'Allied Telesyn embedded switch'
tp24
a(S'Alpha Micro|AMOS||general purpose'
S'Alpha Micro AMOS general purpose'
tp25
a(S'Alteon|embedded||load balancer'
S'Alteon embedded load balancer'
tp26
a(S'Alteon|embedded||switch'
S'Alteon embedded switch'
tp27
a(S'Amiga|AmigaOS||general purpose'
S'Amiga AmigaOS general purpose'
tp28
a(S'APC|embedded||power-device'
S'APC embedded power-device'
tp29
a(S'Apollo|Domain/OS||general purpose'
S'Apollo Domain/OS general purpose'
tp30
a(S'Apple|A/UX||general purpose'
S'Apple A/UX general purpose'
tp31
a(S'Apple|embedded||printer'
S'Apple embedded printer'
tp32
a(S'Apple|embedded||WAP'
S'Apple embedded WAP'
tp33
a(S'Apple|Mac OS|7.X|general purpose'
S'Apple Mac OS 7.X general purpose'
tp34
a(S'Apple|Mac OS|8.X|general purpose'
S'Apple Mac OS 8.X general purpose'
tp35
a(S'Apple|Mac OS|9.X|general purpose'
S'Apple Mac OS 9.X general purpose'
tp36
a(S'Apple|Mac OS X|10.0.X|general purpose'
S'Apple Mac OS X 10.0.X general purpose'
tp37
a(S'Apple|Mac OS X|10.1.X|general purpose'
S'Apple Mac OS X 10.1.X general purpose'
tp38
a(S'Apple|Mac OS X|10.2.X|general purpose'
S'Apple Mac OS X 10.2.X general purpose'
tp39
a(S'Apple|Mac OS X|10.3.X|general purpose'
S'Apple Mac OS X 10.3.X general purpose'
tp40
a(S'Apple|Mac OS X|10.4.X|general purpose'
S'Apple Mac OS X 10.4.X general purpose'
tp41
a(S'Apple|Newton OS||PDA'
S'Apple Newton OS PDA'
tp42
a(S'Arescom|embedded||broadband router'
S'Arescom embedded broadband router'
tp43
a(S'Arlan|embedded||bridge'
S'Arlan embedded bridge'
tp44
a(S'ARRIS|embedded||broadband router'
S'ARRIS embedded broadband router'
tp45
a(S'Asante|embedded||hub'
S'Asante embedded hub'
tp46
a(S'Asante|embedded||switch'
S'Asante embedded switch'
tp47
a(S'Ascend|embedded||broadband router'
S'Ascend embedded broadband router'
tp48
a(S'Ascend|embedded||router'
S'Ascend embedded router'
tp49
a(S'Ascend|Embedded/OS||router'
S'Ascend Embedded/OS router'
tp50
a(S'Ascend|TAOS||terminal server'
S'Ascend TAOS terminal server'
tp51
a(S'ASCOM|embedded||broadband router'
S'ASCOM embedded broadband router'
tp52
a(S'Atari|Atari||game console'
S'Atari game console'
tp53
a(S'Atari|Atari||general purpose'
S'Atari general purpose'
tp54
a(S'AtheOS|AtheOS||general purpose'
S'AtheOS general purpose'
tp55
a(S'AudioCodes|embedded||VoIP gateway'
S'AudioCodes embedded VoIP gateway'
tp56
a(S'Auspex|AuspexOS||fileserver'
S'Auspex AuspexOS fileserver'
tp57
a(S'Avaya|embedded||PBX'
S'Avaya embedded PBX'
tp58
a(S'Avaya|embedded||telecom-misc'
S'Avaya embedded telecom-misc'
tp59
a(S'Avocent|embedded||specialized'
S'Avocent embedded specialized'
tp60
a(S'Avocent|embedded||terminal server'
S'Avocent embedded terminal server'
tp61
a(S'Axent|Windows|NT/2K/XP|firewall'
S'Axent Windows NT/2K/XP firewall'
tp62
a(S'AXIS|embedded||fileserver'
S'AXIS embedded fileserver'
tp63
a(S'AXIS|embedded||print server'
S'AXIS embedded print server'
tp64
a(S'AXIS|embedded||webcam'
S'AXIS embedded webcam'
tp65
a(S'AXIS|Linux||print server'
S'AXIS Linux print server'
tp66
a(S'AXIS|Linux||webcam'
S'AXIS Linux webcam'
tp67
a(S'Barix|embedded||media device'
S'Barix embedded media device'
tp68
a(S'Bay Networks|embedded||router'
S'Bay Networks embedded router'
tp69
a(S'Bay Networks|embedded||switch'
S'Bay Networks embedded switch'
tp70
a(S'Bay Networks|embedded||terminal server'
S'Bay Networks embedded terminal server'
tp71
a(S'BayTech|embedded||power-device'
S'BayTech embedded power-device'
tp72
a(S'BBIagent|Linux|2.4.X|software router'
S'BBIagent Linux 2.4.X software router'
tp73
a(S'Be|BeOS|4.X|general purpose'
S'Be BeOS 4.X general purpose'
tp74
a(S'Be|BeOS|5.X|general purpose'
S'Be BeOS 5.X general purpose'
tp75
a(S'Beck-IPC|embedded||specialized'
S'Beck-IPC embedded specialized'
tp76
a(S'Belkin|embedded||broadband router'
S'Belkin embedded broadband router'
tp77
a(S'Bell Labs|Plan9||general purpose'
S'Bell Labs Plan9 general purpose'
tp78
a(S'BenQ|embedded||WAP'
S'BenQ embedded WAP'
tp79
a(S'Billion|embedded||broadband router'
S'Billion embedded broadband router'
tp80
a(S'BinTec|embedded||broadband router'
S'BinTec embedded broadband router'
tp81
a(S'Blue Coat|embedded||web proxy'
S'Blue Coat embedded web proxy'
tp82
a(S'Blue Coat|SGOS||web proxy'
S'Blue Coat SGOS web proxy'
tp83
a(S'Borderware|embedded||firewall'
S'Borderware embedded firewall'
tp84
a(S'Bosch|embedded||webcam'
S'Bosch embedded webcam'
tp85
a(S'BreezeCOM|embedded||bridge'
S'BreezeCOM embedded bridge'
tp86
a(S'Brix Networks|embedded||specialized'
S'Brix Networks embedded specialized'
tp87
a(S'Brocade|embedded||switch'
S'Brocade embedded switch'
tp88
a(S'Brother|embedded||printer'
S'Brother embedded printer'
tp89
a(S'BSDI|BSD/OS|2.X|general purpose'
S'BSDI BSD/OS 2.X general purpose'
tp90
a(S'BSDI|BSD/OS|3.X|general purpose'
S'BSDI BSD/OS 3.X general purpose'
tp91
a(S'BSDI|BSD/OS|4.X|general purpose'
S'BSDI BSD/OS 4.X general purpose'
tp92
a(S'Cabletron|embedded||router'
S'Cabletron embedded router'
tp93
a(S'Cabletron|embedded||switch'
S'Cabletron embedded switch'
tp94
a(S'CacheFlow|CacheOS||web proxy'
S'CacheFlow CacheOS web proxy'
tp95
a(S'Canon|embedded||printer'
S'Canon embedded printer'
tp96
a(S'Cantillion|embedded||switch'
S'Cantillion embedded switch'
tp97
a(S'Capellix|embedded||storage-misc'
S'Capellix embedded storage-misc'
tp98
a(S'CastleNet|embedded||broadband router'
S'CastleNet embedded broadband router'
tp99
a(S'Cayman|embedded||broadband router'
S'Cayman embedded broadband router'
tp100
a(S'Chase|embedded||terminal server'
S'Chase embedded terminal server'
tp101
a(S'Checkpoint|IPSO||firewall'
S'Checkpoint IPSO firewall'
tp102
a(S'Checkpoint|Solaris|8|firewall'
S'Checkpoint Solaris 8 firewall'
tp103
a(S'Checkpoint|Windows|NT/2K/XP|firewall'
S'Checkpoint Windows NT/2K/XP firewall'
tp104
a(S'Cisco|CacheOS||web proxy'
S'Cisco CacheOS web proxy'
tp105
a(S'Cisco|CBOS||broadband router'
S'Cisco CBOS broadband router'
tp106
a(S'Cisco|Content Networking System||web proxy'
S'Cisco Content Networking System web proxy'
tp107
a(S'Cisco|embedded||bridge'
S'Cisco embedded bridge'
tp108
a(S'Cisco|embedded||broadband router'
S'Cisco embedded broadband router'
tp109
a(S'Cisco|embedded||encryption accelerator'
S'Cisco embedded encryption accelerator'
tp110
a(S'Cisco|embedded||hub'
S'Cisco embedded hub'
tp111
a(S'Cisco|embedded||load balancer'
S'Cisco embedded load balancer'
tp112
a(S'Cisco|embedded||router'
S'Cisco embedded router'
tp113
a(S'Cisco|embedded||switch'
S'Cisco embedded switch'
tp114
a(S'Cisco|embedded||terminal server'
S'Cisco embedded terminal server'
tp115
a(S'Cisco|embedded||VoIP adapter'
S'Cisco embedded VoIP adapter'
tp116
a(S'Cisco|embedded||VoIP phone'
S'Cisco embedded VoIP phone'
tp117
a(S'Cisco|embedded||WAP'
S'Cisco embedded WAP'
tp118
a(S'Cisco|embedded||web proxy'
S'Cisco embedded web proxy'
tp119
a(S'Cisco|IOS|10.X|router'
S'Cisco IOS 10.X router'
tp120
a(S'Cisco|IOS|11.X|router'
S'Cisco IOS 11.X router'
tp121
a(S'Cisco|IOS|11.X|switch'
S'Cisco IOS 11.X switch'
tp122
a(S'Cisco|IOS|11.X|terminal server'
S'Cisco IOS 11.X terminal server'
tp123
a(S'Cisco|IOS|12.X|broadband router'
S'Cisco IOS 12.X broadband router'
tp124
a(S'Cisco|IOS|12.X|router'
S'Cisco IOS 12.X router'
tp125
a(S'Cisco|IOS|12.X|switch'
S'Cisco IOS 12.X switch'
tp126
a(S'Cisco|IOS|12.X|WAP'
S'Cisco IOS 12.X WAP'
tp127
a(S'Cisco|IOS||router'
S'Cisco IOS router'
tp128
a(S'Cisco|NmpSW||switch'
S'Cisco NmpSW switch'
tp129
a(S'Cisco|PIX|4.X|firewall'
S'Cisco PIX 4.X firewall'
tp130
a(S'Cisco|PIX|5.X|firewall'
S'Cisco PIX 5.X firewall'
tp131
a(S'Cisco|PIX|6.X|firewall'
S'Cisco PIX 6.X firewall'
tp132
a(S'Cisco|PIX||firewall'
S'Cisco PIX firewall'
tp133
a(S'Cisco|vxworks||WAP'
S'Cisco vxworks WAP'
tp134
a(S'Clipcomm|embedded||VoIP phone'
S'Clipcomm embedded VoIP phone'
tp135
a(S'Cnet|embedded||broadband router'
S'Cnet embedded broadband router'
tp136
a(S'CNT|embedded||storage-misc'
S'CNT embedded storage-misc'
tp137
a(S'Cobalt|Linux|2.0.X|general purpose'
S'Cobalt Linux 2.0.X general purpose'
tp138
a(S'Commodore|embedded||game console'
S'Commodore embedded game console'
tp139
a(S'Compaq|embedded||remote management'
S'Compaq embedded remote management'
tp140
a(S'Compaq|embedded||WAP'
S'Compaq embedded WAP'
tp141
a(S'Compaq|Tru64 UNIX|4.X|general purpose'
S'Compaq Tru64 UNIX 4.X general purpose'
tp142
a(S'Compaq|Tru64 UNIX|5.X|general purpose'
S'Compaq Tru64 UNIX 5.X general purpose'
tp143
a(S'Compaq|Windows|PocketPC/CE|terminal'
S'Compaq Windows PocketPC/CE terminal'
tp144
a(S'Compatible Systems|embedded||broadband router'
S'Compatible Systems embedded broadband router'
tp145
a(S'Compatible Systems|embedded||router'
S'Compatible Systems embedded router'
tp146
a(S'Compex|embedded||switch'
S'Compex embedded switch'
tp147
a(S'CompUSA|embedded||broadband router'
S'CompUSA embedded broadband router'
tp148
a(S'Computone|embedded||terminal server'
S'Computone embedded terminal server'
tp149
a(S'Conexant|embedded||broadband router'
S'Conexant embedded broadband router'
tp150
a(S'Contiki|Contiki||specialized'
S'Contiki specialized'
tp151
a(S'Convex|ConvexOS||general purpose'
S'Convex ConvexOS general purpose'
tp152
a(S'Convex|SPP-UX||general purpose'
S'Convex SPP-UX general purpose'
tp153
a(S'Copper Mountain|embedded||terminal server'
S'Copper Mountain embedded terminal server'
tp154
a(S'Corega|embedded||broadband router'
S'Corega embedded broadband router'
tp155
a(S'Cray|UNICOS|10.X|general purpose'
S'Cray UNICOS 10.X general purpose'
tp156
a(S'Cray|UNICOS|8.X|general purpose'
S'Cray UNICOS 8.X general purpose'
tp157
a(S'Cray|UNICOS||general purpose'
S'Cray UNICOS general purpose'
tp158
a(S'Cray|Unisys||general purpose'
S'Cray Unisys general purpose'
tp159
a(S'Cyberguard|embedded||firewall'
S'Cyberguard embedded firewall'
tp160
a(S'Cyclades|Cyras||router'
S'Cyclades Cyras router'
tp161
a(S'Cyclades|Cyras||terminal server'
S'Cyclades Cyras terminal server'
tp162
a(S'Cyclades|Cyros||router'
S'Cyclades Cyros router'
tp163
a(S'Cyclades|Cyros||terminal server'
S'Cyclades Cyros terminal server'
tp164
a(S'D-Link|embedded||broadband router'
S'D-Link embedded broadband router'
tp165
a(S'D-Link|embedded||hub'
S'D-Link embedded hub'
tp166
a(S'D-Link|embedded||print server'
S'D-Link embedded print server'
tp167
a(S'D-Link|embedded||telecom-misc'
S'D-Link embedded telecom-misc'
tp168
a(S'D-Link|embedded||WAP'
S'D-Link embedded WAP'
tp169
a(S'D-Link|embedded||webcam'
S'D-Link embedded webcam'
tp170
a(S'Data General|AOS/VS||general purpose'
S'Data General AOS/VS general purpose'
tp171
a(S'Data General|DG/UX||general purpose'
S'Data General DG/UX general purpose'
tp172
a(S'Datavoice|embedded||CSUDSU'
S'Datavoice embedded CSUDSU'
tp173
a(S'DEC|BSD-misc||general purpose'
S'DEC BSD-misc general purpose'
tp174
a(S'DEC|DIGITAL UNIX|1.X|general purpose'
S'DEC DIGITAL UNIX 1.X general purpose'
tp175
a(S'DEC|DIGITAL UNIX|2.X|general purpose'
S'DEC DIGITAL UNIX 2.X general purpose'
tp176
a(S'DEC|DIGITAL UNIX|3.X|general purpose'
S'DEC DIGITAL UNIX 3.X general purpose'
tp177
a(S'DEC|DIGITAL UNIX|4.X|general purpose'
S'DEC DIGITAL UNIX 4.X general purpose'
tp178
a(S'DEC|DIGITAL UNIX|5.X|general purpose'
S'DEC DIGITAL UNIX 5.X general purpose'
tp179
a(S'DEC|embedded||router'
S'DEC embedded router'
tp180
a(S'DEC|embedded||terminal server'
S'DEC embedded terminal server'
tp181
a(S'DEC|IOS|10.X|router'
S'DEC IOS 10.X router'
tp182
a(S'DEC|OpenVMS|6.X|general purpose'
S'DEC OpenVMS 6.X general purpose'
tp183
a(S'DEC|OpenVMS|7.X|general purpose'
S'DEC OpenVMS 7.X general purpose'
tp184
a(S'DEC|TOPS-20||general purpose'
S'DEC TOPS-20 general purpose'
tp185
a(S'DEC|Ultrix||general purpose'
S'DEC Ultrix general purpose'
tp186
a(S'DEC|VMS||general purpose'
S'DEC VMS general purpose'
tp187
a(S'Dell|embedded||printer'
S'Dell embedded printer'
tp188
a(S'Dell|embedded||remote management'
S'Dell embedded remote management'
tp189
a(S'Dell|embedded||storage-misc'
S'Dell embedded storage-misc'
tp190
a(S'Dell|embedded||switch'
S'Dell embedded switch'
tp191
a(S'Digital Link|embedded||CSUDSU'
S'Digital Link embedded CSUDSU'
tp192
a(S'Digital Networks|embedded||switch'
S'Digital Networks embedded switch'
tp193
a(S'Digitel|embedded||router'
S'Digitel embedded router'
tp194
a(S'Draytek|embedded||broadband router'
S'Draytek embedded broadband router'
tp195
a(S'Easytel|embedded||broadband router'
S'Easytel embedded broadband router'
tp196
a(S'Edimax|embedded||broadband router'
S'Edimax embedded broadband router'
tp197
a(S'Edimax|embedded||print server'
S'Edimax embedded print server'
tp198
a(S'Efficient Networks|embedded||broadband router'
S'Efficient Networks embedded broadband router'
tp199
a(S'Eicon|embedded||broadband router'
S'Eicon embedded broadband router'
tp200
a(S'Elsa|embedded||broadband router'
S'Elsa embedded broadband router'
tp201
a(S'EMC|DART||fileserver'
S'EMC DART fileserver'
tp202
a(S'Enterasys|embedded||firewall'
S'Enterasys embedded firewall'
tp203
a(S'Enterasys|embedded||switch'
S'Enterasys embedded switch'
tp204
a(S'Epson|embedded||printer'
S'Epson embedded printer'
tp205
a(S'Ericsson|embedded||broadband router'
S'Ericsson embedded broadband router'
tp206
a(S'Ericsson|embedded||terminal server'
S'Ericsson embedded terminal server'
tp207
a(S'EUSSO|embedded||print server'
S'EUSSO embedded print server'
tp208
a(S'Exabyte|embedded||storage-misc'
S'Exabyte embedded storage-misc'
tp209
a(S'Extreme Networks|embedded||switch'
S'Extreme Networks embedded switch'
tp210
a(S'Extreme Networks|Extremeware||switch'
S'Extreme Networks Extremeware switch'
tp211
a(S'F5 Labs|BSDI||load balancer'
S'F5 Labs BSDI load balancer'
tp212
a(S'F5 Labs|embedded||load balancer'
S'F5 Labs embedded load balancer'
tp213
a(S'FastComm|embedded||specialized'
S'FastComm embedded specialized'
tp214
a(S'FiberLine|embedded||broadband router'
S'FiberLine embedded broadband router'
tp215
a(S'FiberLine|embedded||WAP'
S'FiberLine embedded WAP'
tp216
a(S'FlowPoint|embedded||broadband router'
S'FlowPoint embedded broadband router'
tp217
a(S'Fore|embedded||switch'
S'Fore embedded switch'
tp218
a(S'Fortinet|embedded||firewall'
S'Fortinet embedded firewall'
tp219
a(S'Foundry|embedded||load balancer'
S'Foundry embedded load balancer'
tp220
a(S'Foundry|IronWare||load balancer'
S'Foundry IronWare load balancer'
tp221
a(S'FreeBSD|FreeBSD|2.X|general purpose'
S'FreeBSD 2.X general purpose'
tp222
a(S'FreeBSD|FreeBSD|3.X|general purpose'
S'FreeBSD 3.X general purpose'
tp223
a(S'FreeBSD|FreeBSD|4.X|general purpose'
S'FreeBSD 4.X general purpose'
tp224
a(S'FreeBSD|FreeBSD|4.x|general purpose'
S'FreeBSD 4.x general purpose'
tp225
a(S'FreeBSD|FreeBSD|5.X|general purpose'
S'FreeBSD 5.X general purpose'
tp226
a(S'FreeBSD|FreeBSD|6.X|general purpose'
S'FreeBSD 6.X general purpose'
tp227
a(S'FreeSCO|Linux|2.0.X|router'
S'FreeSCO Linux 2.0.X router'
tp228
a(S'Galacticomm|WorldGroup||BBS'
S'Galacticomm WorldGroup BBS'
tp229
a(S'Gandalf|embedded||router'
S'Gandalf embedded router'
tp230
a(S'Gatorbox|GatorShare||bridge'
S'Gatorbox GatorShare bridge'
tp231
a(S'Gauntlet|Solaris|2.5.X|firewall'
S'Gauntlet Solaris 2.5.X firewall'
tp232
a(S'Genius|embedded||print server'
S'Genius embedded print server'
tp233
a(S'Global Technology Associates|embedded||firewall'
S'Global Technology Associates embedded firewall'
tp234
a(S'GNet|embedded||broadband router'
S'GNet embedded broadband router'
tp235
a(S'GNU|Hurd||general purpose'
S'GNU Hurd general purpose'
tp236
a(S'GrandStream|embedded||VoIP adapter'
S'GrandStream embedded VoIP adapter'
tp237
a(S'Grandstream|embedded||VoIP adapter'
S'Grandstream embedded VoIP adapter'
tp238
a(S'GrandStream|embedded||VoIP phone'
S'GrandStream embedded VoIP phone'
tp239
a(S'Handspring|PalmOS|5.X|PDA'
S'Handspring PalmOS 5.X PDA'
tp240
a(S'Hawking|embedded||print server'
S'Hawking embedded print server'
tp241
a(S'Hitachi|HI-UX||general purpose'
S'Hitachi HI-UX general purpose'
tp242
a(S'HP|BSD-misc||general purpose'
S'HP BSD-misc general purpose'
tp243
a(S'HP|embedded||load balancer'
S'HP embedded load balancer'
tp244
a(S'HP|embedded||print server'
S'HP embedded print server'
tp245
a(S'HP|embedded||printer'
S'HP embedded printer'
tp246
a(S'HP|embedded||remote management'
S'HP embedded remote management'
tp247
a(S'HP|embedded||scanner'
S'HP embedded scanner'
tp248
a(S'HP|embedded||switch'
S'HP embedded switch'
tp249
a(S'HP|embedded||X terminal'
S'HP embedded X terminal'
tp250
a(S'HP|HP-UX|10.X|general purpose'
S'HP HP-UX 10.X general purpose'
tp251
a(S'HP|HP-UX|11.X|general purpose'
S'HP HP-UX 11.X general purpose'
tp252
a(S'HP|HP-UX|7.X|general purpose'
S'HP HP-UX 7.X general purpose'
tp253
a(S'HP|HP-UX|9.X|general purpose'
S'HP HP-UX 9.X general purpose'
tp254
a(S'HP|MPE/iX||general purpose'
S'HP MPE/iX general purpose'
tp255
a(S'HP|Netstation||X terminal'
S'HP Netstation X terminal'
tp256
a(S'HP|VxWorks||switch'
S'HP VxWorks switch'
tp257
a(S'Huawei|VRP||router'
S'Huawei VRP router'
tp258
a(S'Huawei|VRP||switch'
S'Huawei VRP switch'
tp259
a(S'Hydra|embedded||load balancer'
S'Hydra embedded load balancer'
tp260
a(S'IBM|AIX|3.X|general purpose'
S'IBM AIX 3.X general purpose'
tp261
a(S'IBM|AIX|4.X|general purpose'
S'IBM AIX 4.X general purpose'
tp262
a(S'IBM|AIX|5.X|general purpose'
S'IBM AIX 5.X general purpose'
tp263
a(S'IBM|embedded||hub'
S'IBM embedded hub'
tp264
a(S'IBM|embedded||printer'
S'IBM embedded printer'
tp265
a(S'IBM|embedded||remote management'
S'IBM embedded remote management'
tp266
a(S'IBM|embedded||router'
S'IBM embedded router'
tp267
a(S'IBM|embedded||storage-misc'
S'IBM embedded storage-misc'
tp268
a(S'IBM|embedded||switch'
S'IBM embedded switch'
tp269
a(S'IBM|embedded||X terminal'
S'IBM embedded X terminal'
tp270
a(S'IBM|MVS||general purpose'
S'IBM MVS general purpose'
tp271
a(S'IBM|OS/2||general purpose'
S'IBM OS/2 general purpose'
tp272
a(S'IBM|OS/390|V2|general purpose'
S'IBM OS/390 V2 general purpose'
tp273
a(S'IBM|OS/390|V5|general purpose'
S'IBM OS/390 V5 general purpose'
tp274
a(S'IBM|OS/400|V3|general purpose'
S'IBM OS/400 V3 general purpose'
tp275
a(S'IBM|OS/400|V4|general purpose'
S'IBM OS/400 V4 general purpose'
tp276
a(S'IBM|OS/400|V5|general purpose'
S'IBM OS/400 V5 general purpose'
tp277
a(S'IBM|VM/CMS||general purpose'
S'IBM VM/CMS general purpose'
tp278
a(S'Infortrend|embedded||storage-misc'
S'Infortrend embedded storage-misc'
tp279
a(S'innovaphone|embedded||telecom-misc'
S'innovaphone embedded telecom-misc'
tp280
a(S'Intel|embedded||broadband router'
S'Intel embedded broadband router'
tp281
a(S'Intel|embedded||firewall'
S'Intel embedded firewall'
tp282
a(S'Intel|embedded||print server'
S'Intel embedded print server'
tp283
a(S'Intel|embedded||router'
S'Intel embedded router'
tp284
a(S'Intel|embedded||switch'
S'Intel embedded switch'
tp285
a(S'Intergraph|CLiX||general purpose'
S'Intergraph CLiX general purpose'
tp286
a(S'Intracom|embedded||broadband router'
S'Intracom embedded broadband router'
tp287
a(S'IPCop|Linux|2.2.X|firewall'
S'IPCop Linux 2.2.X firewall'
tp288
a(S'IPCop|Linux|2.4.X|firewall'
S'IPCop Linux 2.4.X firewall'
tp289
a(S'IPRoute|DOS||software router'
S'IPRoute DOS software router'
tp290
a(S'IQinVision|embedded||webcam'
S'IQinVision embedded webcam'
tp291
a(S'IronPort|AsyncOS||specialized'
S'IronPort AsyncOS specialized'
tp292
a(S'Isolation|embedded||encryption accelerator'
S'Isolation embedded encryption accelerator'
tp293
a(S'Ixia|embedded||specialized'
S'Ixia embedded specialized'
tp294
a(S'Juniper|JUNOS||router'
S'Juniper JUNOS router'
tp295
a(S'KA9Q|KA9Q||specialized'
S'KA9Q specialized'
tp296
a(S'Kentrox|embedded||CSUDSU'
S'Kentrox embedded CSUDSU'
tp297
a(S'KIRK|embedded||VoIP gateway'
S'KIRK embedded VoIP gateway'
tp298
a(S'Konica|embedded||printer'
S'Konica embedded printer'
tp299
a(S'Kronos|embedded||specialized'
S'Kronos embedded specialized'
tp300
a(S'Kyocera|embedded||printer'
S'Kyocera embedded printer'
tp301
a(S'Labtam|embedded||X terminal'
S'Labtam embedded X terminal'
tp302
a(S'Lantronix|embedded||switch'
S'Lantronix embedded switch'
tp303
a(S'Lantronix|embedded||terminal server'
S'Lantronix embedded terminal server'
tp304
a(S'Lantronix|Punix||print server'
S'Lantronix Punix print server'
tp305
a(S'Lantronix|Punix||terminal server'
S'Lantronix Punix terminal server'
tp306
a(S'Leunig|embedded||power-device'
S'Leunig embedded power-device'
tp307
a(S'Level One|embedded||broadband router'
S'Level One embedded broadband router'
tp308
a(S'Lexmark|embedded||printer'
S'Lexmark embedded printer'
tp309
a(S'LG GoldStream|embedded||router'
S'LG GoldStream embedded router'
tp310
a(S'Liebert|embedded||specialized'
S'Liebert embedded specialized'
tp311
a(S'Liebert-Hiross|embedded||specialized'
S'Liebert-Hiross embedded specialized'
tp312
a(S'Linksys|embedded||bridge'
S'Linksys embedded bridge'
tp313
a(S'Linksys|embedded||broadband router'
S'Linksys embedded broadband router'
tp314
a(S'Linksys|embedded||print server'
S'Linksys embedded print server'
tp315
a(S'Linksys|embedded||WAP'
S'Linksys embedded WAP'
tp316
a(S'Linux|Linux|1.X|general purpose'
S'Linux 1.X general purpose'
tp317
a(S'Linux|Linux|2.0.X|general purpose'
S'Linux 2.0.X general purpose'
tp318
a(S'Linux|Linux|2.1.X|general purpose'
S'Linux 2.1.X general purpose'
tp319
a(S'Linux|Linux|2.2.X|general purpose'
S'Linux 2.2.X general purpose'
tp320
a(S'Linux|Linux|2.3.X|general purpose'
S'Linux 2.3.X general purpose'
tp321
a(S'Linux|Linux|2.4.X|general purpose'
S'Linux 2.4.X general purpose'
tp322
a(S'Linux|Linux|2.5.X|general purpose'
S'Linux 2.5.X general purpose'
tp323
a(S'Linux|Linux|2.6.X|general purpose'
S'Linux 2.6.X general purpose'
tp324
a(S'Livingston|ComOS||terminal server'
S'Livingston ComOS terminal server'
tp325
a(S'Lucent|BSD-misc||general purpose'
S'Lucent BSD-misc general purpose'
tp326
a(S'Lucent|ComOS||terminal server'
S'Lucent ComOS terminal server'
tp327
a(S'lwIP|lwIP||general purpose'
S'lwIP general purpose'
tp328
a(S'm0n0wall|FreeBSD|4.X|firewall'
S'm0n0wall FreeBSD 4.X firewall'
tp329
a(S'm0n0wall|FreeBSD|5.X|firewall'
S'm0n0wall FreeBSD 5.X firewall'
tp330
a(S'Madge|embedded||switch'
S'Madge embedded switch'
tp331
a(S'Magna|embedded||router'
S'Magna embedded router'
tp332
a(S'Maxim-IC|TiniOS||general purpose'
S'Maxim-IC TiniOS general purpose'
tp333
a(S'Megabit|embedded||terminal server'
S'Megabit embedded terminal server'
tp334
a(S'Meridian|embedded||storage-misc'
S'Meridian embedded storage-misc'
tp335
a(S'Microbase|VirtuOS||general purpose'
S'Microbase VirtuOS general purpose'
tp336
a(S'Microplex|embedded||print server'
S'Microplex embedded print server'
tp337
a(S'Microsoft|DOS||general purpose'
S'Microsoft DOS general purpose'
tp338
a(S'Microsoft|embedded||game console'
S'Microsoft embedded game console'
tp339
a(S'Microsoft|Windows|2003/.NET|general purpose'
S'Microsoft Windows 2003/.NET general purpose'
tp340
a(S'Microsoft|Windows|3.X|general purpose'
S'Microsoft Windows 3.X general purpose'
tp341
a(S'Microsoft|Windows|95/98/ME|general purpose'
S'Microsoft Windows 95/98/ME general purpose'
tp342
a(S'Microsoft|Windows||general purpose'
S'Microsoft Windows general purpose'
tp343
a(S'Microsoft|Windows Longhorn||general purpose'
S'Microsoft Windows Longhorn general purpose'
tp344
a(S'Microsoft|Windows|NT/2K/XP|general purpose'
S'Microsoft Windows NT/2K/XP general purpose'
tp345
a(S'Microsoft|Windows|PocketPC/CE|PDA'
S'Microsoft Windows PocketPC/CE PDA'
tp346
a(S'Microsoft|Windows|PocketPC/CE|specialized'
S'Microsoft Windows PocketPC/CE specialized'
tp347
a(S'MikroTik|RouterOS||software router'
S'MikroTik RouterOS software router'
tp348
a(S'Minix|Minix||general purpose'
S'Minix general purpose'
tp349
a(S'Minolta|embedded||printer'
S'Minolta embedded printer'
tp350
a(S'Minolta|VxWorks||printer'
S'Minolta VxWorks printer'
tp351
a(S'MiraPoint|embedded||general purpose'
S'MiraPoint embedded general purpose'
tp352
a(S'Motorola|BSD-misc||general purpose'
S'Motorola BSD-misc general purpose'
tp353
a(S'Motorola|VxWorks||broadband router'
S'Motorola VxWorks broadband router'
tp354
a(S'MultiTech|embedded||firewall'
S'MultiTech embedded firewall'
tp355
a(S'MultiTech|embedded||telecom-misc'
S'MultiTech embedded telecom-misc'
tp356
a(S'MultiTech|embedded||terminal server'
S'MultiTech embedded terminal server'
tp357
a(S'MultiTech|embedded||VoIP gateway'
S'MultiTech embedded VoIP gateway'
tp358
a(S'NAT|embedded||router'
S'NAT embedded router'
tp359
a(S'NCD|embedded||X terminal'
S'NCD embedded X terminal'
tp360
a(S'NCR|BSD-misc||general purpose'
S'NCR BSD-misc general purpose'
tp361
a(S'NEC|UX/4800||general purpose'
S'NEC UX/4800 general purpose'
tp362
a(S'Necomm|embedded||broadband router'
S'Necomm embedded broadband router'
tp363
a(S'Neoware|NetOS||X terminal'
S'Neoware NetOS X terminal'
tp364
a(S'NetApp|Data ONTAP||fileserver'
S'NetApp Data ONTAP fileserver'
tp365
a(S'NetApp|embedded||web proxy'
S'NetApp embedded web proxy'
tp366
a(S'NetBSD|NetBSD||general purpose'
S'NetBSD general purpose'
tp367
a(S'Netburner|embedded||specialized'
S'Netburner embedded specialized'
tp368
a(S'Netgear|embedded||broadband router'
S'Netgear embedded broadband router'
tp369
a(S'Netgear|embedded||print server'
S'Netgear embedded print server'
tp370
a(S'Netgear|embedded||switch'
S'Netgear embedded switch'
tp371
a(S'Netgear|embedded||WAP'
S'Netgear embedded WAP'
tp372
a(S'NetJet|embedded||printer'
S'NetJet embedded printer'
tp373
a(S'NetMatrix|embedded||general purpose'
S'NetMatrix embedded general purpose'
tp374
a(S'Netopia|embedded||broadband router'
S'Netopia embedded broadband router'
tp375
a(S'Netopia|embedded||WAP'
S'Netopia embedded WAP'
tp376
a(S'NetScreen|ScreenOS||firewall'
S'NetScreen ScreenOS firewall'
tp377
a(S'Netscreen|ScreenOS||firewall'
S'Netscreen ScreenOS firewall'
tp378
a(S'NetSilicon|ThreadX||specialized'
S'NetSilicon ThreadX specialized'
tp379
a(S'Network Systems|embedded||router'
S'Network Systems embedded router'
tp380
a(S'Nexland|embedded||broadband router'
S'Nexland embedded broadband router'
tp381
a(S'NeXT|Mach||general purpose'
S'NeXT Mach general purpose'
tp382
a(S'NeXT|NeXTStep||general purpose'
S'NeXT NeXTStep general purpose'
tp383
a(S'NIB|embedded||printer'
S'NIB embedded printer'
tp384
a(S'Nokia|embedded||broadband router'
S'Nokia embedded broadband router'
tp385
a(S'Nokia|embedded||router'
S'Nokia embedded router'
tp386
a(S'Nokia|IPSO||firewall'
S'Nokia IPSO firewall'
tp387
a(S'Nokia|Symbian||phone'
S'Nokia Symbian phone'
tp388
a(S'Nortel|embedded||switch'
S'Nortel embedded switch'
tp389
a(S'Nortel|embedded||telecom-misc'
S'Nortel embedded telecom-misc'
tp390
a(S'Nortel|embedded||terminal server'
S'Nortel embedded terminal server'
tp391
a(S'Novell|NetWare|3.X|general purpose'
S'Novell NetWare 3.X general purpose'
tp392
a(S'Novell|NetWare|4.X|general purpose'
S'Novell NetWare 4.X general purpose'
tp393
a(S'Novell|NetWare|5.X|general purpose'
S'Novell NetWare 5.X general purpose'
tp394
a(S'Novell|NetWare|6.X|general purpose'
S'Novell NetWare 6.X general purpose'
tp395
a(S'NSG|embedded||router'
S'NSG embedded router'
tp396
a(S'NTT|embedded||telecom-misc'
S'NTT embedded telecom-misc'
tp397
a(S'Okidata|embedded||printer'
S'Okidata embedded printer'
tp398
a(S'Open Networks|embedded||broadband router'
S'Open Networks embedded broadband router'
tp399
a(S'OpenBSD|OpenBSD|2.7|general purpose'
S'OpenBSD 2.7 general purpose'
tp400
a(S'OpenBSD|OpenBSD|2.X|general purpose'
S'OpenBSD 2.X general purpose'
tp401
a(S'OpenBSD|OpenBSD|3.X|general purpose'
S'OpenBSD 3.X general purpose'
tp402
a(S'Pace|embedded||media device'
S'Pace embedded media device'
tp403
a(S'Packet Engines|embedded||router'
S'Packet Engines embedded router'
tp404
a(S'Packet8|embedded||VoIP adapter'
S'Packet8 embedded VoIP adapter'
tp405
a(S'Packeteer|pSOS||load balancer'
S'Packeteer pSOS load balancer'
tp406
a(S'Palm|PalmOS|3.X|PDA'
S'Palm PalmOS 3.X PDA'
tp407
a(S'Panasonic|embedded||broadband router'
S'Panasonic embedded broadband router'
tp408
a(S'Panasonic|embedded||printer'
S'Panasonic embedded printer'
tp409
a(S'Panasonic|embedded||webcam'
S'Panasonic embedded webcam'
tp410
a(S'Parks|embedded||broadband router'
S'Parks embedded broadband router'
tp411
a(S'PCS|embedded||specialized'
S'PCS embedded specialized'
tp412
a(S'Pelco|embedded||webcam'
S'Pelco embedded webcam'
tp413
a(S'Perle|embedded||remote management'
S'Perle embedded remote management'
tp414
a(S'Perle|embedded||terminal server'
S'Perle embedded terminal server'
tp415
a(S'Phillips|embedded||media device'
S'Phillips embedded media device'
tp416
a(S'Pigtail|VxWorks||VoIP phone'
S'Pigtail VxWorks VoIP phone'
tp417
a(S'Pirelli|embedded||broadband router'
S'Pirelli embedded broadband router'
tp418
a(S'Pitney Bowes|embedded||printer'
S'Pitney Bowes embedded printer'
tp419
a(S'Planet|embedded||switch'
S'Planet embedded switch'
tp420
a(S'Planet|embedded||WAP'
S'Planet embedded WAP'
tp421
a(S'Polycom|embedded||webcam'
S'Polycom embedded webcam'
tp422
a(S'PolyCom|embedded||webcam'
S'PolyCom embedded webcam'
tp423
a(S'PowerShow|embedded||webcam'
S'PowerShow embedded webcam'
tp424
a(S'Proteon|OpenRoute||router'
S'Proteon OpenRoute router'
tp425
a(S'Proxim|embedded||bridge'
S'Proxim embedded bridge'
tp426
a(S'Proxim|embedded||WAP'
S'Proxim embedded WAP'
tp427
a(S'QMS|embedded||printer'
S'QMS embedded printer'
tp428
a(S'QNX|QNX||general purpose'
S'QNX general purpose'
tp429
a(S'Quanterra|OS/9||specialized'
S'Quanterra OS/9 specialized'
tp430
a(S'Quantum|embedded||storage-misc'
S'Quantum embedded storage-misc'
tp431
a(S'Racal|embedded||encryption accelerator'
S'Racal embedded encryption accelerator'
tp432
a(S'Radionics|embedded||specialized'
S'Radionics embedded specialized'
tp433
a(S'Radware|embedded||load balancer'
S'Radware embedded load balancer'
tp434
a(S'Radware|embedded||security-misc'
S'Radware embedded security-misc'
tp435
a(S'Raptor|embedded||firewall'
S'Raptor embedded firewall'
tp436
a(S'Raptor|Solaris|2.X|firewall'
S'Raptor Solaris 2.X firewall'
tp437
a(S'RCA|embedded||broadband router'
S'RCA embedded broadband router'
tp438
a(S'Redback|AOS||router'
S'Redback AOS router'
tp439
a(S'Redback|embedded||broadband router'
S'Redback embedded broadband router'
tp440
a(S'Ricoh|embedded||printer'
S'Ricoh embedded printer'
tp441
a(S'Ringdale|embedded||print server'
S'Ringdale embedded print server'
tp442
a(S'Rio|embedded||media device'
S'Rio embedded media device'
tp443
a(S'RiverStone|embedded||router'
S'RiverStone embedded router'
tp444
a(S'RoadLanner|embedded||broadband router'
S'RoadLanner embedded broadband router'
tp445
a(S'Rockwell|embedded||telecom-misc'
S'Rockwell embedded telecom-misc'
tp446
a(S'SAR|embedded||broadband router'
S'SAR embedded broadband router'
tp447
a(S'Savin|embedded||printer'
S'Savin embedded printer'
tp448
a(S'Scientific-Atlanta|embedded||media device'
S'Scientific-Atlanta embedded media device'
tp449
a(S'SCO|OpenServer||general purpose'
S'SCO OpenServer general purpose'
tp450
a(S'SCO|SCO UNIX||general purpose'
S'SCO SCO UNIX general purpose'
tp451
a(S'SCO|UnixWare||general purpose'
S'SCO UnixWare general purpose'
tp452
a(S'Secure Computing|embedded||firewall'
S'Secure Computing embedded firewall'
tp453
a(S'Sega|embedded||game console'
S'Sega embedded game console'
tp454
a(S'Sequent|DYNIX||general purpose'
S'Sequent DYNIX general purpose'
tp455
a(S'Sequent|embedded||general purpose'
S'Sequent embedded general purpose'
tp456
a(S'SGI|IRIX|4.X|general purpose'
S'SGI IRIX 4.X general purpose'
tp457
a(S'SGI|IRIX|5.X|general purpose'
S'SGI IRIX 5.X general purpose'
tp458
a(S'SGI|IRIX|6.X|general purpose'
S'SGI IRIX 6.X general purpose'
tp459
a(S'Sharp|embedded||printer'
S'Sharp embedded printer'
tp460
a(S'Shiva|embedded||router'
S'Shiva embedded router'
tp461
a(S'Shiva|embedded||terminal server'
S'Shiva embedded terminal server'
tp462
a(S'Siemens|embedded||broadband router'
S'Siemens embedded broadband router'
tp463
a(S'Siemens|embedded||PBX'
S'Siemens embedded PBX'
tp464
a(S'Siemens|embedded||specialized'
S'Siemens embedded specialized'
tp465
a(S'Siemens|embedded||VoIP phone'
S'Siemens embedded VoIP phone'
tp466
a(S'Siemens|ReliantUNIX||general purpose'
S'Siemens ReliantUNIX general purpose'
tp467
a(S'Siemens|SINIX||general purpose'
S'Siemens SINIX general purpose'
tp468
a(S'Signal|embedded||VoIP gateway'
S'Signal embedded VoIP gateway'
tp469
a(S'Sipura|embedded||VoIP adapter'
S'Sipura embedded VoIP adapter'
tp470
a(S'SMC|embedded||broadband router'
S'SMC embedded broadband router'
tp471
a(S'SMC|embedded||WAP'
S'SMC embedded WAP'
tp472
a(S'Smoothwall|Linux|2.2.X|firewall'
S'Smoothwall Linux 2.2.X firewall'
tp473
a(S'Softek|embedded||specialized'
S'Softek embedded specialized'
tp474
a(S'SonicWall|embedded||firewall'
S'SonicWall embedded firewall'
tp475
a(S'SonicWall|SonicOS||firewall'
S'SonicWall SonicOS firewall'
tp476
a(S'Sony|embedded||robotic pet'
S'Sony embedded robotic pet'
tp477
a(S'Sony|Linux||game console'
S'Sony Linux game console'
tp478
a(S'Sony|Linux||specialized'
S'Sony Linux specialized'
tp479
a(S'Sony|NewsOS||general purpose'
S'Sony NewsOS general purpose'
tp480
a(S'Sony|Symbian||phone'
S'Sony Symbian phone'
tp481
a(S'Soyo|embedded||VoIP phone'
S'Soyo embedded VoIP phone'
tp482
a(S'SpeedStream|embedded||broadband router'
S'SpeedStream embedded broadband router'
tp483
a(S'Spirent|embedded||specialized'
S'Spirent embedded specialized'
tp484
a(S'StackTools|StackTos||general purpose'
S'StackTools StackTos general purpose'
tp485
a(S'Stratus|VOS||general purpose'
S'Stratus VOS general purpose'
tp486
a(S'Sun|embedded||remote management'
S'Sun embedded remote management'
tp487
a(S'Sun|embedded||storage-misc'
S'Sun embedded storage-misc'
tp488
a(S'Sun|Solaris|10|general purpose'
S'Sun Solaris 10 general purpose'
tp489
a(S'Sun|Solaris|2.X|general purpose'
S'Sun Solaris 2.X general purpose'
tp490
a(S'Sun|Solaris|7|general purpose'
S'Sun Solaris 7 general purpose'
tp491
a(S'Sun|Solaris|8|general purpose'
S'Sun Solaris 8 general purpose'
tp492
a(S'Sun|Solaris|9|general purpose'
S'Sun Solaris 9 general purpose'
tp493
a(S'Sun|SunOS||general purpose'
S'Sun SunOS general purpose'
tp494
a(S'Swissvoice|embedded||VoIP phone'
S'Swissvoice embedded VoIP phone'
tp495
a(S'Symantec|embedded||firewall'
S'Symantec embedded firewall'
tp496
a(S'Symantec|Solaris|8|firewall'
S'Symantec Solaris 8 firewall'
tp497
a(S'Symantec|Windows|NT/2K/XP|firewall'
S'Symantec Windows NT/2K/XP firewall'
tp498
a(S'Symbol|embedded||WAP'
S'Symbol embedded WAP'
tp499
a(S'Systech|embedded||specialized'
S'Systech embedded specialized'
tp500
a(S'Tahoe|Tahoe OS||router'
S'Tahoe Tahoe OS router'
tp501
a(S'Tainet|embedded||broadband router'
S'Tainet embedded broadband router'
tp502
a(S'Talaris|embedded||printer'
S'Talaris embedded printer'
tp503
a(S'Tally|embedded||printer'
S'Tally embedded printer'
tp504
a(S'Tandberg|embedded||X terminal'
S'Tandberg embedded X terminal'
tp505
a(S'Tandem|Tandem NSK||general purpose'
S'Tandem Tandem NSK general purpose'
tp506
a(S'Tektronix|embedded||printer'
S'Tektronix embedded printer'
tp507
a(S'Telebit|embedded||router'
S'Telebit embedded router'
tp508
a(S'Telindus|embedded||broadband router'
S'Telindus embedded broadband router'
tp509
a(S'Telocity|embedded||broadband router'
S'Telocity embedded broadband router'
tp510
a(S'Telos|embedded||media device'
S'Telos embedded media device'
tp511
a(S'Telsey|embedded||broadband router'
S'Telsey embedded broadband router'
tp512
a(S'Teltrend|embedded||router'
S'Teltrend embedded router'
tp513
a(S'Terayon|embedded||broadband router'
S'Terayon embedded broadband router'
tp514
a(S'Thales|embedded||encryption accelerator'
S'Thales embedded encryption accelerator'
tp515
a(S'Thomson|embedded||broadband router'
S'Thomson embedded broadband router'
tp516
a(S'Toshiba|embedded||broadband router'
S'Toshiba embedded broadband router'
tp517
a(S'Toshiba|embedded||printer'
S'Toshiba embedded printer'
tp518
a(S'Trancell|embedded||router'
S'Trancell embedded router'
tp519
a(S'Treck|Treck||general purpose'
S'Treck general purpose'
tp520
a(S'TrueTime|embedded||specialized'
S'TrueTime embedded specialized'
tp521
a(S'Turtle Beach|embedded||media device'
S'Turtle Beach embedded media device'
tp522
a(S'uIP|uIP||specialized'
S'uIP specialized'
tp523
a(S'US Robotics|embedded||switch'
S'US Robotics embedded switch'
tp524
a(S'US Robotics|embedded||terminal server'
S'US Robotics embedded terminal server'
tp525
a(S'US Robotics|embedded||WAP'
S'US Robotics embedded WAP'
tp526
a(S'UTStarcom|embedded||VoIP phone'
S'UTStarcom embedded VoIP phone'
tp527
a(S'Vanguard|embedded||router'
S'Vanguard embedded router'
tp528
a(S'VegaStream|embedded||VoIP gateway'
S'VegaStream embedded VoIP gateway'
tp529
a(S'VersaNet|embedded||terminal server'
S'VersaNet embedded terminal server'
tp530
a(S'Virtual Access|embedded||router'
S'Virtual Access embedded router'
tp531
a(S'WatchGuard|embedded||firewall'
S'WatchGuard embedded firewall'
tp532
a(S'Westel|embedded||broadband router'
S'Westel embedded broadband router'
tp533
a(S'Wiesemann &amp; Theis|embedded||specialized'
S'Wiesemann &amp; Theis embedded specialized'
tp534
a(S'Wooksung|embedded||telecom-misc'
S'Wooksung embedded telecom-misc'
tp535
a(S'WTI|embedded||power-device'
S'WTI embedded power-device'
tp536
a(S'WYSE|WYSE OS||terminal server'
S'WYSE WYSE OS terminal server'
tp537
a(S'XCD|embedded||print server'
S'XCD embedded print server'
tp538
a(S'Xerox|embedded||printer'
S'Xerox embedded printer'
tp539
a(S'xMach|xMach||general purpose'
S'xMach general purpose'
tp540
a(S'Xylan|embedded||switch'
S'Xylan embedded switch'
tp541
a(S'Xylogics|embedded||terminal server'
S'Xylogics embedded terminal server'
tp542
a(S'Xylogics|LynxOS||terminal server'
S'Xylogics LynxOS terminal server'
tp543
a(S'Xyplex|embedded||terminal server'
S'Xyplex embedded terminal server'
tp544
a(S'Xyplex|MAXserver||terminal server'
S'Xyplex MAXserver terminal server'
tp545
a(S'Zcomax|embedded||WAP'
S'Zcomax embedded WAP'
tp546
a(S'Zebra|embedded||printer'
S'Zebra embedded printer'
tp547
a(S'Zero One|embedded||print server'
S'Zero One embedded print server'
tp548
a(S'ZoomAir|embedded||WAP'
S'ZoomAir embedded WAP'
tp549
a(S'ZyXel|ZyNOS||broadband router'
S'ZyXel ZyNOS broadband router'
tp550
a(S'ZyXel|ZyNOS||firewall'
S'ZyXel ZyNOS firewall'
tp551
a(S'ZyXel|ZyNOS||switch'
S'ZyXel ZyNOS switch'
tp552
a(S'ZyXel|ZyNOS||WAP'
S'ZyXel ZyNOS WAP'
tp553
a."""

os_dump_content = """(dp1
S'Microsoft | Windows | 3.X | general purpose'
p2
(lp3
S'Microsoft Windows 3.1 with Trumpet Winsock 2.0 revision B'
p4
asS'Intel | embedded || switch'
p5
(lp6
S'Intel Express 510T switch'
p7
aS'Intel Express 510T switch'
p8
aS'Intel NetStructure 470T Switch'
p9
asS'Ringdale | embedded || print server'
p10
(lp11
S'Ringdale RP21 Print Server'
p12
asS'Cabletron | embedded || switch'
p13
(lp14
S'Cabletron SmartSwitch'
p15
aS'Cabletron switch'
p16
asS'NCR | BSD-misc || general purpose'
p17
(lp18
S'NCR MP-RAS 3.0.x'
p19
aS'NCR MP-RAS 3.01'
p20
aS'NCR S26 server (i386) running NCR MP-RAS SVR4 UNIX System'
p21
aS'NCR server running MP-RAS SVR4 UNIX System Version 3'
p22
asS'Microsoft | embedded || game console'
p23
(lp24
S'Microsoft Xbox (modified)'
p25
aS'Microsoft Xbox (modified) running evolutionX'
p26
aS'Microsoft Xbox (modified) running UnleashX 0.26'
p27
asS'Foundry | IronWare || load balancer'
p28
(lp29
S'Foundry FastIronII 4000 load balancer running 06.6.34T43'
p30
aS'Foundry NetIron load balancer OS Ver. 7.1.23T13'
p31
aS'Foundry Networks, Inc. Router/Load balancer, IronWare Version 06.5.12T43'
p32
aS'Foundry ServerIron XL load balancing IP Switch Version 06.0.00T12'
p33
asS'Linux | Linux | 1.X | general purpose'
p34
(lp35
S'Linux 1.0.9'
p36
aS'Linux 1.2.13'
p37
aS'Linux 1.2.8 - 1.2.13'
p38
aS'Linux 1.3.20 (x86)'
p39
asS'Ericsson | embedded || broadband router'
p40
(lp41
S'Ericsson Congo router'
p42
aS'Ericsson HM220dp ADSL modem/router'
p43
asS'Allied Telesyn | embedded || switch'
p44
(lp45
S'Allied Telesyn AT-3726 Ethernet Switch: 2.1cycleA'
p46
aS'Allied Telesyn AT-8748XL or Rapier 24i Switch'
p47
aS'Allied Telesyn AT-RP24i switch or Ericcson HiS V2.0'
p48
asS'Arescom | embedded || broadband router'
p49
(lp50
S'Arescom 800 series dsl router'
p51
aS'Arescom NetDSL 1000NDS series ADSL router'
p52
asS'Cray | Unisys || general purpose'
p53
(lp54
S'Cray Unisys LX/NX MCP 46.1/HMP 5.0 on LX5120'
p55
asS'Symantec | Windows | NT/2K/XP | firewall'
p56
(lp57
S'Symantec Enterprise Firewall 7.0 running on Windows 2000 SP2'
p58
asS'HP | embedded || printer'
p59
(lp60
S'HP JetDirect Card in a LaserJet printer'
p61
aS'HP LaserJet 4000N Printer'
p62
aS'HP LaserJet 4100N printer'
p63
aS'HP LaserJet 5'
p64
aS'HP printer w/Jet Direct'
p65
aS'HP printer w/JetDirect card'
p66
aS'HP printer w/JetDirect card'
p67
aS'HP printer w/JetDirect card'
p68
aS'HP printer w/JetDirect card'
p69
aS'HP printer w/JetDirect card'
p70
aS'HP printer w/JetDirect J2556b card (firmware A.05.32)'
p71
aS'HP printer w/JetDirect J2556b card firmware A.05.32'
p72
asS'Planet | embedded || WAP'
p73
(lp74
S'Planet WAP 1950 Wireless Access Point'
p75
asS'Linux | Linux | 2.5.X | general purpose'
p76
(lp77
S'Linux 2.4.0 - 2.5.20'
p78
aS'Linux 2.4.0 - 2.5.20 w/o tcp_timestamps'
p79
aS'Linux 2.5.25 - 2.6.8 or Gentoo 1.2 Linux 2.4.19 rc1-rc7'
p80
asS'Microsoft | Windows || general purpose'
p81
(lp82
S'Microsoft Windows 2000 Professional SP4'
p83
aS'Microsoft Windows 2000 Professional with SP4 and latest Windows Update patches as of August 11, 2004'
p84
aS'Microsoft Windows 2000 Server SP3'
p85
aS'Microsoft Windows Longhorn eval build 4051'
p86
asS'Cisco | embedded || VoIP adapter'
p87
(lp88
S'Cisco ATA 186 POTS<->VoIP phone gateway device'
p89
asS'Netgear | embedded || print server'
p90
(lp91
S'Netgear PS101 Print Server'
p92
aS'Netgear PS110 Print Server'
p93
asS'Cyberguard | embedded || firewall'
p94
(lp95
S'Cyberguard 4.0 firewall'
p96
aS'Cyberguard Firewall 5.2'
p97
asS'Netopia | embedded || broadband router'
p98
(lp99
S'Cisco Catalyst 1900 switch, Bay networks 350-450 switch,  or Netopia DSL/ISDN router'
p100
aS'Netopia 4541/R7100 DSL router'
p101
aS'Netopia Cayman 3341-ENT ADSL Router'
p102
aS'Netopia DSL router'
p103
aS'Netopia DSL Router'
p104
aS'Netopia R5300 Router'
p105
aS'Netopia R9100 DSL Router'
p106
asS'Talaris | embedded || printer'
p107
(lp108
S'Talaris 1794 Printstation'
p109
asS'Ricoh | embedded || printer'
p110
(lp111
S'Ricoh Aficio AP4500 Network Laser Printer'
p112
aS'Savin 9927 Copier or Ricoh Aficio 270 copier'
p113
asS'Raptor | Solaris | 2.X | firewall'
p114
(lp115
S'Raptor Firewall 6 on Solaris 2.6'
p116
asS'HP | HP-UX | 9.X | general purpose'
p117
(lp118
S'HP-UX 9.01 - 9.07'
p119
aS'HP-UX A.09.00 E 9000/817 - A.09.07 A 9000/777'
p120
asS'Sony | Linux || specialized'
p121
(lp122
S'Sony PlayStation 2 Performance Analyser'
p123
asS'Ascend | Embedded/OS || router'
p124
(lp125
S'Ascend GRF Router running Ascend Embedded/OS 2.1'
p126
asS'Avocent | embedded || specialized'
p127
(lp128
S'Avocent net KVM switch'
p129
asS'MultiTech | embedded || firewall'
p130
(lp131
S'MultiTech standalone firewall box, version 3'
p132
asS'FreeSCO | Linux | 2.0.X | router'
p133
(lp134
S'FreeSCO 0.27 (Linux 2.0.38)'
p135
aS'FreeSCO 0.27 (Linux 2.0.38)'
p136
asS'Commodore | embedded || game console'
p137
(lp138
S'Commodore 64 with TFE Ethernet Card (Contiki)'
p139
aS'Commodore 64 with TFE Ethernet Card (uIP TCP/IP stack)'
p140
asS'ZoomAir | embedded || WAP'
p141
(lp142
S'ZoomAir IG-4165 Wireless gateway (WAP)'
p143
asS'Checkpoint | Solaris | 8 | firewall'
p144
(lp145
S'Checkpoint Firewall-1 NG on Sun Solaris 8'
p146
asS'Spirent | embedded || specialized'
p147
(lp148
S'Spirent AX4000 Network Testing Tool'
p149
asS'Treck | Treck || general purpose'
p150
(lp151
S'Treck TCP/IP stack v2.1'
p152
asS'Adtran | embedded || telecom-misc'
p153
(lp154
S'Adtran Atlas 890 digital cross-connect device'
p155
asS'FreeBSD | FreeBSD | 4.x | general purpose'
p156
(lp157
S'DragonFly 1.1-Stable (FreeBSD-4 fork)'
p158
asS'Lucent | BSD-misc || general purpose'
p159
(lp160
S'ATT UNIX SVR4.2 on a Lucent Definity voicemail system'
p161
asS'Avaya | embedded || PBX'
p162
(lp163
S'Avaya G3 PBX version 8.3'
p164
aS'Avaya IP Office 403 PBX'
p165
asS'Netgear | embedded || WAP'
p166
(lp167
S'WAP: Compaq iPAQ Connection Point or Netgear MR814'
p168
asS'IBM | VM/CMS || general purpose'
p169
(lp170
S'IBM VM/CMS (mainframe)'
p171
aS'IBM VM/ESA 2.2.0 CMS Mainframe System'
p172
asS'3Com | embedded || PBX'
p173
(lp174
S'3Com NBX PBX'
p175
asS'Blue Coat | embedded || web proxy'
p176
(lp177
S'Blue Coat Security Proxy Appliance'
p178
asS'Motorola | BSD-misc || general purpose'
p179
(lp180
S'Motorola BSR 1000R'
p181
aS'Motorola System V/68 version R3V7 on a 68030'
p182
asS'AXIS | embedded || webcam'
p183
(lp184
S'AXIS 200+ Web Camera running OS v1.42'
p185
aS'AXIS 2120 network camera'
p186
aS'AXIS Neteye 200+ Webcam running software version 1.42'
p187
aS'AXIS NetEye Camera Server V1.20'
p188
asS'Linux | Linux | 2.3.X | general purpose'
p189
(lp190
S'Linux 2.3.12'
p191
aS'Linux 2.3.28-33'
p192
aS'Linux 2.3.47 - 2.3.99-pre2 x86'
p193
aS'Linux 2.3.49 x86'
p194
asS'LG GoldStream | embedded || router'
p195
(lp196
S'LG Goldstream LR3001f router, software version 4.0'
p197
aS'LG Goldstream LR3100p router, software version 1.0-1.5'
p198
asS'Cisco | PIX | 4.X | firewall'
p199
(lp200
S'Cisco PIX 4.2(2) Internal Interface'
p201
aS'Cisco PIX 515 firewall running software 4.4(5)'
p202
aS'Cisco PIX Firewall running PIX 4.1(5)'
p203
aS'Cisco Pix Firewall running PIX 4.1.6'
p204
aS'Cisco PIX v4.2 Firewall'
p205
asS'Cisco | embedded || terminal server'
p206
(lp207
S'Cisco AS5200 terminal server'
p208
asS'Siemens | embedded || PBX'
p209
(lp210
S'Siemens HICOM 300 Phone switch (PBX)'
p211
aS'Siemens HICOM Phone switch (PBX)'
p212
aS'Siemens HiPATH3500 VoIP PBX'
p213
asS'FiberLine | embedded || WAP'
p214
(lp215
S'FiberLine WL-1200R1 (also known as InterEpoch IWE-1200A-1) Wireless Broadband Router (WAP)'
p216
asS'F5 Labs | BSDI || load balancer'
p217
(lp218
S'F5 Labs Big/IP HA TCP/IP Load Balancer (BSDI kernel/x86)'
p219
asS'Minolta | embedded || printer'
p220
(lp221
S'Konica-Minolta Di3010 photocopier/printer/scanner'
p222
aS'Minolta Di183 printer/copier'
p223
asS'Sequent | embedded || general purpose'
p224
(lp225
S'Sequent DYNIX/ptx V4.2.1'
p226
aS'Sequent DYNIX/ptx V4.4.6'
p227
asS'Thales | embedded || encryption accelerator'
p228
(lp229
S'Thales WebSentry HSM Crypto Accelerator'
p230
asS'Atari | Atari || game console'
p231
(lp232
S'MiNT with MiNTnet 1.03 running on Atari TT'
p233
asS'Apple | Mac OS X | 10.4.X | general purpose'
p234
(lp235
S'Apple Mac OS X 10.3.8 or 10.4'
p236
asS'KA9Q | KA9Q || specialized'
p237
(lp238
S'KA9Q amateur radio OS'
p239
asS'Symbol | embedded || WAP'
p240
(lp241
S'Symbol/Spectrum24 Wireless AP'
p242
asS'Infortrend | embedded || storage-misc'
p243
(lp244
S'Infortrend EonStor A16U-G1410'
p245
asS'Cray | UNICOS | 8.X | general purpose'
p246
(lp247
S'Cray UNICOS/mk 8.6'
p248
asS'Tainet | embedded || broadband router'
p249
(lp250
S'Tainet WANpro 2000i Broadband router'
p251
asS'DEC | BSD-misc || general purpose'
p252
(lp253
S'4.3BSD-tahoe on a MicroVax III'
p254
asS'Linux | Linux | 2.6.X | general purpose'
p255
(lp256
S'Linux 2.4.20 or 2.6.0-test5-love3 (x86)'
p257
aS'Linux 2.4.21 - 2.4.23'
p258
aS'Linux 2.4.22 or 2.6.10'
p259
aS'Linux 2.4.7 - 2.6.11'
p260
aS'Linux 2.5.5 (Gentoo)'
p261
aS'Linux 2.6.0 (x86)'
p262
aS'Linux 2.6.0 - 2.6.11'
p263
aS'Linux 2.6.0 - 2.6.11'
p264
aS'Linux 2.6.0 - 2.6.11'
p265
aS'Linux 2.6.0 - 2.6.11'
p266
aS'Linux 2.6.0 - 2.6.11'
p267
aS'Linux 2.6.0-test10 (x86)'
p268
aS'Linux 2.6.0-test5 x86'
p269
aS'Linux 2.6.0-test7 (x86)'
p270
aS'Linux 2.6.0-test9 - 2.6.0 (x86)'
p271
aS'Linux 2.6.10'
p272
aS'Linux 2.6.10'
p273
aS'Linux 2.6.10'
p274
aS'Linux 2.6.10'
p275
aS'Linux 2.6.10 - 2.6.11'
p276
aS'Linux 2.6.11'
p277
aS'Linux 2.6.11 (gentoo)'
p278
aS'Linux 2.6.3 - 2.6.10'
p279
aS'Linux 2.6.3 - 2.6.7 (X86)'
p280
aS'Linux 2.6.3 or 2.6.8'
p281
aS'Linux 2.6.4 (Suse)'
p282
aS'Linux 2.6.5'
p283
aS'Linux 2.6.6'
p284
aS'Linux 2.6.6-1-k7 (X86)'
p285
aS'Linux 2.6.7'
p286
aS'Linux 2.6.7'
p287
aS'Linux 2.6.7'
p288
aS'Linux 2.6.7 (X86)'
p289
aS'Linux 2.6.7 w/grsecurity.org patch'
p290
aS'Linux 2.6.8'
p291
aS'Linux 2.6.8'
p292
aS'Linux 2.6.8'
p293
aS'Linux 2.6.8'
p294
aS'Linux 2.6.8 (Debian)'
p295
aS'Linux 2.6.8 (Ubuntu)'
p296
aS'Linux 2.6.8 - 2.6.11'
p297
aS'Linux 2.6.8 - 2.6.9'
p298
aS'Linux 2.6.9'
p299
aS'Linux 2.6.9'
p300
aS'Linux kernel 2.6.5 - 2.6.8'
p301
asS'2Wire | embedded || WAP'
p302
(lp303
S'2Wire Home Portal 100 residential gateway, v.3.1.0'
p304
asS'Radionics | embedded || specialized'
p305
(lp306
S'Lantronix CoBox serial device server or Radionics RAM IV Alarm'
p307
asS'Cisco | embedded || bridge'
p308
(lp309
S'Cisco Accesspoint 1200'
p310
aS'Cisco AIR-WGB340 V8.38 Wireless workgroup bridge 340'
p311
aS'Cisco WGB350 Wireless WorkGroup Bridge'
p312
asS'Cisco | IOS | 12.X | router'
p313
(lp314
S'Cisco IOS 11.3 - 12.0(11)'
p315
aS'Cisco 1601 router running IOS 12.0(8)'
p316
aS'Cisco 1601R router running IOS 12.1(5)'
p317
aS'Cisco 1721 router running IOS 12.3(10)'
p318
aS'Cisco 2514 router running IOS 12.0(21)'
p319
aS'Cisco 2600 router running IOS 12.2(3)'
p320
aS'Cisco 2610 router running IOS 12.2(21a)'
p321
aS'Cisco 2611 router running IOS 12.0(7)T'
p322
aS'Cisco 2611 router running IOS 12.2(7a)'
p323
aS'Cisco 2620 router running IOS 12.2(15)'
p324
aS'Cisco 2620 router running IOS 12.3(5)'
p325
aS'Cisco 2620 running IOS 12.2(19a)'
p326
aS'Cisco 3660 running IOS 12.0(6r)T'
p327
aS'Cisco 3725 router running IOS 12.3(6c)'
p328
aS'Cisco 3745 Router running IOS 12.2(15)T13'
p329
aS'Cisco 4000 Series running IOS 12.0(10.3)'
p330
aS'Cisco 7200 router running IOS 12.1(14)E6'
p331
aS'Cisco 7200 router running IOS 12.4(1a)'
p332
aS'Cisco 7204 router running IOS 12.1(19)'
p333
aS'Cisco 7206 router running IOS 12.2(13)T8'
p334
aS'Cisco 800 Series Broadband Routers running IOS 12.0(7)T'
p335
aS'Cisco 837 router running IOS 12.3(11)T or Cisco 2811 router running IOS 12.3(8r)T7'
p336
aS'Cisco 837 router running IOS 12.3(8)T'
p337
aS'Cisco AS5350 running IOS 12.2(2)XB6'
p338
aS'Cisco IOS 12.0(3.3)S (perhaps a 7200 router)'
p339
aS'Cisco IOS 12.0(5)WC3 - 12.0(16a)'
p340
aS'Cisco IOS 12.0(7)T (on a 1700 router)'
p341
aS'Cisco IOS 12.1(4) on a 2600 router'
p342
aS'Cisco IOS 12.2(8)T5 on a 7507 router'
p343
aS'Cisco router or WAP running IOS 12.2'
p344
aS'Cisco router running IOS 12.0(18)S or 12.0(18)S1'
p345
aS'Cisco router running IOS 12.1'
p346
aS'Cisco router running IOS 12.1(5)-12.2(7a)'
p347
aS'Cisco router running IOS 12.1.5-12.2.13a'
p348
aS'Cisco router running IOS 12.2(8)T'
p349
aS'Cisco router running IOS 12.3(11)'
p350
aS'Cisco router running IOS v12.0(15)'
p351
aS'Cisco SOHO 91 secure router running IOS 12.3'
p352
aS'Cisco switch running IOS 12.1(23)E'
p353
aS'router Cisco 3640 running IOS 12.2(23a)'
p354
asS'Bell Labs | Plan9 || general purpose'
p355
(lp356
S'Bell Labs Plan9 Fourth Edition'
p357
aS'Bell Labs Plan9 Fourth Edition (x86)'
p358
aS'Bell Labs Plan9 Second Edition'
p359
asS'FreeBSD | FreeBSD | 4.X | general purpose'
p360
(lp361
S'FreeBSD 2.2.1 - 4.1'
p362
aS'FreeBSD 3.2-4.0'
p363
aS'FreeBSD 4.0-20000208-CURRENT'
p364
aS'FreeBSD 4.1.1 - 4.3 (x86)'
p365
aS'FreeBSD 4.10-STABLE'
p366
aS'FreeBSD 4.2 - 4.3-RC (X86)'
p367
aS'FreeBSD 4.3 - 4.4-RELEASE'
p368
aS'FreeBSD 4.3 - 4.4PRERELEASE'
p369
aS'FreeBSD 4.4 for i386 (IA-32)'
p370
aS'FreeBSD 4.4-STABLE'
p371
aS'FreeBSD 4.5-RELEASE (or -STABLE) through 4.6-RC (x86)'
p372
aS'FreeBSD 4.6'
p373
aS'FreeBSD 4.6'
p374
aS'FreeBSD 4.6'
p375
aS'FreeBSD 4.6 through 4.6.2 (July 2002) (x86)'
p376
aS'FreeBSD 4.6-RC on Alpha'
p377
aS'FreeBSD 4.6.2-RELEASE'
p378
aS'FreeBSD 4.6.2-RELEASE - 4.8-RELEASE'
p379
aS'FreeBSD 4.7 - 4.8-RELEASE'
p380
aS'FreeBSD 4.7-RELEASE'
p381
aS'FreeBSD 4.7-RELEASE through 4.8-RELEASE (x86)'
p382
aS'FreeBSD 4.7-RELEASE-p3'
p383
aS'FreeBSD 4.7-STABLE'
p384
aS'FreeBSD 4.8-RELEASE through 4.9-STABLE'
p385
aS'FreeBSD 4.8-STABLE'
p386
aS'FreeBSD 4.8-STABLE'
p387
aS'FreeBSD 4.8-STABLE - 4.9-PRERELEASE'
p388
aS'FreeBSD 4.9 - 5.1'
p389
aS'FreeBSD 4.9-RELEASE'
p390
aS'FreeBSD 4.9-RELEASE'
p391
aS'FreeBSD 4.9-STABLE'
p392
asS'Microbase | VirtuOS || general purpose'
p393
(lp394
S'Microbase VirtuOS v3.00b R.09'
p395
asS'Lantronix | embedded || switch'
p396
(lp397
S'Lantronix LSB4 Ethernet Switch'
p398
asS'EMC | DART || fileserver'
p399
(lp400
S'EMC DART running on a Data Mover fileserver. Version T4.1.8.1'
p401
aS'EMC IP4700 Filer'
p402
asS'Cisco | CBOS || broadband router'
p403
(lp404
S'Cisco 675 DSL router -- cbos 2.1'
p405
asS'Cisco | embedded || switch'
p406
(lp407
S'Cisco 1548M managed switch'
p408
aS'Cisco Catalyst 2820 switch Management Console'
p409
aS'Cisco Catalyst 5500/6500 or Alcatel OmniSwitch/Router'
p410
aS'Cisco Catalyst 6509 switch running IOS Version 12.1(23)E'
p411
aS'Cisco Catalyst switch'
p412
asS'Sega | embedded || game console'
p413
(lp414
S'Sega Dreamcast game console'
p415
asS'Nortel | embedded || terminal server'
p416
(lp417
S'Nortel Networks CVX1800 RAS. Software version 2.02'
p418
asS'Draytek | embedded || broadband router'
p419
(lp420
S'Draytek Vigor 2000 ISDN router'
p421
aS'Draytek Vigor 2200e DSL router v2.1a'
p422
aS'Draytek Vigor 2200e DSL router v2.1b'
p423
asS'Sony | NewsOS || general purpose'
p424
(lp425
S'Sony NewsOS 6.1.2'
p426
asS'FastComm | embedded || specialized'
p427
(lp428
S'FastComm FRAD (Frame Relay Access Device) F9200-DS-DNI -- Ver. 4.2.3A'
p429
asS'Radware | embedded || security-misc'
p430
(lp431
S'Radware Content Inspection Director v2.10.03'
p432
asS'AXIS | embedded || fileserver'
p433
(lp434
S'AXIS or Meridian Data Network CD-ROM server'
p435
aS'AXIS StorPoint CD E100 CD-ROM Server'
p436
aS'AXIS StorPoint CD E100 CD-ROM Server V5.20'
p437
aS'AXIS StorPoint CD E100 CD-ROM Server V5.38'
p438
asS'Microsoft | Windows | PocketPC/CE | PDA'
p439
(lp440
S'Microsoft Windows 95/98/NT 4.0 or PocketPC'
p441
aS'HP Jornada running Microsoft Windows CE 2.11 (Handheld/PC Pro 3.0 PDA)'
p442
aS'Microsoft PocketPC 3.0.11171 running on Compaq iPAQ 3870 Pocket PC'
p443
asS'3Com | embedded || terminal server'
p444
(lp445
S'3Com SuperStack II RAS remote access server'
p446
aS'3Com terminal server ESPL CS2100'
p447
asS'RoadLanner | embedded || broadband router'
p448
(lp449
S'RoadLanner Broadband router BRL-04FW 6.15.02r Build 0091 L:01'
p450
asS'3Com | embedded || broadband router'
p451
(lp452
S'3Com Home Connect Cable Modem'
p453
aS'3Com OfficeConnect 812 aDSL router'
p454
aS'3Com OfficeConnect Remote 812 aDSL Router'
p455
aS'3Com Sharkfin/Tailfin Cable Modem'
p456
aS'3Com Sharkfin/Tailfin Cable Modem'
p457
aS'US Robotics USR8000 Broadband router'
p458
asS'Netburner | embedded || specialized'
p459
(lp460
S'Netburner Model 5282 Embedded Ethernet Microcontroller'
p461
asS'Lucent | ComOS || terminal server'
p462
(lp463
S'Lucent Portmaster 4 running ComOS v4.0.3c2'
p464
asS'Easytel | embedded || broadband router'
p465
(lp466
S'Easytel TeleWell EA-701B ADSL Modem/Router'
p467
asS'SGI | IRIX | 4.X | general purpose'
p468
(lp469
S'SGI IRIX 4.0.5F'
p470
asS'DEC | DIGITAL UNIX | 4.X | general purpose'
p471
(lp472
S'DEC DIGITAL UNIX OSF1 V 4.0-4.0F'
p473
aS'DIGITAL UNIX OSF1 V 4.0,4.0B,4.0D,4.0E,4.0F'
p474
asS'Konica | embedded || printer'
p475
(lp476
S'Konica-Minolta magicolor2300DL printer controller'
p477
aS'Pitney Bowes photocopier, Konica printer/fax/scanner, or Toshiba E-Studio16 printer'
p478
asS'Packet Engines | embedded || router'
p479
(lp480
S'Packet Engines PowerRail 5200 router version 2.6.0r10 - 16 Sep, 1999'
p481
asS'US Robotics | embedded || WAP'
p482
(lp483
S'D-Link DI-804HV VPN Router or US-Robotics 8022 WAP or DI-714P+ Wireless router'
p484
aS'US Robotics Broadband router (model #8000-02)'
p485
aS'US Robotics USR8022 Broadband Wireless router (WAP)'
p486
asS'Cyclades | Cyros || terminal server'
p487
(lp488
S'Cyclades PathRAS Remote Access Server v1.1.8 - 1.3.12'
p489
asS'StackTools | StackTos || general purpose'
p490
(lp491
S'StackTools StackTos 1.0 embedded networking OS'
p492
aS'StackTos 2.1'
p493
asS'MultiTech | embedded || telecom-misc'
p494
(lp495
S'MultiTech MultiVoIP Version 2.01A Firmware'
p496
asS'Nexland | embedded || broadband router'
p497
(lp498
S'Nexland ISB Pro800 Turbo Cable/DSL router'
p499
asS'Fore | embedded || switch'
p500
(lp501
S'Fore ForeThought 7.1.0 ATM switch'
p502
aS'Fore ForeThought 8.3.0.N ATM BX200 switch'
p503
asS'Aironet | embedded || WAP'
p504
(lp505
S'Aironet AP4800E v8.07 - Aironet (Cisco?) 11 Mbps Wireless access point'
p506
asS'Minolta | VxWorks || printer'
p507
(lp508
S'Minolta QMS Printer running VxWorks 5.4.2'
p509
asS'Apple | embedded || printer'
p510
(lp511
S'Apple Color LaserWriter 12/660 PS (Model No. M3036)'
p512
aS'Apple Color LaserWriter 600 Printer'
p513
aS'Apple Color LaserWriter 600 Printer'
p514
aS'Apple LaserWriter 12/640 PS'
p515
aS'Apple LaserWriter 16/600 PS, HP 6P, or HP 5 Printer'
p516
aS'Apple LaserWriter 8500 (PostScript version 3010.103)'
p517
asS'Proteon | OpenRoute || router'
p518
(lp519
S'Proteon OpenRoute 2.1 on a RBX200 Router or IBM 2210 Router'
p520
aS'Proteon OpenRoute 3.0 gt series router'
p521
asS'NetBSD | NetBSD || general purpose'
p522
(lp523
S'NetBSD 1.0 big endian arch'
p524
aS'NetBSD 1.0 little endian arch'
p525
aS'NetBSD 1.1 - 1.2.1 litle endian arch'
p526
aS'NetBSD 1.2 - 1.2.1 big endian arch'
p527
aS'NetBSD 1.3 - 1.3.3 big endian arch'
p528
aS'NetBSD 1.3 - 1.3.3 little endian arch'
p529
aS'NetBSD 1.3H (after 19980919) or 1.3I (before 19990119) little endian arch'
p530
aS'NetBSD 1.3H-1.5  big endian arch'
p531
aS'NetBSD 1.5.2 running on a Commodore Amiga (68040 processor)'
p532
aS'NetBSD 1.5_ALPHA i386'
p533
aS'NetBSD 1.6'
p534
aS'NetBSD 1.6 - 1.6.1 (Alpha)'
p535
aS'NetBSD 1.6 BETA 4 i386 (20020630 snapshot)'
p536
aS'NetBSD 1.6.2 (alpha)'
p537
aS'NetBSD 1.6.2 (X86)'
p538
aS'NetBSD 1.6.2 - 2.0_BETA or Avocent Switchview net KVM switch'
p539
aS'NetBSD 1.6ZC (SPARC)'
p540
aS'NetBSD 1.6ZD'
p541
aS'NetBSD 2.0'
p542
aS'NetBSD 2.0'
p543
aS'NetBSD/Alpha 1.5.2 on a DEC 000/300 LX'
p544
asS'XCD | embedded || print server'
p545
(lp546
S'XCD Xconnect Print Server, firmware version CC8S-3.58 (98.09.21)'
p547
asS'Panasonic | embedded || broadband router'
p548
(lp549
S'Panasonic IP Technology Broadband Networking Gateway, KX-HGW200'
p550
asS'RCA | embedded || broadband router'
p551
(lp552
S'RCA/Thomson cable modem DCM-235/245'
p553
asS'Symantec | Solaris | 8 | firewall'
p554
(lp555
S'Symantec Enterprise Firewall v7.0.4 (on Solaris 8)'
p556
asS'BSDI | BSD/OS | 3.X | general purpose'
p557
(lp558
S'BSDI BSD/OS 3.0-3.1 (or possibly Mac OS, NetBSD)'
p559
asS'Sun | Solaris | 9 | general purpose'
p560
(lp561
S'Sun Solaris 9'
p562
aS'Sun Solaris 9'
p563
aS'Sun Solaris 9'
p564
aS'Sun Solaris 9 with TCP_STRONG_ISS set to 2'
p565
asS'Extreme Networks | Extremeware || switch'
p566
(lp567
S'Extreme Networks Alpine 3804 Switch running Extremeware 6.2.1'
p568
aS'Extremeware 6.2.2'
p569
asS'Extreme Networks | embedded || switch'
p570
(lp571
S'Extreme Gigabit switch (unknown version)'
p572
aS'Extreme Networks Black Diamond switch'
p573
asS'Blue Coat | SGOS || web proxy'
p574
(lp575
S'Blue Coat ProxySG (SGOS 3.2.2.1)'
p576
aS'Blue Coat Secure Gateway'
p577
aS'BlueCoat SG4'
p578
asS'Telos | embedded || media device'
p579
(lp580
S'Telos Zephyr Xstream v2.71p ISDN/POTS/Ethernet audio transceiver'
p581
asS'Global Technology Associates | embedded || firewall'
p582
(lp583
S'Gnat Box Light firewall v3.0.3 (from the inside interface)'
p584
asS'IBM | MVS || general purpose'
p585
(lp586
S'IBM MVS'
p587
aS'IBM MVS TCP/IP stack V. 3.2 or AIX 4.3.2'
p588
aS'IBM MVS TCP/IP TCPMVS 3.2'
p589
aS'IBM MVS TCP/IP TCPOE 3.3'
p590
asS'PCS | embedded || specialized'
p591
(lp592
S'PCS Intus 3100 time management device'
p593
asS'HP | MPE/iX || general purpose'
p594
(lp595
S'HP MPE/iX 5.5'
p596
aS'HP MPE/iX 5.5 on HP 3000'
p597
asS'Bay Networks | embedded || router'
p598
(lp599
S'Bay Networks BLN-2 Network Router or ASN Processor revision 9'
p600
aS'Bay Networks Instant Internet router'
p601
aS'Bay Networks Instant Internet router'
p602
aS'Baystack Instant Internet 400 SoHo Router'
p603
asS'SMC | embedded || WAP'
p604
(lp605
S'SMC Barricade Router, firmware 1.94a'
p606
aS'SMC Barricade Wireless Broadband Router (firmware R1.93e)'
p607
asS'US Robotics | embedded || switch'
p608
(lp609
S'Kentrox DataSMART 656 CSU/DSU, USR NETserver/16, or 3Com OfficeConnect ADSL router'
p610
asS'Billion | embedded || broadband router'
p611
(lp612
S'Billion ADSL router'
p613
aS'Billion BIPAC-741GE V2 aDSL Router'
p614
asS'Allied Telesyn | embedded || hub'
p615
(lp616
S'Allied Telesyn AT-S10 version 3.0 on an AT-TS24TR hub'
p617
asS'Brix Networks | embedded || specialized'
p618
(lp619
S'Brix 1000 Verifier'
p620
asS'Systech | embedded || specialized'
p621
(lp622
S'Systech RCS/3182 Ethernet serial port server (firmware 06D)'
p623
asS'Elsa | embedded || broadband router'
p624
(lp625
S'ELSA LANCOM 1100 office router'
p626
aS'ELSA LANCOM DSL I-10 Office router'
p627
aS'ELSA LANCOM DSL I-10 Office router or Wireless L-11'
p628
aS'ELSA LANCOM DSL/10 Office DSL router'
p629
aS'ELSA LANCOM DSL/10 office router'
p630
aS'ELSA LANCOM DSL/10 office router'
p631
aS'ELSA LANCOM DSL/I-1611 Office router'
p632
asS'Canon | embedded || printer'
p633
(lp634
S'Canon GP 160 PF printer'
p635
aS'Canon iR 2200 printer'
p636
aS'Canon iR C3200 printer'
p637
aS'Canon iR2270 printer'
p638
aS'Canon iR6000 printer'
p639
aS'Canon iR7200 Printer'
p640
aS'Canon photocopier/fax/scanner/printer GP30F'
p641
aS'Canon Pixmar IP4000R printer'
p642
asS'IPCop | Linux | 2.2.X | firewall'
p643
(lp644
S'IPCop 1.20 Linux 2.2.2X-based firewall'
p645
asS'DEC | embedded || router'
p646
(lp647
S'DECNIS 600 V4.1.3B multiprotocol bridge/router'
p648
asS'Nortel | embedded || switch'
p649
(lp650
S'Nortel Networks BayStack switch'
p651
aS'Nortel Networks Passport 1100 switch'
p652
aS'Nortel Networks Passport 8600 routing switch sw 3.3.0.0'
p653
asS'Rio | embedded || media device'
p654
(lp655
S'Rio Karma mp3 player'
p656
asS'Sharp | embedded || printer'
p657
(lp658
S'Sharp DIGITAL Imager (copier) AR-507'
p659
aS'Sharp Network Printer AR-337'
p660
asS'IBM | embedded || hub'
p661
(lp662
S'Cisco 760 Series ISDN router (non IOS) or IBM Stackable Hub'
p663
aS'IBM 8222 hub'
p664
aS'IBM 8239 Token-Ring Stackable Hub'
p665
asS'IPRoute | DOS || software router'
p666
(lp667
S'IPRoute (DOS based software router)'
p668
asS'Redback | AOS || router'
p669
(lp670
S'Redback SMS 1800 router'
p671
aS'Redback SMS 1800/10000 router or Thomson TMC 390 cable modem'
p672
aS'Redback SMS500 Redback Networks router AOS Release 5.0.3.8 - 5.0.4.0'
p673
asS'ZyXel | ZyNOS || firewall'
p674
(lp675
S'ZyXel ZyWALL 1 firewall'
p676
aS'ZyXel Zywall 10W firewall'
p677
aS'ZyXel ZyWALL 50 (ZyNOS 3.52)'
p678
asS'3Com | embedded || router'
p679
(lp680
S'3Com AccessBuilder Remote Office 500 router'
p681
aS'3Com NetBuilder & NetBuilder II OS v 9.3'
p682
aS'3Com Netbuilder & Netbuilder II router OS v8.1'
p683
aS'3Com Netbuilder II Router Ver 11.4.0.51'
p684
aS'3Com Netbuilder Remote Office 222 (ESPL-310), Version 10.1 (SW/NBRO-AB,10.1)'
p685
aS'3Com Netbuilder Remote Office 222 router'
p686
aS'3Com NetBuilder-II, OS version SW/NB2M-BR-5.1.0.27'
p687
aS'3Com OfficeConnect Netbuilder router'
p688
aS'3com OfficeConnect Remote 812 ADSL Router'
p689
aS'Shiva AccessPort Bridge/Router Software V 2.1.0 or 3Com HiPer Access Router Card hardware V1.0.0 software V4.1.59'
p690
asS'Zebra | embedded || printer'
p691
(lp692
S'Zebra Technologies TLP2844-Z printer'
p693
asS'DEC | OpenVMS | 6.X | general purpose'
p694
(lp695
S'DEC OpenVMS 6.1'
p696
aS'DEC OpenVMS 6.2'
p697
aS'DEC OpenVMS 6.2'
p698
aS'DEC OpenVMS 6.2'
p699
aS'DEC OpenVMS 6.2/Alpha'
p700
aS'DEC OpenVMS Alpha 6.2 running DIGITAL TCP/IP Services (UCX) v4.0'
p701
aS'DEC OpenVMS AXP 6.2 running Attachmate Pathway 3.1 TCP stack'
p702
aS'DEC OpenVMS V6.1 on VAX 4000-105A'
p703
asS'ARRIS | embedded || broadband router'
p704
(lp705
S'Apple Airport Extreme Base Station (WAP) or ARRIS Cadant C3 CMTS Cable Modem'
p706
asS'Compaq | Tru64 UNIX | 4.X | general purpose'
p707
(lp708
S'Compaq Tru64 UNIX (formerly DIGITAL UNIX) 4.0e'
p709
aS'Compaq Tru64 UNIX 4.0e'
p710
aS'Tru64 UNIX 4.0f - 4.0g'
p711
asS'ZyXel | ZyNOS || broadband router'
p712
(lp713
S'Hardware: ZyXel Prestige Broadband router'
p714
aS'ZyXel 944S Prestige router'
p715
aS'ZyXel P480 ISDN router running ZyNOS v2.42(O.00)'
p716
aS'ZyXel Prestige 642R-11 ASDL router running ZyNOS'
p717
aS'ZyXel Prestige 643 router'
p718
aS'ZyXel Prestige 700/Netgear MR314 Broadband router'
p719
aS'ZyXel Prestige 791R'
p720
asS'Palm | PalmOS | 3.X | PDA'
p721
(lp722
S'PalmOS 3.5.1 on m100 PDA'
p723
asS'Efficient Networks | embedded || broadband router'
p724
(lp725
S'Efficient Networks/SpeedStream DSL router'
p726
asS'Shiva | embedded || terminal server'
p727
(lp728
S'Shiva LanRover/8E Version 3.5'
p729
asS'Data General | AOS/VS || general purpose'
p730
(lp731
S'AOS/VS on a Data General mainframe'
p732
aS'AOS/VS or VSII'
p733
asS'Actiontec | embedded || broadband router'
p734
(lp735
S'Actiontec 1520 DSL gateway firmware 8.2.0.16'
p736
asS'D-Link | embedded || print server'
p737
(lp738
S'D-Link Print Server'
p739
asS'AXIS | Linux || webcam'
p740
(lp741
S'AXIS 2100 Network Camera running Linux/CRIS v2.32'
p742
asS'Cisco | IOS | 11.X | terminal server'
p743
(lp744
S'Cisco 2501/5260/5300 terminal server IOS 11.3.6(T1)'
p745
asS'Liebert | embedded || specialized'
p746
(lp747
S'Liebert Intellislot SNMP/Web Card (power devices, air conditioning, etc.)'
p748
asS'BSDI | BSD/OS | 4.X | general purpose'
p749
(lp750
S'BSDI BSD/OS 4.0-4.0.1'
p751
aS'BSDI BSD/OS 4.0.1'
p752
aS'BSDI BSD/OS 4.2'
p753
asS'Parks | embedded || broadband router'
p754
(lp755
S'Parks Altavia 671R router'
p756
asS'Toshiba | embedded || broadband router'
p757
(lp758
S'Toshiba DOCSIS Cable Modem'
p759
aS'Toshiba TR650 ISDN Router'
p760
asS'IBM | embedded || printer'
p761
(lp762
S'IBM Infoprint 12 Net-Printer'
p763
asS'SCO | UnixWare || general purpose'
p764
(lp765
S'SCO UnixWare 2.01'
p766
aS'SCO UnixWare 2.1'
p767
aS'SCO UnixWare 2.1'
p768
aS'SCO UnixWare 2.1.2'
p769
aS'SCO UnixWare 7.0.0 or OpenServer 5.0.4-5.0.6'
p770
aS'SCO UnixWare 7.1.0 - 7.1.1 (x86)'
p771
aS'SCO UnixWare 7.1.0 x86'
p772
aS'SCO UnixWare 7.1.1'
p773
asS'Xylogics | LynxOS || terminal server'
p774
(lp775
S'Xylogics Remote Annex 4000 terminal server running LynxOS realtime OS'
p776
asS'IBM | OS/400 | V4 | general purpose'
p777
(lp778
S'IBM AS/400 V3 and V4'
p779
aS'IBM AS/400 running OS/400 R4.4'
p780
aS'IBM OS/400 V4 r4-5'
p781
aS'IBM OS/400 V4R2M0'
p782
aS'IBM OS/400 V4R5'
p783
aS'IBM OS/400 V4R5M0'
p784
asS'HP | Netstation || X terminal'
p785
(lp786
S'HP Entria X station (running Netstation 7.x)'
p787
asS'Ascend | TAOS || terminal server'
p788
(lp789
S'Ascend / Lucent MAX TNT terminal server'
p790
aS'Ascend Mac 6000 Terminal access server'
p791
aS'Ascend Max terminal server firmware 7.0.4'
p792
aS'Ascend TNT OS +5.0Ap48+'
p793
aS'Ascend/Lucent Max (HP,4000-6000) version 6.1.3 - 7.0.2+'
p794
asS'Enterasys | embedded || switch'
p795
(lp796
S'Enterasys/Cabletron switch running Enterasys E8.2.0.0 - E9.0.0.0'
p797
aS'SonicWall SOHO firewall, Enterasys Matrix E1, or Accelerated Networks VoDSL, or Cisco 350 Access Point'
p798
asS'Panasonic | embedded || printer'
p799
(lp800
S'Panasonic DP-3520 multi-function printer'
p801
aS'Panasonic panafax DX2000 SuperG3 fax machine'
p802
asS'Enterasys | embedded || firewall'
p803
(lp804
S'Enterasys XSR-1805 Security Route'
p805
asS'HP | embedded || remote management'
p806
(lp807
S'HP Integrated Lights Out remote configuration Board'
p808
asS'Microplex | embedded || print server'
p809
(lp810
S'IBM 6400 printer or Microplex Pocket Print Server'
p811
aS'Microplex Print Server'
p812
asS'Microsoft | Windows | 2003/.NET | general purpose'
p813
(lp814
S'Microsoft Windows 2003 Server'
p815
aS'Microsoft Windows 2003 Server'
p816
aS'Microsoft Windows 2003 Server'
p817
aS'Microsoft Windows 2003 Server'
p818
aS'Microsoft Windows 2003 Server'
p819
aS'Microsoft Windows 2003 Server Enterprise Edition'
p820
aS'Microsoft Windows 2003 Server Enterprise Edition'
p821
aS'Microsoft Windows 2003 Server SP1'
p822
aS'Microsoft Windows 2003 Server SP1'
p823
aS'Microsoft Windows 2003 Server Standard Edition'
p824
aS'Microsoft Windows 2003 Server Standard Edition'
p825
aS'Microsoft Windows 2003 Server Standard Edition'
p826
aS'Microsoft Windows 2003 Server Standart Edition SP1'
p827
aS'Microsoft Windows 2003 standard edition'
p828
aS'Microsoft Windows Server 2003'
p829
aS'Microsoft Windows Server 2003 Enterprise Edition'
p830
asS'Linksys | embedded || print server'
p831
(lp832
S'Linksys EtherFast Print Server'
p833
aS'Linksys EtherFast Print Server'
p834
aS'Linksys PSUS4 USB Print Server and switch'
p835
aS'Linksys WPS54GU2 Wireless Print Server'
p836
asS'Digital Link | embedded || CSUDSU'
p837
(lp838
S'Digital Link DL2001 CSU/DSU Management Access Processor'
p839
asS'D-Link | embedded || telecom-misc'
p840
(lp841
S'D-Link VoIP Gateway GS-104SH'
p842
asS'Kronos | embedded || specialized'
p843
(lp844
S'Kronos Time clock'
p845
asS'IBM | OS/390 | V2 | general purpose'
p846
(lp847
S'IBM OS/390 V2R10'
p848
asS'Nokia | Symbian || phone'
p849
(lp850
S'Symbian OS 6.1 on Nokia N-Gage v 4.03 phone'
p851
asS'Bay Networks | embedded || terminal server'
p852
(lp853
S'VxWorks 5.3.x bases system (usually an Ethernet hub or switch such as HP ProCurve) or Bay Networks MicroAnnex XL terminal server'
p854
asS'Maxim-IC | TiniOS || general purpose'
p855
(lp856
S'Maxim-IC TiniOS DS80c400'
p857
aS'Maxim/Dallas TINI embedded Java v1.02b'
p858
aS'Maxim/Dallas TINI embedded Java v1.02d'
p859
asS'NetScreen | ScreenOS || firewall'
p860
(lp861
S'Netscreen 5GT Plus running ScreenOS 4.0.0r5.3'
p862
aS'NetScreen NS-204 Firewall'
p863
aS'NetScreen-100'
p864
asS'MultiTech | embedded || terminal server'
p865
(lp866
S'MultiTech CommPlete (modem server) RAScard'
p867
aS'MultiTech CommPlete Controller (terminal server)'
p868
asS'Netgear | embedded || switch'
p869
(lp870
S'Netgear GS724T Gigabit Smart Switch'
p871
asS'Sun | SunOS || general purpose'
p872
(lp873
S'Sun RSC (Remote System Control card) v1.14 (in Solaris 2.7)'
p874
aS'Sun SunOS 4.0.3'
p875
aS'Sun SunOS 4.1.3_U1 + ISI RFC1323 mods from ISI'
p876
asS'RiverStone | embedded || router'
p877
(lp878
S'RiverStone RS3000 router'
p879
asS'Cisco | embedded || VoIP phone'
p880
(lp881
S'Cisco 7960 SIP Phone running OS 4.2'
p882
aS'Cisco IP phone (POS3-04-3-00, PC030301)'
p883
aS'Cisco IP Phone 7910 or 7940 Firmware 3.1'
p884
aS'Cisco IP Phone 7940'
p885
aS'Cisco IP Phone 7960'
p886
aS'Cisco IP Phone 7970G'
p887
asS'KIRK | embedded || VoIP gateway'
p888
(lp889
S'KIRK Wireless Server 600'
p890
asS'Pace | embedded || media device'
p891
(lp892
S'Pace digital cable TV receiver'
p893
asS'Alteon | embedded || load balancer'
p894
(lp895
S'Alteon Networks ACEswitch 180e Software Version 8.0.62.7'
p896
aS'Nortel/Alteon ACE Director 3 Version 6.0.42-B'
p897
asS'NCD | embedded || X terminal'
p898
(lp899
S'NCD X server (NCD16 server 2.3.0 03/12/91)'
p900
asS'Xylogics | embedded || terminal server'
p901
(lp902
S'Xylogics Micro Annex ELS terminal server x7.1.8'
p903
asS'Lantronix | Punix || print server'
p904
(lp905
S'Lantronix EPS1 Print Server version V3.5/1(970325)'
p906
aS'Lantronix EPS1 Printer Server'
p907
aS'Lantronix EPS2 Print Server Version V3.5/2(970721)'
p908
asS'SCO | OpenServer || general purpose'
p909
(lp910
S'SCO OpenServer 5.0.5'
p911
aS'SCO OpenServer 5.0.7'
p912
aS'SCO OpenServer Release 5'
p913
aS'SCO OpenServer Release 5'
p914
asS'Intel | embedded || router'
p915
(lp916
S'Intel ER8100ST Express Router 8100'
p917
aS'Intel ER9100 Express Router 9100'
p918
asS'Edimax | embedded || broadband router'
p919
(lp920
S'Edimax BR-6004 Broadband router'
p921
asS'Sun | Solaris | 8 | general purpose'
p922
(lp923
S'Sun Solaris 2.6 - 8 (SPARC)'
p924
aS'Sun Solaris 8'
p925
aS'Sun Solaris 8'
p926
aS'Sun Solaris 8'
p927
aS'Sun Solaris 8'
p928
aS'Sun Solaris 8'
p929
aS'Sun Solaris 8'
p930
aS'Sun Trusted Solaris 8'
p931
asS'Linux | Linux | 2.1.X | general purpose'
p932
(lp933
S'Linux 2.1.24 PowerPC'
p934
aS'Linux 2.1.76'
p935
aS'Linux 2.1.88'
p936
aS'Linux 2.1.91 - 2.1.103'
p937
asS'FreeBSD | FreeBSD | 6.X | general purpose'
p938
(lp939
S'FreeBSD 5.2.1-RELEASE or 6.0-CURRENT'
p940
asS'Apple | Mac OS X | 10.3.X | general purpose'
p941
(lp942
S'Apple Mac OS X 10.3.3 (Panther)'
p943
aS'Apple Mac OS X 10.3.5 or 10.3.7'
p944
aS'Apple Mac OS X 10.3.6 or 10.3.7'
p945
aS'Apple Mac OS X 10.3.9'
p946
aS'Apple Mac OS X 10.4.1 (Tiger)'
p947
asS'NeXT | Mach || general purpose'
p948
(lp949
S'NeXT Mach'
p950
asS'Foundry | embedded || load balancer'
p951
(lp952
S'Foundry FastIron Edge Switch (load balancer) 2402'
p953
aS'Foundry Load Balancer OS Ver 7.2.X - 7.3.X'
p954
aS'Foundry Networks Biglron 8000 load balancer'
p955
asS'SAR | embedded || broadband router'
p956
(lp957
S'GNet BB0040 or SAR 703 DSL modem + router'
p958
asS'Netgear | embedded || broadband router'
p959
(lp960
S'HP Advancestack Etherswitch 224T or 210 or Netgear RP114 DSL-Router w/Switch'
p961
aS'Netgear DG824M WAP'
p962
aS'Netgear FVL238 vpn/firewall/router'
p963
aS'Netgear FVL328 vpn/firewall/router'
p964
aS'Netgear WGR614 Wireless router'
p965
aS'Netgear Wireless router or Netgear FM114P/REPOTEC IP515H Router & Print Server'
p966
asS'Turtle Beach | embedded || media device'
p967
(lp968
S'Turtle Beach AudioTron network MP3 player'
p969
aS'Turtle Beach AudioTron network MP3 player'
p970
asS'Level One | embedded || broadband router'
p971
(lp972
S'Fingerprint LevelOne WBR-3406TX Wireless Broadband router'
p973
aS'LevelOne WBR-3403TX Wireless Broadband router'
p974
asS'IBM | OS/390 | V5 | general purpose'
p975
(lp976
S'IBM OS/390 V5R0M0'
p977
asS'Quanterra | OS/9 || specialized'
p978
(lp979
S'Quanterra seismic data acquisition system running OS/9 V2.4 on 68K'
p980
asS'Nokia | embedded || broadband router'
p981
(lp982
S'Nokia M1122 DSL Router'
p983
asS'D-Link | embedded || hub'
p984
(lp985
S'D-Link Corp. DE-1800 Stackable Hub SNMP/Telnet Agent Software version 2.04B3 boot PROM 2.21'
p986
asS'Cabletron | embedded || router'
p987
(lp988
S'Cabletron Smart Switch Router 8600'
p989
aS'Cabletron Systems SSR 8000 smart switch router System Software, Version 3.1.B.16'
p990
asS'Xylan | embedded || switch'
p991
(lp992
S'IBM LAN RouteSwitch/Xylan OmniSwitch Version 3.2.5/NeXT'
p993
asS'Exabyte | embedded || storage-misc'
p994
(lp995
S'Exabyte X80 tape backup robot'
p996
asS'3Com | embedded || switch'
p997
(lp998
S'3Com / USR TotalSwitch Firmware: 02.02.00R'
p999
aS'3Com Access Builder 4000 Switch'
p1000
aS'3Com LANplex 6004 switch'
p1001
aS'3Com SuperStack II switch (OS v 2.0)'
p1002
aS'3Com SuperStack II switch SW/NBSI-CF,11.1.0.00S38'
p1003
aS'Cisco VPN 3000 or 3Com 4924 GigE Switch'
p1004
asS'IQinVision | embedded || webcam'
p1005
(lp1006
S'IQinVison IQeye3 webcam'
p1007
asS'DEC | VMS || general purpose'
p1008
(lp1009
S'DEC OpenVMS 7.3-1 w/Multinet 4.4'
p1010
aS'DEC VAX 7000-610 or 4200/SPX OR 6000-430'
p1011
aS'DEC VAX/VMS 5.3 on a MicroVAX II'
p1012
aS'DEC VAX/VMS 5.5-2'
p1013
aS'DEC VAX/VMS v5.5, CMU-TEK TCP/IP stack'
p1014
aS'DEC VMS MultiNet V4.1(16)'
p1015
asS'Isolation | embedded || encryption accelerator'
p1016
(lp1017
S'Isolation Systems Infocrypt Enterprise'
p1018
asS'HP | embedded || print server'
p1019
(lp1020
S'HP printer w/JetDirect card'
p1021
aS'HP Deskjet 6127 printer or InkJet 1200 printer server'
p1022
aS'HP LaserJet printer/print server'
p1023
asS'Sony | Linux || game console'
p1024
(lp1025
S'PS2 Linux 1.0 on Sony PS2 game console'
p1026
asS'IBM | OS/400 | V3 | general purpose'
p1027
(lp1028
S'IBM OS/400 V3'
p1029
asS'IBM | embedded || X terminal'
p1030
(lp1031
S'AGE Logic, Inc. IBM XStation'
p1032
asS'Xyplex | embedded || terminal server'
p1033
(lp1034
S'Xyplex Network 9000 terminal server'
p1035
aS'Xyplex Terminal Server CSERV-20 software v6.0.4'
p1036
aS'Xyplex Terminal Server v6.0.2S5'
p1037
asS'Linux | Linux | 2.0.X | general purpose'
p1038
(lp1039
S'Linux 2.0.0'
p1040
aS'Linux 2.0.27 - 2.0.30'
p1041
aS'Linux 2.0.32-34'
p1042
aS'Linux 2.0.32-34'
p1043
aS'Linux 2.0.34-38'
p1044
aS'Linux 2.0.35 (S.u.S.E. Linux 5.3 (i386)'
p1045
aS'Linux 2.0.39'
p1046
asS'xMach | xMach || general purpose'
p1047
(lp1048
S'xMach free distributed OS version 0.1 current'
p1049
asS'MultiTech | embedded || VoIP gateway'
p1050
(lp1051
S'MultiTech MultiVoip 2410'
p1052
asS'Convex | SPP-UX || general purpose'
p1053
(lp1054
S'Convex SPP-UX 5.2.1'
p1055
aS'SPP-UX 5.x on a Convex SPP-1600'
p1056
asS'Apollo | Domain/OS || general purpose'
p1057
(lp1058
S'Apollo Domain/OS SR10.3.5'
p1059
aS'Apollo Domain/OS SR10.4'
p1060
asS'Soyo | embedded || VoIP phone'
p1061
(lp1062
S'Soyo G668 VoIP phone'
p1063
asS'Cisco | vxworks || WAP'
p1064
(lp1065
S'Cisco Aironet WAP, Brocade Fibre Switch, or Sun Remote System Console'
p1066
asS'FreeBSD | FreeBSD | 2.X | general purpose'
p1067
(lp1068
S'FreeBSD 2.1.0 - 2.1.5'
p1069
aS'FreeBSD 2.2.1-STABLE'
p1070
asS'Intel | embedded || print server'
p1071
(lp1072
S'Intel InBusiness Print Station'
p1073
aS'Intel NetportExpress 10 3-port Print Server'
p1074
aS'Intel NetportExpress 10/100 3-port Print Server'
p1075
aS'Intel NetportExpress PRO Print Server V04.33a'
p1076
aS'Intel NetportExpress XL Print Server'
p1077
asS'Gauntlet | Solaris | 2.5.X | firewall'
p1078
(lp1079
S'Gauntlet 4.0a firewall on Solaris 2.5.1'
p1080
asS'Genius | embedded || print server'
p1081
(lp1082
S'Genius Print Server'
p1083
asS'Compex | embedded || switch'
p1084
(lp1085
S'Compex CGX3224 Switch'
p1086
asS'Alcatel | embedded || broadband router'
p1087
(lp1088
S'Alcatel 1000 ADSL (modem)'
p1089
aS'Alcatel 1000 DSL Router'
p1090
aS'Alcatel Speed Touch *DSL modem/router'
p1091
aS'Alcatel Speed Touch 510 *DSL modem/router'
p1092
aS'Alcatel Speed Touch Pro aDSL modem'
p1093
asS'Tektronix | embedded || printer'
p1094
(lp1095
S'Tektronix Phaser 350 printer'
p1096
aS'Tektronix Phaser 560 printer'
p1097
aS'Tektronix Phaser printer'
p1098
aS'Tektronix Phaser printer'
p1099
aS'Tektronix/Xerox Phaser printer'
p1100
asS'ZyXel | ZyNOS || switch'
p1101
(lp1102
S'ZyXel switch ES-3024 ZyNOS V3.50'
p1103
asS'Proxim | embedded || bridge'
p1104
(lp1105
S'Proxim Stratum MP Wireless bridge'
p1106
asS'Cyclades | Cyras || terminal server'
p1107
(lp1108
S'Cyclades PathRAS Remote Access Server v1.1.7'
p1109
asS'Hitachi | HI-UX || general purpose'
p1110
(lp1111
S'Hitachi HI-UX/MPP'
p1112
aS'Xylan OmniSwitch 5x/9x Ethernet switch, Xylogics Annex-III Comm server R10.0, or Hitachi HI-UX/WE2'
p1113
asS'Juniper | JUNOS || router'
p1114
(lp1115
S'Juniper Networks JUNOS 5.3 on an Olive router'
p1116
aS'Juniper Networks JUNOS 5.6R1.3 routing software on x86 box'
p1117
aS'Juniper Networks router JUNOS 5.5R1.2'
p1118
aS'Juniper Networks router M10i running JUNOS 7.2R1.7'
p1119
aS'Juniper Router running JUNOS'
p1120
asS'Cisco | embedded || web proxy'
p1121
(lp1122
S'Cisco Cache Engine Web Proxy'
p1123
asS'Magna | embedded || router'
p1124
(lp1125
S'Magna SG10 intranet router'
p1126
asS'Arlan | embedded || bridge'
p1127
(lp1128
S'ARLAN BR2000E V5.0E Wireless Radio Bridge'
p1129
asS'Minix | Minix || general purpose'
p1130
(lp1131
S'Minix 32-bit/Intel 2.0.0'
p1132
aS'Minix 32-bit/Intel 2.0.3'
p1133
aS'Minix v2.0.2 32bits'
p1134
asS'Bosch | embedded || webcam'
p1135
(lp1136
S"Bosch Security Systems's Divar Digital Video Recorder Version 2.00"
p1137
asS'Be | BeOS | 5.X | general purpose'
p1138
(lp1139
S'BeOS 5.0.4 (BeOS 5 Pro + BONE 7a)'
p1140
aS'BeOS 5.03 x86 with the BONE network stack'
p1141
aS'BeOS 5.1d0/DANO on x86'
p1142
aS'BeOS R5.03 Personal Edition'
p1143
asS'IBM | AIX | 3.X | general purpose'
p1144
(lp1145
S'IBM AIX 3.2'
p1146
aS'IBM AIX 3.2'
p1147
aS'IBM AIX 3.2 running on RS/6000'
p1148
aS'IBM AIX 3.2.3 running on RS6000 model 560'
p1149
aS'IBM AIX 3.2.5 (Bull HardWare)'
p1150
aS'IBM AIX v3.2.5 - 4'
p1151
asS'NeXT | NeXTStep || general purpose'
p1152
(lp1153
S'NeXTStep/OpenStep 4.2/Intel'
p1154
aS'OpenStep 4.0-4.2 or NeXTStep 1.0-3.3 (Intel)'
p1155
aS'OpenStep 4.1/NeXTStep 3.3'
p1156
asS'DEC | DIGITAL UNIX | 3.X | general purpose'
p1157
(lp1158
S'DIGITAL UNIX OSF1 V 3.0,3.2,3.2C'
p1159
asS'Aethra | embedded || webcam'
p1160
(lp1161
S'Aethra Vega Conference System'
p1162
asS'Stratus | VOS || general purpose'
p1163
(lp1164
S'Stratus VOS Release 14.3.1ae'
p1165
asS'Microsoft | Windows | NT/2K/XP | general purpose'
p1166
(lp1167
S'Microsoft Windows 2003 Server Enterprise Edition or XP Pro SP2'
p1168
aS'Microsoft Windows 2003 Server or XP SP2'
p1169
aS'Microsoft Windows NT 3.51 SP5, NT 4.0 or 95/98/98SE'
p1170
aS'Microsoft Windows 2000 Advanced Server SP2'
p1171
aS'Microsoft Windows 2000 Advanced Server SP3'
p1172
aS'Microsoft Windows 2000 Advanced Server SP3'
p1173
aS'Microsoft Windows 2000 Advanced Server SP4'
p1174
aS'Microsoft Windows 2000 Advanced Server SP4'
p1175
aS'Microsoft Windows 2000 Advanced Server SP4'
p1176
aS'Microsoft Windows 2000 Professional'
p1177
aS'Microsoft Windows 2000 Professional (Russian) SP2'
p1178
aS'Microsoft Windows 2000 Professional RC1 or Windows 2000 Advanced Server Beta3'
p1179
aS'Microsoft Windows 2000 Professional SP2'
p1180
aS'Microsoft Windows 2000 Professional SP3'
p1181
aS'Microsoft Windows 2000 Professional SP4'
p1182
aS'Microsoft Windows 2000 Server SP1'
p1183
aS'Microsoft Windows 2000 Server SP2'
p1184
aS'Microsoft Windows 2000 Server SP3'
p1185
aS'Microsoft Windows 2000 Server SP3'
p1186
aS'Microsoft Windows 2000 Server SP3'
p1187
aS'Microsoft Windows 2000 Server SP3 or Windows XP Pro SP1'
p1188
aS'Microsoft Windows 2000 Server SP4'
p1189
aS'Microsoft Windows 2000 Server SP4'
p1190
aS'Microsoft Windows 2000 Server SP4'
p1191
aS'Microsoft Windows 2000 Server SP4'
p1192
aS'Microsoft Windows 2000 Server SP4'
p1193
aS'Microsoft Windows 2000 Server SP4 or 2003 Server Standard Edition'
p1194
aS'Microsoft Windows 2000 Server SP4 or XP SP1'
p1195
aS'Microsoft Windows 2000 SP1'
p1196
aS'Microsoft Windows 2000 SP1'
p1197
aS'Microsoft Windows 2000 SP2'
p1198
aS'Microsoft Windows 2000 SP2'
p1199
aS'Microsoft Windows 2000 SP2'
p1200
aS'Microsoft Windows 2000 SP2'
p1201
aS'Microsoft Windows 2000 SP2 or XP or XP SP1'
p1202
aS'Microsoft Windows 2000 SP2 with Hotfix (Pre-SP3)'
p1203
aS'Microsoft Windows 2000 SP3'
p1204
aS'Microsoft Windows 2000 SP3'
p1205
aS'Microsoft Windows 2000 SP3'
p1206
aS'Microsoft Windows 2000 SP3'
p1207
aS'Microsoft Windows 2000 SP3'
p1208
aS'Microsoft Windows 2000 SP3'
p1209
aS'Microsoft Windows 2000 SP3'
p1210
aS'Microsoft Windows 2000 SP3'
p1211
aS'Microsoft Windows 2000 SP3'
p1212
aS'Microsoft Windows 2000 SP3'
p1213
aS'Microsoft Windows 2000 SP4'
p1214
aS'Microsoft Windows 2000 SP4'
p1215
aS'Microsoft Windows 2000 SP4'
p1216
aS'Microsoft Windows 2000 SP4'
p1217
aS'Microsoft Windows 2000 SP4'
p1218
aS'Microsoft Windows 2000 SP4'
p1219
aS'Microsoft Windows 2000 SP4'
p1220
aS'Microsoft Windows 2000 SP4'
p1221
aS'Microsoft Windows 2000 SP4'
p1222
aS'Microsoft Windows 2000 SP4 or Windows XP SP1'
p1223
aS'Microsoft Windows NT 3.10 (Build 528)'
p1224
aS'Microsoft Windows NT 4.0 Server SP5-SP6'
p1225
aS'Microsoft Windows NT 4.0 SP 6a + hotfixes'
p1226
aS'Microsoft Windows NT 4.0 SP3'
p1227
aS'Microsoft Windows NT 4.0 SP3'
p1228
aS'Microsoft Windows NT 4.0 SP5'
p1229
aS'Microsoft Windows NT 4.0 SP5-SP6'
p1230
aS'Microsoft Windows NT 4.0 SP6'
p1231
aS'Microsoft Windows NT 4.0 SP6a'
p1232
aS'Microsoft Windows NT 4.0 SP6a'
p1233
aS'Microsoft Windows NT 4.0 SP6a with Kerio WinRoute Pro 4.27 Firewall'
p1234
aS'Microsoft Windows NT 4.0 Terminal Server Edition'
p1235
aS'Microsoft Windows NT 4.0 Workstation SP6a'
p1236
aS'Microsoft Windows NT 4.0 Workstation SP6a'
p1237
aS'Microsoft Windows NT Version 4 (Build 1381) Service Pack 6a'
p1238
aS'Microsoft Windows XP'
p1239
aS'Microsoft Windows XP Home Edition'
p1240
aS'Microsoft Windows XP Home Edition (English) SP2'
p1241
aS'Microsoft Windows XP Home Edition (German) SP1'
p1242
aS'Microsoft Windows XP Home Edition (German) SP2'
p1243
aS'Microsoft Windows XP Home Edition SP1'
p1244
aS'Microsoft Windows XP Home Edition SP1 or SP2'
p1245
aS'Microsoft Windows XP Pro'
p1246
aS'Microsoft Windows XP Pro (German)'
p1247
aS'Microsoft Windows XP Pro (German) SP1'
p1248
aS'Microsoft Windows XP Pro (German) SP1'
p1249
aS'Microsoft Windows XP Pro (Italian)'
p1250
aS'Microsoft Windows XP Pro (Spanish) SP2'
p1251
aS'Microsoft Windows XP Pro or Windows 2000 Professional SP2+'
p1252
aS'Microsoft Windows XP Pro RC1+ through final release'
p1253
aS'Microsoft Windows XP Pro SP1'
p1254
aS'Microsoft Windows XP Pro SP1'
p1255
aS'Microsoft Windows XP Pro SP1'
p1256
aS'Microsoft Windows XP Pro SP1'
p1257
aS'Microsoft Windows XP Pro SP1'
p1258
aS'Microsoft Windows XP Pro SP1'
p1259
aS'Microsoft Windows XP Pro SP1'
p1260
aS'Microsoft Windows XP Pro SP1'
p1261
aS'Microsoft Windows XP Pro SP1'
p1262
aS'Microsoft Windows XP Pro SP1'
p1263
aS'Microsoft Windows XP Pro SP1'
p1264
aS'Microsoft Windows XP Pro SP1'
p1265
aS'Microsoft Windows XP Pro SP1'
p1266
aS'Microsoft Windows XP Pro SP1'
p1267
aS'Microsoft Windows XP Pro SP1 or Windows 2000 Advanced Server SP3'
p1268
aS'Microsoft Windows XP Pro SP2'
p1269
aS'Microsoft Windows XP Pro SP2'
p1270
aS'Microsoft Windows XP Pro SP2'
p1271
aS'Microsoft Windows XP Pro SP2'
p1272
aS'Microsoft Windows XP Pro SP2'
p1273
aS'Microsoft Windows XP Pro SP2'
p1274
aS'Microsoft Windows XP Pro SP2'
p1275
aS'Microsoft Windows XP Pro SP2 (firewall disabled)'
p1276
aS'Microsoft Windows XP Pro Version 5.1 Build 2600'
p1277
aS'Microsoft Windows XP SP1'
p1278
aS'Microsoft Windows XP SP1'
p1279
aS'Microsoft Windows XP SP1'
p1280
aS'Microsoft Windows XP SP1 or Windows 2000 SP3'
p1281
aS'Microsoft Windows XP SP1 or Windows 2000 SP4'
p1282
aS'Microsoft Windows XP SP2'
p1283
aS'Microsoft Windows XP SP2'
p1284
aS'Microsoft Windows XP SP2'
p1285
aS'Microsoft Windows XP SP2'
p1286
aS'Microsoft Windows XP SP2'
p1287
aS'Microsoft Windows XP SP2 or 2003 Server'
p1288
asS'Tandberg | embedded || X terminal'
p1289
(lp1290
S'Tandberg X-terminal'
p1291
asS'Polycom | embedded || webcam'
p1292
(lp1293
S'Polycom Video Conference node'
p1294
aS'Polycom ViewStation'
p1295
aS'Polycom ViewStation 512K videoconferencing system'
p1296
asS'Alpha Micro | AMOS || general purpose'
p1297
(lp1298
S'Amos 2.3A'
p1299
asS'Scientific-Atlanta | embedded || media device'
p1300
(lp1301
S'Scientific Atlanta Explorer 4200 Digital Cable Box'
p1302
aS'Scientific Atlanta PowerVu Program Receiver Model D9850/9010'
p1303
asS'Handspring | PalmOS | 5.X | PDA'
p1304
(lp1305
S'PalmOS 5.2.1 on Handspring Treo'
p1306
asS'Compaq | Tru64 UNIX | 5.X | general purpose'
p1307
(lp1308
S'Compaq Tru64 UNIX V5.1 (Rev. 732)'
p1309
aS'Compaq Tru64 UNIX V5.1 (Rev. 732)'
p1310
aS'Compaq Tru64 UNIX V5.1A (Rev. 1885)'
p1311
aS'Compaq Tru64 UNIX V5.1A (Rev. 1885)'
p1312
aS'Compaq Tru64 UNIX V5.1B'
p1313
aS'HP Tru64 UNIX v5.1B'
p1314
aS'OSF1 5.0 Rev. 910 (AKA Compaq/DIGITAL Tru64 UNIX)'
p1315
asS'Proxim | embedded || WAP'
p1316
(lp1317
S'Proxim 8571 802.11a Access Point'
p1318
asS'HP | embedded || load balancer'
p1319
(lp1320
S'HP Procurve Routing Switch 9304M'
p1321
aS'HP Procurve Switch 2600 series or 5304XL'
p1322
asS'Raptor | embedded || firewall'
p1323
(lp1324
S'Raptor firewall 5.03 on NT 4'
p1325
asS'Corega | embedded || broadband router'
p1326
(lp1327
S'Corega BAR SW-4P Broadband Access Router'
p1328
asS'Digital Networks | embedded || switch'
p1329
(lp1330
S'Digital Networks VNswitch 900'
p1331
asS'SonicWall | embedded || firewall'
p1332
(lp1333
S'SonicWall Pro 200 firewall'
p1334
asS'WTI | embedded || power-device'
p1335
(lp1336
S'WTI Internet Power Switch 1.01'
p1337
aS'WTI Network Power Switch v3.02'
p1338
asS'Cray | UNICOS | 10.X | general purpose'
p1339
(lp1340
S'UNICOS 10.0.0 on Cray 90'
p1341
asS'PolyCom | embedded || webcam'
p1342
(lp1343
S'PolyCom ViewStation video-conferencing system (firmware v7.2)'
p1344
asS'Phillips | embedded || media device'
p1345
(lp1346
S'Phillips ReplayTV 5000 DVR'
p1347
asS'Telocity | embedded || broadband router'
p1348
(lp1349
S'Telocity (DirectTVDSL) Gateway x2 Model'
p1350
asS'MiraPoint | embedded || general purpose'
p1351
(lp1352
S'Mirapoint messaging server M1000 (OS v 1.0.0)'
p1353
aS'MiraPoint messaging server v3.1'
p1354
asS'Racal | embedded || encryption accelerator'
p1355
(lp1356
S'Racal 7100 Host Security Module 1.05 / 5.05'
p1357
asS'Rockwell | embedded || telecom-misc'
p1358
(lp1359
S'Rockwell Spectrum 100 POTS switcher release 7.2'
p1360
asS'Sony | Symbian || phone'
p1361
(lp1362
S'Sony Ericsson P800 mobile phone, Symbian OS v7.0'
p1363
asS'Bay Networks | embedded || switch'
p1364
(lp1365
S'Bay Networks BayStack 310T switch'
p1366
aS'BayStack 28115/ADV Fast Ethernet Switch'
p1367
aS'BayStack 450-24T switch'
p1368
asS'Teltrend | embedded || router'
p1369
(lp1370
S'Teltrend (aka Securicor 3net) Router'
p1371
asS'Galacticomm | WorldGroup || BBS'
p1372
(lp1373
S'Galacticomm WorldGroup BBS (MajorBBS) w/TCP/IP'
p1374
aS'Galacticomm WorldGroup BBS / Vircom TCP/IP stack'
p1375
asS'Intracom | embedded || broadband router'
p1376
(lp1377
S'Intergraph jetSpeed 520 ADSL Router'
p1378
asS'Linux | Linux | 2.2.X | general purpose'
p1379
(lp1380
S'Linux 2.1.19 - 2.2.25'
p1381
aS'Linux 2.2.12 - 2.2.25'
p1382
aS'Linux 2.2.13'
p1383
aS'Linux 2.2.13 (SuSE; x86)'
p1384
aS'Linux 2.2.14'
p1385
aS'Linux 2.2.16C37_III on Sun Cobalt'
p1386
aS'Linux 2.2.19'
p1387
aS'Linux 2.2.19 (Alpha)'
p1388
aS'Linux 2.2.19 - 2.2.20'
p1389
aS'Linux 2.2.19 on a DEC Alpha'
p1390
aS'Linux 2.2.20 SMP'
p1391
aS'Linux 2.2.21 SMP (x86)'
p1392
aS'Linux 2.2.22'
p1393
aS'Linux 2.2.5 - 2.2.13 SMP'
p1394
aS'Linux 2.4.4'
p1395
asS'Linksys | embedded || broadband router'
p1396
(lp1397
S'Linksys BEFSR41 Broadband router'
p1398
aS'Linksys BEFSR41 Broadband router'
p1399
aS'Linksys BEFSR41 V3 Etherfast cable/DSL router'
p1400
aS'Linksys BEFVP41 VPN Router'
p1401
aS'Linksys BEFW11S4 Wireless DSL/Cable Router'
p1402
aS'Linksys BEFW11S4 Wireless DSL/Cable Router'
p1403
aS'Linksys WAG54G Wireless Broadband Router'
p1404
aS'Linksys WAG54G Wireless Gateway'
p1405
aS'Linksys WRT54G Wireless Broadband Router (Linux kernel 2.4.20)'
p1406
asS'DEC | DIGITAL UNIX | 2.X | general purpose'
p1407
(lp1408
S'DEC OSF/1 V1.3A - 2.0'
p1409
asS'HP | HP-UX | 11.X | general purpose'
p1410
(lp1411
S'Apple Mac OS 9.04 or HP-UX B.11.00'
p1412
aS'HP-UX 11'
p1413
aS'HP-UX 11 w/tcp_isn_passphrase'
p1414
aS'HP-UX 11.00'
p1415
aS'HP-UX 11.11'
p1416
aS'HP-UX 11.11'
p1417
aS'HP-UX B.11.00 A 9000/785'
p1418
aS'HP-UX B.11.00 A 9000/800'
p1419
aS'HP-UX B11.00 U 9000/839'
p1420
asS'Sun | Solaris | 2.X | general purpose'
p1421
(lp1422
S'Sun Solaris 2.3 - 2.4'
p1423
aS'Sun Solaris 2.4 w/most Sun patches (jumbo cluster patch, security patches, etc)'
p1424
aS'Sun Solaris 2.5, 2.5.1'
p1425
aS'Sun Solaris 2.6'
p1426
aS'Sun Solaris 2.6 (SPARC)'
p1427
asS'HP | embedded || X terminal'
p1428
(lp1429
S'HP Entria II X station'
p1430
asS'Cray | UNICOS || general purpose'
p1431
(lp1432
S'Cray UNICOS 9.0 - 10.0 or UNICOS/mk 1.5.1'
p1433
aS'Cray UNICOS 9.0.1ai - 10.0.0.2'
p1434
asS'GrandStream | embedded || VoIP phone'
p1435
(lp1436
S'Grandstream BT-100 IP Phone'
p1437
aS'GrandStream BT-100 IP Phone'
p1438
aS'Grandstream BT-101 IP phone'
p1439
aS'GrandStream BT-101 IP phone'
p1440
aS'Grandstream BudgeTone 101 IP Phone'
p1441
aS'Grandstream IP Phone'
p1442
aS'GrandStream VoIP Phone (BudgeTone-100)'
p1443
aS'Grandstream VoIP Phone (BudgeTone-101)'
p1444
asS'ACC | embedded || router'
p1445
(lp1446
S'ACC Amazon 9.2.29 or Congo 9.2.35 WAN concentrator'
p1447
asS'Siemens | SINIX || general purpose'
p1448
(lp1449
S'Siemens SINIX-N 5.41C0005'
p1450
aS'Siemens SINIX-N 5.43C3002'
p1451
aS'Siemens SINIX-Y 5.43B0045'
p1452
aS'Siemens SINIX-Y 5.43C4001'
p1453
asS'Cisco | PIX | 5.X | firewall'
p1454
(lp1455
S'Cisco PIX Firewall (PixOS 5.2 - 6.1)'
p1456
aS'Cisco Secure PIX Firewall Version 5.0(2)'
p1457
asS'D-Link | embedded || webcam'
p1458
(lp1459
S'D-Link DCS-1000 webcam with firmware 1.06'
p1460
aS'D-Link dcs-5300w Wireless WebCam'
p1461
aS'D-Link DVC-1000 Wireless Broadband VideoPhone'
p1462
asS'Cisco | CacheOS || web proxy'
p1463
(lp1464
S'Cisco CacheOS (1.1.0)'
p1465
asS'Smoothwall | Linux | 2.2.X | firewall'
p1466
(lp1467
S'Smoothwall Linux-based firewall 2.2.23'
p1468
asS'IBM | embedded || storage-misc'
p1469
(lp1470
S'IBM 3494 Magnetic Tape Library'
p1471
asS'Apple | Mac OS X | 10.2.X | general purpose'
p1472
(lp1473
S'Apple Mac OS X 10.1.5-10.2.8'
p1474
aS'Apple Mac OS X 10.2.6'
p1475
aS'Apple Mac OS X 10.2.6 (Jaguar)'
p1476
aS'Apple Mac OS X 10.2.8 (Jaguar)'
p1477
aS'Apple Mac OS X Server 10.2.8'
p1478
asS'Softek | embedded || specialized'
p1479
(lp1480
S'Softek Digi One serial device server'
p1481
asS'Asante | embedded || hub'
p1482
(lp1483
S'Asante FriendlyNet FR3004 Series Internet Hub'
p1484
aS'AsanteHub 2072 Ethernet hub'
p1485
asS'NetApp | Data ONTAP || fileserver'
p1486
(lp1487
S'NetApp Data ONTAP 3.1.6 or BSDi 1.1'
p1488
aS'NetApp Data ONTAP 5.1.2 - 5.3.5r2'
p1489
aS'NetApp Data ONTAP 6.1.2R3 on an F840 filer'
p1490
aS'NetApp Data ONTAP Release 6.3.1'
p1491
aS'NetApp F360 or F760 Filer'
p1492
aS'NetApp ONTAP Release 6.3.3'
p1493
aS'Network Appliance Filer running Data ONTAP Release 6.4.3'
p1494
asS'Microsoft | Windows Longhorn || general purpose'
p1495
(lp1496
S'Microsoft Windows Longhorn Preview'
p1497
asS'Cisco | PIX | 6.X | firewall'
p1498
(lp1499
S'Cisco Firewall (PIX 6.1.4 - 6.2.2)'
p1500
aS'Cisco PIX 501 firewall running PIX 6.1(1)'
p1501
aS'Cisco PIX 515 or 525 Firewall running 6.1(4) - 6.2(1)'
p1502
aS'Cisco PIX Firewall Version 6.1(2)'
p1503
aS'Cisco PIX Firewall Version 6.2(1)'
p1504
aS'Cisco PIX Firewall Version 6.2(2) - 6.3'
p1505
asS'Chase | embedded || terminal server'
p1506
(lp1507
S'Chase IOLan Terminal Server'
p1508
aS'Chase/Perle IOLAN Terminal Server'
p1509
aS'Chase/Perle IOLAN terminal server'
p1510
asS'ZyXel | ZyNOS || WAP'
p1511
(lp1512
S'ZyXel ZyAir B-4000 Wireless Lan Access Point'
p1513
asS'NetSilicon | ThreadX || specialized'
p1514
(lp1515
S'NetSilicon NetARM running ThreadX 2.0'
p1516
asS'Leunig | embedded || power-device'
p1517
(lp1518
S'Leunig ePower Switch b723 v5.2'
p1519
asS'Clipcomm | embedded || VoIP phone'
p1520
(lp1521
S'Clipcomm CP-100 VoIP phone'
p1522
asS'BayTech | embedded || power-device'
p1523
(lp1524
S'BayTech Remote Power Control RPC3-15NC or RPC4'
p1525
asS'Microsoft | Windows | PocketPC/CE | specialized'
p1526
(lp1527
S'Microsoft Windows CE 3.0'
p1528
aS'Microsoft Windows CE or Pocket PC (PDA or other embedded device)'
p1529
asS'Cisco | embedded || router'
p1530
(lp1531
S'Cisco Router C2600 running IOS 12.2(2)T'
p1532
aS'Cisco X.25/TCP/LAT Protocol Translator ver 8.2(4)'
p1533
asS'Cantillion | embedded || switch'
p1534
(lp1535
S'Alteon AceSwitch 110 or Cantillion C100 ATM Switch'
p1536
asS'Wooksung | embedded || telecom-misc'
p1537
(lp1538
S'Wooksung TelePhoSee WVP-2100 teleconference system'
p1539
asS'Alcatel | embedded || telecom-misc'
p1540
(lp1541
S'Alcatel OmniPcx 4400 telephone system'
p1542
asS'APC | embedded || power-device'
p1543
(lp1544
S'APC MasterSwitch Network Power Controller'
p1545
aS'APC Network management Card AP9616'
p1546
aS'APC network-enabled UPS'
p1547
aS'APC UPS Network Management Card'
p1548
aS'APC UPS system'
p1549
aS'APC UPS System network management card (runs AOS v2.5.3)'
p1550
aS'APC Web/SNMP UPS management card'
p1551
asS'Sony | embedded || robotic pet'
p1552
(lp1553
S'Sony AIBO ERS-7 running AIBO Mind 2'
p1554
asS'Be | BeOS | 4.X | general purpose'
p1555
(lp1556
S'BeOS 4 - 4.5'
p1557
asS'Intel | embedded || firewall'
p1558
(lp1559
S'Intel NetStructure 3110 VPN Gateway'
p1560
asS'Hawking | embedded || print server'
p1561
(lp1562
S'Hawking PS12U Embedded Print Server'
p1563
asS'BinTec | embedded || broadband router'
p1564
(lp1565
S'BinTEC BIANCA/BRIK-XS Broadband router V. 6.X'
p1566
aS'BinTec BingoDSL/X4000 Router Firmware V. 7.1'
p1567
aS'BinTec XS/XM ISDN access router V. 4.9.1-4.9.3'
p1568
aS'VPN Access 25 version V. 7.1'
p1569
asS'FreeBSD | FreeBSD | 3.X | general purpose'
p1570
(lp1571
S'FreeBSD 3.4-RELEASE'
p1572
asS'Apple | Mac OS X | 10.1.X | general purpose'
p1573
(lp1574
S'Apple Mac OS X 10.1 - 10.1.4'
p1575
aS'Apple Mac OS X 10.1.4 (Darwin Kernel 5.4) on iMac'
p1576
aS'Apple Mac OS X 10.1.5'
p1577
aS'Apple Mac OS X Server 10.1.2 (ppc)'
p1578
asS'SMC | embedded || broadband router'
p1579
(lp1580
S'SMC Barricade SMC7004VR2.0EU DSL router'
p1581
asS'Dell | embedded || storage-misc'
p1582
(lp1583
S'Dell Powervault 132T Automated Tape Library'
p1584
aS'Dell Powervault 132T Automated Tape Library'
p1585
aS'Dell Tape Library MSL6030'
p1586
asS'Siemens | embedded || VoIP phone'
p1587
(lp1588
S'Siemens HiCom 300E business phone system Release 6.5'
p1589
asS'Necomm | embedded || broadband router'
p1590
(lp1591
S'Necomm NB1300 DSL router'
p1592
asS'3Com | ComOS || terminal server'
p1593
(lp1594
S'ComOS based terminal server - Livingston PortMaster or U.S. Robotics/3Com Total Control'
p1595
asS'Microsoft | Windows | 95/98/ME | general purpose'
p1596
(lp1597
S'Microsoft Windows for Workgroups 3.11 / TCP/IP-32 3.11b stack or Windows 98'
p1598
aS'Microsoft Windows 95 4.00.950'
p1599
aS'Microsoft Windows 95 4.00.950B'
p1600
aS'Microsoft Windows 95 4.00.950B (IE 5 5.00 2314.1003)'
p1601
aS'Microsoft Windows 98'
p1602
aS'Microsoft Windows 98'
p1603
aS'Microsoft Windows 98 4.10.1998'
p1604
aS'Microsoft Windows 98 4.10.1998'
p1605
aS'Microsoft Windows 98 or 98SE'
p1606
aS'Microsoft Windows 98 SP1'
p1607
aS'Microsoft Windows 98 SP2'
p1608
aS'Microsoft Windows 98SE'
p1609
aS'Microsoft Windows 98SE'
p1610
aS'Microsoft Windows 98SE'
p1611
aS'Microsoft Windows 98SE'
p1612
aS'Microsoft Windows 98SE'
p1613
aS'Microsoft Windows 98SE'
p1614
aS'Microsoft Windows 98SE + IE5.5sp1'
p1615
aS'Microsoft Windows 98SE SP1'
p1616
aS'Microsoft Windows 98SE with security patch A'
p1617
aS'Microsoft Windows Millennium Edition (Me)'
p1618
aS'Microsoft Windows Millennium Edition (Me)'
p1619
aS'Microsoft Windows Millennium Edition (Me)'
p1620
aS'Microsoft Windows Millennium Edition (Me), Windows 2000, or Windows XP'
p1621
aS'Turtle Beach AudioTron 100 network MP3 player or Microsoft Windows 98SE'
p1622
asS'Linux | Linux | 2.4.X | general purpose'
p1623
(lp1624
S'Astaro Security Linux 4 (Kernel 2.4.19)'
p1625
aS'Gentoo 1.2 linux (Kernel 2.4.19-gentoo-rc5)'
p1626
aS'Linux 2.2.16'
p1627
aS'Linux 2.4.0-test5'
p1628
aS'Linux 2.4.10 - 2.4.18'
p1629
aS'Linux 2.4.16 - 2.4.18'
p1630
aS'Linux 2.4.17 on HP 9000 s700'
p1631
aS'Linux 2.4.18'
p1632
aS'Linux 2.4.18'
p1633
aS'Linux 2.4.18 (PPC)'
p1634
aS'Linux 2.4.18 (x86)'
p1635
aS'Linux 2.4.18 (x86)'
p1636
aS'Linux 2.4.18 - 2.4.19 w/o tcp_timestamps'
p1637
aS'Linux 2.4.18 - 2.4.20'
p1638
aS'Linux 2.4.18 - 2.4.20 (x86)'
p1639
aS'Linux 2.4.18 - 2.4.21 (x86)'
p1640
aS'Linux 2.4.18 - 2.4.27'
p1641
aS'Linux 2.4.19'
p1642
aS'Linux 2.4.19'
p1643
aS'Linux 2.4.19 (Mandrake, X86)'
p1644
aS'Linux 2.4.19 (x86)'
p1645
aS'Linux 2.4.19 - 2.4.20'
p1646
aS'Linux 2.4.19 w/grsecurity patch'
p1647
aS'Linux 2.4.20'
p1648
aS'Linux 2.4.20'
p1649
aS'Linux 2.4.20'
p1650
aS'Linux 2.4.20'
p1651
aS'Linux 2.4.20'
p1652
aS'Linux 2.4.20'
p1653
aS'Linux 2.4.20'
p1654
aS'Linux 2.4.20 (Red Hat)'
p1655
aS'Linux 2.4.20 (X86, Redhat 7.3)'
p1656
aS'Linux 2.4.20 - 2.4.22 w/grsecurity.org patch'
p1657
aS'Linux 2.4.20 x86'
p1658
aS'Linux 2.4.20-ac2'
p1659
aS'Linux 2.4.21'
p1660
aS'Linux 2.4.21 (RedHat)'
p1661
aS'Linux 2.4.21 (RedHat)'
p1662
aS'Linux 2.4.21 (Suse)'
p1663
aS'Linux 2.4.21 (Suse, X86)'
p1664
aS'Linux 2.4.21 (x86 SuSE)'
p1665
aS'Linux 2.4.21 (x86)'
p1666
aS'Linux 2.4.21 (x86, RedHat)'
p1667
aS'Linux 2.4.22'
p1668
aS'Linux 2.4.22 (SPARC)'
p1669
aS'Linux 2.4.22 (x86) w/grsecurity patch and with timestamps disabled'
p1670
aS'Linux 2.4.22 - 2.6.8'
p1671
aS'Linux 2.4.22 or 2.6.4 - 2.6.10'
p1672
aS'Linux 2.4.22-ck2 (x86)   w/grsecurity.org and HZ=1000 patches'
p1673
aS'Linux 2.4.22-gentoo-r2 i686'
p1674
aS'Linux 2.4.22-gentoo-r5 (x86) w/grsecurity'
p1675
aS'Linux 2.4.22-gentoo-rc'
p1676
aS'Linux 2.4.23 (x86)'
p1677
aS'Linux 2.4.23-grsec w/o timestamps'
p1678
aS'Linux 2.4.25 w/grsec (x86)'
p1679
aS'Linux 2.4.26'
p1680
aS'Linux 2.4.26'
p1681
aS'Linux 2.4.26'
p1682
aS'Linux 2.4.26'
p1683
aS'Linux 2.4.26 (gentoo)'
p1684
aS'Linux 2.4.26-gentoo-r6 w/grsec'
p1685
aS'Linux 2.4.27 with grsec'
p1686
aS'Linux 2.4.27 with grsec'
p1687
aS'Linux 2.4.29'
p1688
aS'Linux 2.4.30'
p1689
aS'Linux 2.4.4'
p1690
aS'Linux 2.4.6 - 2.4.26 or 2.6.9'
p1691
aS'Linux 2.4.7 (x86)'
p1692
aS'Linux 2.4.7 (zLinux on OS/390)'
p1693
aS'Linux 2.4.9 - 2.4.18'
p1694
aS'Microsoft Xbox running Debian Linux 2.4.20'
p1695
asS'BenQ | embedded || WAP'
p1696
(lp1697
S'BenQ Wireless Lan Router AWL700'
p1698
asS'Cisco | NmpSW || switch'
p1699
(lp1700
S'Cisco Catalyst 4006 Switch running NmpSW 7.4(2)'
p1701
asS'lwIP | lwIP || general purpose'
p1702
(lp1703
S'lwIP (Lightweight TCP/IP stack) version lwip-0.5.3-win32'
p1704
asS'uIP | uIP || specialized'
p1705
(lp1706
S'Contiki 1.2-devel0 embedded OS on Ethernut card or uIP 0.9 TCP/IP stack'
p1707
asS'Siemens | ReliantUNIX || general purpose'
p1708
(lp1709
S'ReliantUNIX-Y 5.44 B0033 RM600 1/256 R10000'
p1710
aS'Siemens Reliant UNIX 5.45B20'
p1711
aS'Siemens RM200-C40 running ReliantUNIX-N 5.45'
p1712
asS'Linksys | embedded || WAP'
p1713
(lp1714
S'Linksys WAP11 Wireless AP'
p1715
asS'Cisco | embedded || broadband router'
p1716
(lp1717
S'Cisco 761 running c760-in.r.NET3 4.3(1)'
p1718
aS'Cisco 762 Non-IOS Software release 4.1(2) or 766 ISDN router'
p1719
aS'Cisco 766 non-IOS software 4.2(3.5)'
p1720
aS'Cisco Soho 97 router running IOS 12.3(8)'
p1721
asS'Datavoice | embedded || CSUDSU'
p1722
(lp1723
S'Datavoice 3Com WAP or TxPORT PRISM T1 CSU/DSU'
p1724
asS'SGI | IRIX | 6.X | general purpose'
p1725
(lp1726
S'SGI IRIX 6.2'
p1727
aS'SGI IRIX 6.2 - 6.5'
p1728
aS'SGI IRIX 6.2 - 6.5'
p1729
aS'SGI IRIX 6.4 - 6.5.3m  # Lamont Granquist (again :)'
p1730
aS'SGI IRIX 6.5'
p1731
aS'SGI IRIX 6.5 (MIPS)'
p1732
aS'SGI IRIX 6.5 Origin2'
p1733
aS'SGI IRIX 6.5-6.5.15m'
p1734
aS'SGI IRIX 6.5.14'
p1735
aS'SGI IRIX 6.5.15m on SGI O2'
p1736
aS'SGI IRIX 6.5.16m'
p1737
aS'SGI IRIX 6.5.20m'
p1738
aS'SGI IRIX 6.5.20m'
p1739
aS'SGI IRIX 6.5.25'
p1740
aS'SGI IRIX 6.5.7f-6.5.8f'
p1741
aS'SGI IRIX 6.5.7f-6.5.8f'
p1742
asS'Telebit | embedded || router'
p1743
(lp1744
S'Telebit NetBlazer router version 3.0'
p1745
aS'Telebit NetBlazer router Version 3.05'
p1746
aS'Telebit NetBlazer router Version 3.1'
p1747
asS'Sun | Solaris | 7 | general purpose'
p1748
(lp1749
S'Sun Solaris 2.6 - 7 with tcp_strong_iss=0'
p1750
aS'Sun Solaris 2.6 - 7 with tcp_strong_iss=2'
p1751
aS'Sun Solaris 2.6 - 7 x86'
p1752
asS'innovaphone | embedded || telecom-misc'
p1753
(lp1754
S'innovaphone IP200/IP400 VoIP phone/gateway'
p1755
asS'Open Networks | embedded || broadband router'
p1756
(lp1757
S'Open Network 501r or 531r (ADSL Router)'
p1758
asS'Packet8 | embedded || VoIP adapter'
p1759
(lp1760
S'Packet8 BPA410 Broadband Phone Adapter'
p1761
aS'Packet8 DTA310 VoIP/POTS gateway'
p1762
aS'Packet8 DTA310 VoIP/POTS gateway'
p1763
asS'Redback | embedded || broadband router'
p1764
(lp1765
S'Redback SMS 1000-2000 DSL Router'
p1766
asS'Asante | embedded || switch'
p1767
(lp1768
S'Asante 6524-2G GigE switch'
p1769
aS'Asante IntraStack Ethernet Switch (6014 DSB Versions: BP(2.06 ), FW(1.03 ))'
p1770
aS'Asante IntraSwitch 5324'
p1771
aS'Asante IntraSwitch 6216M firmware v2.05A'
p1772
asS'CompUSA | embedded || broadband router'
p1773
(lp1774
S'CompUSA Broadband Router'
p1775
asS'Brother | embedded || printer'
p1776
(lp1777
S'Brother HL-1230 Printer'
p1778
aS'Brother HL-2070N Printer'
p1779
asS'Network Systems | embedded || router'
p1780
(lp1781
S'Network Systems router NS6614 (NSC 6600 series)'
p1782
asS'DEC | IOS | 10.X | router'
p1783
(lp1784
S'Cisco 1601 (IOS 11.0) or DECbrouter90T1 (Runs Cisco IOS 10.2(5))'
p1785
asS'Swissvoice | embedded || VoIP phone'
p1786
(lp1787
S'Swissvoice IP 10S VoIP phone'
p1788
asS'HP | BSD-misc || general purpose'
p1789
(lp1790
S'HP-BSD 2.0'
p1791
asS'Cnet | embedded || broadband router'
p1792
(lp1793
S'Cnet CNIG904B Internet Broadband Gateway firmware version 1.11'
p1794
asS'Checkpoint | IPSO || firewall'
p1795
(lp1796
S'Nokia IPSO 3.2-3.5 Running Checkpoint Firewall-1 or NG FP2'
p1797
aS'Nokia IPSO 3.6 running CheckPoint FW-1 NG FP2'
p1798
asS'Alteon | embedded || switch'
p1799
(lp1800
S'Alteon ACEswitch 184 V. 8.0.49'
p1801
asS'Cisco | IOS | 11.X | switch'
p1802
(lp1803
S'Cisco Router/Switch with IOS 11.2'
p1804
aS'Cisco switch/router with IOS 11.1(7)-11.2(8.10)'
p1805
asS'Ascend | embedded || broadband router'
p1806
(lp1807
S'Ascend DSLPipe DSL-50S-CELL DSL router'
p1808
asS'AXIS | Linux || print server'
p1809
(lp1810
S'AXIS Network Print Server'
p1811
asS'Apple | Mac OS X | 10.0.X | general purpose'
p1812
(lp1813
S'Apple Mac OS X 1.1-1.2 (Rhapsody 5.5-5.6) on a G3'
p1814
aS'Apple Mac OS X Server 1.0-1.0-1 (Rhapsody 5.3 - 5.4)'
p1815
aS'FreeBSD 4.4-5 or Apple Mac OS X 10.0.4 (Darwin V. 1.3-1.3.7 or 4P13)'
p1816
asS'Amiga | AmigaOS || general purpose'
p1817
(lp1818
S'Amiga OS 3.5 (Miami TCP/IP Stack v3.1)'
p1819
aS'AmigaOS 2.1 running AmiTCP4.3'
p1820
aS'AmigaOS 3.1 running Miami Deluxe 0.9m'
p1821
aS'AmigaOS 3.5/3.9 running Miami Deluxe 1.0c'
p1822
aS'AmigaOS AmiTCP/IP 4.3'
p1823
aS'AmigaOS AmiTCP/IP Genesis 4.6'
p1824
aS'AmigaOS Miami 2.1-3.0'
p1825
aS'AmigaOS Miami 3.0'
p1826
aS'AmigaOS Miami 3.1-3.2'
p1827
aS'AmigaOS Miami Deluxe 0.9 - Miami 3.2B'
p1828
asS'Hydra | embedded || load balancer'
p1829
(lp1830
S'Hydra HydraWEB 5000'
p1831
asS'Linksys | embedded || bridge'
p1832
(lp1833
S'Linksys WET-11 Wireless Ethernet bridge'
p1834
aS'Linksys WGA54G Wireless Game Adapter (bridge)'
p1835
asS'm0n0wall | FreeBSD | 5.X | firewall'
p1836
(lp1837
S'M0n0wall 1.2b7 FreeBSD 5.3 based firewall'
p1838
asS'Tandem | Tandem NSK || general purpose'
p1839
(lp1840
S'Tandem NSK D39'
p1841
aS'Tandem NSK D40'
p1842
asS'MikroTik | RouterOS || software router'
p1843
(lp1844
S'MikroTik RouterOS 2.7.20'
p1845
asS'AXIS | embedded || print server'
p1846
(lp1847
S'AXIS 540 Ethernet Print Server ver 5.48'
p1848
aS'AXIS 540 Print Server'
p1849
aS'AXIS 540/542 Print Server v5.30'
p1850
aS'AXIS Print Server firmware 7.0.2'
p1851
asS'Kyocera | embedded || printer'
p1852
(lp1853
S'Kyocera FS-1700+ printer'
p1854
aS'Kyocera IB-21 Printer NIC'
p1855
aS'Kyocera SB-4e printer NIC'
p1856
asS'OpenBSD | OpenBSD | 2.7 | general purpose'
p1857
(lp1858
S'OpenBSD 2.7/SPARC or NFR IDS Appliance ( 12/10/00 )'
p1859
asS'Quantum | embedded || storage-misc'
p1860
(lp1861
S'Quantum Snap server 4100'
p1862
aS'Quantum Snap Server Network Storage Box'
p1863
asS'Tally | embedded || printer'
p1864
(lp1865
S'Tally 9112 Printer'
p1866
aS'Tallycom+ Print Server'
p1867
asS'Apple | A/UX || general purpose'
p1868
(lp1869
S'Apple A/UX 3.1.1 SVR2 or OpenStep 4.2'
p1870
asS'Nokia | embedded || router'
p1871
(lp1872
S'Nokia Rooftop Wireless Router model R240A'
p1873
asS'NEC | UX/4800 || general purpose'
p1874
(lp1875
S'NEC UX/4800'
p1876
asS'Terayon | embedded || broadband router'
p1877
(lp1878
S'Terayon Tj715x cable modem'
p1879
asS'Huawei | VRP || router'
p1880
(lp1881
S'Huawei Quidway R2621 router running VRP 1.5.6(1)'
p1882
aS'Huawei Quidway Router R2621E VRP 1.5.6'
p1883
asS'Ericsson | embedded || terminal server'
p1884
(lp1885
S'Ericsson Tigris Access Server Software V. 12.1.*'
p1886
asS'Perle | embedded || remote management'
p1887
(lp1888
S'Perle 594e Network Controller'
p1889
asS'Netscreen | ScreenOS || firewall'
p1890
(lp1891
S'Netscreen 5XP firewall+vpn (OS 3.0.1r2)'
p1892
aS'Netscreen 5XP firewall+vpn (os 4.0.3r2.0)'
p1893
asS'Cisco | Content Networking System || web proxy'
p1894
(lp1895
S'Cisco ACNS 5.1 Content Engine'
p1896
aS'Cisco Content Engine 505 Software V. 4.2.1'
p1897
aS'Cisco Content Engine 560 running Content Networking System V. 4.2.3'
p1898
aS'Cisco Content Engine ACNSS V5.2.1 or V5.3.1'
p1899
asS'HP | HP-UX | 10.X | general purpose'
p1900
(lp1901
S'HP-UX 10.20 # 9000/777 or A 712/60 with tcp_random_seq = 1 or 2'
p1902
aS'HP-UX 10.20 A 9000/715 or 9000/899'
p1903
aS'HP-UX 10.20 E 9000/777 or A 712/60 with tcp_random_seq = 0'
p1904
aS'HP-UX B.10.01 A 9000/715'
p1905
aS'HP-UX B.10.20 9000/897'
p1906
aS'HP-UX B.10.20 A 9000/715 or 9000/712 or 9000/871 with tcp_random_seq = 1'
p1907
aS'HP-UX B.10.20 A 9000/750'
p1908
aS'HP-UX B.10.20 A with tcp_random_seq = 0'
p1909
aS'HP-UX release B.10.20 version A'
p1910
asS'SonicWall | SonicOS || firewall'
p1911
(lp1912
S'SonicWall 4060 firewall'
p1913
aS'SonicWall PRO 3060 firewall'
p1914
aS'SonicWall SOHO-3 firewall'
p1915
aS'SonicWall SOHO-3 firewall'
p1916
aS'SonicWall SOHO3 firewall'
p1917
aS'SonicWall TZ 170'
p1918
aS'SonicWall TZ 170 Firewall'
p1919
aS'SonicWall TZ170 Firewall'
p1920
aS'SonicWall/10 firewall'
p1921
aS'SonicWall/10 firewall'
p1922
asS'Cisco | PIX || firewall'
p1923
(lp1924
S'Cisco PIX 506 Firewall'
p1925
asS'Meridian | embedded || storage-misc'
p1926
(lp1927
S'Meridian Data Network CD-ROM Server (V4.20 Nov 26 1997)'
p1928
asS'Gandalf | embedded || router'
p1929
(lp1930
S'Gandalf LanLine Router'
p1931
asS'Eicon | embedded || broadband router'
p1932
(lp1933
S'Eicon Diva1830 ISDN router running 1.5 firmware'
p1934
asS'IBM | AIX | 5.X | general purpose'
p1935
(lp1936
S'IBM AIX 5.1'
p1937
aS'IBM AIX 5.1'
p1938
aS'IBM AIX 5.1'
p1939
aS'IBM AIX 5.1 - 5.2'
p1940
aS'IBM AIX 5.1 - 5.2'
p1941
aS'IBM AIX 5.1 on a p610-6C1'
p1942
aS'IBM AIX 5.1-5.2'
p1943
aS'IBM AIX 5.103'
p1944
aS'IBM AIX 5.2'
p1945
aS'IBM AIX 5.2 (on RS/6000)'
p1946
aS'IBM AIX 5.2.3'
p1947
aS'IBM AIX 5.3'
p1948
aS'IBM AIX 5.3 ML01'
p1949
asS'Cisco | IOS | 12.X | broadband router'
p1950
(lp1951
S'Cisco 827 ADSL router running IOS 112.2(11)'
p1952
aS'Cisco 827 ADSL router running IOS 12.1(1)XB1'
p1953
asS'Cisco | embedded || encryption accelerator'
p1954
(lp1955
S'Cisco 3000 Series VPN Concentrator'
p1956
aS'Cisco 3000 Series VPN concentrator (OS ver 4.1.x)'
p1957
asS'Cisco | IOS | 12.X | switch'
p1958
(lp1959
S'Cisco catalyst 2924 running IOS 12.0(5)WC5'
p1960
aS'Cisco Catalyst 2924XL switch running IOS 12.0(5)'
p1961
aS'Cisco Catalyst 2950 switch running IOS 12.0(5.3)WC(1)'
p1962
aS'Cisco Catalyst 2950 switch running IOS 12.1(9)EA1 or IOS 12.1(22)EA2'
p1963
aS'Cisco IOS 12.0(5)WC5a on a catalyst 2900XL switch'
p1964
asS'Apple | Mac OS | 8.X | general purpose'
p1965
(lp1966
S'Apple Mac OS 8 running on an LC 475'
p1967
aS'Apple Mac OS 8.0'
p1968
aS'Apple Mac OS 8.1'
p1969
aS'Apple Mac OS 8.1'
p1970
aS'Apple Mac OS 8.1'
p1971
aS'Apple Mac OS 8.1 running on a PowerPC G3 (iMac)'
p1972
aS'Apple Mac OS 8.5'
p1973
aS'Apple Mac OS 8.5.1 (Appleshare IP 6.0)'
p1974
aS'Apple Mac OS 8.6'
p1975
aS'Apple Mac OS 8.6'
p1976
aS'Apple Mac OS 8.6'
p1977
aS'Apple Mac OS 8.6'
p1978
asS'Beck-IPC | embedded || specialized'
p1979
(lp1980
S'IPC@CHIP CHIP-RTOS version SC12'
p1981
asS'Compatible Systems | embedded || broadband router'
p1982
(lp1983
S'Compatible Systems ISDN/leased-line/dialup Microrouter 2220R w/ firmware v4.5'
p1984
aS'Compatible Systems ISDN/leased-line/dialup MicroRouter 900i v3.0.9'
p1985
asS'SGI | IRIX | 5.X | general purpose'
p1986
(lp1987
S'SGI IRIX 5.2'
p1988
aS'SGI IRIX 5.3'
p1989
asS'FiberLine | embedded || broadband router'
p1990
(lp1991
S'FiberLine Wireless DSL router'
p1992
asS'Microsoft | DOS || general purpose'
p1993
(lp1994
S"Bart's Network Boot Disk 2.7 (X86) MS-DOS"
p1995
aS'NCSA Telnet (dos)'
p1996
aS'NCSA Telnet 2.3.08 for the PC (DOS)'
p1997
aS'Watt-32 DOS tcp/ip stack'
p1998
aS'WNOS 5.0 on Microsoft DOS 6.22'
p1999
asS'Novell | NetWare | 5.X | general purpose'
p2000
(lp2001
S'Novell NetWare 3.12 - 5.00'
p2002
aS'Novell NetWare 4.11-5.0SP5'
p2003
aS'NetWare 5.0 SP 3a'
p2004
aS'NetWare 5.1 SP3'
p2005
aS'Novell NetWare 5.0 with Border Manager'
p2006
aS'Novell NetWare 5.00.09 SP06'
p2007
aS'Novell NetWare 5.1 SP5'
p2008
aS'Novell NetWare 5.1 SP5 with Groupwise'
p2009
aS'Novell NetWare 5.x'
p2010
asS'PowerShow | embedded || webcam'
p2011
(lp2012
S'PowerShow NetworKam webcam'
p2013
asS'Grandstream | embedded || VoIP adapter'
p2014
(lp2015
S'Grandstream HT-286 POTS<->VoIP phone gateway device'
p2016
asS'Ascend | embedded || router'
p2017
(lp2018
S'Ascend Max 1800 50Ap8+ or 2024 router'
p2019
aS'Ascend P130 Router'
p2020
aS'Ascend P75 router'
p2021
aS'Ascend Pipeline 400/T1 (Software V 4.5B)'
p2022
aS'Ascend Pipeline 50'
p2023
aS'Ascend Pipeline 50 rev 4.6C'
p2024
aS'Ascend Pipeline 50 running 5.1A Firmware'
p2025
aS'Ascend Pipeline P130 or 50'
p2026
asS'IBM | embedded || router'
p2027
(lp2028
S'IBM 2210 router'
p2029
aS'IBM 2210 Router MRS 2.x on Token Ring interface'
p2030
aS'IBM 8210 Multiprotocol Switching Server/router for ATM networks'
p2031
asS'Toshiba | embedded || printer'
p2032
(lp2033
S'Toshiba estudio 4511 Multifunction Copier/Fax/Scanner/Printer'
p2034
asS'BreezeCOM | embedded || bridge'
p2035
(lp2036
S'BreezeCOM BreezeACCESS Wireless bridge'
p2037
asS'CacheFlow | CacheOS || web proxy'
p2038
(lp2039
S'CacheFlow 6000 web proxy cache running CacheOS 4.1.05'
p2040
aS'CacheFlow 6000 web proxy running Security Gateway 2.1.0'
p2041
aS'Cacheflow 6x5 web proxy cache running CacheOS 3.1.19-4.1.05'
p2042
aS'CacheFlow CacheOS (web proxy cache) CFOS 2.1.08 - 2.2.1'
p2043
aS'CacheFlow CacheOS 3.1 on a model 6000 web proxy cache'
p2044
aS'CacheOS (CacheFlow 2000 proxy cache)'
p2045
asS'Dell | embedded || printer'
p2046
(lp2047
S'Dell 3100cn/5100cn printer'
p2048
asS'NAT | embedded || router'
p2049
(lp2050
S'NAT LANB/290 router Console Program V4.00'
p2051
asS'Sun | embedded || storage-misc'
p2052
(lp2053
S'Sun StorEdge T3 Storage Array'
p2054
asS'Zcomax | embedded || WAP'
p2055
(lp2056
S'Zcomax Wireless Access Point XI-1500'
p2057
asS'Belkin | embedded || broadband router'
p2058
(lp2059
S'Belkin DSL/Cable Router'
p2060
asS'Cyclades | Cyros || router'
p2061
(lp2062
S'Cyclades PathRouter V 1.2.4'
p2063
asS'Wiesemann & Theis | embedded || specialized'
p2064
(lp2065
S'WuT Web Thermometer'
p2066
asS'NetApp | embedded || web proxy'
p2067
(lp2068
S'NetApp NetCache C1100 (NetApp 5.1D4)'
p2069
aS'NetApp NetCache C1100 with NetAppliance 5.0'
p2070
aS'NetApp NetCache C6100 (NetApp 5.5)'
p2071
aS'NetApp NetCache C760 os 4.x'
p2072
aS'NetApp NetCache running OS 5.4R2'
p2073
asS'Ixia | embedded || specialized'
p2074
(lp2075
S'Ixia 1600 -- Ixia Socket/Serial TCL traffic generation and analysis server'
p2076
asS'FreeBSD | FreeBSD | 5.X | general purpose'
p2077
(lp2078
S'FreeBSD 5.0-CURRENT (Apr 2002)'
p2079
aS'FreeBSD 5.0-RELEASE'
p2080
aS'FreeBSD 5.0-RELEASE'
p2081
aS'FreeBSD 5.0-RELEASE or -CURRENT (Jan 2003)'
p2082
aS'FreeBSD 5.1-CURRENT (June 2003) on Sparc64'
p2083
aS'FreeBSD 5.1-RELEASE (x86)'
p2084
aS'FreeBSD 5.2'
p2085
aS'FreeBSD 5.2 - 5.3'
p2086
aS'FreeBSD 5.2-CURRENT - 5.3 (x86) with pf scrub all'
p2087
aS'FreeBSD 5.2.1 (SPARC)'
p2088
aS'FreeBSD 5.3'
p2089
aS'FreeBSD 5.3'
p2090
aS'FreeBSD 5.3-RELEASE'
p2091
aS'FreeBSD 5.3-RELEASE'
p2092
aS'FreeBSD 5.3-STABLE'
p2093
aS'FreeBSD 5.3-STABLE'
p2094
aS'FreeBSD 5.4'
p2095
aS'FreeBSD 5.4-RELEASE'
p2096
asS'Gatorbox | GatorShare || bridge'
p2097
(lp2098
S'Sun SunOS 4.1.1 - 4.1.4 (or derivative)'
p2099
asS'SpeedStream | embedded || broadband router'
p2100
(lp2101
S'DSL Router: FlowPoint 144/22XX v3.0.8 or SpeedStream 5851 v4.0.5.1'
p2102
aS'Speedstream 5871 DSL router'
p2103
asS'Pirelli | embedded || broadband router'
p2104
(lp2105
S'Pirelli Microbusiness ADSL router'
p2106
asS'Novell | NetWare | 3.X | general purpose'
p2107
(lp2108
S'Novell NetWare 3.12 or 386 TCP/IP'
p2109
asS'NetMatrix | embedded || general purpose'
p2110
(lp2111
S'IPAD (Internet Protocol Adapter) Model 5000 or V.1.52'
p2112
asS'Nokia | IPSO || firewall'
p2113
(lp2114
S'Nokia IP530 Network Appliance (IPSO 3.4-3.4.2)'
p2115
aS'Nokia IPSO 3.7 running CheckPoint FW-1'
p2116
aS'Nokia IPSO 3.8.x'
p2117
asS'Lexmark | embedded || printer'
p2118
(lp2119
S'Lexmark M412n network printer'
p2120
aS'Lexmark Marknet X2031e printer'
p2121
aS'Lexmark Optra N Laser Printer'
p2122
aS'Lexmark Optra network printer'
p2123
aS'Lexmark Optra printer'
p2124
aS'Lexmark Optra printer w/MarkNet XL Network Adapter'
p2125
aS'Lexmark Optra S Printer'
p2126
aS'Lexmark T520 printer'
p2127
aS'Lexmark T522 printer'
p2128
aS'Lexmark T522/T622 printer'
p2129
asS'IBM | embedded || remote management'
p2130
(lp2131
S'Alcatel Advanced Reflexes IP Phone or IBM x450 remote management console'
p2132
aS'IBM BladeCenter Remote Management Module'
p2133
aS'IBM Remote Supervisor Adapter II'
p2134
asS'NIB | embedded || printer'
p2135
(lp2136
S'NIB 450-E printer network interface'
p2137
asS'Huawei | VRP || switch'
p2138
(lp2139
S'3Com 7700/8800 Switch or Huawei S6506R routing switch VRP 3.10'
p2140
asS'Siemens | embedded || specialized'
p2141
(lp2142
S'Siemens S7-400 programmable logic controller'
p2143
asS'Digitel | embedded || router'
p2144
(lp2145
S'Digitel NetRouter NR3000'
p2146
aS'Digitel NetRouter NR3100'
p2147
asS'Novell | NetWare | 4.X | general purpose'
p2148
(lp2149
S'NetWare 4.11 SP7- 5 SP3A BorderManager 3.5'
p2150
aS'NetWare 4.11 SP8a - NetWare 5 SP4'
p2151
aS'novell netware 4.11'
p2152
asS'Compatible Systems | embedded || router'
p2153
(lp2154
S'Compatible Systems (RISC Router, IntraPort)'
p2155
aS'Broadband Router (Farralon Netopia or Compatible Systems 900i)'
p2156
asS'Apple | Mac OS | 9.X | general purpose'
p2157
(lp2158
S'Apple Mac OS 7.5.5 - 9'
p2159
aS'Apple Mac OS 9 - 9.1'
p2160
aS'Apple Mac OS 9.2.2'
p2161
aS'Apple MacOS 9.2.2'
p2162
aS'Apple Mac OS 9, or HP-UX 11.00'
p2163
asS'DEC | OpenVMS | 7.X | general purpose'
p2164
(lp2165
S'Compaq Tru64 UNIX 5.0 or DEC OpenVMS 7.2'
p2166
aS'DEC OpenVMS 6.2 - 7.2-1 on VAX or AXP'
p2167
aS'DEC OpenVMS 7.1'
p2168
aS'DEC OpenVMS 7.1 ALPHA'
p2169
aS"DEC OpenVMS 7.1 Alpha running DIGITAL's UCX v4.1ECO2 TCP/IP package"
p2170
aS"DEC OpenVMS 7.1 using Process Software's TCPWare 5.3 TCP/IP package"
p2171
aS'DEC OpenVMS 7.2'
p2172
aS'DEC OpenVMS 7.2'
p2173
aS'DEC OpenVMS 7.2 Alpha'
p2174
aS'DEC OpenVMS 7.3'
p2175
aS'DEC OpenVMS 7.3 (Alpha) TCP/IP 5.3'
p2176
aS'DEC OpenVMS 7.3 (Compaq TCP/IP 5.3)'
p2177
aS'DEC OpenVMS 7.3-1'
p2178
aS'DEC OpenVMS Alpha 7.2-3'
p2179
aS'DEC OpenVMS Alpha V7.1-1H2 running DIGITAL TCP/IP Services (UCX) V4.2'
p2180
aS'DEC OpenVMS V7.1 on VAX 6000-530'
p2181
aS"DEC OpenVMS v7.1 VAX running Process Software's TCPWare 5.1-5 TCP/IP package"
p2182
aS'DEC OpenVMS v7.3 on VAXStation 4000/60'
p2183
aS'DEC OpenVMS VAX V7.3, Process Software MultiNet V5.0'
p2184
aS"DEC OpenVMS/Alpha 7.1 using Process Software's TCPWare V5.3-4"
p2185
aS'DEC VMS MultiNet V4.2(16)/ OpenVMS V7.1-2'
p2186
aS'DEC VMS MultiNet V4.4 / OpenVMS V7.1'
p2187
asS'Sequent | DYNIX || general purpose'
p2188
(lp2189
S'Sequent DYNIX/PTX 4.4.2'
p2190
aS'Sequent DYNIX/ptx 4.4.6 x86'
p2191
asS'Data General | DG/UX || general purpose'
p2192
(lp2193
S'Data General DG/UX Release R4.11MU02'
p2194
aS'Data General DG/UX Release R4.20MU02'
p2195
aS'Data General DG/UX Release R4.20MU04'
p2196
aS'Data General DG/UX Release R4.20MU06'
p2197
asS'ASCOM | embedded || broadband router'
p2198
(lp2199
S'FlowPoint/2000 - 2200 SDSL Router (v1.2.3 - 3.0.4) or ASCOM Timeplex Access Router'
p2200
asS'CastleNet | embedded || broadband router'
p2201
(lp2202
S'CastleNet AR502/GlobespanVirata GS8100 (same thing) DSL router'
p2203
asS'OpenBSD | OpenBSD | 2.X | general purpose'
p2204
(lp2205
S'OpenBSD 2.1 - 2.3/SPARC'
p2206
aS'OpenBSD 2.1/x86'
p2207
aS'OpenBSD 2.2 - 2.3'
p2208
aS'OpenBSD 2.6 with all available patches as of roughly Feb01'
p2209
aS'OpenBSD 2.6-2.8'
p2210
aS'OpenBSD 2.6-2.8'
p2211
aS'OpenBSD 2.8 (x86)'
p2212
aS'OpenBSD 2.9-beta through release (x86)'
p2213
aS'OpenBSD 2.9-stable'
p2214
aS'OpenBSD Post 2.4 (November 1998) - 2.5'
p2215
asS'VegaStream | embedded || VoIP gateway'
p2216
(lp2217
S'Vega 50/400'
p2218
asS'NetJet | embedded || printer'
p2219
(lp2220
S'NetJet Version 3.0 - 4.0 Printer'
p2221
asS'DEC | Ultrix || general purpose'
p2222
(lp2223
S'DEC Ultrix 4.1'
p2224
aS'DEC Ultrix 4.2 - 4.5'
p2225
asS'Apple | Mac OS | 7.X | general purpose'
p2226
(lp2227
S'Apple Mac OS 7.0-7.1 With MacTCP 1.1.1 - 2.0.6'
p2228
aS'Apple Mac OS 7.1'
p2229
asS'GNU | Hurd || general purpose'
p2230
(lp2231
S'GNU Hurd 0.2 (GNUmach-1.2/Hurd-0.2) x86'
p2232
asS'Motorola | VxWorks || broadband router'
p2233
(lp2234
S'Motorola SurfBoard 4401 cable modem'
p2235
aS'Motorola SurfBoard SB4100E Cable Modem'
p2236
aS'Motorola Surfboard SB5100 cable modem'
p2237
aS'Motorola SURFboard SBG1000 Broadband router'
p2238
asS'Avaya | embedded || telecom-misc'
p2239
(lp2240
S'Avaya TN2302 Prowler/Medpro H.323 gateway'
p2241
asS'Pigtail | VxWorks || VoIP phone'
p2242
(lp2243
S'Pigtail Express VoIP phone (runs VxWorks)'
p2244
asS'D-Link | embedded || WAP'
p2245
(lp2246
S'D-Link DI-713P WAP'
p2247
aS'D-Link DI-713P Wireless Gateway (2.57 build 3a)'
p2248
aS'D-Link DI-774 WAP'
p2249
aS'D-Link DWL-5000AP WAP/BSP 1.3'
p2250
aS'Wireless access point (WAP): D-Link DRC-1000AP or 3Com Access Point 2000'
p2251
asS'Edimax | embedded || print server'
p2252
(lp2253
S'Edimax PS-1001 Print Server model'
p2254
aS'Edimax PS-901 Print Server model 1P/13E-9.5.12'
p2255
asS'Perle | embedded || terminal server'
p2256
(lp2257
S'Perle JetStream 8500 Serial/Access Server, v 2.6.0'
p2258
asS'IBM | OS/2 || general purpose'
p2259
(lp2260
S'IBM OS/2 V 2.1'
p2261
aS'IBM OS/2 V.3'
p2262
aS'IBM OS/2 Warp 4.0'
p2263
aS'IBM OS/2 Warp Server for E-business (Aurora) Beta'
p2264
aS'IBM OS/2 Warp Server for E-business (Aurora) Beta'
p2265
aS'OS/2 Warp Server for eBusiness 4.52'
p2266
asS'UTStarcom | embedded || VoIP phone'
p2267
(lp2268
S'UTStarcom F1000 wifi voip phone'
p2269
asS'VersaNet | embedded || terminal server'
p2270
(lp2271
S'VersaNet ISP-Accelerator(TM) Remote Access Server'
p2272
asS'Epson | embedded || printer'
p2273
(lp2274
S'EPSON Ethernet Ver. 4.20 6.04, 13395E-98'
p2275
aS'Epson Stylus 800n/EPSON Ethernet Ver. 4.20'
p2276
asS'DEC | embedded || terminal server'
p2277
(lp2278
S'DECserver 700-16 terminal server, Network Access SW V2.2'
p2279
asS'Siemens | embedded || broadband router'
p2280
(lp2281
S'Siemens Broadband Router 5940 T1/E1'
p2282
aS'Siemens Santis 50 Wireless adsl router'
p2283
aS'Siemens Speedstream 2602 DSL/Cable router'
p2284
asS'Pelco | embedded || webcam'
p2285
(lp2286
S'Pelco Network Camera'
p2287
asS'Cyclades | Cyras || router'
p2288
(lp2289
S'Cyclades PathRouter'
p2290
aS'Cyclades PathRouter/PC'
p2291
asS'Capellix | embedded || storage-misc'
p2292
(lp2293
S'Capellix 3000 Modular SAN Switch'
p2294
asS'Packeteer | pSOS || load balancer'
p2295
(lp2296
S'Packeteer PacketShaper 4000 v4.1.3b2 2000-04-05'
p2297
aS'pSOS embedded IP stack, such as Packeteer IP-PacketShaper 2000 V3.1'
p2298
asS'Atari | Atari || general purpose'
p2299
(lp2300
S'Atari Mega STE running JIS-68k 3.0'
p2301
asS'D-Link | embedded || broadband router'
p2302
(lp2303
S'D-Link 2630 Broadband router'
p2304
aS'D-Link 704P Broadband Gateway or DI-713P WAP'
p2305
aS'D-Link DI-604 Broadband router'
p2306
aS'D-Link DI-604 Ethernet Broadband Router'
p2307
aS'D-Link DI-604 Ethernet router'
p2308
aS'D-Link DI-701, Version 2.22'
p2309
aS'D-Link DI-704 cable/DSL residential gateway, firmware 2.50 build 9'
p2310
aS'D-Link DI-704P Cable/DSL Residential Gateway'
p2311
aS'D-Link DI-804 Cable/DSL Residential Gateway'
p2312
aS'D-Link DSL-300G+ DSL modem'
p2313
aS'D-Link DSL-500 DSL modem'
p2314
aS'D-Link DSL-500 DSL modem'
p2315
aS'D-Link Systems DI-713P Wireless Gateway'
p2316
aS'D-Link VPN Router DI-714P+/DI-804HV'
p2317
aS'DI-701 Residential Gateway or KA9Q NOS - KO4KS-TNOS v. 2.30'
p2318
aS'Linux 2.4.27 or D-Link DSL-500T (running linux 2.4)'
p2319
asS'Cayman | embedded || broadband router'
p2320
(lp2321
S'Cayman 2E DSL/CABLE router'
p2322
aS'Cayman 3000 DSL Router'
p2323
aS'Netopia Cayman 3346 DSL router'
p2324
asS'Nortel | embedded || telecom-misc'
p2325
(lp2326
S'Nortel Micronode telephone switch running OS version GSM15'
p2327
aS'Nortel Passport 4400 Series multiservice access switch'
p2328
asS'AtheOS | AtheOS || general purpose'
p2329
(lp2330
S'AtheOS ( www.atheos.cx )'
p2331
aS'AtheOS/Syllable 0.4.2'
p2332
asS'BSDI | BSD/OS | 2.X | general purpose'
p2333
(lp2334
S'BSDI BSD/OS 2.0 - 2.1'
p2335
asS'Okidata | embedded || printer'
p2336
(lp2337
S'OkiData 20nx printer with OkiLAN ethernet module'
p2338
aS'Okidata 7200 Printer'
p2339
aS'Okidata OKI C5100 Laser Printer'
p2340
aS'Okidata OKI C7200 Printer'
p2341
asS'Labtam | embedded || X terminal'
p2342
(lp2343
S'Labtam MT300, X-Terminal Kernel'
p2344
asS'Megabit | embedded || terminal server'
p2345
(lp2346
S'MegaBit Gear TE4111C modem'
p2347
asS'Tahoe | Tahoe OS || router'
p2348
(lp2349
S'Tahoe OS 1.2.1 running on Tahoe router'
p2350
asS'Cisco | IOS | 12.X | WAP'
p2351
(lp2352
S'Cisco 1200 access point (WAP) running IOS 12.2(8)'
p2353
aS'Cisco AP1220 WAP running IOS 12.2(11)'
p2354
asS'Cisco | IOS || router'
p2355
(lp2356
S'Cisco CPA2500 (68030) or 2511 router'
p2357
aS'Cisco uBR 7223 router'
p2358
asS'Signal | embedded || VoIP gateway'
p2359
(lp2360
S'CPV Telsey Broadband + voip residential gateway or Signal SP100x VoIP appliance'
p2361
asS'Secure Computing | embedded || firewall'
p2362
(lp2363
S'Secure Computing SECUREZone Firewall Version 2.0'
p2364
aS'Secure Computing Sidewinder firewall 3.2 update 4'
p2365
aS'Secure Computing Sidewinder firewall 5.2.1.06'
p2366
asS'AudioCodes | embedded || VoIP gateway'
p2367
(lp2368
S'AudioCodes MP-104 VoIP Gateway FXO'
p2369
aS'AudioCodes MP-108 VoIP Gateway FXS'
p2370
asS'Virtual Access | embedded || router'
p2371
(lp2372
S'Virtual Access LinXpeed Pro 120 router running Software 7.4.33CM'
p2373
asS'Planet | embedded || switch'
p2374
(lp2375
S'Planet FGSW-2620VS switch'
p2376
asS'Computone | embedded || terminal server'
p2377
(lp2378
S'Computone Power Rack IntelliServer terminal server Release 1.5.4d'
p2379
asS'DEC | TOPS-20 || general purpose'
p2380
(lp2381
S'DEC TOPS-20 Monitor 7(102540)-1,TD-1'
p2382
aS'DEC TOPS-20 Monitor 7(21733),KL-10 (DEC 2065)'
p2383
asS'Compaq | Windows | PocketPC/CE | terminal'
p2384
(lp2385
S'Compaq T1010 Thin Client Windows CE 2.12'
p2386
asS'Cisco | embedded || hub'
p2387
(lp2388
S'Cisco 1538M HUB running Cisco 1538M EES (1.00.00) or Assured Access Technology ISAS Switch Release-2.3.0 or Thomson Multimedia RCA DCM245 Cable Modem'
p2389
asS'WatchGuard | embedded || firewall'
p2390
(lp2391
S'WatchGuard Firebox 700 firewall'
p2392
aS'WatchGuard Firebox II version 7.00'
p2393
aS'WatchGuard Firebox SOHO 6tc firewall'
p2394
aS'WatchGuard Firebox SOHO V.5-V.6 firewall'
p2395
aS'WatchGuard Firebox X700'
p2396
asS'Sun | Solaris | 10 | general purpose'
p2397
(lp2398
S'Sun Solaris 5.10.1'
p2399
aS'SunOS 5.10 (sparc)'
p2400
aS'SunOS webbox 5.10 Generic'
p2401
asS'IBM | AIX | 4.X | general purpose'
p2402
(lp2403
S'IBM AIX 4.0 - 4.2'
p2404
aS'IBM AIX 4.02.0001.0000'
p2405
aS'IBM AIX 4.1'
p2406
aS'IBM AIX 4.1-4.1.5'
p2407
aS'IBM AIX 4.2'
p2408
aS'IBM AIX 4.2-4.3.3'
p2409
aS'IBM AIX 4.2.X-4.3.3.0'
p2410
aS'IBM AIX 4.3'
p2411
aS'IBM AIX 4.3.1 on a IBM RS/6000 R40'
p2412
aS'IBM AIX 4.3.2.0-4.3.3.0 on an IBM RS/*'
p2413
aS'IBM AIX 4.3.3.0 on an IBM RS/*'
p2414
aS'IBM AIX v4.1 running on a C10'
p2415
aS'IBM AIX v4.2'
p2416
aS'IBM AIX Version 4.3'
p2417
asS'Telindus | embedded || broadband router'
p2418
(lp2419
S'Telindus 11xx ADSL Router'
p2420
asS'QNX | QNX || general purpose'
p2421
(lp2422
S'QNX 4.24 - 4.25 realtime embedded OS'
p2423
aS'QNX 6.00 realtime embedded OS (x86)'
p2424
aS'QNX 6.00 realtime embedded OS (x86)'
p2425
asS'IronPort | AsyncOS || specialized'
p2426
(lp2427
S'IronPort C60 email security appliance'
p2428
asS'Convex | ConvexOS || general purpose'
p2429
(lp2430
S'Convex OS Release 10.1'
p2431
asS'GrandStream | embedded || VoIP adapter'
p2432
(lp2433
S'GrandStream 486 VoIP adapter'
p2434
asS'Novell | NetWare | 6.X | general purpose'
p2435
(lp2436
S'Novell NetWare 5.1-6.0'
p2437
aS'Novell NetWare 5.1SP4 - 6.0'
p2438
aS'Novell NetWare 5.1SP5 - 6.5'
p2439
aS'NetWare 6.5 SP2'
p2440
aS'Novell Netware 6 (no service packs)'
p2441
aS'Novell NetWare 6 SP1'
p2442
aS'Novell NetWare 6 SP2'
p2443
aS'Novell NetWare 6.0 SP3'
p2444
aS'Novell Netware 6.0 SP4'
p2445
aS'Novell Netware 6.5 SP2'
p2446
asS'Xyplex | MAXserver || terminal server'
p2447
(lp2448
S'Xyplex 1600 terminal server running MAXserver V6.0.2 firmware'
p2449
aS'Xyplex Maxserver 1600 Terminal Server'
p2450
asS'Cisco | IOS | 11.X | router'
p2451
(lp2452
S'Cisco 2501/2504/4500 router with IOS Version 10.3(15) - 11.1(20)'
p2453
aS'Cisco 1600/3640/7513 Router (IOS 11.2(14)P)'
p2454
aS'Cisco 4500 router running IOS 11.2(2)'
p2455
aS'Cisco 4500-M router running IOS 11.3(6) IP Plus'
p2456
aS'Cisco 7206 router (IOS 11.1(17)'
p2457
aS'Cisco 7206 running IOS 11.1(24)'
p2458
aS'Cisco IOS v11.14(CA)/12.0.2aT1/v12.0.3T'
p2459
asS'CNT | embedded || storage-misc'
p2460
(lp2461
S'CNT UltraNet EDGE (SAN Router) V. 1.4.1.2'
p2462
asS'Alcatel | embedded || switch'
p2463
(lp2464
S'Alcatel OmniStack switch version 4.3.3 GA'
p2465
asS'Symantec | embedded || firewall'
p2466
(lp2467
S'Symantec Gateway Security 5310 Firewall'
p2468
aS'Symantec Gateway Security 5420 firewall'
p2469
asS'Checkpoint | Windows | NT/2K/XP | firewall'
p2470
(lp2471
S'Check Point FireWall-1 4.0 SP-5 (IPSO build)'
p2472
aS'Checkpoint Firewall-1 on Windows NT 4.0 Server SP4-SP5'
p2473
aS'Checkpoint SecurePlatform NG FP3'
p2474
asS'Cobalt | Linux | 2.0.X | general purpose'
p2475
(lp2476
S'Cobalt Linux 4.0 (Fargo) Kernel 2.0.34C52_SK on MIPS or TEAMInternet Series 100 WebSense'
p2477
asS'Fortinet | embedded || firewall'
p2478
(lp2479
S'Fortinet firewall Fortigate 50A (FortiOS V2.80)'
p2480
aS'Fortinet firewall Fortigate 60'
p2481
asS'Lantronix | embedded || terminal server'
p2482
(lp2483
S'Lantronix Consoleserver 800'
p2484
aS'Lantronix ETS16 terminal server Version V3.4/5(961028)'
p2485
aS'Lantronix ETS16P terminal server Version V3.5/2(970721)'
p2486
aS'Lantronix SCS1600 secure console server version V1.0/2(010620)'
p2487
aS'Lantronix SCS1600 secure console server version V1.0/2(010620)'
p2488
asS'Apple | Newton OS || PDA'
p2489
(lp2490
S'Apple Newton MessagePad 2100, Newton OS 2.1'
p2491
asS'DEC | DIGITAL UNIX | 5.X | general purpose'
p2492
(lp2493
S'DEC OSF1 (AKA Compaq/DIGITAL Tru64 UNIX) Version 5.0.0'
p2494
aS'OSF/1 (AKA Compaq/DIGITAL Tru64 UNIX) 5.60'
p2495
asS'US Robotics | embedded || terminal server'
p2496
(lp2497
S'US Robotics Total Control NETServer Card'
p2498
asS'Intergraph | CLiX || general purpose'
p2499
(lp2500
S'Intergraph CLiX R3.1 Vr.7.6.20 6480'
p2501
aS'Intergraph Workstation (2000 Series) running CLiX R3.1'
p2502
asS'Borderware | embedded || firewall'
p2503
(lp2504
S'Borderware 5.0 Firewall'
p2505
aS'Borderware 5.2 firewall'
p2506
aS'Borderware 6.0.2 firewall'
p2507
asS'IBM | OS/400 | V5 | general purpose'
p2508
(lp2509
S'IBM AS/400 running OS/400 5.1'
p2510
aS'IBM OS/400 V5R1 - V5R2'
p2511
aS'IBM OS/400 V5R1M0'
p2512
aS'IBM OS/400 V5R2M0'
p2513
aS'IBM OS/400 V5R2M0'
p2514
asS'WYSE | WYSE OS || terminal server'
p2515
(lp2516
S'Winterm WYSE System Version 4.2.077'
p2517
aS'WYSE Winterm terminal server'
p2518
asS'SCO | SCO UNIX || general purpose'
p2519
(lp2520
S'SCO Open Desktop 2.0'
p2521
aS'SCO UNIX release 3.2'
p2522
asS'Lantronix | Punix || terminal server'
p2523
(lp2524
S'Lantronix ETS16 terminal server'
p2525
asS'Axent | Windows | NT/2K/XP | firewall'
p2526
(lp2527
S'Axent Raptor Firewall running on Windows NT'
p2528
asS'Thomson | embedded || broadband router'
p2529
(lp2530
S'Thomson THG 520 Cable Modem'
p2531
asS'Aironet | embedded || bridge'
p2532
(lp2533
S'Aironet 630-2400 V3.3P Wireless LAN bridge'
p2534
aS'Aironet Wireless Bridge running firmware V5.0J'
p2535
asS'OpenBSD | OpenBSD | 3.X | general purpose'
p2536
(lp2537
S'OpenBSD 3.0 or 3.3'
p2538
aS'OpenBSD 3.0 SPARC with pf "scrub in all"'
p2539
aS'OpenBSD 3.0-STABLE (x86)'
p2540
aS'OpenBSD 3.1 (x86)'
p2541
aS'OpenBSD 3.1 (x86)'
p2542
aS'OpenBSD 3.1 on an Alpha'
p2543
aS'OpenBSD 3.2 (x86)'
p2544
aS'OpenBSD 3.2 with pf scrub and no-df'
p2545
aS'OpenBSD 3.3'
p2546
aS'OpenBSD 3.3 x86 with pf "scrub in all"'
p2547
aS'OpenBSD 3.3 x86 with pf "scrub in all"'
p2548
aS'OpenBSD 3.4'
p2549
aS'OpenBSD 3.4 (X86)'
p2550
aS'OpenBSD 3.4 x86'
p2551
aS'OpenBSD 3.4 x86 with pf "scrub in all"'
p2552
aS'OpenBSD 3.4 x86 with pf "scrub in all"'
p2553
aS'OpenBSD 3.4-BETA'
p2554
aS'OpenBSD 3.5 or 3.6'
p2555
aS'OpenBSD 3.5 or 3.6'
p2556
aS'OpenBSD 3.5 or 3.6'
p2557
aS'OpenBSD 3.6'
p2558
aS'OpenBSD 3.6'
p2559
aS'OpenBSD 3.6'
p2560
aS'OpenBSD 3.6'
p2561
aS'OpenBSD 3.6'
p2562
aS'OpenBSD 3.6'
p2563
aS'OpenBSD 3.6 (i386)'
p2564
aS'OpenBSD 3.6 x86 with pf "scrub in all"'
p2565
aS'OpenBSD 3.7'
p2566
asS'Panasonic | embedded || webcam'
p2567
(lp2568
S'Panasonic WJ-NT104 Network video device'
p2569
aS'Panasonic network camera or SMC WAP'
p2570
asS'Auspex | AuspexOS || fileserver'
p2571
(lp2572
S'Auspex Fileserver (AuspexOS 1.9.1/SunOS 4.1.4)'
p2573
asS'HP | HP-UX | 7.X | general purpose'
p2574
(lp2575
S'HP-UX 7.0'
p2576
asS'Avocent | embedded || terminal server'
p2577
(lp2578
S'Avocent CPS 1610 serial port server'
p2579
asS'Dell | embedded || switch'
p2580
(lp2581
S'Dell PowerConnect Switch 3324 or 3348'
p2582
aS'Dell PowerConnect Switch 5324'
p2583
aS'Dell PowerConnect Switch running SW V.1.0.0.52'
p2584
asS'QMS | embedded || printer'
p2585
(lp2586
S'QMS Magicolor 2200 DeskLaser printer'
p2587
asS'Conexant | embedded || broadband router'
p2588
(lp2589
S'Conexant ADSL Router'
p2590
aS'Sphairon Turbolink ADSL Modem/Router (AR800C2-B01B)'
p2591
asS'Vanguard | embedded || router'
p2592
(lp2593
S'MOTOROLA VANGUARD 320 IP router running OS version 5.4'
p2594
aS'Motorola Vanguard 320 multi-protocol network access device V5.5 - 5.6'
p2595
asS'Acorn | RISC OS || general purpose'
p2596
(lp2597
S'Acorn RISC OS 3.60 (Acorn TCP/IP Stack 4.07)'
p2598
aS'Acorn RISC OS 3.70 using AcornNet TCP/IP stack or RISC OS 4 (Pace, RISCOS Ltd)'
p2599
asS'Cisco | embedded || load balancer'
p2600
(lp2601
S'Cisco CSS 11501 Content Services Switch'
p2602
aS'Cisco CSS 11501 Content Services Switch'
p2603
aS'Cisco Local Director 420 version 2.1.1'
p2604
aS'Cisco Localdirector load balancer'
p2605
aS'Cisco LocalDirector load balancer'
p2606
asS'Barix | embedded || media device'
p2607
(lp2608
S'Barix Exstreamer network MP3 player'
p2609
asS'NSG | embedded || router'
p2610
(lp2611
S'NSG-300/500 series router running Version 7.6.x'
p2612
asS'Madge | embedded || switch'
p2613
(lp2614
S'Madge Smart Ringswitch'
p2615
asS'Compaq | embedded || remote management'
p2616
(lp2617
S'Compaq Inside Management Board'
p2618
aS'Compaq Integrated Lights Out remote configuration Board'
p2619
aS'Compaq ProLiant DL580 Integrated Lights-Out remote configuration board V1.06'
p2620
asS'F5 Labs | embedded || load balancer'
p2621
(lp2622
S'F5 Labs BIG-IP Load balancer Kernel 4.1.1PTF-03 (x86)'
p2623
aS'F5 Labs BIG-IP load balancer kernel 4.2PTF-05a (x86)'
p2624
asS'BBIagent | Linux | 2.4.X | software router'
p2625
(lp2626
S'BBIagent v1.8.1 software router'
p2627
asS'Xerox | embedded || printer'
p2628
(lp2629
S'Dell Laser Printer 5100cn'
p2630
aS'Xerox 8830 Plotter'
p2631
aS'Xerox Document Centre 440 w/ CentreWare Internet Services'
p2632
aS'Xerox Document Centre ColorSeries 50'
p2633
aS'Xerox DocuPrint C55'
p2634
aS'Xerox Docuprint N2125 network printer'
p2635
aS'Xerox DocuPrint N24/N32/N40 Network Laser Printer'
p2636
aS'Xerox DocuPrint N40'
p2637
as."""

def create_user_dir(user_home):
    log.debug("Create user dir at given home: %s" % user_home)
    user_dir = os.path.join(user_home, base_paths['config_dir'])

    if os.path.exists(user_home) and os.access(user_home, os.R_OK and os.W_OK)\
           and not os.path.exists(user_dir):
        os.mkdir(user_dir)
        log.debug("Umit user dir successfully created! %s" % user_dir)
    else:
        log.warning("No permissions to create user dir!")
        return False

    return dict(user_dir=user_dir,
                config_dir=user_dir,
                config_file=create_umit_conf(user_dir),
                target_list=create_target_list(user_dir),
                recent_scans=create_recent_scans(user_dir),
                scan_profile=create_scan_profile(user_dir),
                profile_editor=create_profile_editor(user_dir),
                options=create_options(user_dir),
                wizard=create_wizard(user_dir))

def create_config_file(user_dir, filename, default_content):
    log.debug("create_config_file %s" % filename)
    
    config_file_path = os.path.join(user_dir, filename)
    if not os.path.exists(config_file_path):
        open(config_file_path, 'w').write(default_content)
    return config_file_path

def create_profile_editor(user_dir):
    return create_config_file(user_dir,
                              base_paths['profile_editor'],
                              profile_editor_content)

def create_recent_scans(user_dir):
    return create_config_file(user_dir,
                              base_paths['recent_scans'],
                              recent_scans_content)

def create_scan_profile(user_dir):
    return create_config_file(user_dir,
                              base_paths['scan_profile'],
                              scan_profile_content)

def create_target_list(user_dir):
    return create_config_file(user_dir,
                              base_paths['target_list'],
                              target_list_content)

def create_umit_conf(user_dir):
    return create_config_file(user_dir,
                              base_paths['config_file'],
                              umit_conf_content)

def create_wizard(user_dir):
    return create_config_file(user_dir,
                              base_paths['wizard'],
                              wizard_content)

def create_options(user_dir):
    return create_config_file(user_dir, base_paths['options'], options_content)

def create_umit_version(user_dir, version):
    return create_config_file(user_dir, base_paths["umit_version"],
                              "%s\n" % version)

def create_services_dump(user_dir):
    return create_config_file(user_dir,
                              base_paths['services_dump'],
                              services_dump_content)

def get_os_classification(user_dir):
    return create_config_file(user_dir,
                              base_paths['os_classification'],
                              os_classification_content)

def get_os_dump(user_dir):
    return create_config_file(user_dir,
                              base_paths['os_dump'],
                              os_dump_content)

if __name__ == "__main__":
    create_user_dir("/home/adriano")
