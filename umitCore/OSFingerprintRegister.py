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

import urllib
import urllib2

insecure_site = "http://www.insecure.org/"
nmap_submission_page = insecure_site + "cgi-bin/nmap-submit.cgi"

class OSFingerprintRegister(object):
    def __init__(self):
        try:
            urllib.urlopen(insecure_site)
        except:
            return None

        self.email = ""
        self.os = ""
        self.classification = ""
        self.ip = ""
        self.fingerprint = ""
        self.notes = ""

    def report(self):
        data = urllib.urlencode({"email":self.email,
                                 "os":self.os,
                                 "class":self.classification,
                                 "ip":self.ip,
                                 "fingerprint":self.fingerprint,
                                 "notes":self.notes})

        # The submit page source code points that the info should be set
        # using POST method. But, it only worked sending it through GET 
        # method. So, I decided to send using both methods, to insure 
        # that it's going to work.
        request = urllib2.Request(nmap_submission_page + "?" + data, data)
        response = urllib2.urlopen(request)

        from tempfile import mktemp
        import webbrowser

        tfile = mktemp()
        open(tfile, "w").write(response.read())
        webbrowser.open(tfile)


if __name__ == "__main__":
    f = OSFingerprintRegister()
    f.report()

    