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

import re
import os
import os.path
import time

from types import StringTypes
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl as Attributes

from umitCore.I18N import _
from umitCore.UmitLogging import log

months = ('',_('January'),
             _('February'),
             _('March'),
             _('April'),
             _('May'),
             _('June'),
             _('July'),
             _('August'),
             _('September'),
             _('October'),
             _('November'),
             _('December'),)

class HostInfo(object):
    def __init__(self, id):
        self.id = id
    
    # Host ID
    def get_id(self):
        if self._id != 0:
            return self._id
        raise Exception("Id was not set yet.")

    def set_id(self, id):
        if type(id) == type(0):
            self._id = id
        elif type(id) in StringTypes:
            try:
                self._id = int(id)
            except:
                raise Exception("Id invalid! Id must be an integer, \
but received this instead: '%s'" % str(id))
        else:
            raise Exception("Id invalid! Id must be an integer, but received \
this instead: '%s'" % str(id))
    
    # TCP SEQUENCE
    def set_tcpsequence(self, sequence):
        if type(sequence) == type([]):
            self._tcpsequence = sequence[0]
        else:
            self._tcpsequence = sequence
    
    def get_tcpsequence(self):
        if self._tcpsequence:
            return self._tcpsequence
        return {}

    # TCPTS SEQUENCE
    def set_tcptssequence(self, sequence):
        if type(sequence) == type([]):
            self._tcptssequence = sequence[0]
        else:
            self._tcptssequence = sequence
    
    def get_tcptssequence(self):
        if self._tcptssequence:
            return self._tcptssequence
        return {}

    # VENDOR
    def get_vendor(self):
        try:return self._mac['vendor']
        except:return _('Unknown')

    # IP ID SEQUENCE
    def set_ipidsequence(self, sequence):
        if type(sequence) == type([]):
            self._ipidsequence = sequence[0]
        else:
            self._ipidsequence = sequence
    
    def get_ipidsequence(self):
        if self._ipidsequence:
            return self._ipidsequence
        return {}

    # OS CLASSES
    def set_osclasses(self, classes):
        self._osclasses = classes
    
    def get_osclasses(self):
        return self._osclasses
    
    # OS MATCH
    def set_osmatch(self, match):
        if type(match) == type([]):
            self._osmatch = match[0]
        else:
            self._osmatch = match
    
    def get_osmatch(self):
        if self._osmatch:
            return self._osmatch
        return {}

    # PORTS USED
    def set_ports_used(self, ports):
        self._ports_used = ports
    
    def get_ports_used(self):
        return self._ports_used

    # UPTIME
    # FORMAT: {"seconds":"", "lastboot":""}
    def set_uptime(self, uptime):
        self._uptime = uptime
    
    def get_uptime(self):
        if self._uptime:
            return self._uptime
        
        # Avoid empty dict return
        return {"seconds":"", "lastboot":""}

    # PORTS
    def set_ports(self, port_list):
        self._ports = port_list
    
    def get_ports(self):
        return self._ports
    def set_extraports(self, port_list):
        self._extraports = port_list
    
    def get_extraports(self):
        return self._extraports
    # HOSTNAMES
    def set_hostnames(self, hostname_list):
        self._hostnames = hostname_list
    
    def get_hostnames(self):
        return self._hostnames

    # IP
    def set_ip_address(self, addr):
        log.warning(_("umitCore.NmapParser.set_ip_address deprecated! Use \
umitCore.NmapParser.set_ip instead."))
        self.set_ip(addr)
    
    def get_ip_address(self):
        log.warning(_("umitCore.NmapParser.get_ip_address deprecated! Use \
umitCore.NmapParser.get_ip instead."))
        return self.get_ip()

    def set_ip(self, addr):
        self._ip = addr

    def get_ip(self):
        return self._ip

    # COMMENT
    def get_comment(self):
        return self._comment
    
    def set_comment(self, comment):
        self._comment = comment

    # MAC
    def set_mac_address(self, addr):
        log.warning(_("umitCore.NmapParser.set_mac_address deprecated! Use \
umitCore.NmapParser.set_mac instead."))
        self.set_mac(addr)
    
    def get_mac_address(self):
        log.warning(_("umitCore.NmapParser.get_mac_address deprecated! Use \
umitCore.NmapParser.get_mac instead."))
        return self.get_mac()

    def set_mac(self, addr):
        self._mac = addr

    def get_mac(self):
        return self._mac

    # IPv6
    def set_ipv6_address(self, addr):
        log.warning(_("umitCore.NmapParser.set_ipv6_address deprecated! Use \
umitCore.NmapParser.set_ipv6 instead."))
        self.set_ipv6(addr)
    
    def get_ipv6_address(self):
        log.warning(_("umitCore.NmapParser.get_ipv6_address deprecated! Use \
umitCore.NmapParser.get_ipv6 instead."))
        return self.get_ipv6()

    def set_ipv6(self, addr):
        self._ipv6 = addr

    def get_ipv6(self):
        return self._ipv6

    # STATE
    def set_state(self, status):
        self._state = status
    
    def get_state(self):
        return self._state

    # HOSTNAME
    def get_hostname(self):
        hostname = ''
        try:
            hostname = self._hostnames[0]['hostname'] + ' '
        except:
            pass

        # FIXME: Check if i can return the 'addr' key directly from get_ip,
        # get_ipv6 and get_mac
        if self.ip:
            hostname += self._ip['addr']
        elif self.ipv6:
            hostname += self._ipv6['addr']
        elif self.mac:
            hostname += self._mac['addr']
        else:
            hostname = _('Unknown Host')
        
        return hostname

    def get_open_ports(self):
        ports = self.get_ports()
        open = 0
        
        for i in ports:
            port = i['port']
            for p in port:
                if re.findall('open', p['port_state']):
                    open+=1
        
        return open
    
    def get_filtered_ports(self):
        ports = self.get_ports()
        extraports = self.get_extraports()
        filtered = 0
        
        for i in ports:
            port = i['port']
            for p in port:
                if re.findall('filtered', p['port_state']):
                    filtered+=1
        for extra in extraports:
            if extra["state"] == "filtered":
                filtered += int(extra["count"])
        return filtered
    
    def get_closed_ports(self):
        ports = self.get_ports()
        extraports = self.get_extraports()
        closed = 0
        
        for i in ports:
            port = i['port']
            for p in port:
                if re.findall('closed', p['port_state']):
                    closed+=1
        for extra in extraports:
            if extra["state"] == "closed":
                closed += int(extra["count"])
        return closed
    
    def get_scanned_ports(self):
        ports = self.get_ports()
        extraports = self.get_extraports()
        scanned = 0
        
        for i in ports:
            port = i['port']
            for p in port:
                scanned+=1
        for extra in extraports:
            scanned += int(extra["count"])
        return scanned

    def get_services(self):
        services = []
        for port in self.ports:
            for p in port.get("port", []):
                services.append({"service_name":p.get("service_name",
                                                      _("unknown")),
                                 "portid":p.get("portid", ""),
                                 "service_version":p.get("service_version",
                                                         _("Unknown version")),
                                 "service_product":p.get("service_product", ""),
                                 "port_state":p.get("port_state", _("Unknown")),
                                 "protocol":p.get("protocol", "")})
        return services

    # Properties
    id = property(get_id, set_id)
    tcpsequence = property(get_tcpsequence, set_tcpsequence)
    osclasses = property(get_osclasses, set_osclasses)
    osmatch = property(get_osmatch, set_osmatch)
    ports = property(get_ports, set_ports)
    ports_used = property(get_ports_used, set_ports_used)
    uptime = property(get_uptime, set_uptime)
    hostnames = property(get_hostnames, set_hostnames)
    tcptssequence = property(get_tcptssequence, set_tcptssequence)
    ipidsequence = property(get_ipidsequence, set_ipidsequence)
    ip = property(get_ip, set_ip)
    ipv6 = property(get_ipv6, set_ipv6)
    mac = property(get_mac, set_mac)
    state = property(get_state, set_state)
    comment = property(get_comment, set_comment)
    services = property(get_services)

    _id = 0
    _tcpsequence = {}
    _osclasses = []
    _osmatch = []
    _ports = []
    _ports_used = []
    _uptime = {}
    _hostnames = []
    _tcptssequence = {}
    _ipidsequence = {}
    _ip = {}
    _ipv6 = {}
    _mac = {}
    _state = ''
    _comment = ''


