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

from optparse import OptionParser
from umitCore.I18N import _

protocol_re = re.compile("^(umit|scan|nmap)://.*")

class UmitOptionParser(OptionParser):
    def __init__(self, args=False):
        OptionParser.__init__(self)

        ## Network Inventory (GUI)
        ### This option should raise the Network Inventory window 
        ### with the last used inventory
        self.add_option("-i", "--inventory", 
                        default=False,
                        action="store_true",
                        help=_("*NOT IMPLEMENTED* - Start Umit and go \
straight to Network Inventory window."))

        ## Run nmap with args (GUI)
        ### Open Umit and runs nmap with specified args. The positional 
        ### args should be used to feed the nmap command
        self.add_option("-n", "--nmap",
                        default=[],
                        action="callback",
                        callback=self.__nmap_callback,
                        help=_("Open Umit and runs a Nmap scan with \
specified args."))

        ## Execute a profile against a target (GUI)
        ### Positional args should be taken as targets to feed this scan
        self.add_option("-p", "--profile",
                        default="",
                        action="store",
                        help=_("Open Umit with the specified profile \
selected. If combined with the -t (--target) option, open Umit and \
automatically run the profile against the specified target."))

        ## Compare results in compare mode (GUI)
        ### Run the diff compare window in compare mode as default
        self.add_option("-c", "--compare",
                        action="store",
                        nargs=2,
                        help=_("*NOT IMPLEMENTED* - Open the diff compare \
window, in compare mode comparing the two given scan result files \
(Nmap XML output or usr (Umit Scan Result) file)."))

        ## Compare results in text mode (GUI)
        ### Run the diff compare window in text mode as default
        self.add_option("-e", "--compare-text",
                        action="store",
                        nargs=2,
                        help=_("*NOT IMPLEMENTED* - Open the diff compare \
window, in text mode comparing the two given scan result files (Nmap XML \
output or usr, Umit Scan Result)."))

        ## Compare results showing text diff in terminal (TEXT)
        ### Doesn't actually run Umit interface. Just take the result files,
        ### generate the text diff and send it back to terminal
        self.add_option("-d", "--diff",
                        action="store",
                        nargs=2,
                        help=_("*NOT IMPLEMENTED* - Take two scan result files \
(Nmap XML output or usr, Umit Scan Result), make a text diff and print it in \
the terminal without openning Umit Interface."))

        ## NSE Facilitator (GUI)
        ### Opens Umit and go straigh to NSE Facilitator interface.
        ### If a positional argument is given, it can be an nse script which
        ### should be openned by the NSE Facilitator interface
        self.add_option("-s", "--nse-facilitator",
                        default=False,
                        action="store_true",
                        help=_("*NOT IMPLEMENTED* - Run Umit and go straight \
to NSE Facilitator Interface. You may specify nse scripts as arguments \
if you want use them."))

        ## Targets (GUI)
        ### Specify a target to be used along with other command line option
        ### or simply opens Umit with the first tab target field filled with
        ### the target specified with this option
        self.add_option("-t", "--target",
                        default=False,
                        action="store",
                    help=_("Specify a target to be used along with other \
options. If specified alone, opens Umit with the target field filled with the \
specified target"))

        ## Open Scan Results (GUI)
        ### Run Umit openning the specified scan result file, which should be
        ### a nmap XML output or an usr (Umit Scan Result) xml file.
        ### This option should be verified if there is no options, and user
        ### specified some positional arguments, which should be considered as
        ### scan result files.
        self.add_option("-f", "--file",
                        default=[],
                        action="append",
                        type="string",
                        dest="result_files",
                        help=_("Specify a scan result file in Nmap XML Output \
or Umit Scan Result file. Can be used more than once to specify several \
scan result files."))

        ## Open a give file, showing it at mapper (GUI)
        ### Specify a scan file result to open at mapper
        self.add_option("-m", "--mapper",
                        default=False,
                        action="store",
                        help=_("*NOT IMPLEMENTED* - Open Umit showing the \
given file at Umit Mapper"))

        ## Verbosity
        self.add_option("-v", "--verbose",
                        default=0,
                        action="count",
                        help=_("Increase verbosity of the output. May be \
used more than once to get even more verbosity"))

        # Parsing options and arguments
        if args:
            self.options, self.args = self.parse_args(args)
        else:
            self.options, self.args = self.parse_args()

    def __nmap_callback(self, option, opt_str, value, parser):
        nmap_args = []
        # Iterate over next arguments that were passed at the command line
        # that wasn't parsed yet.
        while parser.rargs:
            # Store the next argument in a specific list
            nmap_args.append(parser.rargs[0])

            # Remove the added argument from rargs to avoid it's latter
            # parsing by optparse
            del parser.rargs[0]

        # Set the variable nmap at parser.values, so you may call option.nmap
        # and have the nmap_args as result
        setattr(parser.values, "nmap", nmap_args)

    def get_inventory(self):
        """Return the string 'default' when the option is used without
        any argument or a string with the content of the first argument passed
        by the user. Return False if this option was not called by the user"""
        if self.options.inventory:
            if len(self.args) > 0:
                return self.args[0]
            return True
        return False

    def get_nmap(self):
        """Return a list of nmap arguments or False if this option was not
        called by the user"""

        try:
            nmap = self.options.nmap
            if nmap:
                return nmap
        except AttributeError:
            return False

    def get_profile(self):
        """Return a string with the profile name, or False if no profile
        option was specified by the user"""
        if self.options.profile != "":
            return self.options.profile
        return False

    def get_compare(self):
        """Return a list of two elements, containing the two files passed
        as argument, or False if user didn't call this option"""
        compare = self.options.compare
        if compare:
            return compare
        return False

    def get_compare_text(self):
        """Return a list of two elements, containing the two files passed
        as argument, or False if user didn't call this option"""
        compare = self.options.compare_text
        if compare:
            return compare
        return False

    def get_diff(self):
        """Return a list of two elements, containing the two files passed
        as argument, or False if user didn't call this option"""
        try:
            diff = self.options.diff
            if diff:
                return diff
        except AttributeError:
            return False

    def get_nse_facilitator(self):
        """Return the list ['default'] if no positional argument is passed,
        and a list with the strings of the script file names passed as
        positional arguments. Returns False if this option was not called
        by the user"""
        nse = self.options.nse_facilitator
        if nse:
            if len(self.args) > 0:
                return self.args
            return ["default"]
        return False

    def get_target(self):
        """Returns a string with the target specified, or False if this option
        wass not called by the user"""
        return self.options.target

    def get_protocol(self):
        """Return a string with the whole protocol url passed as positional arg
        or False, if no protocol arg was called by the user."""
        for arg in self.args:
            if protocol_re.match(arg):
                return arg
        return False

    def get_open_results(self):
        """Returns a list of strings with the name of the files specified with
        the -f (--file) option, or every positional arguments when no other
        is called by the user"""
        files = []
        if self.options.result_files:
            files = self.options.result_files[:]

        if self.no_option_defined():
            files += self.args

        return (False or files)

    def get_verbose(self):
        """Returns an integer representing the verbosity level of the 
        application. Verbosity level starts in 40, which means that only 
        messages above the ERROR level are going to be reported at the output. 
        As this value gets lower, the verbosity increases.
        """
        return 40 - (self.options.verbose * 10)

    def no_option_defined(self):
        """Return True if any of the listed options were called, of False is
        none of them was called"""

        return not (self.options.compare or \
                    self.options.compare_text or \
                    self.options.diff or \
                    self.options.inventory or \
                    getattr(self.options, "nmap", False) or \
                    self.options.nse_facilitator or \
                    self.options.profile or \
                    self.get_protocol() or \
                    self.options.target or\
                    self.options.mapper)

    def get_mapper(self):
        """Returns a string with the name of the file which should be open at
        mapper. False if this option was not called by the user"""
        return self.options.mapper

option_parser = UmitOptionParser()

if __name__ == "__main__":
    opt = UmitOptionParser()
    options, args = opt.parse_args()
    print opt.get_compare()