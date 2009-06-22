"""
    Two additional classes, for the purpose of sniffing.
"""
import struct

from sniffcommon import *
from bluetooth import _bluetooth as pybt

class State(object):
    """
        Port of struct state in the original tool
        Added an additional attribute - btsocket - which is the socket representation
        of a Bluetooth connection.
       
    """
    
    def __init__(self, sock):
        _members = ['device', 'data', 'slen', 'llid', 'master', 'ignore_types', 'dump',\
                    'ignore_zero', 'type', 'pin', 'pin_data', 'pin_master']
        # List of attributes. Lazy way to initialize attributes.
        # 
        # device: sniffing device
        # llid: llid for l2cap
        # dump: file object storing an opened dump file (if -w option is selected) 
        #
        
        
        for attr in _members: 
            exec 'self.%s = None' % attr
            
        self.ignore_types = MAX_TYPES_DATA * [-1]
        self._socket = sock
        """
        Bluetooth socket.
        """
    
    def getsocket(self):
        return self._socket
    
    def setsocket(self, sock):
        self._socket = sock
    
    socket = property(getsocket, setsocket)
    

class HCIDumpHdr(object):
    """
        Port of struct hcidump_hdr in the original tool. 
    """
    def __init__(self):
        _members = ['length', 'input', 'pad', 'ts_sec', 'ts_usec']
        # Lazy initialization once again.
         
        for attr in _members:
            exec 'self.%s = None' % attr
        self._pad = 0

    def pack(self):
        """
            Returns Python string representation of the HCIDumpHdr attributes, prepared
            using struct.pack.
        
        """
        try:
            return struct.pack('HBBII', self.length, self.input, self.pad,
                           self.ts_sec, self.ts_usec)
        except struct.error:
            print "None passed to struct.pack"
    
  

def send_debug(state, dbg_packet, retlen):
    """
        Sends a command to the USB dongle using hci_send_req.
        
        Parameters:
        -`state`: contains a btsocket object that is associated with the USB dongle.
        -`dbg_packet`: DbgPacket instance.
        -`retlen`: Length of data to be returned
        
        Returns a Python string which the calling function should know how to interpret with struct.unpack 
    """
    preamble = FRAG_FIRST | FRAG_LAST | CHAN_DEBUG
    hci_sock = state.socket
   
    # pkt is passed as argument params to hci_send_req
    # pkt must contain the preamble as well as the contents of the DbgPacket in a Python
    # string before it can be passed to hci_send_req.
    # Refer to PyBluez implementation of hci_send_req to further understand why pkt
    # is packed as such.
    pkt = struct.pack("BBHH19B", preamble, dbg_packet.command,
                       0, 0, *dbg_packet.data )
    response = pybt.hci_send_req(hci_sock, OGF_VENDOR_CMD, 0x00, 
                                 EVT_VENDOR, retlen, pkt)
    status = struct.unpack("B", response[0])[0] 
    assert status == 0
    return response

def send_debug_no_rp(state, dbg_packet):
    send_debug(state, dbg_packet, 254)

def get_timer(state):
    """
        Returns int timer value.
    """
    dbg_pkt = DbgPacket(CMD_TIMER)
    response = send_debug(state, dbg_pkt, 254)
    #cast response to unsigned int... needs testing
    return struct.unpack("I", response[2: struct.calcsize("I") + 2])[0]

def set_filter(state, val):
    """
        Parameters:
        -`state`: State object.
        -`val`: Python integer. To be converted into unsigned char when transmitted.
    """
    dbg_pkt = DbgPacket(CMD_FILTER)
    dbg_pkt.data[0] = val
    send_debug_no_rp(state, dbg_pkt)

def sniff_stop(state):
    
    dbg_pkt = DbgPacket(CMD_STOP)
    send_debug_no_rp(state, dbg_pkt)
    
    
