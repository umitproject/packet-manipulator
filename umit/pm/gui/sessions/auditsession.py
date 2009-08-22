#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Adriano Monteiro Marques
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

from base import Session
from umit.pm.gui.pages.auditpage import AuditPage
from umit.pm.gui.pages.auditoutputpage import AuditOutputPage

class AuditSession(Session):
    session_id = 2
    session_name = "AUDIT"

    def create_ui(self):
        self.audit_page = self.add_perspective(AuditPage, True,
                                                True, False)
        self.output_page = self.add_perspective(AuditOutputPage, True,
                                                True, False)

        self.editor_cbs.insert(0, lambda: self.audit_page.reload())

        self.pack_start(self.paned)
        self.show_all()
