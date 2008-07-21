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

from glob import glob
from fnmatch import fnmatch
from tempfile import mktemp
from types import StringTypes

from umitCore.UmitDB import UmitDB
from umitCore.NmapParser import NmapParser
from umitCore.UmitLogging import log


class SearchResult(object):    
    def __init__(self):
        """This method is called by classes that inherit this one at their
        constructor methods. If in the future this method get some 
        functionallity, then, it will work fine for those classes that inherit
        this one.
        """
        pass
    
    def search(self, **kargs):
        log.debug(">>> Starting search process...")
        parameters = ["keyword", "profile", "option", "target",
                      "mac", "ipv4", "ipv6", "port", "service",
                      "osclass", "osmatch", "product"]

        # If nothing is passed, let's considerate that we want to search
        # every port
        self.port_closed = kargs.get("port_closed", True)
        self.port_open = kargs.get("port_open", True)
        self.port_filtered = kargs.get("port_filtered", True)


        # Iterate over scan results searching for patterns
        # Obs: This search looks for a result that matches each received
        # parameters ("and" based search). If something fail, it
        # desconsiderates the result
        
        keys = kargs.keys() # Catch given parameters names
        log.debug(">>> Search parameters: %s" % keys)
        
        # Get parsed results, as NmapParser objects
        for scan_result in self.get_scan_results():
            self.parsed_scan = scan_result

            # Test each given parameter against current parsed result
            for parameter in parameters:
                if parameter in keys:
                    log.debug(">>> Searching '%s' at '%s'" % (parameter,
                                                              kargs[parameter]))
                    
                    if not self.__getattribute__("match_%s" % parameter)\
                       (kargs[parameter]):
                        # A break here, means that there is no match for the 
                        # given pattern and, as it is an "and" based search, the
                        # parsed result must be discarted
                        log.debug(">>> Parsed result doesn't match patterns!")
                        break
            else:
                log.debug(">>> Parsed result matches given patterns!")
                yield self.parsed_scan

        # If current scan result matches the pattern, yield the parsed object
        # Else discart parsed result, and get another! ;-)

    def get_scan_results(self):
        # To be implemented by classes that are going to inherit this one
        pass

    def basic_match(self, keyword, property):
        if keyword == "*" or keyword == "" or \
           fnmatch(str(self.parsed_scan.__getattribute__(property)),
                   "*%s*" % keyword):
            return True # Pattern matches
        return False # Pattern doesn't match

    def match_keyword(self, keyword):
        log.debug("Match keyword: %s" % keyword)
        if self.match_profile(keyword) or \
           self.match_option(keyword) or \
           self.match_target(keyword) or \
           self.match_mac(keyword) or \
           self.match_ipv4(keyword) or \
           self.match_ipv6(keyword) or \
           self.match_service(keyword) or \
           self.match_osmatch(keyword) or \
           self.match_product(keyword) or \
           self.basic_match(keyword, "nmap_output") or \
           self.basic_match(keyword, "profile_name"):
            return True

    def match_profile(self, profile):
        log.debug("Match profile: %s" % profile)
        log.debug("Comparing: %s == %s ??" % \
                  (str(self.parsed_scan.profile_name).lower(),
                   "*%s*" % profile.lower()))
        if profile == "*" or profile == "" or \
           fnmatch(str(self.parsed_scan.profile_name).lower(),
                   "*%s*" % profile.lower()):
            return True # Pattern matches

        return False # Pattern doesn't match

        # FIXME: What is this?? I have commented this line, because it was
        # useless Though, I don't have the time now to find out what is going
        # on here but I'll do that later 
        #return self.basic_match(profile, "profile_name")
    
    def match_option(self, option):
        log.debug("Match option: %s" % option)
        return self.basic_match(option, "profile_options")

    def match_target(self, target):
        log.debug("Match target: %s" % target)
        return self.basic_match(target, "target") or\
               self.basic_match(target, "nmap_command")

    def match_mac(self, mac):
        log.debug("Match mac: %s" % mac)
        return self.basic_match(mac, "mac")

    def match_ipv4(self, ipv4):
        log.debug("Match IPv4: %s" % ipv4)
        return self.basic_match(ipv4, "ipv4")

    def match_ipv6(self, ipv6):
        log.debug("Match IPv6: %s" % ipv6)
        return self.basic_match(ipv6, "ipv6")

    def match_port(self, port):
        log.debug("Match port:%s" % port)
        if port == [""] or port == ["*"]:
            return True
        
        ports = []
        
        for p in self.parsed_scan.ports:
            for port_dic in p:
                for portid in port_dic["port"]:
                    if self.port_open and portid["port_state"] == "open":
                        ports.append(portid["portid"])
                    elif self.port_filtered and\
                         portid["port_state"] == "filtered":
                        ports.append(portid["portid"])
                    elif self.port_closed and portid["port_state"] == "closed":
                        ports.append(portid["portid"])
                    elif not self.port_open and \
                             not self.port_filtered and \
                             not self.port_closed:
                        # In case every port state is False, add every port
                        ports.append(portid["portid"])

        for keyport in port:
            if keyport not in ports:
                return False # No match for asked port
        else:
            return True # Every given port matched current result

    def match_service(self, service):
        log.debug("Match service: %s" % service)
        if service == "" or service == "*":
            return True
        
        services = []
        for first in self.parsed_scan.ports:
            for ports in first:
                for port in ports["port"]:
                    if port.has_key('service_name'):
                        if port["service_name"] not in services:
                            services.append(port["service_name"])
                        
        if service in services:
            return True # Given service name matched current result
        return False # Given service name didn't match current result

    def match_osclass(self, osclass):
        log.debug("Match osclass: %s" % osclass)
        if osclass == "" or osclass == "*":
            return True

        class_info = self.split_osclass(osclass)
        log.debug("Class info: %s" % class_info)
        
        for host in self.parsed_scan.hosts:
            for oc in host.osclasses:
                #log.debug("Vendor: %s" % oc.get("vendor", ""))
                #log.debug("OS Family: %s" % oc.get("osfamily", ""))
                #log.debug("OS Gen: %s" % oc.get("osgen", ""))
                #log.debug("Type: %s" % oc.get("type", ""))
                
                if oc.get("vendor", "").lower() == class_info[0] and \
                       oc.get("osfamily", "").lower() == class_info[1] and \
                       oc.get("osgen", "").lower() == class_info[2] and \
                       oc.get("type", "").lower() == class_info[3]:
                    return True # Found a match
        return False

    def match_osmatch(self, osmatch):
        log.debug("Match osmatch: %s" % osmatch)
        if osmatch == "" or osmatch == "*":
            return True

        for host in self.parsed_scan.hosts:
            match = host.osmatch.get("name", False)
            if match and fnmatch(match.lower(), "*%s*" % osmatch.lower()):
                return True
        return False

    def match_product(self, product):
        log.debug("Match product: %s" % product)
        if product == "" or product == "*":
            return True
        
        products = []
        for first in self.parsed_scan.ports:
            for ports in first:
                for port in ports["port"]:
                    if fnmatch(port.get("service_product", "").lower(),
                               "*%s*" % product.lower()):

                        # Given service product matched current result
                        return True

        # Given service product didn't match current result
        return False

    def split_osclass(self, osclass):
        return [i.strip().lower() for i in osclass.split("|")]

