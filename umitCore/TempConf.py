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

from os.path import join
from tempfile import mkdtemp, mkstemp
from umitCore.UserConf import *

def create_temp_conf_dir(version):
    conf_dir = mkdtemp("umit-")

    # Creating an empty target_list file
    create_target_list(conf_dir)

    # Creating the options.xml file
    create_options(conf_dir)

    # Creating the wizard.xml file
    create_wizard(conf_dir)

    # Creating the profile_editor.xml file
    create_profile_editor(conf_dir)

    # Creating the scan_profile.usp file
    create_scan_profile(conf_dir)

    # Creating the umit.conf file
    create_umit_conf(conf_dir)

    # Creating the umit_version file
    create_umit_version(conf_dir, version)

    # Creating an empty recent_scans file
    create_recent_scans(conf_dir)

    return conf_dir

if __name__ == "__main__":
    pass
