#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
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

import urllib
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError

from umit.pm.core.const import PM_VERSION

from tempfile import mktemp
import re

trac_site="http://trac.umitproject.org/"
trac_new_ticket=trac_site + "newticket"
trac_submit=trac_new_ticket


class BugRegister(object):
    def __init__(self, emsg):
        urllib.urlopen(trac_new_ticket)

        if emsg:
            self.summary = "CrashReporter: %s" % emsg
        else:
            self.summary = "CrashReporter: Unknown exception"

        self.details = ""
        self.input_file = ""
        self.file_description = ""
        self.submit = "submit"
        self.cc = ""
        self.reporter = "user"
        self.keywords = "user crash"
        self.milestore = ""
        self.version = "PacketManipulator " + str(PM_VERSION)
        self.assigned_to = "nopper"
        self.component = "PacketManipulator"
        self.type = "defect"

    # Function to get the cookie of headers
    def __get_cookie(self, header, name):
        """
        Receive header and the name intended to find
        Returns the value or None if not found
        """
        try:
            pattern = r".*%s=([^;]+)[;]{0,1}.*" % name
            return re.findall(pattern, header['Set-cookie'])[0]
        except Exception, ex:
            return None



    def report(self):
        f = urllib2.urlopen(trac_new_ticket)

        # Get cookie trac_session
        trac_session = self.__get_cookie(f.headers, "trac_session")
        # Get value of __FORM_TOKEN
        trac_form = self.__get_cookie(f.headers, "trac_form_token")
        if (trac_form == None or trac_session == None ):
            return None

        data = urllib.urlencode({"field_summary":self.summary,
                                 "__FORM_TOKEN":trac_form,
                                 "field_type":self.type,
                                 "field_description":self.details,
                                 "field_milestone":self.milestore,
                                 "field_component":self.component,
                                 "field_version":self.version,
                                 "field_keywords":self.keywords,
                                 #"owner":self.assigned_to,
                                 "cc":self.cc,
                                 "author":self.reporter,
                                 #"attachment":self.input_file,
                                 "field_status":"new",
                                 "action":"create",
                                 "submit":self.submit})
        request = urllib2.Request(trac_new_ticket, data)
        request.add_header("Cookie", "trac_session=%s; \
                           trac_form_token=%s" % (trac_session, trac_form))

        response = urllib2.urlopen(request)

        tfile = mktemp()
        open(tfile, "w").write(response.read())

        return tfile

if __name__ == "__main__":
    bug = BugRegister()
    bug.report()
