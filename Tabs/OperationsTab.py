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
import Backend

from umitCore.I18N import _

from views import UmitView
from Icons import get_pixbuf

class Operation(object):
    """
    This is an abstract class representing a network operation
    like sending packets or receiving packets and should be ovverriden
    """

    NOT_STARTED, RUNNING, PAUSED, STOPPED = range(4)

    def __init__(self):
        self.state = Operation.NOT_STARTED
        self.percentage = 0

        self.iter = None
        self.model = None

    def set_iter(self, model, iter):
        self.iter = iter
        self.model = model
    
    def notify_parent(self):
        # emit a row-changed to update the model

        if self.iter and self.model:
            self.model.row_changed(self.model.get_path(self.iter), self.iter)

    def get_percentage(self):
        "@return the percentage of the work"
        return self.percentage

    def get_text(self):
        "@return a summary text of the operation"
        raise Exception("Not implemented")

    # This methods can't fail

    def start(self):
        "Start the current operation"
        pass

    def stop(self):
        "Stop the current operations forever"
        self.state = Operation.STOPPED

    def pause(self):
        "Pause the current operations for a future resume"
        self.state = Operation.PAUSED

    def resume(self):
        "Resume the paused operations"
        self.state = Operation.RUNNING

    # Attributes
    
    def get_state(self):
        "@retuns a id representing the status of the operation"
        return self.state

class SendOperation(Operation):
    def __init__(self, packet, count, inter):
        self.packet = packet

        self.tot_count = count
        self.count = 0

        self.inter = inter / 100.0

        super(SendOperation, self).__init__()

    def get_text(self):
        return _("Sent %d of %d packets ...") % (self.count, self.tot_count)

    def start(self):
        self.state = Operation.RUNNING
        Backend.send_packet(self.packet, self.tot_count, self.inter, self.__send_callback)

    def resume(self):
        if self.state == Operation.PAUSED:
            self.state = Operation.RUNNING
            Backend.send_packet(self.packet, self.tot_count - self.count, self.inter, self.__send_callback)

    def __send_callback(self, packet, count, inter, udata=None):
        self.count += 1
        
        # Calc the percentage
        self.percentage = float(self.count) / float(self.tot_count)
        self.percentage *= 100.0

        self.notify_parent()

        # Stop if the Operation is paused or stopped
        return self.state == Operation.PAUSED or \
               self.state == Operation.STOPPED

class SendReceiveOperation(Operation):
    pass

class OperationTree(gtk.TreeView):
    def __init__(self):
        self.store = gtk.ListStore(object)
        super(OperationTree, self).__init__(self.store)

        # We have only one column with a progress bar
        # showing a text

        rend = gtk.CellRendererProgress()
        col = gtk.TreeViewColumn('', rend)
        col.set_cell_data_func(rend, self.__cell_data_func)

        self.append_column(col)
        self.set_headers_visible(False)
        self.set_rules_hint(True)

        self.update_id = None
        self.connect('button-release-event', self.__on_button_release)

    def __cell_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)

        cell.set_property('text', operation.get_text())
        cell.set_property('value', operation.get_percentage())

    def __on_button_release(self, widget, evt):
        if evt.button != 3:
            return

        model, iter = self.get_selection().get_selected()

        if not iter:
            return

        menu = gtk.Menu()
        operation = model.get_value(iter, 0)

        labels = (
            'Resume operation',
            'Pause operation',
            'Stop operation',
            'Remove finished'
        )

        stocks = (
            gtk.STOCK_MEDIA_PLAY,
            gtk.STOCK_MEDIA_PAUSE,
            gtk.STOCK_MEDIA_STOP,
            gtk.STOCK_CLEAR
        )

        callbacks = (
            self.__on_resume,
            self.__on_pause,
            self.__on_stop,
            self.__on_clear
        )

        for lbl, stock, cb in zip(labels, stocks, callbacks):
            action =  gtk.Action(None, lbl, None, stock)
            action.connect('activate', cb, operation)

            menu.append(action.create_menu_item())

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

    # Callbacks section

    def __on_resume(self, action, operation):
        operation.resume()

    def __on_pause(self, action, operation):
        operation.pause()

    def __on_stop(self, action, operation):
        operation.stop()

    def __on_clear(self, action, operation):
        pass

class OperationsTab(UmitView):
    icon_name = gtk.STOCK_INFO
    tab_position = gtk.POS_BOTTOM
    label_text = "Operations"

    def create_ui(self):
        self.tree = OperationTree()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.add(self.tree)

        self._main_widget.add(sw)
        self._main_widget.show_all()
