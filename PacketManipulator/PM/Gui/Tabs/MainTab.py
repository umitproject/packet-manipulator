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

from PM import Backend
from PM.Core.I18N import _
from PM.Core.Atoms import Node

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Views import UmitView

from PM.Gui.Sessions.Base import Session
from PM.Gui.Sessions.SniffSession import SniffSession
from PM.Gui.Sessions.AttackSession import AttackSession
from PM.Gui.Sessions.SequenceSession import SequenceSession
from PM.Gui.Sessions.BtSniffSession import BtSniffSession

from PM.Manager.PreferenceManager import Prefs

import os.path
from PM.Core.Const import PIXMAPS_DIR

class IntroPage(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self, False, 2)

        pix = gtk.gdk.pixbuf_new_from_file(os.path.join(PIXMAPS_DIR,
                                                         'pm-logo.png'))
        saturate = pix.copy()

        pix.saturate_and_pixelate(pix, 0, False)
        saturate.saturate_and_pixelate(saturate, 10, False)

        self.pixbufs = (pix, saturate)

        self.image = gtk.Image()
        self.image.set_from_pixbuf(self.pixbufs[0])

        ebox = gtk.EventBox()
        ebox.add(self.image)

        alignment = gtk.Alignment(0.5, 1.0)
        alignment.add(ebox)

        #self.pack_start(gtk.Label('Drop a packet here'))
        self.pack_end(alignment, False, False)

        self.set_tooltip_markup('<span size="large"><b>'
                                'Drag and drop a packet here.'
                                '</b></span>')
        self.image.set_tooltip_markup('<tt>PM: now nopper addicted.</tt>')

        ebox.connect('enter-notify-event', self.__on_enter)
        ebox.connect('leave-notify-event', self.__on_leave)
        ebox.connect('realize', self.__on_realize)

    def __on_realize(self, ebox):
        ebox.modify_bg(gtk.STATE_NORMAL, self.style.bg[gtk.STATE_NORMAL])

    def __on_enter(self, widget, evt):
        self.image.set_from_pixbuf(self.pixbufs[1])

    def __on_leave(self, widget, evt):
        self.image.set_from_pixbuf(self.pixbufs[0])

