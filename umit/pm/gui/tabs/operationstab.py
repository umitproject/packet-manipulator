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
import gobject

from threading import Thread

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.core.tracing import trace
from umit.pm.core.logger import log
from umit.pm.core.bus import ServiceBus

from umit.pm.gui.core.app import PMApp
from umit.pm.gui.core.views import UmitView
from umit.pm.gui.core.icons import get_pixbuf

from umit.pm.manager.preferencemanager import Prefs

class Operation(object):
    """
    This is an abstract class representing a network operation
    like sending packets or receiving packets and should be ovverriden
    """

    RUNNING, NOT_RUNNING = range(2)

    # CHECKME: Add this to avoid multiple request of that prefs.
    SKIP_UPDATE = Prefs()['gui.operationstab.uniqueupdate'].value

    def __init__(self):
        self.iter = None
        self.model = None
        self.state = self.NOT_RUNNING

    def set_iter(self, model, iter):
        self.iter = iter
        self.model = model

    def notify_parent(self):
        # emit a row-changed to update the model

        if self.iter and self.model:
            self.model.row_changed(self.model.get_path(self.iter), self.iter)

    def activate(self):
        "Called when the user clicks on the row"
        pass

    def get_summary(self):
        return 'Implement me'

    def get_percentage(self):
        """
        @return None if we should pulse or a int
                if None you should provide percentage attribute
        """
        return None

class FileOperation(Operation):
    """
    Abstract class to manage file operations like save/load
    """
    TYPE_LOAD, TYPE_SAVE = range(2)

    has_pause = False
    has_stop = False
    has_start = True
    has_restart = False

    def __init__(self, obj, type):
        """
        @param obj if type is TYPE_LOAD the path of the file to load or a
                   Session to save.
        @param type TYPE_LOAD or TYPE_SAVE
        """
        Operation.__init__(self)

        self.file = file
        self.type = type

        if type == FileOperation.TYPE_LOAD:
            self.file = obj
        else:
            self.session = obj
            self.ctx = self.session.context

        self.percentage = 0
        self.thread = None
        self.state = self.NOT_RUNNING
        self.loading_view = False

        if type == FileOperation.TYPE_LOAD:
            self.summary = _('Loading of %s pending.') % self.file
        else:
            self.summary = _('Saving to %s pending.') % self.ctx.cap_file

    def start(self):
        if self.state == self.RUNNING:
            return

        self.state = self.RUNNING

        if self.type == FileOperation.TYPE_LOAD:
            self.summary = _('Loading %s') % self.file
            self._read_file()
        else:
            self.summary = _('Saving to %s') % self.ctx.cap_file
            self._save_file()

    def get_percentage(self):
        if self.loading_view:
            self.percentage = (self.percentage + 536870911) % gobject.G_MAXINT
            return None
        else:
            return self.percentage

    def get_summary(self):
        return self.summary

    @trace
    def _save_file(self):
        """
        @see umit.pm.gui.sessions.base.Session.save_session
        """

        log.debug('Saving context %s to %s' % (self.ctx, self.ctx.cap_file))

        if isinstance(self.ctx, backend.StaticContext):
            self.summary = _('Saving packets to %s') % self.ctx.cap_file
        elif isinstance(self.ctx, backend.SequenceContext):
            self.summary = _('Saving sequence to %s') % self.ctx.cap_file

        self.start_async_thread(())

    @trace
    def _read_file(self):
        types = {}
        sessions = (backend.StaticContext,
                    backend.SequenceContext,
                    backend.SniffContext)

        for ctx in sessions:
            for name, pattern in ctx.file_types:
                types[pattern] = (name, ctx)

        try:
            find = self.file.split('.')[-1]

            for pattern in types:
                if pattern.split('.')[-1] == find:
                    ctx = types[pattern][1]
        except:
            pass

        if ctx is not backend.SequenceContext and \
           ctx is not backend.SniffContext and \
           ctx is not backend.StaticContext:

            self.summary = _('Unable to recognize file type.')
        else:
            self.start_async_thread((ctx, ))

    @trace
    def start_async_thread(self, udata):
        self.thread = Thread(target=self._thread_main, name='FileOperation',
                             args=udata)
        self.thread.setDaemon(True)
        self.thread.start()

    @trace
    def __on_idle(self, udata):
        if self.type == FileOperation.TYPE_LOAD:
            ctx, rctx = udata

            self.loading_view = True

            log.debug('Creating a new session after loading for %s' % str(ctx))

            if ctx is backend.SequenceContext:
                from umit.pm.gui.sessions.sequencesession import SequenceSession

                ServiceBus().call('pm.sessions', 'bind_session',
                                  SequenceSession, rctx)

            elif ctx is backend.SniffContext or \
                 ctx is backend.StaticContext:

                from umit.pm.gui.sessions.sniffsession import SniffSession

                ServiceBus().call('pm.sessions', 'bind_session',
                                  SniffSession, rctx)

        else:
            from umit.pm.gui.sessions.sniffsession import SniffSession

            if isinstance(self.session, SniffSession):
                self.session.sniff_page.statusbar.label = '<b>%s</b>' % \
                                                          self.ctx.summary
        self.loading_view = False
        self.percentage = 100.0
        self.state = self.NOT_RUNNING

        # Force update.
        self.notify_parent()
        return False

    @trace
    def _thread_main(self, udata=None):
        if self.type == FileOperation.TYPE_LOAD:
            ctx = udata
            rctx = None

            log.debug('Loading file as %s' % str(ctx))

            if ctx is backend.SequenceContext:
                rctx = backend.SequenceContext(self.file)

            elif ctx is backend.SniffContext or \
                 ctx is backend.StaticContext:

                rctx = backend.StaticContext(self.file, self.file,
                                 Prefs()['backend.system.static.audits'].value)

            if rctx is not None:
                # Let's update our operation directly from load
                if rctx.load(operation=self) == True:
                    # Now let's add a callback to when
                    gobject.idle_add(self.__on_idle, (ctx, rctx))
                else:
                    log.error('Error while loading context on %s.' % self.file)
                    self.state = self.NOT_RUNNING
        else:
            log.debug('Saving %s to %s' % (self.ctx, self.ctx.cap_file))

            if self.ctx.save(operation=self) == True:
                gobject.idle_add(self.__on_idle, ())
            else:
                log.error('Error while saving context on %s.' % \
                          self.ctx.cap_file)
                self.state = self.NOT_RUNNING

        self.thread = None