def sniff_start(state, master_add, slave_add):
    
    dbg_pkt = DbgPacket(CMD_START)
    startpkt = StartPacket(master_add, slave_add)
    dbg_pkt.attach_start_pkt(startpkt)
    send_debug_no_rp(s, dbg_pkt)

def hexdump(data):
    """
        Parameters: 
        
        - `data`: Python string to be written to dump file. String needs to first be
        prepared using struct.pack
    """
    # print using %.2X
    for d in data:
        print '%.2X' % d,
    print
    

def process_l2cap(state, data):
    """
        Called by process_payload. Processes L2CAP payload.
        data - Python string to be written to dump file. String can be prepared using struct.pack
    """
    
    hdh = HCIDumpHdr()
    type = HCI_ACLDATA_PKT
    
    print "L2CAP:", 
    # do a hexdump of the data
    hexdump(data)
    
    # an acl_header is 2 shorts in length
    # first member is the handle and the next member is the dlen
    # 'BHH' = sizeof(type = 8 bits) + 2 * sizeof(short)
    if( not state.dump): return
    
    # hdh.length = sizeof(type) + sizeof(acl_header) + length of data in bytes
    # since data is a string we assume that each character in the string can be represented by one byte
    # hence len(data) is good enough for length of data in bytes
    hdh.length = struct.calcsize('BHH') + len(data) 
    hdh.input, hdh.ts_sec, hdh.ts_usec = 1, 0, 0
    dumpfile = state.dump
    
    try:
    
        dumpfile.write(hdh.pack())
        dumpfile.write(struct.pack('B',type))
        
        acl_dlen = len(data)
        acl_handle = ( 0 & 0x0fff ) | (state.llid << 12)     
        dumpfile.write(struct.pack('HH', acl_handle, acl_dlen))
        dumpfile.write(data)
        
    except IOError: 
        dumpfile.close()
        raise UmitBTError("File error: process_l2cap")
    

def dump_lmp(state, data):
    """
        Writes LMP data from Bluetooth packet into dump file.
        
        Parameters:
        
        -`state`: Contains a dump attribute which is a file object representing the dump file.
        
    """
    hdh = HCIDumpHdr()
    type = HCI_EVENT_PKT
    csr_lmp = [0] * (1 + 1 + 17 + 1) # initializing the csr_lmp data structure
    assert len(data) <= 17
    hdh.length = struct.calcsize('BBB') + len(csr_lmp)
    hdh.input, hdh.ts_sec, hdh.ts_usec = 1, 0, 0
    dumpfile = state.dump
    
    try:
        
        dumpfile.write(hdh.pack())
        dumpfile.write(struct.pack('B', type))
        
        evt_evt = EVT_VENDOR 
        # Note: some constants like EVT_VENDOR are also defined in PyBluez. However,
        # we continue to use those defined in sniffcommon for consistency with the original
        # tool.
        evt_plen = len(csr_lmp)
        dumpfile.write(struct.pack('BB', evt_evt, evt_plen))
        
        index = 0
        # Channel ID = 20
        csr_lmp[index], index = 20, index + 1
        csr_lmp[index], index = 0x10 if state.master else 0x0f, index + 1
        buf = struct.unpack(`(len(data) / struct.calcsize('B'))` + 'B', data )
        for d in range(len(buf)):
            csr_lmp[index + d] = buf[d]
        else:
            index += d
        csr_lmp[index] = 0 # connection handle
        dumpfile.write(struct.pack(`len(csr_lmp)`+'B', *csr_lmp))
        
    except IOError:
        
        dumpfile.close()
        raise UmitBTError("File error: dump_lmp")
        
    
    

def process_lmp(state, data):
    
    if(state.dump):
        dump_lmp(state, data)
    
    index, op2  = 0, -1
    op1, index = struct.unpack('B', data[0:struct.calcsize('B')])[0], index + 1
    assert len - 1 >= 0
    tid = op1 & LMP_TID_MASK
    op1 >>= LMP_OP1_SHIFT
    
    if(op1 >= 124 and op1 <= 127):
        op2, index = data[index], index + 1
        assert len - 2 >= 0
    print "LMP Tid %i Op1 %i" % (tid, op1),
    
    if not op2 == -1:
        print " Op2 %d" % op2,
    print ": ",
    hexdump(data)
    
    if(state.pin):
        import pincrack
        pincrack.do_pin(state, op1, data)

