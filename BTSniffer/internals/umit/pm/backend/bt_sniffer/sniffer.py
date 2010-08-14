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

import struct, re
from threading import Timer

import btlayers

from btsniff import * 
from sniffcommon import *
from handlers import CollectHandler, PinCrackCollectHandler

# Additional data types

class LMP(btlayers.BtLayerUnit):
    
    def __init__(self, header, payload = None):
        super(LMP, self).__init__(header, payload)


class L2CAP(btlayers.BtLayerUnit):
    
    def __init__(self, header, payload = None):
        super(L2CAP, self).__init__(header, payload)


####     Classes for the backend     #### 

import threading

class BtSniffRunner(object):
    """
        This class has the following responsibilities:
        1. Access handler for packets received
        2. Start/stop the thread for sniffing
        3. Additional roles delegated by application
        
        To use run the sync first, then run start_capture 
        
    """
    __FILTER_PARAM_ALL = 7
    
    def __init__(self, device_name, handler = None):
        """
            @param device_name: name of capturing HCI device (e.g. hci0)
            @param coll_handler: CollectingHandler object 
        """
        self._dev_name = device_name
        self._handler = handler
        self._capstate = CaptureState()
        self._dev = open_device(self._dev_name)
        self._thread = None
    
    def stop_capture(self):
        self._capstate.resume_sniff = False
        # Forcefully close the device socket
        self.__stop_sniff()
    
    def __stop_sniff(self):
        stop_sniff(self._dev_name)
        try: 
            close_device(self._dev)
        except:
            pass

    
    def start_sniff(self, master_add, slave_add):
        start_sniff(self._capstate, self._dev_name, master_add, slave_add)
    
    def sync(self, master_add, slave_add):
        try:
            stop_sniff(self._dev_name)
        except: 
            # stop_sniff sometimes throws an error on the first try
            # we do a second time 
            stop_sniff(self._dev_name)
        finally:
            # if still throws error, we know there is a problem
            try:
                stop_sniff(self._dev_name)
            except:
                raise
            
        set_filter(self._dev_name, self.__FILTER_PARAM_ALL)
        self.start_sniff(master_add, slave_add)
    
    
    def start_capture(self, master_add, slave_add):
        self._capstate.resume_sniff = True
        self._thread = threading.Thread(target = start_capture, args = \
                                         (self._capstate, self._dev_name, self._handler))
        self._thread.daemon = True
        self._thread.start()
        return self._thread
    
    def step_through(self):
        """
            Primarily used for debugging.
        """
        self._thread.join()
        

class BtCollectRunner(BtSniffRunner):
    """
        This subclass collects and allows access to packets
        collected
    """
    
    def __init__(self, device_name):
        super(BtCollectRunner, self).__init__(device_name)
        self._handler = CollectHandler()
    
    def start_sniff(self, master_add, slave_add):
        self._handler.clear_data()
        super(BtCollectRunner, self).start_sniff(master_add, slave_add)
    
    def get_data(self):
        # Return shalllow copy. Original should remain intact
        return self._handler.data[:]
    
    data = property(get_data, None, "Gets collected BtSniffUnits")

class BtCollectPinCrackRunner(BtCollectRunner):
    
    def __init__(self, device_name, master_add, slave_add, check_interval = 5):
        super(BtCollectPinCrackRunner, self).__init__(device_name)
        self._master_add, self._slave_add = master_add, slave_add
        
        self._handler =  PinCrackCollectHandler(self._master_add, 
                                                self._slave_add)
        # This handler should be run every check_interval seconds to check if 
        # pin crack is done. 
        self._callback = None
        self._timer, self._interval = None, check_interval
        
    
    def register_pincrack_handler(self, handler):
        '''
           @param handler Handler signature should be func(str)
        '''
        self._callback = handler
        self.__set_interval_actions()
    
    def __set_interval_actions(self):
        log.debug('__set_interval: _handler is %s' % str(self._handler.is_done()))
        if self._handler.is_done():
            self._callback(self._handler.getpin())
        else:
            self._timer = Timer(self._interval, self.__set_interval_actions)
            self._timer.start()
    
    def stop_capture(self):
        super(BtCollectPinCrackRunner, self).stop_capture()
        self.terminate()
    
    def is_done(self):
        return self._handler.is_done()
    
    def terminate(self):
        if self._timer is not None: self._timer.cancel()
        self._handler.close()
    
## UTILITY FUNCTIONS

def parse_macs(mac_add):
    """
        @return A list of integers composed of the elements of the MAC address.
        @param mac_add: String representation of a Bluetooth MAC address -- XX:XX:XX:XX:XX:XX
        
    """
    p = re.compile(r'([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2}):'
                   '([0-9a-fA-F]{2})')
    m = p.match(mac_add)
    maclist = []
    if(m and len(m.groups()) == 6):
        for i in range(1, 6 + 1):
            maclist.append(int(m.group(i), 16)) # base 16 representation
    else:
        raise sniff.SniffError("Invalid mac address: " + mac_add) #raise an error here. invalid mac address
    return maclist


def getcmdoptions():
    '''
        Returns tuple (option, args) from OptionParser
    '''
    # Process command line arguments.
    from optparse import OptionParser
    parser = OptionParser() 
        
    parser.add_option("-z", action="store_true", dest="ignore_zero", default=False,
                          help='Ignore zero length packets')
    parser.add_option('-d', action='store', type='string', dest='device',
                          help='<dev> e.g. hci0')
    parser.add_option('-t', action='store_true', dest='timer', default=False,
                          help ='timer')
    parser.add_option('-f', action='store', dest='filter', type='int', 
                          help='<filter>')
    parser.add_option('-s', action='store_true', dest='stop', default=False,
                          help='stop')
    parser.add_option('-S', action='store', dest='start', default=False,
                          help='<master@slave>')
    parser.add_option('-i', action='store', dest='ignore_type', type='int', default=0,
                          help='<ignore type>')
    parser.add_option('-e', action='store_true', dest='snif', default=False,
                          help='sniff')
    parser.add_option('-w', action='store', dest='dump', type='string',
                          help='<dump_to_file>')
    parser.add_option('-p', action='store', dest='pin', default = False,
                          help='own pin')
    return parser.parse_args()
    

def run(handler = None, state = None):
    log.debug("Sniffer run")
    if not handler:
        handler = handlers.BTSniffHandler()
    if not state:
        state = btsniff.CaptureState()

    (options, args) = getcmdoptions()

    state.ignore_zero = 1 if options.ignore_zero else 0
#    for i in range(MAX_SNIFF_TYPES):
#        state.ignore_types.append(-1)
    # Note for ignore_types as of now we only allow ignoring of one type
    state.ignore_types[0] = options.ignore_type if options.ignore_type else -1
    
    if not options.device:
        exit("Did not specify device")
    
    if options.timer:
        log.debug("Timer: %x" % btsniff.get_timer(state, options.device))
    
    if options.filter and options.filter >  -1:
        btsniff.set_filter(state, options.device, options.filter)
    
    if options.stop:
        btsniff.stop_sniff(state, options.device)
    
    if options.start:
        at_ind = options.start.find('@')
        if(not at_ind == -1):
            master_add = parse_macs(options.start[0:at_ind])
            slave_add = parse_macs(options.start[at_ind + 1:])
            #print 'master = ', master_add, " slave = ", slave_add
            btsniff.start_sniff(state, options.device, master_add, slave_add)
    
    if options.snif:
        btsniff.start_capture(state, options.device, options.dump, handler)


if __name__=='__main__':
    run()
   