class SessionNotebook(gtk.Notebook):
    def __init__(self):
        gtk.Notebook.__init__(self)

        self.set_show_border(False)
        self.set_scrollable(True)
        self.set_show_tabs(False)

        self._intro_page = IntroPage()
        self.append_page(self._intro_page)

        # We have a static page to manage the packets
        # selected from sniff perspective
        self.view_page = None

        self.connect('page-added', self.__check_last_page)
        self.connect('page-removed', self.__check_last_page)

    def create_sequence_session(self, packets):
        """
        Create a sequence from packets

        @param packets a Node object or a list of packets or a single packet
        """

        if isinstance(packets, Node):
            ctx = Backend.SequenceContext(packets)
        else:
            seq = Node()

            for packet in packets:
                seq.append_node(Node(Backend.SequencePacket(packet)))

            ctx = Backend.SequenceContext(seq)

        session = SequenceSession(ctx)
        return self.__append_session(session)

    def create_edit_session(self, packet):
        if isinstance(packet, basestring):
            packet = Backend.get_proto(packet)()
            packet = Backend.MetaPacket(packet)

        return self.create_sequence_session([packet])

    def create_sniff_session(self, ctx):
        session = SniffSession(ctx)
        return self.__append_session(session)

    def create_btsniff_session(self, ctx):
        session = BtSniffSession(ctx)
        return self.__append_session(session)

    def create_attack_session(self, ctx):
        session = AttackSession(ctx)
        return self.__append_session(session)

    def load_static_session(self, fname):
        ctx = Backend.StaticContext(fname, fname)
        ctx.load()

        session = SniffSession(ctx)
        return self.__append_session(session)

    def load_sniff_session(self, fname):
        return self.load_static_session(fname)

    def load_sequence_session(self, fname):
        ctx = Backend.SequenceContext(fname)
        ctx.load()

        session = SequenceSession(ctx)
        return self.__append_session(session)

    def create_empty_session(self, title):
        session = SniffSession(title=title)
        return self.__append_session(session)

    def bind_session(self, sessk, ctx):
        session = sessk(ctx)
        return self.__append_session(session)

    def create_session(self, sessk, ctxk):
        return self.bind_session(sessk, ctxk())

    def __append_session(self, session):
        session.label.connect('close-clicked', self.__on_close_page, session)

        self.append_page(session, session.label)
        self.set_tab_reorderable(session, True)

        return session

    def __remove_session(self, session):
        tab = PMApp().main_window.get_tab("OperationsTab")

        tab.tree.remove_operation(session.context)

        idx = self.page_num(session)
        self.remove_page(idx)

    def get_current_session(self):
        """
        Get the current Session

        @return a Session instance or None
        """

        idx = self.get_current_page()
        obj = self.get_nth_page(idx)

        if obj and isinstance(obj, Session):
            return obj

        return None

    def __check_last_page(self, widget, child, pagenum):
        if self.get_n_pages() == 1:
            self.set_show_tabs(False)
            self._intro_page.show()
        else:
            self._intro_page.hide()
            self.set_show_tabs(True)

    def __on_close_page(self, label, session):
        # Check if are stopped

        if isinstance(session.context, Backend.TimedContext) and \
           session.context.state != session.context.NOT_RUNNING:

            if Prefs()['gui.maintab.autostop'].value == True:
                session.context.stop()
            else:
                dialog = gtk.MessageDialog(self.get_toplevel(),
                                           gtk.DIALOG_DESTROY_WITH_PARENT,
                                           gtk.MESSAGE_QUESTION,
                                           gtk.BUTTONS_YES_NO,
                                           _('The session is running.\n'
                                             'Do you want stop it?'))
                id = dialog.run()

                dialog.hide()
                dialog.destroy()

                if id == gtk.RESPONSE_YES:
                    session.context.stop()

                return

        if session.context.status == session.context.SAVED or \
           Prefs()['gui.maintab.askforsave'].value == False:
            self.__remove_session(session)
        else:
            dialog = gtk.MessageDialog(self.get_toplevel(),
                                       gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_QUESTION,
                                       gtk.BUTTONS_YES_NO,
                                       _('The session has unsaved changes.\n'
                                         'Do you want to save them?'))

            id = dialog.run()

            dialog.hide()
            dialog.destroy()

            if id == gtk.RESPONSE_NO or \
               (id == gtk.RESPONSE_YES and session.save()):

                self.__remove_session(session)

class MainTab(UmitView):
    tab_position = None
    name = 'MainTab'

    def __create_widgets(self):
        "Create the widgets"
        self.vbox = gtk.VBox(False, 2)
        self.session_notebook = SessionNotebook()

    def __pack_widgets(self):
        "Pack the widgets"

        self.vbox.pack_start(self.session_notebook)

        self.session_notebook.drag_dest_set(
            gtk.DEST_DEFAULT_ALL,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_COPY
        )

        self._main_widget.add(self.vbox)
        self._main_widget.show_all()

    def __connect_signals(self):
        self.session_notebook.connect('drag-data-received', self.__on_drag_data)

    def create_ui(self):
        "Create the ui"
        self.__create_widgets()
        self.__pack_widgets()
        self.__connect_signals()

    def get_current_session(self):
        "@returns the current Session or None"
        page = self.get_current_page()

        if page and isinstance(page, Session):
            return page
        return None

    def get_current_page(self):
        "@return the current page in notebook or None"

        idx = self.session_notebook.get_current_page()
        return self.session_notebook.get_nth_page(idx)

    def __on_drag_data(self, widget, ctx, x, y, data, info, time):
        "drag-data-received callback"

        if data and data.format == 8:
            proto = data.data

            if Backend.get_proto(proto):
                self.session_notebook.create_edit_session(data.data)
                ctx.finish(True, False, time)
                return True

        ctx.finish(False, False, time)