def process_dv(state, data):
    print "DV: ",
    hexdump(data)

def process_payload(state, data):
    
    if state.type == TYPE_DV:
        process_dv(state, data)
        return
    if state.llid == LLID_LMP:
        process_lmp(state, data)
    else:
        process_l2cap(state, data)

def process_frontline(state, data):
    """
       Parameters:
        
       `data`: Python string created using struct.pack. It is the ACL data returned from a 
               btsocket.recv() call.
    """
    fp = UmitBTPacket()
    fp.attach(data[:fp.getlen()])
    type = (fp.hdr0 >> FP_TYPE_SHIFT) & FP_TYPE_MASK
    plen = fp.len >> FP_LEN_SHIFT
    #start = fp.hlen #pointer to the head of the fp packet
    status = fp.hdr0 & FP_ADDR_MASK
    
    if(fp.hlen == HLEN_BC2 or fp.hlen == HLEN_BC4):
        pass
    else:
        print "Unknown header len: %d" % fp.hlen
    
    if type in state.ignore_types or (state.ignore_zero and not plen):
        return #first condition checks for appended packets
    
    
    state.llid = (fp.len >> FP_LEN_LLID_SHIFT) & FP_LEN_LLID_MASK
    state.master = not (fp.clock & FP_SLAVE_MASK)
    state.type  = type
    
    print "HL 0x%.2X Ch %.2d %c Clk 0x%.7X Status " \
        "0x%.1X Hdr0 0x%.2X [type: %d addr: %d] LLID %d Len %d" % \
        fp.hlen, fp.chan, 'M' if state.master else 'S', \
        fp.clock & FP_CLOCK_MASK, fp.clock >> FP_STATUS_SHIFT,\
        fp.hdr0, type, status, state.llid, plen, 
    
    datalen = len(data)
    datalen -= hlen
    assert datalen >= 0
    assert datalen >= plen
    
    if plen:
        print " ",      
        # here we call process_payload, and pass a packed version of 
        # the UmitBTPacket as data
        process_payload(state, fp.packed())
    else:
        print
    
    #firmware seems to append fragments
    datalen -= plen
    assert datalen >= 0
    if datalen:
        process_frontline(state, data[plen:])

def process(state, data):
    """
        Bluetooth packet captured. Processing begins.
        
        Parameters:
        
        - `state`: State object.
        - `data` : Bluetooth packet. Python string representation. Needs unpacking.
        
    """
    buf_index = 0
    type, buf_index = struct.unpack("B", data[buf_index: struct.calcsize("B")])[0],\
        buf_index + 1
    
    if(not type == HCI_ACLDATA_PKT):
        print "Uknown type: %d", type
        return
    
    fmt_str = "HH" # 2 consecutive unsigned shorts
    acl_handle, acl_dlen= struct.unpack(fmt_str, data[buf_index:struct.calcsize(fmt_str)])
    buf_index += 1
    assert acl_dlen == (len(data) - struct.calcsize(fmt_str) - 1)
    process_frontline(state, data[buf_index:])

def sniff(state):
    """
        Called to start sniffing. Loops infinitely.
    """
    flt = pybt.hci_filter_new()
    pybt.hci_filter_all_ptypes(flt)
    pybt.hci_filter_all_events(flt)
    state.socket.setsockopt(pybt.SOL_HCI, pybt.HCI_ACLDATA_PKT, flt)
    
    while True:
        # In original code, buffer has len 1024
        # This API call needs to be tested. As seen in bluez.py in PyBluez.
        # Returns a string, assumed to be packed using struct.pack
        state.data = state.socket.recv(1024) 
        if state.data == None:
            raise UmitBTError('BTSocket recv call error')         
        process(state, state.data)

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
    

