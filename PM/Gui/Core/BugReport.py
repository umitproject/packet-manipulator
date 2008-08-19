#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008 Adriano Monteiro Marques
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

from PM.higwidgets.higboxes import HIGHBox
from PM.higwidgets.higtables import HIGTable
from PM.higwidgets.higlabels import HIGHintSectionLabel
from PM.higwidgets.higdialogs import HIGDialog, HIGAlertDialog

from PM.Core.I18N import _
from PM.Core.Const import PM_VERSION
from PM.Core.BugRegister import BugRegister

class BugReport(HIGDialog):
    def __init__(self, title=_('Bug Report'), summary=None, description=None,
                 category=None, crashreport=False, description_dialog=None):
        HIGDialog.__init__(self, title=title, 
            buttons=(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        
        self.crashreport = crashreport
        self.description_dialog = description_dialog
        self._create_widgets()
        self._set_category_list()
        self._pack_widgets()
        self._connect_widgets()
        self.summary = summary or ''
        self.description_report = description
        if self.description_dialog==None:
            self.description = description or ''
        else:
            self.description = description_dialog or ''
        self.category = category or ''

    def _set_category_list(self):
        # Obtained at bug tracker page source code
        
        self.category_list.append(["PacketManipulator",
                                   "PacketManipulator"])
        
    def _create_widgets(self):
        self.category_label = HIGHintSectionLabel(_("Category (optional)"),
            _("If you know in which section of the program "
            "is the bug, please, select it from the choosebox. "
            "If you don't know what section to choose, leave it blank."))
        self.category_list = gtk.ListStore(str, str)
        self.category_combo = gtk.ComboBoxEntry(self.category_list, 0)

        self.email_label = HIGHintSectionLabel(_("Email"),
            _("Please inform a valid e-mail address from "
            "where you can be reached to be notified when the bug gets "
            "fixed. Not used for other purposes."))
        self.email_entry = gtk.Entry()

        self.summary_label = HIGHintSectionLabel(_("Summary"),
            _("This should be a quick description of the issue. "
            "Try to be clear and concise."))
        self.summary_entry = gtk.Entry()

        self.description_label = HIGHintSectionLabel(_("Description"),
            _("This is where you should write about the bug, "
            "describing it as clear as possible and giving as many "
            "informations as you can along with your system informations, "
            "like: Which operating system are you using? Which Nmap "
            "version do you have installed?"))
        self.description_scrolled = gtk.ScrolledWindow()
        self.description_text = gtk.TextView()

        self.bug_icon = gtk.Image()
        self.bug_text = gtk.Label(_("This Bug Report dialog allows you "
            "to easily tell us about a problem that you may have found on "
            "Umit. Doing so, you help us to help you, by fixing and "
            "improving Umit faster than usual."))

        self.hbox = HIGHBox(False)
        self.table = HIGTable()

    def _pack_widgets(self):
        self.description_scrolled.add(self.description_text)
        self.description_scrolled.set_policy(gtk.POLICY_AUTOMATIC, 
            gtk.POLICY_AUTOMATIC)
        self.description_scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.description_scrolled.set_size_request(400, 150)
        self.description_text.set_wrap_mode(gtk.WRAP_WORD)
        self.description_text.modify_font(pango.FontDescription("Monospace 10"))

        self.bug_icon.set_from_stock(gtk.STOCK_DIALOG_INFO, 
            gtk.ICON_SIZE_DIALOG)
        self.bug_icon.set_padding(10, 0)
        self.bug_text.set_line_wrap(True)
        #self.bug_text.set_justify(gtk.JUSTIFY_LEFT)
        self.bug_text.set_alignment(0, 0.5)

        self.hbox.set_border_width(4)
        
        nextpos = (0, 1)
        if not self.crashreport:
            self.table.attach(self.category_label, 0, 1, 0, 1, yoptions=gtk.SHRINK)
            self.table.attach(self.category_combo, 1, 2, 0, 1, yoptions=gtk.SHRINK)
            nextpos = (1, 2)

        self.table.attach(self.email_label, 0, 1, nextpos[0], nextpos[1], yoptions=gtk.SHRINK)
        self.table.attach(self.email_entry, 1, 2, nextpos[0], nextpos[1], yoptions=gtk.SHRINK)

        nextpos = (2, 3)
        if not self.crashreport:
            self.table.attach(self.summary_label, 0, 1, 2, 3, yoptions=gtk.SHRINK)
            self.table.attach(self.summary_entry, 1, 2, 2, 3, yoptions=gtk.SHRINK)
            nextpos = (3, 4)

        self.table.attach(self.description_label, 0, 2, nextpos[0], nextpos[1], yoptions=gtk.SHRINK)
        nextpos = nextpos[0] + 1, nextpos[1] + 1
        self.table.attach(self.description_scrolled, 0, 2, nextpos[0], nextpos[1])

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
        if self.summary == "" or self.description == "" or self.email == "":
            cancel_dialog = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                message_format=_("Bug report is incomplete!"),
                secondary_text=_("The bug report is incomplete. "
                    "You must inform a description that explains clearly "
                    "what is happening and a valid e-mail, so you can be "
                    "contacted when the bug gets fixed."))
            cancel_dialog.run()
            cancel_dialog.destroy()
            return self.restore_state()

        bug_register = BugRegister()

        bug_register.component = self.category
        bug_register.summary = self.summary
        if self.description_report!=None:
            bug_register.details = self.description_report
        else:
            bug_register.details = self.description.replace("\n", "[[BR]]")
        bug_register.reporter = self.email
        
        bug_page = None
        try:
            bug_page = bug_register.report()
            assert bug_page
        except Exception, err:
            print err

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
            webbrowser.open(bug_page, autoraise=1)

        if bug_page:
            try:
                webbrowser.open(bug_page)
            except: # XXX What exceptions should be caught here ?
                page_dialog = HIGAlertDialog(type=gtk.MESSAGE_ERROR,
                    message_format=_("Could not open default Web Browser"),
                    secondary_text=_("Umit was unable to open your default "
                        "web browser to show the bug tracker page with the "
                        "report status. Try visiting Umit's bug tracker "
                        "page to see if your bug was reported."))
                page_dialog.run()
                page_dialog.destroy()

        # report sent successfully
        self.response(gtk.RESPONSE_DELETE_EVENT)

    def get_category(self):
        return self.category_combo.child.get_text()

    def set_category(self, category):
        self.category_combo.child.set_text(category)

    def get_summary(self):
        return self.summary_entry.get_text()

    def set_summary(self, summary):
        self.summary_entry.set_text(summary)
    def get_description(self):
        buff = self.description_text.get_buffer()
        return buff.get_text(buff.get_start_iter(), buff.get_end_iter())
    def set_description(self, description):
        self.description_text.get_buffer().set_text(description)

    def get_category_id(self):
        for i in self.category_list:
            if i[0] == self.category:
                return i[1]
        return "100"

    def get_email(self):
        return self.email_entry.get_text()

    def set_email(self, email):
        self.email_entry.set_text(email)


    category_id = property(get_category_id)
    category = property(get_category, set_category)
    summary = property(get_summary, set_summary)
    description = property(get_description, set_description)
    email = property(get_email, set_email)

class CrashReport(BugReport):
    def __init__(self, summary, description, title=_('Crash Report'),\
                 description_dialog=None):
        BugReport.__init__(self, title, summary, description,
                           "CrashReport", True, 
                           description_dialog=description_dialog)
    
if __name__ == "__main__":
    c = BugReport()
    c.show_all()
    while True:
        result = c.run()
        if result in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT, 
            gtk.RESPONSE_NONE):
            c.destroy()
            break
