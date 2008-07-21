# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>#
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
#
# 30 April 2007 -- More generic structure
#                  Maxim Gavrilov <lovelymax@gmail.com>
# 16 May 2007 -- Removing specific files at clean to avoid removing help.html
#                Adriano Monteiro Marques <adriano@umitproject.org>

VPATH = comparing_results \
	profile_editor \
	nse_facilitator \
	scanning \
	searching \
	wizard 

OUTDIR = .
XSL = /usr/share/xml/docbook/stylesheet/nwalsh/html/docbook.xsl

OUTPUTS = $(addsuffix .html, $(VPATH))

%.html : %.xml
	xsltproc -o $(OUTDIR)/$@ $(XSL) $<

all: create-dir $(OUTPUTS)

create-dir:
	@mkdir -p $(OUTDIR)

clean:
	@rm -f $(OUTDIR)/comparing_results.html
	@rm -f $(OUTDIR)/profile_editor.html
	@rm -f $(OUTDIR)/nse_facilitator.html
	@rm -f $(OUTDIR)/scanning.html
	@rm -f $(OUTDIR)/searching.html
	@rm -f $(OUTDIR)/wizard.html


