#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
#
# Author: Luís A. Bastião Silva <luis.kop@gmail.com>
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

setup(
    name='plotstats',
    version='1.0',
    author=['Luís A. Bastião Silva'],
    license=['GPL'],
    copyright=['2009 Adriano Monteiro Marques'],
    url='http://www.umitproject.org',
    scripts=['sources/main.py', 'sources/cairoplot.py', 'sources/gtkcairoplot.py', 'sources/Series.py'],
    start_file="main",
    provide=['=plotstats-1.0'],
    description='Statistics',
    output='plotstats.ump'
)