class SendOperation(backend.SendContext, Operation):
    def __init__(self, packet, count, inter, iface):
        Operation.__init__(self)
        backend.SendContext.__init__(self, packet, count, inter, iface, \
                                     self.__send_callback, None)

    def __send_callback(self, packet, udata=None):
        if not self.SKIP_UPDATE:
            self.notify_parent()


class SendReceiveOperation(backend.SendReceiveContext, Operation):
    """
    A send receive operation
    """

    def __init__(self, packet, count, inter, \
                 iface=None, strict=True, report_recv=False, \
                 report_sent=True, background=True):
        """
        Construct a SendReceive Operation

        @param packet the packet to send
        @param count how many times the packet will be sent
        @param inter the interval between emission
        @param iface the iface to listen to
        @param strict strict checking for reply
        @param report_recv report received packets
        @param report_sent report sent packets
        @param background if the operation should have a session when starts
        """

        capmethod = Prefs()['backend.system.sendreceive.capmethod'].value

        if capmethod < 0 or capmethod > 2:
            Prefs()['backend.system.sendreceive.capmethod'].value = 0
            capmethod = 0

        log.debug('Using %d as capmethod for SendReceiveContext' % capmethod)

        Operation.__init__(self)
        backend.SendReceiveContext.__init__(self, packet, count, inter, iface,
                                            strict, report_recv, report_sent,
                                            capmethod,
                                            self.__send_callback,
                                            self.__receive_callback,
                                            None, None)

        if background:
            self.session = None
        else:
            self.__create_session()

    def _start(self):
        ret = backend.SendReceiveContext._start(self)

        if ret and self.session:
            self.session.sniff_page.reload()

        return ret

    def _restart(self):
        ret = backend.SendReceiveContext._restart(self)

        if ret and self.session:
            self.session.sniff_page.clear()

        return ret

    def __create_session(self):
        self.session = ServiceBus().call('pm.sessions', 'create_sniff_session',
                                         self)

    def __send_callback(self, packet, idx, udata):
        if not self.SKIP_UPDATE:
            self.notify_parent()

    def __receive_callback(self, reply, is_reply, udata):
        if not self.SKIP_UPDATE:
            self.notify_parent()

    def activate(self):
        if not self.session:
            self.__create_session()