def main():
    """
        Main method. Program entry point.
    """
    
    # Process command line arguments.
    from optparse import OptionParser
    parser = OptionParser() 
    
    parser.add_option("-z", action="store_true", dest="ignore_zero", default=False,
                      help='Ignore zero length packets')
    parser.add_option('-d', action='store', type='int', dest='device',
                      help='<dev> e.g. hci0')
    parser.add_option('-t', action='store_true', dest='timer', default=False,
                      help ='timer')
    parser.add_option('-f', action='store', dest='filter', type='int', 
                      help='<filter>')
    parser.add_option('-s', action='store_true', dest='stop', default=False,
                      help='stop')
    parser.add_option('-S', action='store', dest='start', default=False,
                      help='<master@slave>')
    parser.add_option('-i', action='store', dest='ignore_type',
                      help='<ignore type>')
    parser.add_option('-e', action='store_true', dest='snif', default=False,
                      help='sniff')
    parser.add_option('-w', action='store', dest='dump', type='string',
                      help='<dump_to_file>')
    parser.add_option('-p', action='store', dest='pin', 
                      help='own pin')
    (options, args) = parser.parse_args()
    # print options
    # print args
    
    if options.dump: #dump file not mandatory
        state.dump = open(options.dump, 'w')
        
    if not options.device:
        raise UmitBTError("Specify device")
    else:
        state.device = options.device    
    
    devadd = pybt.hci_devid(state.device)
    state.socket = pybt.hci_open_dev(devadd)
    
    if options.timer:
        print "Timer %x:" % get_timer(state)
    
    if options.filter and options.filter > -1:
        set_filter(state, options.filter)
    
    if options.stop:
        sniff_stop(state)
    
    if options.start:
        at_ind = options.start.find('@')
        if(not at_ind == -1):
            master_add = parse_macs(options.start[0:at_ind])
            slave_add = parse_macs(options.start[at_ind + 1:])
            sniff_start(state, master_add, slave_add)
    
    if options.snif:
        sniff(state)
    
    pybt.hci_close_dev(devadd)    
    if(state.dump):
        state.dump.close()
    
    
if __name__ == '__main__':
    main()

#hci_acl_hdr used in original process_l2cap
#typedef struct {
#    uint16_t    handle;        /* Handle & Flags(PB, BC) */
#    uint16_t    dlen;
#} __attribute__ ((packed))    hci_acl_hdr;


#struct frontline_packet {
#    uint8_t        fp_hlen;
#    uint32_t    fp_clock;
#    uint8_t        fp_hdr0;
#    uint16_t    fp_len;
#    uint32_t    fp_timer;
#    uint8_t        fp_chan;
#    uint8_t        fp_seq;
#} __packed;
    
    
    
#hci_event_hdr
#typedef struct {
#    uint8_t        evt;
#    uint8_t        plen;
#} __attribute__ ((packed))    hci_event_hdr;



#def _read_flush_timeout (addr):
#    hci_sock = _bt.hci_open_dev ()
#    # get the ACL connection handle to the remote device
#    handle = _get_acl_conn_handle (hci_sock, addr)
#    # XXX should this be "<H"?
#    pkt = struct.pack ("H", handle) # "H" means pack from Python integer to C unsigned short
#    response = _bt.hci_send_req (hci_sock, _bt.OGF_HOST_CTL, 
#        0x0027, _bt.EVT_CMD_COMPLETE, 5, pkt)
#    status = struct.unpack ("B", response[0])[0]  # "B" means unpack from C unsigned char to Python integer
#    rhandle = struct.unpack ("H", response[1:3])[0] # "H" means unpack from C unsigned short to Python integer
#    assert rhandle == handle
#    assert status == 0
#    fto = struct.unpack ("H", response[3:5])[0] 
#    return fto
    
