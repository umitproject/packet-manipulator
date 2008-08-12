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

        self.inter = float(float(inter) / 1000.0)

        super(SendOperation, self).__init__()

    def get_text(self):
        if self.count == self.tot_count:
            return _("%d packet(s) sent.") % self.tot_count
        else:
            return _("Sending packet %d of %d") % (self.count, self.tot_count)

    def start(self):
        self.state = Operation.RUNNING
        Backend.send_packet(self.packet, self.tot_count, self.inter, self.__send_callback)

    def resume(self):
        if self.state == Operation.PAUSED:
            self.state = Operation.RUNNING
            Backend.send_packet(self.packet, self.tot_count - self.count, self.inter, self.__send_callback)

    def __send_callback(self, packet, count, inter, udata=None):
        if packet:
            self.count += 1
            
            # Calc the percentage
            self.percentage = float(self.count) / float(self.tot_count)
            self.percentage *= 100.0

            self.notify_parent()
        else:
            self.state = Operation.STOPPED

        # Stop if the Operation is paused or stopped
        return self.state == Operation.PAUSED or \
               self.state == Operation.STOPPED

class SendReceiveOperation(Operation):
    def __init__(self, packet, count, inter, iface=None):
        self.packet = packet
        self.tot_count = count

        self.inter = float(float(inter) / 1000.0)
        self.iface = iface

        self.scount = 0
        self.percentage = 1

        self.summary = ''

        super(SendReceiveOperation, self).__init__()

    def start(self):
        self.state = Operation.RUNNING
        Backend.send_receive_packet(self.packet, self.tot_count, self.inter, self.iface,
                                    self.__send_callback, self.__receive_callback)

    def __send_callback(self, idx, udata):
        self.scount += 1

        self.summary = _("Sending packet %d of %d") % (idx + 1, self.tot_count)
        self.__update()

        return self.state == Operation.PAUSED or \
               self.state == Operation.STOPPED

    def __receive_callback(self, reply, is_reply, received, answered, remaining, udata):

        if reply:
            self.summary = _("Received/Answered/Remaining %d/%d/%d") % (received, answered, remaining)
        else:
            self.state = Operation.STOPPED

        self.__update()

        return self.state == Operation.PAUSED or \
               self.state == Operation.STOPPED

    def __update(self):
        self.percentage += gobject.G_MAXINT / 4
        self.percentage %= gobject.G_MAXINT

        self.notify_parent()

    def get_percentage(self):
        if self.state == Operation.STOPPED:
            return 100.0
        else:
            return None

    def resume(self):
        if self.state == Operation.PAUSED:
            self.state = Operation.RUNNING
            Backend.send_receive_packet(self.packet, self.tot_count - self.scount, self.inter, self.iface,
                                        self.__send_callback, self.__receive_callback)

    def get_text(self):
        return self.summary

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
        cell.set_property('text', operation.get_text())

    def __progress_data_func(self, col, cell, model, iter):
        operation = model.get_value(iter, 0)

        if operation.get_percentage() != None:
            cell.set_property('value', operation.get_percentage())
            cell.set_property('pulse', -1)
        else:
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
    icon_name = 'operation_small'
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