class ParserBasics(object):
    def __init__ (self):
        self.nmap = {'nmaprun':{},\
                     'scaninfo':[],\
                     'verbose':'',\
                     'debugging':'',\
                     'hosts':[],\
                     'runstats':{}}

    def set_host_comment(self, host_id, comment):
        for host in self.nmap['hosts']:
            if host.id == host_id:
                host.comment = comment
                break
        else:
            raise Exception("Comment could not be saved! Host not \
found at NmapParser!")

    def get_host_comment(self, host_id):
        for host in self.nmap.get('hosts', []):
            if host.id == host_id:
                return host.comment
        else:
            raise Exception("Comment could not be saved! Host not \
found at NmapParser!")

    def get_profile(self):
        return self.nmap['nmaprun'].get('profile', '')

    def set_profile(self, profile):
        self.nmap['nmaprun']['profile'] = profile
    
    def get_profile_name(self):
        return self.nmap['nmaprun'].get('profile_name', '')

    def set_profile_name(self, name):
        self.nmap['nmaprun']['profile_name'] = name
    
    def get_profile_description(self):
        return self.nmap['nmaprun'].get('description', '')

    def set_profile_description(self, description):
        self.nmap['nmaprun']['description'] = description
    
    def get_profile_hint(self):
        return self.nmap['nmaprun'].get('hint', '')

    def set_profile_hint(self, hint):
        self.nmap['nmaprun']['hint'] = hint
    
    def get_profile_annotation(self):
        return self.nmap['nmaprun'].get('annotation', '')

    def set_profile_annotation(self, annotation):
        self.nmap['nmaprun']['annotation'] = annotation
    
    def get_profile_options(self):
        options = self.nmap['nmaprun'].get('options', '')
        if type(options) == type([]):
            return ','.join(options)
        elif type(options) in StringTypes:
            return options

    def set_profile_options(self, options):
        if (type(options) == type([])) or (type(options) in StringTypes):
            self.nmap['nmaprun']['options'] = options
        elif type(options) == type({}):
            self.nmap['nmaprun']['options'] = options.keys()
        else:
            raise Exception("Profile option error: wrong argument format! \
Need a string or list.")
    
    def get_target(self):
        return self.nmap['nmaprun'].get('target', '')

    def set_target(self, target):
        self.nmap['nmaprun']['target'] = target

    def get_nmap_output(self):
        return self.nmap['nmaprun'].get('nmap_output', '')

    def set_nmap_output(self, nmap_output):
        self.nmap['nmaprun']['nmap_output'] = nmap_output
    
    def get_debugging_level (self):
        return self.nmap.get('debugging', '')

    def set_debugging_level(self, level):
        self.nmap['debugging'] = level
    
    def get_verbose_level (self):
        return self.nmap.get('verbose', '')

    def set_verbose_level(self, level):
        self.nmap['verbose'] = level
    
    def get_scaninfo(self):
        return self.nmap.get('scaninfo', '')

    def set_scaninfo(self, info):
        self.nmap['scaninfo'] = info
    
    def get_services_scanned (self):
        if self._services_scanned == None:
            return self._services_scanned
        
        services = []
        for scan in self.nmap.get('scaninfo', []):
            services.append(scan['services'])

        self._services_scanned = ','.join(services)
        return self._services_scanned

    def set_services_scanned (self, services_scanned):
        self._services_scanned = services_scanned

    def get_nmap_command (self):
        return self._verify_output_options(self.nmap['nmaprun'].get('args', ''))

    def set_nmap_command(self, command):
        self.nmap['nmaprun']['args'] = self._verify_output_options(command)

    def get_scan_type (self):
        types = []
        for t in self.nmap.get('scaninfo', []):
            types.append(t['type'])
        return types

    def get_protocol (self):
        protocols = []
        for proto in self.nmap.get('scaninfo', []):
            protocols.append(proto['protocol'])
        return protocols

    def get_num_services (self):
        if self._num_services == None:
            return self._num_services
        
        num = 0
        for n in self.nmap.get('scaninfo', []):
            num += int(n['numservices'])

        self._num_services = num
        return self._num_services

    def set_num_services (self, num_services):
        self._num_services = num_services

    def get_date (self):
        epoch = int(self.nmap['nmaprun'].get('start', '0'))
        return time.localtime (epoch)

    def get_start(self):
        return self.nmap['nmaprun'].get('start', '0')

    def set_start(self, start):
        self.nmap['nmaprun']['start'] = start

    def set_date(self, date):
        if type(date) == type(int):
            self.nmap['nmaprun']['start'] = date
        else:
            raise Exception("Wrong date format. Date should be saved \
in epoch format!")
    
    def get_open_ports(self):
        ports = 0

        for h in self.nmap.get('hosts', []):
            ports += h.get_open_ports()

        return ports

    def get_filtered_ports(self):
        ports = 0

        for h in self.nmap.get('hosts', []):
            ports += h.get_filtered_ports()


        log.debug(">>> EXTRAPORTS: %s" % str(self.list_extraports))

        return ports

    def get_closed_ports(self):
        ports = 0
        
        for h in self.nmap['hosts']:
            ports += h.get_closed_ports()

        return ports

    def get_formated_date(self):
        date = self.get_date()
        return "%s %s, %s - %s:%s" % (months[date[1]], 
                                      str(date[2]), 
                                      str(date[0]),
                                      str(date[3]).zfill(2), 
                                      str(date[4]).zfill(2))

    def get_scanner (self):
        return self.nmap['nmaprun'].get('scanner', '')

    def set_scanner(self, scanner):
        self.nmap['nmaprun']['scanner'] = scanner
    
    def get_scanner_version (self):
        return self.nmap['nmaprun'].get('version', '')

    def set_scanner_version(self, version):
        self.nmap['nmaprun']['version'] = version

    # IPv4
    def get_ipv4_addresses (self):
        log.warning(_("umitCore.NmapParser.get_ipv4_address deprecated! Use \
umitCore.NmapParser.get_ipv4 instead."))
        return self.get_ipv4()

    def get_ipv4(self):
        addresses = []
        for host in self.nmap.get('hosts', []):
            try:
                addresses.append(host.get_ip().get('addr', ''))
            except:
                pass
        
        return addresses

    # MAC
    def get_mac_addresses (self):
        log.warning(_("umitCore.NmapParser.get_mac_address deprecated! Use \
umitCore.NmapParser.get_mac instead."))
        return self.get_mac()

    def get_mac(self):
        addresses = []
        for host in self.nmap.get('hosts', []):
            try:
                addresses.append(host.get_mac().get('addr', ''))
            except:
                pass
        
        return addresses

    # IPv6
    def get_ipv6_addresses (self):
        log.warning(_("umitCore.NmapParser.get_ipv6_address deprecated! Use \
umitCore.NmapParser.get_ipv6 instead."))
        return self.get_ipv6()

    def get_ipv6(self):
        addresses = []
        for host in self.nmap.get('hosts', []):
            try:
                addresses.append(host.get_ipv6().get('addr', ''))
            except:
                pass

        return addresses

    def get_hostnames (self):
        hostnames = []
        for host in self.nmap.get('hosts', []):
            hostnames += host.get_hostnames()
        return hostnames

    def get_ports(self):
        ports = []
        for port in self.nmap.get('hosts', []):
            ports.append(port.get_ports())
        
        return ports

    def get_hosts(self):
        return self.nmap.get('hosts', None)

    def get_runstats(self):
        return self.nmap.get('runstats', None)

    def set_runstats(self, stats):
        self.nmap['runstats'] = stats
    
    def get_hosts_down(self):
        return int(self.nmap['runstats'].get('hosts_down', '0'))

    def set_hosts_down(self, down):
        self.nmap['runstats']['hosts_down'] = int(down)
    
    def get_hosts_up(self):
        return int(self.nmap['runstats'].get('hosts_up', '0'))

    def set_hosts_up(self, up):
        self.nmap['runstats']['hosts_up'] = int(up)
    
    def get_hosts_scanned(self):
        return int(self.nmap['runstats'].get('hosts_scanned', '0'))

    def set_hosts_scanned(self, scanned):
        self.nmap['runstats']['hosts_scanned'] = int(scanned)
    
    def get_finish_time (self):
        return time.localtime(int(self.nmap['runstats'].get('finished_time',
                                                            '0')))

    def set_finish_time(self, finish):
        self.nmap['runstats']['finished_time'] = int(finish)

    def get_finish_epoc_time(self):
        return int(self.nmap['runstats'].get('finished_time', '0'))

    def set_finish_epoc_time(self, time):
        self.nmap['runstats']['finished_time'] = time

    def get_scan_name(self):
        return self.nmap.get("scan_name", "")

    def set_scan_name(self, scan_name):
        self.nmap["scan_name"] = scan_name
    
    def get_formated_finish_date(self):
        date = self.get_finish_time()
        return "%s %s, %s - %s:%s" % (months[date[1]], 
                                      str(date[2]), 
                                      str(date[0]),
                                      str(date[3]).zfill(2), 
                                      str(date[4]).zfill(2))

    def _verify_output_options (self, command):
        found = re.findall ('(-o[XGASN]{1}) {0,1}', command)
        splited = command.split (' ')
        
        if found:
            for option in found:
                pos = splited.index(option)
                del(splited[pos+1])
                del(splited[pos])
        
        return ' '.join (splited)

    def get_comments(self):
        return [host.comment for host in self.nmap['hosts']]

    profile = property(get_profile, set_profile)
    profile_name = property(get_profile_name, set_profile_name)
    profile_description = property(get_profile_description, 
                                   set_profile_description)
    profile_hint = property(get_profile_hint, set_profile_hint)
    profile_annotation = property(get_profile_annotation, 
                                  set_profile_annotation)
    profile_options = property(get_profile_options, set_profile_options)
    target = property(get_target, set_target)
    nmap_output = property(get_nmap_output, set_nmap_output)
    debugging_level = property(get_debugging_level, set_debugging_level)
    verbose_level = property(get_verbose_level, set_verbose_level)
    scaninfo = property(get_scaninfo, set_scaninfo)
    services_scanned = property(get_services_scanned, set_services_scanned)
    nmap_command = property(get_nmap_command, set_nmap_command)
    scan_type = property(get_scan_type)
    protocol = property(get_protocol)
    num_services = property(get_num_services, set_num_services)
    date = property(get_date, set_date)
    open_ports = property(get_open_ports)
    filtered_ports = property(get_filtered_ports)
    closed_ports = property(get_closed_ports)
    formated_date = property(get_formated_date)
    scanner = property(get_scanner, set_scanner)
    scanner_version = property(get_scanner_version, set_scanner_version)
    ipv4 = property(get_ipv4)
    mac = property(get_mac)
    ipv6 = property(get_ipv6)
    hostnames = property(get_hostnames)
    ports = property(get_ports)
    hosts = property(get_hosts)
    runstats = property(get_runstats, set_runstats)
    hosts_down = property(get_hosts_down, set_hosts_down)
    hosts_up = property(get_hosts_up, set_hosts_up)
    hosts_scanned = property(get_hosts_scanned, set_hosts_scanned)
    finish_time = property(get_finish_time, set_finish_time)
    finish_epoc_time = property(get_finish_epoc_time, set_finish_epoc_time)
    formated_finish_date = property(get_formated_finish_date)
    comments = property(get_comments)
    start = property(get_start, set_start)
    scan_name = property(get_scan_name, set_scan_name)

    _num_services = None
    _services_scanned = None


