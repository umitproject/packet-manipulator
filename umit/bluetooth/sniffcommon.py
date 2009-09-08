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


try:
    from PM.Core.Logger import log
except ImportError:
    class log(object):
        
        @staticmethod
        def debug(debug_str):
            print debug_str

#class SniffSession(object):
#    """
#        Stores the state of the sniff session.
#        Attributes:
#            state (State), master (list), slave (list), 
#            device (string), dump (string), filter (int)
#            pindata (PinCrackData)
#    """
#    def __init__(self, state, master, slave, 
#                 device, dump, filter = _FILTER_ALL):
#        self.state = state
#        self.master, self.slave = master, slave
#        self.device, self.dump = device, dump        
#        self.filter = filter
#        self.pindata = None


