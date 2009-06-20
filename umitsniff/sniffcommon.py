"""

Constants that are likely to be used throughout the backend will be placed here, as well as 
well-used utility functions. Similar in function to btcommon.py in PyBluez

This implementation is to be a port of the original darkircop Bluetooth sniffing application.


- qsy 11th Jun 09

"""

#These constants are from the Bluez library. These are especially used in the tool.

# From hci.h
OGF_VENDOR_CMD  = 0x3F
EVT_VENDOR = 0xFF

#/* HCI Packet types */
#define HCI_COMMAND_PKT        0x01
#define HCI_ACLDATA_PKT        0x02
HCI_ACLDATA_PKT = 0x02

#define HCI_SCODATA_PKT        0x03
#define HCI_EVENT_PKT        0x04
#define HCI_VENDOR_PKT        0xff

#/* HCI Packet types */
#define HCI_2DH1    0x0002
#define HCI_3DH1    0x0004
#define HCI_DM1        0x0008
#define HCI_DH1        0x0010
#define HCI_2DH3    0x0100
#define HCI_3DH3    0x0200
#define HCI_DM3        0x0400
#define HCI_DH3        0x0800
#define HCI_2DH5    0x1000
#define HCI_3DH5    0x2000
#define HCI_DM5        0x4000
#define HCI_DH5        0x8000

#define HCI_HV1        0x0020
#define HCI_HV2        0x0040
#define HCI_HV3        0x0080

#define HCI_EV3        0x0008
#define HCI_EV4        0x0010
#define HCI_EV5        0x0020
#define HCI_2EV3    0x0040
#define HCI_3EV3    0x0080
#define HCI_2EV5    0x0100
#define HCI_3EV5    0x0200

#define SCO_PTYPE_MASK    (HCI_HV1 | HCI_HV2 | HCI_HV3)
#define ACL_PTYPE_MASK    (HCI_DM1 | HCI_DH1 | HCI_DM3 | HCI_DH3 | HCI_DM5 | HCI_DH5)


# From hci_lib.h

# Internal methods taken from PyBluez


# These constants are not used in frontline.c
# Their inclusion is for the purpose of retainining consistency.
STATUS_OK = 0
STATUS_ERROR_HDR = 1 << 2
STATUS_ERROR_LEN = (STATUS_ERROR_HDR | 1)
STATUS_ERROR_CRC = (STATUS_ERROR_HDR | (1 << 1))
STATUS_UNSUPPORTED = ((1 << 3) | 1)

HLEN_BC2 = 0xE
HLEN_BC4 = 0xF

TYPE_DV = 8

LMP_IN_RAND = 8
LMP_COMB_KEY = 9
LMP_AU_RAND = 11
LMP_SRES = 12

FRAG_FIRST = (1 << 6)
FRAG_LAST = (1 << 7)
CHAN_DEBUG = 20

FILTER_DATA = 1
FILTER_SCO = (1 << 1)
FILTER_NULL_POLL = (1 << 2)

LLID_FRAG = 1
LLID_START = (1 << 1)
LLID_LMP = (LLID_START|LLID_FRAG)

CMD_START  = 0x30
CMD_STOP = 0x32
CMD_FILTER = 0x33
CMD_TIMER = 0x34

LMP_TID_MASK = 1
LMP_OP1_SHIFT = 1

FP_CLOCK_MASK = 0xFFFFFFF
FP_SLAVE_MASK = 0x2
FP_STATUS_SHIFT = 28
FP_TYPE_SHIFT = 3
FP_TYPE_MASK = 0xF
FP_ADDR_MASK = 7

FP_LEN_LLID_SHIFT = 2
FP_LEN_LLID_MASK = 3
FP_LEN_ARQN_MASK = 1
FP_LEN_SEQN_MASK = ( 1 << 1 )
FP_LEN_FLOW = ( 1 << 4 )
FP_LEN_SHIFT = 5