class SniffOperation(backend.SniffContext, Operation):
    def __init__(self, iface, filter=None, minsize=0, maxsize=0, capfile=None, \
                 scount=0, stime=0, ssize=0, real=True, scroll=True, \
                 resmac=True, resname=False, restransport=True, promisc=True, \
                 background=False, capmethod=0, audits=True):

        Operation.__init__(self)
        backend.SniffContext.__init__(self, iface, filter, minsize, maxsize,
                                      capfile, scount, stime, ssize, real,
                                      scroll, resmac, resname, restransport,
                                      promisc, background, capmethod, audits,
                                      self.__recv_callback, None)

        if not self.background:
            self.session = ServiceBus().call('pm.sessions',
                                             'create_sniff_session', self)
        else:
            self.session = None

    def _start(self):
        ret = backend.SniffContext._start(self)

        if self.session:
            if ret:
                self.session.sniff_page.clear()

            # We have to call it also in case of start failed to set up the
            # correct summary on the label.
            self.session.sniff_page.reload()

        return ret

    def activate(self):
        if not self.session:
            self.session = ServiceBus().call('pm.sessions',
                                             'create_sniff_session', self)

    def __recv_callback(self, packet, udata):
        if not self.SKIP_UPDATE:
            self.notify_parent()


class SequenceOperation(backend.SequenceContext, Operation):
    def __init__(self, seq, count, inter, iface=None, strict=True, \
                 report_recv=False, report_sent=True):

        capmethod = Prefs()['backend.system.sequence.capmethod'].value

        if capmethod < 0 or capmethod > 2:
            Prefs()['backend.system.sendreceive.capmethod'].value = 0
            capmethod = 0

        log.debug('Using %d as capmethod for SendReceiveContext' % capmethod)

        Operation.__init__(self)
        backend.SequenceContext.__init__(self, seq, count, inter, iface,   \
                                         strict, report_recv, report_sent, \
                                         capmethod,                        \
                                         self.__send_callback,             \
                                         self.__receive_callback)

        self.session = ServiceBus().call('pm.sessions', 'create_sniff_session',
                                         self)

    def __send_callback(self, packet, want_reply, loop, count, udata):
        if not self.SKIP_UPDATE:
            self.notify_parent()

    def __receive_callback(self, packet, reply, udata):
        if not self.SKIP_UPDATE:
            self.notify_parent()

    def _start(self):
        ret = backend.SequenceContext._start(self)

        if ret and self.session:
            self.session.sniff_page.clear()
            self.session.sniff_page.reload()

        return ret

class AuditOperation(backend.AuditContext, Operation):
    def __init__(self, dev1, dev2, bpf_filter, skipfwd, unoffensive):
        capmethod = Prefs()['backend.system.audit.capmethod'].value

        if capmethod < 0 or capmethod > 2:
            Prefs()['backend.system.sendreceive.capmethod'].value = 0
            capmethod = 0

        Operation.__init__(self)
        backend.AuditContext.__init__(self, dev1, dev2, bpf_filter, capmethod)

        self.session = ServiceBus().call('pm.sessions', 'create_audit_session',
                                         self)