class NmapParserSAX(ParserBasics, ContentHandler):
    def __init__(self):
        ParserBasics.__init__(self)
        self.id_sequence = 0

        self.in_run_stats = False
        self.in_host = False
        self.in_ports = False
        self.in_port = False
        self.in_os = False
        self.list_extraports = []

        self.nmap_xml_file = None
        self.unsaved = False

    def set_parser(self, parser):
        self.parser = parser

    def set_xml_file(self, nmap_xml_file):
        self.nmap_xml_file = nmap_xml_file

    def parse(self):
        if self.nmap_xml_file:
            if type(self.nmap_xml_file) in StringTypes:
                self.parser.parse(self.nmap_xml_file)
            else:
                log.debug(">>> XML content: %s" % self.nmap_xml_file.read())
                self.nmap_xml_file.seek(0)
                self.parser.parse(self.nmap_xml_file)

                # Closing file to avoid problems with file descriptors
                self.nmap_xml_file.close()
        else:
            raise Exception("There's no file to be parsed!")

    def _parse_nmaprun(self, attrs):
        run_tag = "nmaprun"
        
        self.nmap[run_tag]["nmap_output"] = attrs.get("nmap_output", "")
        self.nmap[run_tag]["profile"] = attrs.get("profile", "")
        self.nmap[run_tag]["profile_name"] = attrs.get("profile_name", "")
        self.nmap[run_tag]["hint"] = attrs.get("hint", "")
        self.nmap[run_tag]["description"] = attrs.get("description", "")
        self.nmap[run_tag]["annotation"] = attrs.get("annotation", "")
        self.nmap[run_tag]["options"] = attrs.get("options", "")
        self.nmap[run_tag]["target"] = attrs.get("target", "")
        self.nmap[run_tag]["start"] = attrs.get("start", "")
        self.nmap[run_tag]["args"] = attrs.get("args", "")
        self.nmap[run_tag]["scanner"] = attrs.get("scanner", "")
        self.nmap[run_tag]["version"] = attrs.get("version", "")
        self.nmap[run_tag]["xmloutputversion"] = attrs.get("xmloutputversion", 
                                                           "")
        self.nmap["scan_name"] = attrs.get("scan_name", "")

    def _parse_scaninfo(self, attrs):
        dic = {}
        
        dic["type"] = attrs.get("type", "")
        dic["protocol"] = attrs.get("protocol", "")
        dic["numservices"] = attrs.get("numservices", "")
        dic["services"] = attrs.get("services", "")
        
        self.nmap["scaninfo"].append(dic)

    def _parse_verbose(self, attrs):
        self.nmap["verbose"] = attrs.get("level", "")

    def _parse_debugging(self, attrs):
        self.nmap["debugging"] = attrs.get("level", "")

    def _parse_runstats_finished(self, attrs):
        self.nmap["runstats"]["finished_time"] = attrs.get("time", "")

    def _parse_runstats_hosts(self, attrs):
        self.nmap["runstats"]["hosts_up"] = attrs.get("up", "")
        self.nmap["runstats"]["hosts_down"] = attrs.get("down", "")
        self.nmap["runstats"]["hosts_scanned"] = attrs.get("total", "")

    def generate_id(self):
        self.id_sequence += 1
        return self.id_sequence

    def _parse_host(self, attrs):
        self.host_info = HostInfo(self.generate_id())
        self.host_info.comment = attrs.get("comment", "")

    def _parse_host_status(self, attrs):
        self.host_info.set_state(attrs.get("state", ""))

    def _parse_host_address(self, attrs):
        address_attributes = {"type":attrs.get("addrtype", ""),
                              "vendor":attrs.get("vendor", ""),
                              "addr":attrs.get("addr", "")}

        if address_attributes["type"] == "ipv4":
            self.host_info.set_ip(address_attributes)
        elif address_attributes["type"] == "ipv6":
            self.host_info.set_ipv6(address_attributes)
        elif address_attributes["type"] == "mac":
            self.host_info.set_mac(address_attributes)

    def _parse_host_hostname(self, attrs):
        self.list_hostnames.append({"hostname":attrs.get("name", ""),
                                    "hostname_type":attrs.get("type", "")})

    def _parse_host_extraports(self, attrs):
        self.list_extraports.append({"state":attrs.get("state", ""),
                                     "count":attrs.get("count", "")})

    def _parse_host_port(self, attrs):
        self.dic_port = {"protocol":attrs.get("protocol", ""), 
                         "portid":attrs.get("portid", "")}

    def _parse_host_port_state(self, attrs):
        self.dic_port["port_state"] = attrs.get("state", "")

    def _parse_host_port_service(self, attrs):
        self.dic_port["service_name"] = attrs.get("name", "")
        self.dic_port["service_method"] = attrs.get("method", "")
        self.dic_port["service_conf"] = attrs.get("conf", "")
        self.dic_port["service_product"] = attrs.get("product", "")
        self.dic_port["service_version"] = attrs.get("version", "")
        self.dic_port["service_extrainfo"] = attrs.get("extrainfo", "")

    def _parse_host_osmatch(self, attrs):
        self.host_info.set_osmatch(self._parsing(attrs, ['name', 'accuracy']))

    def _parse_host_portused(self, attrs):
        self.list_portused.append(self._parsing(attrs, 
                                                ['state','proto','portid']))

    def _parse_host_osclass(self, attrs):
        self.list_osclass.append(self._parsing(attrs, ['type',
                                                       'vendor',
                                                       'osfamily',
                                                       'osgen',
                                                       'accuracy']))

    def _parsing(self, attrs, attrs_list):
        # Returns a dict with the attributes of a given tag with the
        # atributes names as keys and their respective values
        dic = {}
        for at in attrs_list:
            dic[at] = attrs.get(at, "")
        return dic

    def _parse_host_uptime(self, attrs):
        self.host_info.set_uptime(self._parsing(attrs, ["seconds", "lastboot"]))


    def _parse_host_tcpsequence(self, attrs):
        self.host_info.set_tcpsequence(self._parsing(attrs, ['index',
                                                             'class',
                                                             'difficulty',
                                                             'values']))
    
    def _parse_host_tcptssequence(self, attrs):
        self.host_info.set_tcptssequence(self._parsing(attrs, ['class',
                                                               'values']))

    def _parse_host_ipidsequence(self, attrs):
        self.host_info.set_ipidsequence(self._parsing(attrs, ['class',
                                                              'values']))

    def startElement(self, name, attrs):
        if name == "nmaprun":
            self._parse_nmaprun(attrs)
        elif name == "scaninfo":
            self._parse_scaninfo(attrs)
        elif name == "verbose":
            self._parse_verbose(attrs)
        elif name == "debugging":
            self._parse_debugging(attrs)
        elif name == "runstats":
            self.in_run_stats = True
        elif self.in_run_stats and name == "finished":
            self._parse_runstats_finished(attrs)
        elif self.in_run_stats and name == "hosts":
            self._parse_runstats_hosts(attrs)
        elif name == "host":
            self.in_host = True
            self._parse_host(attrs)
            self.list_ports = []
        elif self.in_host and name == "status":
            self._parse_host_status(attrs)
        elif self.in_host and name == "address":
            self._parse_host_address(attrs)
        elif self.in_host and name == "hostnames":
            self.in_hostnames = True
            self.list_hostnames = []
        elif self.in_host and self.in_hostnames and name == "hostname":
            self._parse_host_hostname(attrs)
        elif self.in_host and name == "ports":
            self.list_extraports = []
            self.list_port = []
            self.in_ports = True
        elif self.in_host and self.in_ports and name == "extraports":
            self._parse_host_extraports(attrs)
        elif self.in_host and self.in_ports and name == "port":
            self.in_port = True
            self._parse_host_port(attrs)
        elif self.in_host and self.in_ports and \
             self.in_port and name == "state":
            self._parse_host_port_state(attrs)
        elif self.in_host and self.in_ports and \
             self.in_port and name == "service":
            self._parse_host_port_service(attrs)
        elif self.in_host and name == "os":
            self.in_os = True
            self.list_portused = []
            self.list_osclass = []
        elif self.in_host and self.in_os and name == "osmatch":
            self._parse_host_osmatch(attrs)
        elif self.in_host and self.in_os and name == "portused":
            self._parse_host_portused(attrs)
        elif self.in_host and self.in_os and name == "osclass":
            self._parse_host_osclass(attrs)
        elif self.in_host and name == "uptime":
            self._parse_host_uptime(attrs)
        elif self.in_host and name == "tcpsequence":
            self._parse_host_tcpsequence(attrs)
        elif self.in_host and name == "tcptssequence":
            self._parse_host_tcptssequence(attrs)
        elif self.in_host and name == "ipidsequence":
            self._parse_host_ipidsequence(attrs)


    def endElement(self, name):
        if name == "runstats":
            self.in_run_stats = False
        elif name == "host":
            self.in_host = False
            self.host_info.set_ports(self.list_ports)
            self.nmap["hosts"].append(self.host_info)
            del(self.list_ports)
        elif self.in_host and name == "hostnames":
            self.in_hostnames = False
            self.host_info.set_hostnames(self.list_hostnames)
        elif self.in_host and name == "ports":
            self.in_ports = False
            self.list_ports.append({"extraports":self.list_extraports,
                                    "port":self.list_port})
            self.host_info.set_extraports(self.list_extraports)
        elif self.in_host and self.in_ports and name == "port":
            self.in_port = False
            self.list_port.append(self.dic_port)
            del(self.dic_port)
        elif self.in_host and self.in_os and name == "os":
            self.in_os = False
            self.host_info.set_ports_used(self.list_portused)
            self.host_info.set_osclasses(self.list_osclass)

            del(self.list_portused)
            del(self.list_osclass)

    def write_xml(self, xml_file):
        xml_file = self._verify_file(xml_file)
        self.write_parser = XMLGenerator(xml_file)

        # First, start the document:
        self.write_parser.startDocument()

        # Nmaprun element:
        self._write_nmaprun()

        # Scaninfo element:
        self._write_scaninfo()

        # Verbose element:
        self._write_verbose()

        # Debugging element:
        self._write_debugging()

        # Hosts elements:
        self._write_hosts()

        # Runstats element:
        self._write_runstats()

        # End of the xml file:
        self.write_parser.endElement("nmaprun")
        self.write_parser.endDocument()

    def _write_runstats(self):
        ##################
        # Runstats element
        self.write_parser.startElement("runstats", Attributes(dict()))

        ## Finished element
        self.write_parser.startElement("finished",
                        Attributes(dict(time = str(self.finish_epoc_time))))
        self.write_parser.endElement("finished")

        ## Hosts element
        self.write_parser.startElement("hosts",
                            Attributes(dict(up = str(self.hosts_up),
                                            down = str(self.hosts_down),
                                            total = str(self.hosts_scanned))))
        self.write_parser.endElement("hosts")


        self.write_parser.endElement("runstats")
        # End of Runstats element
        #########################

    def _write_hosts(self):
        for host in self.hosts:
            # Start host element
            self.write_parser.startElement("host",
                                Attributes(dict(comment=host.comment)))

            # Status element
            self.write_parser.startElement("status",
                                Attributes(dict(state=host.state)))
            self.write_parser.endElement("status")


            ##################
            # Address elements
            ## IPv4
            if type(host.ip) == type({}):
                self.write_parser.startElement("address",
                            Attributes(dict(addr=host.ip.get("addr", ""),
                                        vendor=host.ip.get("vendor", ""),
                                        addrtype=host.ip.get("type", ""))))
                self.write_parser.endElement("address")

            ## IPv6
            if type(host.ipv6) == type({}):
                self.write_parser.startElement("address",
                            Attributes(dict(addr=host.ipv6.get("addr", ""),
                                        vendor=host.ipv6.get("vendor", ""),
                                        addrtype=host.ipv6.get("type", ""))))
                self.write_parser.endElement("address")

            ## MAC
            if type(host.mac) == type({}):
                self.write_parser.startElement("address",
                            Attributes(dict(addr=host.mac.get("addr", ""),
                                        vendor=host.mac.get("vendor", ""),
                                        addrtype=host.mac.get("type", ""))))
                self.write_parser.endElement("address")
            # End of Address elements
            #########################


            ###################
            # Hostnames element
            self.write_parser.startElement("hostnames", Attributes({}))

            for hname in host.hostnames:
                if type(hname) == type({}):
                    self.write_parser.startElement("hostname",
                            Attributes(dict(name = hname.get("hostname", ""),
                                        type = hname.get("hostname_type", ""))))
                    
                    self.write_parser.endElement("hostname")

            self.write_parser.endElement("hostnames")
            # End of Hostnames element
            ##########################


            ###############
            # Ports element
            self.write_parser.startElement("ports", Attributes({}))

            for ps in host.ports:
                ## Extraports elements
                for ext in ps["extraports"]:
                    if type(ext) == type({}):
                        self.write_parser.startElement("extraports",
                            Attributes(dict(count = ext.get("count", ""),
                                            state = ext.get("state", ""))))
                        self.write_parser.endElement("extraports")

                ## Port elements
                for p in ps["port"]:
                    if type(p) == type({}):
                        self.write_parser.startElement("port",
                            Attributes(dict(portid = p.get("portid", ""),
                                            protocol = p.get("protocol", ""))))

                        ### Port state
                        self.write_parser.startElement("state",
                            Attributes(dict(state=p.get("port_state", ""))))
                        self.write_parser.endElement("state")

                        ### Port service info
                        self.write_parser.startElement("service",
                            Attributes(dict(conf = p.get("service_conf", ""),
                                    method = p.get("service_method", ""),
                                    name = p.get("service_name", ""),
                                    product = p.get("service_product", ""),
                                    version = p.get("service_version", ""),
                                    extrainfo = p.get("service_extrainfo", "")\
                                )))
                        self.write_parser.endElement("service")

                        self.write_parser.endElement("port")

            self.write_parser.endElement("ports")
            # End of Ports element
            ######################


            ############
            # OS element
            self.write_parser.startElement("os", Attributes({}))
            
            ## Ports used elements
            for pu in host.ports_used:
                if type(pu) == type({}):
                    self.write_parser.startElement("portused",
                                Attributes(dict(state = pu.get("state", ""),
                                                proto = pu.get("proto", ""),
                                                portid = pu.get("portid", ""))))
                    self.write_parser.endElement("portused")

            ## Osclass elements
            for oc in host.osclasses:
                if type(oc) == type({}):
                    self.write_parser.startElement("osclass",
                        Attributes(dict(vendor = oc.get("vendor", ""),
                                        osfamily = oc.get("osfamily", ""),
                                        type = oc.get("type", ""),
                                        osgen = oc.get("osgen", ""),
                                        accuracy = oc.get("accuracy", ""))))
                    self.write_parser.endElement("osclass")

            ## Osmatch elements
            if type(host.osmatch) == type({}):
                self.write_parser.startElement("osmatch",
                    Attributes(dict(name = host.osmatch.get("name", ""),
                                accuracy = host.osmatch.get("accuracy", ""))))
                self.write_parser.endElement("osmatch")

            self.write_parser.endElement("os")
            # End of OS element
            ###################

            # Uptime element
            if type(host.uptime) == type({}):
                self.write_parser.startElement("uptime",
                    Attributes(dict(seconds = host.uptime.get("seconds", ""),
                                lastboot = host.uptime.get("lastboot", ""))))
                self.write_parser.endElement("uptime")

            #####################
            # Sequences elementes
            ## TCP Sequence element
            # Cannot use dict() here, because of the 'class' attribute.
            if type(host.tcpsequence) == type({}):
                self.write_parser.startElement("tcpsequence",
                    Attributes({"index":host.tcpsequence.get("index", ""),
                            "class":host.tcpsequence.get("class", ""),
                            "difficulty":host.tcpsequence.get("difficulty", ""),
                            "values":host.tcpsequence.get("values", "")}))
                self.write_parser.endElement("tcpsequence")

            ## IP ID Sequence element
            if type(host.ipidsequence) == type({}):
                self.write_parser.startElement("ipidsequence",
                    Attributes({"class":host.ipidsequence.get("class", ""),
                                "values":host.ipidsequence.get("values", "")}))
                self.write_parser.endElement("ipidsequence")

            ## TCP TS Sequence element
            if type(host.tcptssequence) == type({}):
                self.write_parser.startElement("tcptssequence",
                    Attributes({"class":host.tcptssequence.get("class", ""),
                            "values":host.tcptssequence.get("values", "")}))
                self.write_parser.endElement("tcptssequence")
            # End of sequences elements
            ###########################

            # End host element
            self.write_parser.endElement("host")

    def _write_debugging(self):
        self.write_parser.startElement("debugging", Attributes(dict(
                                            level=str(self.debugging_level))))
        self.write_parser.endElement("debugging")

    def _write_verbose(self):
        self.write_parser.startElement("verbose", Attributes(dict(
                                            level=str(self.verbose_level))))
        self.write_parser.endElement("verbose")

    def _write_scaninfo(self):
        for scan in self.scaninfo:
            if type(scan) == type({}):
                self.write_parser.startElement("scaninfo",
                    Attributes(dict(type = scan.get("type", ""),
                                    protocol = scan.get("protocol", ""),
                                    numservices = scan.get("numservices", ""),
                                    services = scan.get("services", ""))))
                self.write_parser.endElement("scaninfo")

    def _write_nmaprun(self):
        self.write_parser.startElement("nmaprun",
                Attributes(dict(annotation = str(self.profile_annotation),
                                args = str(self.nmap_command),
                                description = str(self.profile_description),
                                hint = str(self.profile_hint),
                                nmap_output = str(self.nmap_output),
                                options = str(self.profile_options),
                                profile = str(self.profile),
                                profile_name = str(self.profile_name),
                                scanner = str(self.scanner),
                                start = str(self.start),
                                startstr = str(self.formated_date),
                                target = str(self.target),
                                version = str(self.scanner_version),
                                scan_name = str(self.scan_name))))

    def _verify_file(self, xml_file):
        if type(xml_file) in StringTypes:
            if os.access(os.path.split(xml_file)[0], os.W_OK):
                xml_file = open(xml_file, "w")
                xml_file.seek(0)
                return xml_file
            else:
                raise Exception("Don't have write permissions to given path.")
        elif type(xml_file) not in StringTypes:
            try:
                mode = xml_file.mode
                if mode == "r+" or mode == "w" or mode == "w+":
                    xml_file.seek(0)
            except IOError:
                raise Exception("File descriptor is not able to write!")
            else:
                return xml_file

    def set_unsaved(self):
        self.unsaved = True

    def is_unsaved(self):
        return self.unsaved

