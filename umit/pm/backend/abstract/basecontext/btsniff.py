#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2008, 2009 Adriano Monteiro Marques
#
# Author: Quek Shu Yang <quekshuy@gmail.com>
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

import threading

from timed import TimedContext

from umit.pm.core.logger import log
from umit.pm.backend.bt_sniffer import BtCollectRunner, CollectHandler, BtCollectPinCrackRunner


#
# Include options for Bluetooth Sniffing here.
# Reason: Options have to be passed to BtSniffContext for 
# sniffing. We keep the backend separate from PM specific 
# modules
#

# BLUETOOTH SNIFFING OPTIONS

BT_OPTIONS_PINCRACK = ['Never', 'Post-sniffing', 'On the fly']


# END BLUETOOTH SNIFFING OPTIONS

class BaseBtSniffContext(TimedContext):
    """
        There are 3 states: NOT_RUNNING, SET and RUNNING
    """
    
    # Include a state for set
    SET = 4
     
    has_stop = True
    has_resume = False
    has_pause = False
    has_start = True
    
    def __init__(self, hci_device_name, pin_callback = None, capfile = None, scount = 0, stime = 0, 
                 master_add = None, slave_add = None, pinmethod = None, set_timeout = 30):
        '''
            @param hci_device_name     Capture device name (e.g. hci0)
            @param pin_callback        Callback function for when pin has been discovered.
                                        Necessary when pinmethod == BT_OPTIONS_PINCRACK[1|2]
            @param master_add:         master device address as a list of integers
            @param slave_add:         slave device address as a list of integers
            @param capture_info:      CaptureInfo object (more details) 
            @param set_timeout:       Duration of capturing until next sync
            @param bthandler:         Handler for capture of devices
        '''
        super(BaseBtSniffContext, self).__init__()
        self._state = self.NOT_RUNNING
        self.pinmethod = pinmethod
        self._gui_pincallback = pin_callback
        
        if self.pinmethod ==  2: # On the fly
            log.debug('BaseBtSniffContext::__init__:: On the fly. pincrack_handler = %s' % str(pin_callback))
            self._runner = BtCollectPinCrackRunner(hci_device_name, master_add, slave_add)
            self._summary = 'Bluetooth Capture: processing pin on the fly'
#            self._runner.register_pincrack_handler(pin_callback)
        else:
            self._runner = BtCollectRunner(hci_device_name)
            self._summary = "Bluetooth Capture"
            
        self._thread = None
        self._master_add = master_add
        self._slave_add = slave_add
        self.__pinmethod = pinmethod
        self._last = 0
        self._title = "Bluetooth Capture"
         
    
    def __get_pin_action(self, pin):
        log.debug('__get_pin_action')
        self._gui_pincallback('Pin cracked: %s' % pin)
        self._summary = 'Pin crack completed. Pin for this pairing is %s' % pin
    
    def run(self):
        pass
    
    def _start(self):
        log.debug("BtSniffContext: start")
        try:
            self._runner.register_pincrack_handler(self.__get_pin_action)
        except:
            log.debug('_start: not pincracking on the fly')
        self._set()
        self._state  = self.RUNNING
        self._thread = self._runner.start_capture(self._master_add, 
                                                  self._slave_add)
    
    def _resume(self):
        pass
    
    def _restart(self):
        pass
    
    def _set(self):
        """
            Does syncing of the system
        """
        log.debug("BtSniffContext: set")
        self._state = self.SET
        self._runner.sync(self._master_add, self._slave_add)
    
    def _stop(self):
        log.debug("BtSniffContext: stop")
        self._state = self.NOT_RUNNING
        self._runner.stop_capture()
        try:
            if not self._runner.is_done():
                self._runner.terminate()
                self._summary = 'Pin crack could not be completed'
        except:
            # For the case of pincracking, terminate pincrack if incomplete.
            log.debug('Not on the fly pincracking')
    
    def _pause(self):
        log.debug('BtSniffContext: paused called')
    
    def join(self):
        log.debug("BtSniffContext: join")
        self._thread.join()
    
    def is_alive(self):
        if self._thread:
            return self._thread.is_alive()
        return False
    
    def start(self):
        self._start()
    
    def pause(self):
        self._pause()
    
    def stop(self):
        self._stop()
    
    def restart(self):
        self._restart()
    
    def resume(self):
        pass
    
    def get_percentage(self):
        log.debug('BtSniffer: get_percentage called')
        if self.NOT_RUNNING:
            return 100.0
        else:
            return 50.0 #  Stop- gap measure
    
    def set_percentage(self, val):
        self.percentage = val
    
    def get_data(self): 
        end  = len(self._runner.data)
        data = self._runner.data[self._last:]
        self._last = end
        return data
    
    def get_all_data(self):
        return self._runner.data


BtSniffContext = BaseBtSniffContext
    
