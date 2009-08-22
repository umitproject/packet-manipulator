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

import os.path
from umit.pm.gui.plugins.containers import setup

if not os.path.exists("dist/GeoLiteCity.dat"):
    os.system("wget http://www.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz -O - | gzip -d > dist/GeoLiteCity.dat")

setup(
    name='Traceroute',
    version='1.0',
    author=['Francesco Piccinno'],
    license=['GPL'],
    copyright=['2008 Adriano Monteiro Marques'],
    url='http://blog.archpwn.org',
    scripts=['sources/main.py'],
    start_file="main",
    data_files=[('data', ['dist/logo.png',
                          'dist/GeoLiteCity.dat']
                )],
    package_dir={'libtrace' : 'sources/libtrace'},
    packages=['libtrace'],
    provide=['=Traceroute-1.0'],
    description='Simple traceroute plugin',
    output='traceroute.ump'
)
