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

import gtk
import pango
import gobject
import webbrowser

from umit.pm.higwidgets.higboxes import HIGHBox
from umit.pm.higwidgets.higtables import HIGTable
from umit.pm.higwidgets.higlabels import HIGHintSectionLabel
from umit.pm.higwidgets.higdialogs import HIGDialog, HIGAlertDialog

from umit.pm.core.i18n import _
from umit.pm.core.const import PM_VERSION
from umit.pm.core.bugregister import BugRegister

class BugReport(HIGDialog):
    def __init__(self, title=_('Bug Report'), description='', emsg=None):

        HIGDialog.__init__(self, title=title,
                           buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

        self._create_widgets()
        self._pack_widgets()
        self._connect_widgets()

        self.description = description
        self.emsg = emsg

    def _create_widgets(self):
        self.email_label = HIGHintSectionLabel(_("Email"),
            _("Please inform a valid e-mail address from "
            "where you can be reached to be notified when the bug gets "
            "fixed. Not used for other purposes."))
        self.email_entry = gtk.Entry()

        self.description_label = HIGHintSectionLabel(_("Description"),
            _("This is where you should write about the bug, "
            "describing it as clear as possible and giving as many "
            "informations as you can along with your system informations, "
            "like: Which operating system are you using?"))
        self.description_scrolled = gtk.ScrolledWindow()
        self.description_text = gtk.TextView()

        self.bug_icon = gtk.Image()
        self.bug_text = gtk.Label(_("This Bug Report dialog allows you "
            "to easily tell us about a problem that you may have found on "
            "PM. Doing so, you help us to help you, by fixing and "
            "improving PM faster than usual."))

        self.hbox = HIGHBox(False)
        self.table = HIGTable()

    def _pack_widgets(self):
        self.description_scrolled.add(self.description_text)
        self.description_scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.description_scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.description_scrolled.set_size_request(400, 150)
        self.description_text.set_wrap_mode(gtk.WRAP_WORD)
        self.description_text.modify_font(pango.FontDescription("Monospace 10"))

        self.bug_icon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        self.bug_icon.set_padding(10, 0)
        self.bug_text.set_line_wrap(True)
        self.bug_text.set_alignment(0, 0.5)

        self.hbox.set_border_width(4)

        self.table.attach(self.email_label, 0, 1, 0, 1, yoptions=gtk.SHRINK)
        self.table.attach(self.email_entry, 1, 2, 0, 1, yoptions=gtk.SHRINK)

        self.table.attach(self.description_label, 0, 2, 1, 2, yoptions=gtk.SHRINK)
        self.table.attach(self.description_scrolled, 0, 2, 2, 3)

        self.hbox.pack_start(self.bug_icon, False)
        self.hbox.pack_end(self.bug_text)

        self.vbox.pack_start(self.hbox, False, False)
        self.vbox.pack_start(self.table)

    def _connect_widgets(self):
        self.connect('response', self.check_response)

    def check_response(self, widget, response_id):
        if response_id == gtk.RESPONSE_ACCEPT: # clicked on Ok btn
            self.send_report()
        elif response_id in (gtk.RESPONSE_DELETE_EVENT, gtk.RESPONSE_CANCEL):
            # there are tree possibilities to being here:
            # 1) user clicked on 'x' button
            # 2) user clicked on 'cancel' button
            # 3) report was sent successfully and now we can destroy this
            self.destroy()

    def send_report(self):
        """Prepare dialog to send a bug report and then call _send_report."""
        # set cursor to busy cursor (supposing it will take some time
        # to submit the report)
        self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

        # disable dialog controls
        for child in self.vbox.get_children():
            child.set_sensitive(False)

        # now send report
        gobject.idle_add(self._send_report)

    def restore_state(self):
        """Restore dialog state, just like it was before calling
        send_report."""
        self.window.set_cursor(None)
        for child in self.vbox.get_children():
            child.set_sensitive(True)

    def _send_report(self):
        if self.description == "" or self.email == "":
            cancel_dialog = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                message_format=_("Bug report is incomplete!"),
                secondary_text=_("The bug report is incomplete. "
                    "You must inform a description that explains clearly "
                    "what is happening and a valid e-mail, so you can be "
                    "contacted when the bug gets fixed."))
            cancel_dialog.run()
            cancel_dialog.destroy()
            return self.restore_state()

        bug_register = BugRegister(self.emsg)
        bug_register.reporter = self.email

        idx = self.description.find('\n{{{\n')

        if idx > 0:
            bug_register.details = \
                self.description[:idx + 1].replace("\n", "[[BR]]") + \
                self.description[idx:]
        else:
            bug_register.details = self.description.replace("\n", "[[BR]]")

        bug_page = None
        try:
            bug_page = bug_register.report()
            assert bug_page
        except Exception, err:
            cancel_dialog = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                message_format=_("Bug not reported!"),
                secondary_text=_("The bug description could not be "
                    "reported. This problem may be caused by the lack "
                    "of Internet access or indisponibility of the bug "
                    "tracker server. Please, verify your internet access, "
                    "and then try to report the bug once again."))
            cancel_dialog.run()
            cancel_dialog.destroy()
            return self.restore_state()
        else:
            ok_dialog = HIGAlertDialog(type=gtk.MESSAGE_INFO,
                message_format=_("Bug sucessfully reported!"),
                secondary_text=_("The bug description was sucessfully "
                    "reported. A web page with detailed description about "
                    "this report will be opened in your default web browser "
                    "now."))
            ok_dialog.run()
            ok_dialog.destroy()

        if bug_page:
            try:
                webbrowser.open(bug_page, autoraise=1)
            except: # XXX What exceptions should be caught here ?
                page_dialog = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                    message_format=_("Could not open default Web Browser"),
                    secondary_text=_("PM was unable to open your default "
                        "web browser to show the bug tracker page with the "
                        "report status. Try visiting Umit's bug tracker "
                        "page to see if your bug was reported."))
                page_dialog.run()
                page_dialog.destroy()

        # report sent successfully
        self.response(gtk.RESPONSE_DELETE_EVENT)

    def get_description(self):
        buff = self.description_text.get_buffer()
        return buff.get_text(buff.get_start_iter(), buff.get_end_iter())

    def set_description(self, description):
        self.description_text.get_buffer().set_text(description)

    def get_email(self):
        return self.email_entry.get_text()

    def set_email(self, email):
        self.email_entry.set_text(email)

    description = property(get_description, set_description)
    email = property(get_email, set_email)
