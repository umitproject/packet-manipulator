import sniff
from sniffcommon import *
import struct


class UmitBTSniffError(Exception):
    """
        General exception for BTSniffer
    """
    pass

class LMPPacket(object):
    """Wrapper for _LMPPacket. Allows processing to be done on the data payload. 
        Read-only attributes."""
    def __init__(self, packet = None):
        if(not packet):
            packet = sniff._LMPPacket()
        self._packet = packet
        if not self._packet:
            raise UmitBTSniffError("Wrong packet holding type. Should be _LMPPacket") 
    
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

class BTSniffHandler(sniff.SniffHandler):
    """
        Subclassed SniffHandler can be wired to handle recvpacket events
    """
    def __init__(self):
        super(sniff.SniffHandler, self).__init__()
    def recvpacket(self, packet):
        """
            Do duplicate printing as to the original frontline tool. Used to manually diff the 2 outputs
            This can be modified to do anything we wish with the received packet.
        """
        master = not (packet.clock & FP_SLAVE_MASK)
        header_len = packet.hlen
        channel = packet.chan
        clock = packet.clock & FP_CLOCK_MASK
        status = packet.clock >> FP_STATUS_SHIFT
        hdr0 = packet.hdr0
        type = (hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK
        address = hdr0 & FP_ADDR_MASK
        llid = (packet.len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK
        length = packet.len >> FP_LEN_SHIFT
        
        print 'PL 0x%.2X Ch %.2d %c Clk 0x%.7X Status 0x%.1X Hdr0 0x%.2X [type: %d addr: %d] LLID %d Len %d' \
                        % (header_len, 
                            channel,
                            'M' if master else 'S',
                            clock, 
                            status,
                            hdr0,
                            type,
                            address,
                            llid,
                            length),
        # Process payload. We watch for LMPs
        if packet.payload:
            paypkt = LMPPacket(packet.payload)
            print str(paypkt)
        else: print 
        

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
            maclist.append(int(m.group(i), 16)) #base 16 representation
    else:
        raise UmitBTError("Invalid mac address: " + mac_add) #raise an error here. invalid mac address
    return maclist

def run():

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
    parser.add_option('-p', action='store', dest='pin', 
                          help='own pin')
    (options, args) = parser.parse_args()
    
    state = sniff.State()
    state.ignore_zero = 1 if options.ignore_zero else 0
    for i in range(MAX_SNIFF_TYPES):
        state.ignore_types.append(-1)
    # Note for ignore_types as of now we only allow ignoring of one type
    state.ignore_types[0] = options.ignore_type if options.ignore_type else -1
    
    if not options.device:
        exit("Did not specify device")
    
    if options.timer:
        print "Timer: %x" % get_timer(state, options.device)
    
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
        handler = BTSniffHandler()
        sniff.sniff(state, options.device, options.dump, handler)
  
  
if __name__=='__main__':
    run()
   
