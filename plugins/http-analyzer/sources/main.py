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

from umit.pm.core.i18n import _
from umit.pm.core.logger import log
from umit.pm.core.atoms import defaultdict

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.plugins.engine import Plugin

from umit.pm.gui.sessions import SessionType
from umit.pm.gui.pages.base import Perspective

from umit.pm.core.errors import PMErrorException

try:
    import webkit
except ImportError:
    raise PMErrorException("I need python binding for webkit")

g_js_graph = """<html>
  <head>
    <title>$name$ analysis</title>
    <script type="text/javascript">$script$</script>
    <style type="text/css">
      body {
        background: #222;
        margin: 0px;
        height: 100%;
        width: 100%;
        display: table;
      }
      center {
        display: table-cell;
        vertical-align: middle;
      }
      #label {
        position: absolute;
        bottom: 10px;
        right: 10px;
        font: 10px sans-serif;
        color: #999;
      }
      #label a {
        color: #ccc;
      }
    </style>
  </head>
  <body>
    <center>
      <script type="text/javascript+protovis">
        var arr = $data$;
        var maxel = Math.max.apply(Math, arr);
        var fact = 260 / maxel;
        var vis = new pv.Panel().width(arr.length * 70 + 150).height(300).bottom(25);
        vis.add(pv.Rule)
            .data(function() pv.range(7))
            .bottom(function(d) d * 80 / 2 + 20).left(70).right(6)
            .strokeStyle("grey").lineWidth(.1)
            .add(pv.Label)
                .textAlign("right").textBaseline("middle")
                .text(function(d) (d * (maxel / 7)).toFixed(1)).textStyle("grey");
        vis.add(pv.Label).right(10).top(20).textAlign("right")
            .textStyle("grey").font("20px sans-serif").text("$name$ analysis");
        var dot = vis.add(pv.Line)
            .data(arr)
            .bottom(function(d) d * fact + 20)
            .left(function() this.index * 70 + 90).add(pv.Dot);
        var bar = dot.add(pv.Bar)
            .bottom(20)
            .width(1)
            .left(function() dot.left() - .5)
            .height(function(d) dot.bottom() - 25);
        bar.add(pv.Label).bottom(10)
            .textAlign("center").textBaseline("middle")
            .text(function(d) d.toFixed(1)).textStyle("grey");
        vis.render();
      </script>
    <div id="label">
      Created by <a href="http://manipulator.umitproject.org">PacketManipulator</a>
    </div>
    </center>
  </body>
</html>"""

g_js_text = """<html>
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
</html>"""

class CookieChooserDialog(gtk.Dialog):
    def __init__(self, cookies):
        gtk.Dialog.__init__(self, 'Cookie selector', PMApp().main_window,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.store = gtk.ListStore(str, int, str)
        self.tree = gtk.TreeView(self.store)

        rend = gtk.CellRendererText()

        col = gtk.TreeViewColumn('Cookie', rend, text=0, cell_background=2)
        col.set_expand(True)
        self.tree.append_column(col)

        col = gtk.TreeViewColumn('Count', rend, text=1, cell_background=2)
        self.tree.append_column(col)

        self.store.set_sort_column_id(1, gtk.SORT_DESCENDING)

        self.tree.set_headers_clickable(True)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        for k, v in cookies.items():
            found = False

            for i in v:
                if i.isdigit():
                    found = True
                    break

            if found:
                self.store.append([k, len(v), '#8DFF7F'])
            else:
                self.store.append([k, len(v), '#FFE3E5'])

        self.tree.get_selection().select_path((0,))

        self.vbox.pack_start(sw)
        sw.show_all()

        self.vbox.set_border_width(4)
        self.set_size_request(350, 200)

class HTTPage(Perspective):
    icon = gtk.STOCK_INFO
    title = _('HTTP analyzer')

    def create_ui(self):
        self.webview = webkit.WebView()
        self.webview.connect('title-changed', self.__on_title_changed)

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

            lst = map(int, filter(lambda x: x.isdigit(), cookies[key]))
            self.webview.load_html_string(
                g_js_graph.replace('$name$', key) \
                          .replace('$data$', str(lst)), 'file:///')

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

        log.debug('These are the available headers: %s' % headers)
        log.debug('Looking for content type ...')

        if headers and 'content-type' in headers:
            conttype = headers['content-type'][0]

            if not conttype.startswith('text/'):
                self.webview.load_html_string(g_js_text % conttype,
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

        if reader:
            contents = reader.file.read('data/protovis.js')
        else:
            contents = "alert('Protovis not loaded!');"

        global g_js_graph
        g_js_graph = g_js_graph.replace('$script$', contents)

    def stop(self):
        PMApp().main_window.unbind_session(SessionType.SNIFF_SESSION, HTTPage)

__plugins__ = [HTTPAnalyzer]
