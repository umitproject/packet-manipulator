import sniff
from sniffcommon import *
import handlers
import struct

# TODO: State machine for sniffing. To control threads (e.g. running of pincracking, we
# should not resync the sniffer)

####     Classes for the backend     #### 

import threading

_runnerthread = None

class SniffRunner(object):
    
    def __init__(self, session, handler, synctime = 30.0):
        # super(threading.Thread, self).__init__()
        self._session, self._handler = session, handler
        self._synctime = synctime

    def sync(self):
        """
            Every _synctime seconds we are to sync to  compensate for DC-offset.
        """
        self._session.state.cont_sniff = 0
        try:
            print 'Stopping'
            sniff.stop_sniff(self._session.state, self._session.device)
            print 'Set filter'
            sniff.set_filter(self._session.state, self._session.device, 
                             self._session.filter)
            print 'Starting'
            sniff.start_sniff(self._session.state, self._session.device,
                              self._session.master, self._session.slave)
            self._session.state.cont_sniff = 1
            # Continue sniffing
            print 'Continue sniff'
            sniff.sniff(self._session.state, self._session.device, self._session.dump,
                        self._handler)
        except:
            print 'General exception'
            import sys
            print sys.exc_info()        
            self._session.state.cont_sniff = 0
            exit()
            if _runnerthread and _runnerthead.isAlive():
                print 'Cancelling running thread'
                _runnerthread.cancel()
#        except sniff.SniffError: 
#            self._session.state.cont_sniff = 0
#            if _runnerthread:
#                _runnerthread.cancel()
#        except KeyboardInterrupt:
#            print "Keyboard Interrupt"
#            if _runnerthread:
#                _runnerthread.cancel()
        
            
        
    def sniff(self):
        sniff.sniff(self._session.state, self._session.device, self._session.dump,
                    self._handler)
#        _runnerthread = threading.Timer(self._synctime, self.sync)
#        _runnerthread.start()
#        try:
#            self.sync()
#        except KeyboardInterrupt:
#            _runnerthread.cancel()
#            exit()
        
    def run(self):
        print "Start sniffing"
#        self.sniff()
        self.sync()

###############################################
#    Data structures for Bluetooth packets    #
###############################################

## This class is not used at all in the program.
## Mark for removal.
class L2CAPPacket(object):
    
    def __init__(self, packet = None):
        if (not packet):
            packet = sniff._GenericPacket()
        self._packet = packet
    
    def getdata(self):
        return self._packet.data
    
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        pstr = 'L2CAP: '
        payloadstr = (len(self.getdata()) * '%.2X ' % tuple(self.getdata())) if len(self.getdata()) else None
        return ' '.join([pstr, payloadstr if payloadstr else ''])
    
    data = property(getdata, None)

class LMPPacket(object):
    """Wrapper for _LMPPacket. Allows processing to be done on the data payload. 
        Read-only attributes."""
    def __init__(self, packet = None):
        if(not packet):
            packet = sniff._LMPPacket()
        self._packet = packet
    
    def getop1(self):
        return self._packet.op1
    
    def getop2(self):
        if(self.getop1() >= 124 and self.getop1() <= 127):
            return self._packet.op2
        return None
    
    def gettid(self):
        return self._packet.tid
    
    def getdata(self):
        return self._packet.data
        
    def __str__(self):
        pstr = 'LMP Tid %d Op1 %d' % (self.gettid(), self.getop1())
        if self.getop2() >= 0:
            pstr = ' '.join([pstr, 'Op2 %d' % self.getop2(), ':'])
        else:
            pstr = ''.join([pstr, ':'])
        
        payloadstr = (len(self.getdata()) * '%.2X ' % tuple(self.getdata())) if len(self.getdata()) else None
        return ' '.join([pstr, payloadstr if payloadstr else ''])
    
    def __repr__(self):
        return str(self)
        
    op1 = property(getop1, None)
    op2 = property(getop2, None)
    tid = property(gettid, None)
    data = property(getdata, None)



def parse_macs(mac_add):
    """
        Returns a list of integers representing that MAC address (len = 6)
        Parameters:
        
        - `mac_add`: string representation of a Bluetooth MAC address
    """
    import re
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
    print "Sniffer run"
    if not handler:
        handler = handlers.BTSniffHandler()
    if not state:
        state = sniff.State()

    (options, args) = getcmdoptions()

    state.ignore_zero = 1 if options.ignore_zero else 0
#    for i in range(MAX_SNIFF_TYPES):
#        state.ignore_types.append(-1)
    # Note for ignore_types as of now we only allow ignoring of one type
    state.ignore_types[0] = options.ignore_type if options.ignore_type else -1
    
    if not options.device:
        exit("Did not specify device")
    
    if options.timer:
        print "Timer: %x" % sniff.get_timer(state, options.device)
    
    if options.filter and options.filter >  -1:
        sniff.set_filter(state, options.device, options.filter)
    
    if options.stop:
        sniff.stop_sniff(state, options.device)
    
    if options.start:
        at_ind = options.start.find('@')
        if(not at_ind == -1):
            master_add = parse_macs(options.start[0:at_ind])
            slave_add = parse_macs(options.start[at_ind + 1:])
            #print 'master = ', master_add, " slave = ", slave_add
            sniff.start_sniff(state, options.device, master_add, slave_add)
    
    if options.snif:
        sniff.sniff(state, options.device, options.dump, handler)



  
if __name__=='__main__':
    run()
   