#define MAX_TYPES 16 (to find out what are the MAX_TYPE types)
MAX_TYPES_DATA = 16

class MacAddress(list):
    """
        Class representation of a MAC Address.
    """
    def __init__(self, six_bytes):
        for byte in six_bytes: self.append(byte)

class DbgPacket(object):

    """
        dbg_packet is actually class representation of commands to be issued to 
        the Bluetooth sniffing device ( == hacked dongle ) through 
        the HCI Controller. This is a direct port of struct dbg_packet.
    """
    MAX_DATA_LEN = 19
    def __init__(self, command=None, data=None):
        self._cmd = command
        self._data = data #allows data to be anything
    
    def getdata(self):
        """
            Return a list, consisting of 19 elements
        """
        return self._data            
    
    def setdata(self, val):
        '''
            val - sequence containing all data. Length must be less than
            or equal to MAX_DATA_LEN
        '''
        if not (len(val) <= self.MAX_DATA_LEN):
            #should raise an error here
            pass
        if not self._data:
            self._data = DbgPacket.MAX_DATA_LEN * [0]
        for index in range(len(val)):
            self._data[index] = val[index]
        
    def getcommand(self):
        return self._cmd
    
    def setcommand(self, val):
        self._cmd = val
    
    def attach_start_pkt(self, startpkt):
        #test that startpkt.master and startpkt.slave are correctly formatted
        if len(startpkt.master) == 6 and len(startpkt.slave) == len(startpkt.master):
            for i in reverse(range(0, len(startpkt.master))):
                self._data[i] = startpkt.master[i]
                self._data[len(self._data) - i] = startpkt.slave[i]
            
                
                
            

    data = property(getdata, setdata)
    command = property(getcommand, setcommand)
    

class StartPacket(object):
    """
        start_packet is port of struct start_packet.
        Used when initializing sniffing.
        Is encapsulated within a dbg_packet when used.
        Attributes: 
            master - list of len = 6 (number of bytes to represent mac address)
            slave  - list of len = 6
    """
    def __init__(self, master_add, slave_add):
        self._master, self._slave  = master_add, slave_add
    
    def __getattr__(self, name):
        if name == 'master': return self._master
        elif name == 'slave': return self._slave


import struct

class UmitBTPacket(object):
    """
        Python equivalent of frontline_packet (sizeof(frontline) == 14) 
    """
    _PACK_FMT_STR = 'BIBHIBB'
    def __init__(self):
        self.hlen, self.clock, self.hdr0, self.len, self.timer, self.chan, self.seq = \
        None, None, None, None, None, None, None
        
    def attach(self, data):
        """
            data - Python string. Used to unpack into UmitBTPacket attributes.
        """
        
        assert len(data) >= 14
        struct.unpack(UmitBTPacket._PACK_FMT_STR, self.hlen, self.clock, self.hdr0, self.len,
                      self.timer, self.chan, self.seq)
    def packed(self):
        """
            Returns string containing packed attributes.
        """
        return struct.pack(_PACK_FMT_STR, self.hlen, self.clock, self.hdr0,
                           self.len, self.timer, self.chan, self.seq)
    def getlen(self):
        return struct.calcsize(_PACK_FMT_STR)
    
    length = property(getlen, None)
#
#struct frontline_packet {
#    uint8_t        fp_hlen;
#    uint32_t    fp_clock;
#    uint8_t        fp_hdr0;
#    uint16_t    fp_len;
#    uint32_t    fp_timer;
#    uint8_t        fp_chan;
#    uint8_t        fp_seq;
#} __packed;  

class UmitBTPacket_BC4(object):
    """
        Python equivalent of frontline_packet_bc4.
        Written as a wrapper for UmitBTPacket
    """
    def __init__(self, umitbtpacket):
        self._umitbtpacket = umitbtpacket
        self.decrypted = None


class UmitBTError(Exception):
    pass
