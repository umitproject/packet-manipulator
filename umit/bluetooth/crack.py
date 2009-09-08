
import subprocess, os, re
import sys, threading, string
 
import _crack

from sniffcommon import log
from btsniff import CaptureState

## BIG CRACK CHANGES

BTPINCRACKDIR = 'btpincrack-v0.3'
CRACKPROG = 'btpincrack'
LMP_OP1_IN_RAND = 8
LMP_OP1_COMB = 9
LMP_OP1_AU_RAND = 11
LMP_OP1_SRES = 12
LMP_PINCRACK_OPCODES = [LMP_OP1_IN_RAND, LMP_OP1_COMB, LMP_OP1_AU_RAND, LMP_OP1_SRES]



class PinCrackData(object):
    """
        Stores LMP data that is relevant for pincracking using OpenCipher's BTPincrack
        (with thanks!). 
        Attributes:
            in_rand (list of ints)
            m_comb_key (same)
            s_comb_key (same)
            m_au_rand (same)
            s_au_rand (same)
            m_sres (same)
            s_sres (same)
            sniffed_master (boolean)
            pin (string)
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



class PinCrackRunner(object):
    
    def __init__(self, master_add, slave_add, capstate = None):
        self._pcr = None
        self._capstate = capstate if capstate else CaptureState()
        self._master_add, self._slave_add = master_add, slave_add
        self._pcd, self._is_started = None, False
        self._pin = None
    
    def try_crack(self, lmppkt, isPktFromMaster):
        
        if lmppkt is not None and \
            not self._is_started and not self._pcd:
            
            log.debug("Gencrack\n")
            self._pcd = _gen_pincrackdata(self._capstate, 
                              lmppkt.header.op1, 
                              lmppkt.payload.rawdata, 
                              self._master_add, 
                              self._slave_add, isPktFromMaster)
            
        if self._pcd and not self._is_started:
            log.debug("Running crack!!!\n")
            self._is_started = True
            self._pcr = _pincrackrunner(self._pcd, self._master_add, self._slave_add)
            self._pcr.run()
 
        if self._pcr is not None:
            log.debug('%s' % self._pcr.is_done())                    
        return self._pcr is not None and self._pcr.is_done()
        
    
    def is_done(self):
        return self._pcr is not None and self._pcr.is_done()
    
    def terminate(self):
        self._pcr.terminate()
    
    def get_pcd(self):
        return self._pcd
    
    def getpin(self):
        """
            @raise Exception: if pin-cracking is still in process or somehow 
            we missed the capture of one of the required packets.
        """
        if not self._pcr.is_done():
#        if self._pcr.is_alive():
            raise Exception("Pin-cracking still in process")
        self._is_start = False
        self._pin = self._pcr.getpin() if not self._pin else self._pin
        return self._pin

    ### PROPERTIES ###

    pincrackdata = property(get_pcd, None)
         



################################## 
#   INTERNAL PINCRACKING CLASS   #
##################################


class _pincrackrunner(object):
    '''
            Usage:
            Instantiate only after pincrackdata has been created. Then call 
            the run method. Call is_done() to check if pin has been cracked. Once
            is_done() returns True, call getpin() to get the cracked pin.
            Must call terminate() if closing before pin has been cracked or will 
            leave behind zombie btpincrack process.
    '''
    
    __PIN_HEADER = 'pin:'
    __PIN_NOT_READY_EXC = Exception("Pin not ready")
    def __init__(self, pincrackdata, master_add, slave_add, tmpfile = None):
        """
            @param pincrackdata        PinCrackData object
            @param master_add          Master device address as a list of integers.
            @param slave_add           Slave device address as a list of integers.
            @param tmpfile             Temporary file that will be used to store interim output 
                                        for pin-cracking.
        """
        super(_pincrackrunner, self).__init__()
        #self._pcd = self._master = self._slave = None
        self._pcd = pincrackdata
        self._master, self._slave = master_add, slave_add
        print '_pincrackrunner: master', self._master, 'slave: ', self._slave
        if not tmpfile:
            import tempfile
            tmpfile = tempfile.TemporaryFile()
        self._tmpfile = tmpfile
        self.daemon = True
        self.proc = None
    
    
    def _getkeystr(self, keyintlist):
        return ''.join([string.lower('%.2x' % d) for d in keyintlist])
    
    def _getcmd(self, pincrackdata, master, slave):
        cmd = pindatastrs = ''
        pindatastrs = ' '.join([self._getkeystr(pincrackdata.in_rand),
                                self._getkeystr(pincrackdata.m_comb_key),
                                self._getkeystr(pincrackdata.s_comb_key),
                                self._getkeystr(pincrackdata.m_au_rand),
                                self._getkeystr(pincrackdata.s_au_rand),
                                self._getkeystr(pincrackdata.m_sres),
                                self._getkeystr(pincrackdata.s_sres)])
        if pincrackdata.sniffed_master:
            cmd = ' '.join([cmd, ':'.join(['%.2x' % d for d in master]), 
                        ':'.join(['%.2x' % d for d in slave]), pindatastrs])
        else:
            cmd = ' '.join([cmd, ':'.join(['%.2x' % d for d in slave]), 
                        ':'.join(['%.2x' % d for d in master]), pindatastrs])
        
        return ' '.join([''.join([BTPINCRACKDIR, os.sep, CRACKPROG]), 'Go', cmd])
    
    def _startprog(self, pincrackdata, master, slave, tmpfile):
        if os.path.exists(''.join([BTPINCRACKDIR, os.sep, CRACKPROG])):
            cmd = self._getcmd(pincrackdata, master, slave)
            log.debug("Running %s\n" % cmd)
            self.proc = subprocess.Popen(cmd, shell=True, stdout=self._tmpfile)
        else:
            raise IOError("pincrackrunner: %s not found" % BTPINCRACKDIR)
    
    def _find_pin(self, pinstr):
        '''
            Recursive method to find pin given a string.
            Written because of the weird way btpincrack formats its output.
        '''
        pindex = pinstr.find(_pincrackrunner.__PIN_HEADER)
        if pindex > -1:
           return self._find_pin(pinstr[pindex + len(_pincrackrunner.__PIN_HEADER):].strip())
        else:
            return pinstr

    def getpin(self):
        if self._tmpfile is not None:
        # To do fstat on tmpfile, we need to seek to 0 first
            self._tmpfile.seek(0)
            # Test filesize greater than 0
            if os.fstat(self._tmpfile.fileno())[6] == 0:
                log.debug("getpin() tempfile size is 0")
                raise self.__PIN_NOT_READY_EXC
        else:
            log.debug("getpin() tmpfile is None")
            raise self.__PIN_NOT_READY_EXC
            
        procout = self._tmpfile.read().strip()
        self._tmpfile.close()
        if not self.__PIN_HEADER in procout:
            raise StandardError("getpin: error with btpincrack output.\nOutput:\n%s" 
                                % procout)
        else:
            pstr = self._find_pin(procout)
            return pstr
    
        
    def terminate(self):
        # Only in Python 2.6
        if self.proc and self.proc.poll() is None:
            # If not none, already terminated
            self.proc.terminate()
    
    def is_done(self):
        if self.proc is None or self.proc.poll() is None:
            return False
        return True
        
    def get_pcd(self):
        return self._pcd
    
    def set_pcd(self, pcd):
        self._pcd = pcd
    
    def run(self):
        if self._pcd is None:
            raise Exception("Set pincrackdata first before starting")
        self._startprog(self._pcd, self._master, self._slave, self._tmpfile)
        
    pcd = property(get_pcd, set_pcd) 

        

#######################################
#     Internal methods                #
#######################################

__au_rand_from_master = True

def _gen_pincrackdata(state, op, data_list, master_add, slave_add, from_master):
    """
        Returns None when pin not ready. Otherwise return a PinCrackData
        object, that stores info relevant for pin cracking.
        
        @param state     State object
        @param op        LMP op1 code
        @data_list       List of integers representing LMP payload
        @master_add      Master device address
        @slave_add       Slave device address
    """
    
     ## Check for first cracking packet and remember its source.
     ## This is very important, so that state does not need to always
     ## be updated with the source of the latest packet like in the old
     ## implementation.
    
    if op == LMP_OP1_IN_RAND:
        __au_rand_from_master = from_master    
        
    _crack._setpindata(state, op, data_list, from_master)
    
    if not state.pinstate == 0xff:
        return None
    else:
        state.pinstate = 1
        return _create_pincrackdata(state, __au_rand_from_master)

def _create_pincrackdata(state, is_pin_master):
    pcd = PinCrackData(is_pin_master)
    type_d = {0:'in_rand', 1:'m_comb_key', 2:'s_comb_key', 3:'m_au_rand', 4:
              's_au_rand', 5:'m_sres', 6:'s_sres'}
    for i in range(7):
        length = 4 if i >= 5 else 16
        keyintlist = []
        for j in range(length):
            keyintlist.append(state.pindata[i][j])
        pcd.__setattr__(type_d[i], keyintlist)
    # print 'create_pincrackdata:\n', str(pcd)
    return pcd

