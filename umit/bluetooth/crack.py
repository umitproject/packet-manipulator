'''
Created on Jul 21, 2009

@author: qsy
'''
import sniffcommon 
import _crack
import subprocess, os, re, threading, string

BTPINCRACKDIR = 'btpincrack-v0.3'
CRACKPROG = 'btpincrack'

def gen_pincrackdata(state, op, data_list, master_add, slave_add):
    """
        Returns None when pin not ready. Otherwise return a sniffcommon.PinCrackData
        object, that stores info relevant to pin cracking.
        Parameters:
            state         - sniffer.State object
            op            - is the op1 code for the corresponding LMP PDU
            data_list     - LMP PDU payload as a list of integers
            master_add    - list of integers representing master MAC
            slave_add     - list of integers representing slave MAC
    """
    _crack._setpindata(state, op, data_list)
    
    # Only print when condition is met
    if not state.pinstate == 0xff:
        return None
    else:
        # TODO : populate the PinCrackData object and return
        state.pinstate = 1
        return _create_pincrackdata(state)
        
#        print "done: dataprintout"
#        print state.pindata
    
#    for i in range(7):
#        length  =  4 if i >= 5 else 16
#        pdsubstr = ''
#        for j in range(length):
#            pdsubstr = ''.join([pdsubstr, '%.2x' % state.pindata[i][j]])
#        
#        pindatastrs = ' '.join([pindatastrs, pdsubstr])
#    
#    cmd = BTPINCRACKDIR + os.sep + CRACKPROG + ' Go'    
#    if state.pinmaster:
#        cmd = ' '.join([cmd, ':'.join(['%.2x' % d for d in master_add]), 
#                        ':'.join(['%.2x' % d for d in slave_add]), pindatastrs])
#    else:
#        cmd = ' '.join([cmd, ':'.join(['%.2x' % d for d in slave_add]), 
#                        ':'.join(['%.2x' % d for d in master_add]), pindatastrs])
#    ##
#    ##    TODO: We should have pincracking done in a separate thread.
#    ##    Otherwise, there will be unnecessary delay to sniffing
#    ##
#    if os.path.exists(BTPINCRACKDIR + os.sep + CRACKPROG):
#        
#        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
#        procout = proc.communicate()[0]
#        
#        pinp = re.compile(r'pin:\s*(\d+)')
#        pin = pinp.search(procout)
#        
#        if pin and len(pin.groups()) == 1:
#            print 'found pin: %s' % pin.group(1)
#            return pin.group(1)
#        else:
#            raise StandardError("breakpin: regex error")
#    else:
#        print 'breakpin: not found'
#        raise IOError("breakpin: %s not found" % BTPINCRACKDIR)


#######################################
#     Internal classes and methods    #
#######################################

def _create_pincrackdata(state):
    pcd = sniffcommon.PinCrackData(not state.pinmaster == 0 )
    type_d = {0:'in_rand', 1:'m_comb_key', 2:'s_comb_key', 3:'m_au_rand', 4:
              's_au_rand', 5:'m_sres', 6:'s_sres'}
    for i in range(7):
        length = 4 if i >= 5 else 16
        keyintlist = []
        for j in range(length):
            keyintlist.append(state.pindata[i][j])
        pcd.__setattr__(type_d[i], keyintlist)
    print 'create_pincrackdata:\n', str(pcd)
    return pcd

class PinCrackRunner(threading.Thread):
    
    _PIN_HEADER = 'pin:'
    def __init__(self):
        """
            Parameters: 
            
            tempfile        Temporary file object that will be used to store the
                            results of the pincracking. Rationale: using 
                            subporcess.Popen with stdout = PIPE returns 
                            erroneous result. We are trying with tempfile to 
                            correct that.
                            
            pincrackdata    Stores the results of gen_pincrack_data
            
            master_add      List of integers representing master MAC
            
            slave_add       List of integers representing slave MAC
            
        """
        super(PinCrackRunner, self).__init__()
        self._pcd = self._master = self._slave = None
        self._tmpfile = None
        self.evt = threading.Event()
    
    
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
            proc = subprocess.Popen(cmd, shell=True, stdout=tmpfile)
            proc.wait()
            self.evt.set()
            self.evt.clear()
        else:
            raise IOError("pincrackrunner: %s not found" % BTPINCRACKDIR)
    
    def _find_pin(self, pinstr):
        '''
            Recursive method to find pin given a string.
            Written because of the weird way btpincrack formats its output.
        '''
        pindex = pinstr.find(PinCrackRunner._PIN_HEADER)
        if pindex > -1:
           return self._find_pin(pinstr[pindex + len(PinCrackRunner._PIN_HEADER):].strip())
        else:
            return pinstr
    
    def getpin(self):
        self._tmpfile.seek(0)
        procout = self._tmpfile.read().strip()
        self._tmpfile.close()
        if not PinCrackRunner._PIN_HEADER in procout:
            raise StandardError("getpin: error with btpincrack output.\nOutput:\n%s" 
                                % procout)
        else:
            pstr = self._find_pin(procout)
            return pstr
    
    def runcrack(self, pincrackdata, master_add, slave_add, tmpfile = None):
        '''
            Usage: call runcrack and receive threading.Event object. 
            Wait on object to determine when pin-cracking is complete. Then call
            PinCrackRunner.getpin() for the computed pin.
        '''
        self._pcd, self._master, self._slave = pincrackdata, master_add, slave_add
        if not tmpfile:
            import tempfile
            tmpfile = tempfile.TemporaryFile()
        self._tmpfile = tmpfile
        self.start()
        return self.evt
    
    def run(self):
        self._startprog(self._pcd, self._master, self._slave, self._tmpfile) 