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

import os
import tempfile

from Cookie import SimpleCookie

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Core.Atoms import defaultdict

from PM.Gui.Core.App import PMApp
from PM.Gui.Plugins.Engine import Plugin

from PM.Gui.Sessions import SessionType
from PM.Gui.Pages.Base import Perspective

from PM.Core.Errors import PMErrorException

try:
    import webkit
except ImportError:
    raise PMErrorException("I need python binding for webkit")

class CookieChooserDialog(gtk.Dialog):
    def __init__(self, cookies):
        gtk.Dialog.__init__(self, 'Cookie selector', PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.store = gtk.ListStore(str, int)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererText()
        self.tree.append_column(gtk.TreeViewColumn('Cookie', rend, text=0))
        self.tree.append_column(gtk.TreeViewColumn('Count', rend, text=1))

        self.store.set_sort_column_id(1, gtk.SORT_DESCENDING)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add(self.tree)

        for k, v in cookies.items():
            self.store.append([k, len(v)])

        self.tree.get_selection().select_path((0,))

        self.vbox.pack_start(sw)
        sw.show_all()

class HTTPage(Perspective):
    icon = gtk.STOCK_INFO
    title = _('HTTP analyzer')

    def create_ui(self):
        self.webview = webkit.WebView()
        self.webview.connect('title-changed', self.__on_title_changed)

        self.js_text = """
        <html>
        <head>
        <script>
        function show() {
            document.title = 'null';
            document.title = 'yes';
        }
        </script>
        </head>
        <body>
        <pre>The HTTP payload doesn't contain text but %s.
        <form name="content_eval" action="">
            <input type="button" value="Show payload" onClick="show()">
        </form>
        </body>
        </html>
        """

        self.tempfile = None
        self.lastpacket = None

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.webview)

        btn = gtk.Button(_('Analyze cookies'))
        btn.connect('clicked', self.__on_analyze)

        bb = gtk.HButtonBox()
        bb.set_layout(gtk.BUTTONBOX_END)
        bb.pack_start(btn)

        self.pack_start(sw)
        self.pack_start(bb, False, False)
        self.show_all()

        self.session.editor_cbs.append(self.reload_webpage)

    def __on_analyze(self, btn):
        cookies = defaultdict(list)
        packets = self.session.sniff_page.get_selected_packets()

        def is_present(mpkt):
            hdrs = mpkt.cfields.get('dissector.http.headers', None)

            if not hdrs:
                return False

            if 'cookie' in hdrs:
                for cstr in hdrs['cookie']:
                    cookie = SimpleCookie()
                    cookie.load(cstr)

                    for k, mar in cookie.items():
                        cookies[k].append(mar.value)

                return True

            elif 'set-cookie' in hdrs:
                for cstr in hdrs['set-cookie']:
                    cookie = SimpleCookie()
                    cookie.load(cstr)

                    for k, mar in cookie.items():
                        cookies[k].append(mar.value)

                return True

            return False

        packets = filter(is_present, packets)

        d = CookieChooserDialog(cookies)

        if d.run() == gtk.RESPONSE_ACCEPT:
            model, iter = d.tree.get_selection().get_selected()
            key = model.get_value(iter, 0)

        d.hide()
        d.destroy()

    def __on_title_changed(self, widget, frame, title):
        if title == 'yes':
            self.render_image()

    def render_image(self):
        if not self.session.packet:
            return

        if self.lastpacket is self.session.packet and self.tempfile:
            self.webview.open('file://' + self.tempfile.name)
        else:
            self.lastpacket = self.session.packet

            if self.tempfile:
                os.unlink(self.tempfile.name)
                self.tempfile = None

            page = self.session.packet.cfields.get('dissector.http.response',
                                                   None)

            if not page:
                return

            self.tempfile = tempfile.NamedTemporaryFile(delete=False)
            self.tempfile.write(page)
            self.tempfile.close()

            self.webview.open('file://' + self.tempfile.name)

    def reload_webpage(self):
        if not self.session.packet:
            return

        page = self.session.packet.cfields.get('dissector.http.response', None)
        headers = self.session.packet.cfields.get('dissector.http.headers',
                                                  None)

        if not page:
            self.webview.load_html_string('<pre>No HTTP payload set.<pre>',
                                          'file:///')
            return

        if headers and 'content-type' in headers:
            conttype = headers['content-type'][0]

            if not conttype.startswith('text/'):
                self.webview.load_html_string(self.js_text % conttype,
                                              'file:///')
                return
        try:
            self.webview.load_html_string(unicode(page), 'file:///')
        except:
            self.webview.load_html_string('<pre>Not plain text</pre>',
                                          'file:///')

class HTTPAnalyzer(Plugin):
    def start(self, reader):
        log.info('HTTP Analyzer plugin started')
        PMApp().main_window.bind_session(SessionType.SNIFF_SESSION, HTTPage)

    def stop(self):
        pass

__plugins__ = [HTTPAnalyzer]