class SearchDB(SearchResult, object):
    def __init__(self):
        SearchResult.__init__(self)
        log.debug(">>> SearchDB initialized")

    def get_scan_results(self):
        log.debug(">>> Getting scan results stored in data base")
        u = UmitDB()

        for scan in u.get_scans():
            log.debug(">>> Retrieving result of scans_id %s" % scan.scans_id)
            log.debug(">>> Nmap xml output: %s" % scan.nmap_xml_output)
            
            temp_file = mktemp(".usr", "umit_")
            
            tmp = open(temp_file, "w")
            tmp.write(scan.nmap_xml_output)
            tmp.close()

            try:
                parsed = NmapParser()
                parsed.set_xml_file(temp_file)
                parsed.parse()
                
                # Remove temporary file reference
                parsed.nmap_xml_file = ""
            except:
                pass
            else:
                yield parsed

class SearchDir(SearchResult, object):
    def __init__(self, search_directory, file_extensions=["usr"]):
        SearchResult.__init__(self)
        log.debug(">>> SearchDir initialized")
        self.search_directory = search_directory

        if type(file_extensions) in StringTypes:
            self.file_extensions = file_extensions.split(";")
        elif type(file_extensions) == type([]):
            self.file_extensions = file_extensions
        else:
            raise Exception("Wrong file extension format! '%s'" %
                            file_extensions)

    def get_scan_results(self):
        log.debug(">>> Getting directory's scan results")
        files = []
        for ext in self.file_extensions:
            files += glob(os.path.join(self.search_directory, "*.%s" % ext))

        log.debug(">>> Scan results at selected directory: %s" % files)
        for scan_file in files:
            log.debug(">>> Retrieving scan result %s" % scan_file)
            if os.access(scan_file, os.R_OK) and os.path.isfile(scan_file):

                try:
                    parsed = NmapParser()
                    parsed.set_xml_file(scan_file)
                    parsed.parse()
                except:
                    pass
                else:
                    yield parsed

class SearchTabs(SearchResult, object):
    def __init__(self, notebook):
        self.scan_notebook = notebook

    def get_scan_results(self):
        scan_file = None
        for i in range(self.scan_notebook.get_n_pages()):
            sbook_page = self.scan_notebook.get_nth_page(i)

            if not sbook_page.status.get_empty():
                scan_file = sbook_page.parsed.nmap_xml_file
                if hasattr(scan_file, "name"):
                    # this scan was loaded from a file so nmap_xml_file is
                    # actually a file object, but we are interested only in
                    # the file name.
                    scan_file = scan_file.name

            if scan_file and os.access(scan_file, os.R_OK) and\
               os.path.isfile(scan_file):
                log.debug(">>> Retrieving unsaved scan result: %s" % scan_file)

                try:
                    parsed = NmapParser()
                    parsed.set_xml_file(scan_file)
                    parsed.parse()
                    parsed.set_scan_name("Unsaved " + \
                                         sbook_page.get_tab_label())
                    parsed.set_unsaved()
                except:
                    pass
                else:
                    yield parsed

if __name__ == "__main__":
    s = SearchDir("/home/adriano/umit/test", ["usr", "xml"])
    for result in s.search(\
        keyword="",
        #profile="",
        #option="",
        #started="1121737119",
        #finished="1121737192",
        #target="10.0.0.100-180",
        #mac=":",
        #ipv4="10.0.0.150",
        #ipv6="",
        #uptime=209980,
        # lastboot="", MUST BE REMOVED FROM THE UI!
        #port=["22", "80"],
        #port_open="",
        #port_filtered="",
        #port_closed="",
        #service="",
        #osclass="Microsoft | Windows | 95/98/ME | General Purpose",
        #osmatch="gentoo",
        #product="Apache"\
        ):

        print "Ports:", result.hosts[-1].ports