def nmap_parser_sax(nmap_xml_file=""):
    parser = make_parser()
    nmap_parser = NmapParserSAX()
    
    parser.setContentHandler(nmap_parser)
    nmap_parser.set_parser(parser)
    nmap_parser.set_xml_file(nmap_xml_file)

    return nmap_parser

NmapParser = nmap_parser_sax

if __name__ == '__main__':
    file_to_parse = open("/home/adriano/umit/test/diff1.usr")
    file_to_write = open("/tmp/teste_write.xml", "w+")
    
    np = NmapParser(file_to_parse)
    np.parse()

    from pprint import pprint

    print "Comment:",
    pprint(np.nmap["hosts"][-1].comment)
    #comment = property(get_comment, set_comment)

    print "TCP sequence:",
    pprint(np.nmap["hosts"][-1].tcpsequence)
    #tcpsequence = property(get_tcpsequence, set_tcpsequence)

    print "TCP TS sequence:",
    pprint(np.nmap["hosts"][-1].tcptssequence)
    #tcptssequence = property(get_tcptssequence, set_tcptssequence)

    print "IP ID sequence:",
    pprint(np.nmap["hosts"][-1].ipidsequence)
    #ipidsequence = property(get_ipidsequence, set_ipidsequence)

    print "Uptime:",
    pprint(np.nmap["hosts"][-1].uptime)
    #uptime = property(get_uptime, set_uptime)

    print "OS Match:",
    pprint(np.nmap["hosts"][-1].osmatch)
    #osmatch = property(get_osmatch, set_osmatch)

    print "Ports:",
    pprint(np.nmap["hosts"][-1].ports)
    #ports = property(get_ports, set_ports)

    print "Ports used:",
    pprint(np.nmap["hosts"][-1].ports_used)
    #ports_used = property(get_ports_used, set_ports_used)

    print "OS Class:",
    pprint(np.nmap["hosts"][-1].osclasses)
    #osclasses = property(get_osclasses, set_osclasses)

    print "Hostnames:",
    pprint(np.nmap["hosts"][-1].hostnames)
    #hostnames = property(get_hostnames, set_hostnames)

    print "IP:",
    pprint(np.nmap["hosts"][-1].ip)
    #ip = property(get_ip, set_ip)

    print "IPv6:",
    pprint(np.nmap["hosts"][-1].ipv6)
    #ipv6 = property(get_ipv6, set_ipv6)

    print "MAC:",
    pprint(np.nmap["hosts"][-1].mac)
    #mac = property(get_mac, set_mac)

    print "State:",
    pprint(np.nmap["hosts"][-1].state)
    #state = property(get_state, set_state)


    """
    print "Profile:", np.profile
    print "Profile name:", np.profile_name
    print "Profile description:", np.profile_description
    print "Profile hint:", np.profile_hint
    print "Profile annotation:", np.profile_annotation
    print "Profile options:", np.profile_options
    print "Target:", np.target
    print "Nmap output:", np.nmap_output
    print "Debugging:", np.debugging_level
    print "Verbose:", np.verbose_level
    print "Scaninfo:", np.scaninfo
    print "Services scanned:", np.services_scanned
    print "Nmap command:", np.nmap_command
    print "Scan type:", np.scan_type
    print "Protocol:", np.protocol
    print "Num services:", np.num_services
    print "Date:", np.date
    print "Open ports:", np.open_ports
    print "Filtered ports:", np.filtered_ports
    print "Closed ports:", np.closed_ports
    print "Formated date:", np.formated_date
    print "Scanner:", np.scanner
    print "Scanner version:", np.scanner_version
    print "IPv4:", np.ipv4
    print "MAC:", np.mac
    print "IPv6:", np.ipv6
    print "Hostnames", np.hostnames
    print "Ports:", np.ports
    print "Hosts:", np.hosts
    print "Runstats:", np.runstats
    print "Hosts down:", np.hosts_down
    print "Hosts up:", np.hosts_up
    print "Hosts scanned:", np.hosts_scanned
    print "Finished time:", np.finish_time
    print "Finished epoc time:", np.finish_epoc_time
    print "Formated finish date:", np.formated_finish_date
    print "Comments:", np.comments
    print "Start:", np.start
    """
