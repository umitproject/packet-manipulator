'''
Created on 06-Jul-2009

@author: quekshuy
'''

MAX_SNIFF_TYPES = 16

#Frontline specific constants
FP_CLOCK_MASK = 0xFFFFFFF
FP_SLAVE_MASK = 0x02
FP_STATUS_SHIFT = 28
FP_TYPE_SHIFT = 3
FP_TYPE_MASK = 0xF
FP_ADDR_MASK = 7

FP_LEN_LLID_SHIFT = 2
FP_LEN_LLID_MASK = 3
FP_LEN_SHIFT = 5

LMP_TID_MASK = 1
LMP_OP1_SHIFT = 1

# Constants specific to our purposes
_FILTER_ALL = 7

class SniffSession(object):
    """
        Stores the state of the sniff session.
        Attributes:
            state (State), master (list), slave (list), 
            device (string), dump (string), filter (int)
            pindata (PinCrackData)
    """
    def __init__(self, state, master, slave, 
                 device, dump, filter = _FILTER_ALL):
        self.state = state
        self.master, self.slave = master, slave
        self.device, self.dump = device, dump        
        self.filter = filter
        self.pindata = None


class PinCrackData(object):
    """
        Stores LMP data that is relevant for pincracking using OpenCipher's BTPincrack
        (with thanks!). The rationale for this is that pin-cracking can take ages. And since
        frequency of transmission of BT packets is so high, storing the data until sniffing is 
        completed and subsequently running the pincrack would avoid the possibility of missing
        packets during the sniff due to switching between concurrent runs of a sniffing thread and
        a pincracking thread.
        
        Attributes:
            in_rand (list of ints)
            m_comb_key (same)
            s_comb_key (same)
            m_au_rand (same)
            s_au_rand (same)
            m_sres (same)
            s_sres (same)
            sniffed_master (boolean)
    """
    
    def __init__(self, sniffedmaster = True):
        self.in_rand = self.m_comb_key = self.s_comb_key = self.m_au_rand = \
            self.s_au_rand = self.m_sres = self.s_sres = None
        self.sniffed_master = sniffedmaster
        self.pin = None
    
    def ready_to_crack(self):
        return self.in_rand and self.m_comb_key and \
            self.m_au_rand and self.s_comb_key and self.s_au_rand \
            and self.s_sres and self.m_sres
    
    def __str__(self):
        strrep = 'in_rand: %s\nm_comb_key: %s\ns_comb_key: %s\nm_au_rand: %s\n' \
                's_au_rand: %s\nm_sres: %s\ns_sres: %s' % (str(self.in_rand), 
                                                           str(self.m_comb_key),
                                                           str(self.s_comb_key),
                                                           str(self.m_au_rand),
                                                           str(self.s_au_rand),
                                                           str(self.m_sres),
                                                           str(self.s_sres))
            
        return strrep
    
    def __repr__(self):
        return str(self)