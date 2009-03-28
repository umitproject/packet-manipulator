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
import gobject

from PM import Backend
from PM.Core.I18N import _

from PM.Gui.Core.App import PMApp
from PM.Gui.Core.Views import UmitView
from PM.Gui.Core.Icons import get_pixbuf

class Operation(object):
    """
    This is an abstract class representing a network operation
    like sending packets or receiving packets and should be ovverriden
    """

    def __init__(self):
        self.iter = None
        self.model = None

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

class SendOperation(Backend.SendContext, Operation):
    def __init__(self, packet, count, inter, iface):
        Operation.__init__(self)
        Backend.SendContext.__init__(self, packet, count, inter, iface, \
                                     self.__send_callback, None)

    def __send_callback(self, packet, udata=None):
        self.notify_parent()


class SendReceiveOperation(Backend.SendReceiveContext, Operation):
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

        Operation.__init__(self)
        Backend.SendReceiveContext.__init__(self, packet, count, inter, iface,
                                            strict, report_recv, report_sent,
                                            self.__send_callback,
                                            self.__receive_callback,
                                            None, None)
        
        if background:
            self.session = None
        else:
            self.__create_session()

    def _start(self):
        ret = Backend.SendReceiveContext._start(self)

        if ret and self.session:
            self.session.sniff_page.reload()

        return ret

    def _restart(self):
        ret = Backend.SendReceiveContext._restart(self)

        if ret and self.session:
            self.session.sniff_page.clear()

        return ret

    def __create_session(self):
        nb = PMApp().main_window.get_tab("MainTab").session_notebook
        self.session = nb.create_sniff_session(self)

    def __send_callback(self, packet, idx, udata):
        self.notify_parent()

    def __receive_callback(self, reply, is_reply, udata):
        self.notify_parent()

    def activate(self):
        if not self.session:
            self.__create_session()


class SniffOperation(Backend.SniffContext, Operation):
    def __init__(self, iface, filter=None, minsize=0, maxsize=0, capfile=None, \
                 scount=0, stime=0, ssize=0, real=True, scroll=True, \
                 resmac=True, resname=False, restransport=True, promisc=True, background=False):

        Operation.__init__(self)
        Backend.SniffContext.__init__(self, iface, filter, minsize, maxsize, capfile,
                                      scount, stime, ssize, real, scroll,
                                      resmac, resname, restransport, promisc,
                                      background, self.__recv_callback, None)

        if not self.background:
            nb = PMApp().main_window.get_tab("MainTab").session_notebook
            self.session = nb.create_sniff_session(self)
        else:
            self.session = None

    def _start(self):
        ret = Backend.SniffContext._start(self)

        if ret and self.session:
            self.session.sniff_page.clear()
            self.session.sniff_page.reload()

        return ret

    def activate(self):
        if not self.session:
            nb = PMApp().main_window.get_tab("MainTab").session_notebook
            self.session = nb.create_sniff_session(self)

    def __recv_callback(self, packet, udata):
        self.notify_parent()


class SequenceOperation(Backend.SequenceContext, Operation):
    def __init__(self, seq, count, inter, iface=None, strict=True, \
                 report_recv=False, report_sent=True):

        Operation.__init__(self)
        Backend.SequenceContext.__init__(self, seq, count, inter, iface,   \
                                         strict, report_recv, report_sent, \
                                         self.__send_callback,             \
                                         self.__receive_callback)

        nb = PMApp().main_window.get_tab("MainTab").session_notebook
        self.session = nb.create_sniff_session(self)

    def __send_callback(self, packet, want_reply, loop, count, udata):
        self.notify_parent()

    def __receive_callback(self, packet, reply, udata):
        self.notify_parent()

    def _start(self):
        ret = Backend.SequenceContext._start(self)

        if ret and self.session:
            self.session.sniff_page.clear()
            self.session.sniff_page.reload()

        return ret


class OperationTree(gtk.TreeView):
    def __init__(self):
        self.store = gtk.ListStore(object)
        super(OperationTree, self).__init__(self.store)

        # We have only one column with a progress bar
        # showing a text

        col = gtk.TreeViewColumn(_('Operation'))
        col.set_resizable(True)

        rend = gtk.CellRendererPixbuf()
        col.pack_start(rend, False)
        col.set_cell_data_func(rend, self.__pix_data_func)

        rend = gtk.CellRendererText()
        col.pack_start(rend)
        col.set_cell_data_func(rend, self.__text_data_func)

        self.append_column(col)

        rend = gtk.CellRendererProgress()
        col = gtk.TreeViewColumn(_('Status'), rend)
        col.set_resizable(True)
        col.set_cell_data_func(rend, self.__progress_data_func)

        self.append_column(col)

        self.set_rules_hint(True)

        self.icon_operation = get_pixbuf('operation_small')
        self.connect('button-release-event', self.__on_button_release)

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
        operation.set_iter(self.store, iter) # This is for managing real-time updates
        
        if start:
            operation.start()

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