class OperationTree(gtk.TreeView):
    def __init__(self):
        self.store = gtk.ListStore(object)
        super(OperationTree, self).__init__(self.store)

        # We have only one column with a progress bar
        # showing a text

        col = gtk.TreeViewColumn(_('Operation'))

        col.set_expand(True)
        col.set_resizable(True)
        col.set_resizable(True)

        col.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)

        rend = gtk.CellRendererPixbuf()
        col.pack_start(rend, False)
        col.set_cell_data_func(rend, self.__pix_data_func)

        rend = gtk.CellRendererText()
        col.pack_start(rend)
        col.set_cell_data_func(rend, self.__text_data_func)

        self.append_column(col)

        rend = gtk.CellRendererProgress()
        col = gtk.TreeViewColumn(_('Status'), rend)

        col.set_expand(False)
        col.set_resizable(True)
        col.set_fixed_width(150)
        col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)

        col.set_cell_data_func(rend, self.__progress_data_func)

        self.append_column(col)

        self.set_rules_hint(True)

        self.icon_operation = get_pixbuf('operation_small')
        self.connect('button-release-event', self.__on_button_release)

        self.timeout_id = None
        self.timeout_update()

    def is_someone_running(self):
        def check_running(model, path, iter, lst):
            op = model.get_value(iter, 0)

            if op.state == op.RUNNING:
                lst[0] = True
                return True

        lst = [False]
        self.store.foreach(check_running, lst)

        return lst[0]

    def timeout_update(self):
        if Prefs()['gui.operationstab.uniqueupdate'].value == True and \
           not self.timeout_id and self.is_someone_running():

            # We're not empty so we can set a timeout callback to update all
            # actives iters at the same time reducing the CPU usage.

            self.timeout_id = gobject.timeout_add(
                Prefs()['gui.operationstab.updatetimeout'].value or 500,
                self.__timeout_cb
            )

            log.debug('Adding a timeout function to update the OperationsTab')

    def __timeout_cb(self):
        def update(model, path, iter, idx):
            operation = model.get_value(iter, 0)

            if operation.state == operation.RUNNING:
                operation.notify_parent()
                idx[0] += 1

        idx = [0]
        self.store.foreach(update, idx)

        if not idx[0]:
            log.debug('Removing the timeout callback for OperationsTab updates')
            self.timeout_id = None
            return False

        return True

    def __pix_data_func(self, col, cell, model, iter):
        cell.set_property('pixbuf', self.icon_operation)

    def __text_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)
        cell.set_property('text', operation.get_summary())

    def __progress_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)

        if operation.get_percentage() != None:
            cell.set_property('value', operation.get_percentage())
            cell.set_property('pulse', -1)
        else:
            cell.set_property('value', 0)
            cell.set_property('pulse', operation.percentage)

    def __on_button_release(self, widget, evt):
        if evt.button != 3:
            return

        model, iter = self.get_selection().get_selected()

        if not iter:
            return

        menu = gtk.Menu()
        operation = model.get_value(iter, 0)

        labels = (
            _('Open'),
            _('Resume operation'),
            _('Pause operation'),
            _('Stop operation'),
            _('Restart operation'),
            _('Remove finished')
        )

        stocks = (
            gtk.STOCK_OPEN,
            gtk.STOCK_MEDIA_PLAY,
            gtk.STOCK_MEDIA_PAUSE,
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_REFRESH,
            gtk.STOCK_CLEAR
        )

        callbacks = (
            self.__on_open,
            self.__on_resume,
            self.__on_pause,
            self.__on_stop,
            self.__on_restart,
            self.__on_clear
        )

        idx = 0
        for lbl, stock, cb in zip(labels, stocks, callbacks):
            action =  gtk.Action(None, lbl, None, stock)
            action.connect('activate', cb, operation)
            item = action.create_menu_item()

            if idx in (1, 2) and not operation.has_pause or \
               idx == 3 and not operation.has_stop or \
               idx == 4 and not operation.has_restart:
                item.set_sensitive(False)

            menu.append(item)

            idx += 1

        menu.show_all()
        menu.popup(None, None, None, evt.button, evt.time)

    # Public functions

    def append_operation(self, operation, start=True):
        """
        Append an operation to the store

        @param operation an Operation object
        @param start if the operation should be started
        """

        assert (isinstance(operation, Operation))

        iter = self.store.append([operation])
        # This is for managing real-time updates
        operation.set_iter(self.store, iter)

        if start:
            operation.start()

        self.timeout_update()

    def remove_operation(self, operation):
        """
        Remove an operation from the store

        @param operation the Operation to remove
        """

        if not isinstance(operation, Operation):
            return

        def remove(model, path, iter, operation):
            if model.get_value(iter, 0) is operation:
                model.remove(iter)
                return True

        self.store.foreach(remove, operation)

    # Callbacks section

    def __on_open(self, action, operation):
        operation.activate()

    def __on_resume(self, action, operation):
        operation.resume()

    def __on_pause(self, action, operation):
        operation.pause()

    def __on_stop(self, action, operation):
        operation.stop()

    def __on_restart(self, action, operation):
        operation.restart()

    def __on_clear(self, action, operation):
        def scan(model, path, iter, lst):
            op = model.get_value(iter, 0)

            if op.state == op.NOT_RUNNING:
                lst.append(gtk.TreeRowReference(model, path))

        lst = []
        self.store.foreach(scan, lst)

        for ref in lst:
            self.store.remove(self.store.get_iter(ref.get_path()))

class OperationsTab(UmitView):
    icon_name = 'operation_small'
    tab_position = gtk.POS_BOTTOM
    label_text = _('Operations')
    name = 'OperationsTab'

    def create_ui(self):
        self.tree = OperationTree()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self._main_widget.add(sw)
        self._main_widget.show_all()
