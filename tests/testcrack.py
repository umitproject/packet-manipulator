

import unittest,sys,time

import umit.bluetooth.btsniff as btsniff
import umit.bluetooth.crack as crack
import umit.bluetooth.sniffcommon as sniffcommon

from umit.bluetooth.btlayers import LMPHeader, BtRaw, BtLayerUnit

LMP = BtLayerUnit

def _show(string):
    sys.stderr.write(str(string))
    sys.stderr.write('\n')

class CrackTest(unittest.TestCase):
    '''Test internal functions of crack'''
    
    MASTER_ADD = [0x00, 0x1b, 0xaf, 0xaf, 0x84, 0x9e]
    SLAVE_ADD = [0x00, 0x1b, 0xaf, 0xaf, 0x96, 0xa4]
    IN_RAND = [0xb4, 0xf6, 0x89, 0xce, 0x76, 0x91, 0x15, 0x96, 0x49, 0x7f, 0x99,
                   0xdf, 0x93, 0xc4, 0x79, 0x32]
    M_COMB_KEY = [0x00, 0xa7, 0x61, 0x01, 0x10, 0x52, 0x0b, 0x21, 0x2f, 0x20, 0x50,
                      0x04, 0xac, 0x04, 0xce, 0x5a]
    S_COMB_KEY = [0x44, 0x9c, 0xe7, 0x36, 0x26, 0xe8, 0xdc, 0x1a, 0xb1, 0x00, 0x2b,
                      0x70, 0xa9, 0x88, 0x69, 0x53]
    M_AU_RAND = [0x13, 0x8d, 0xfb, 0xb7, 0x68, 0x8a, 0x49, 0xd1, 0xac, 0xa3, 0xc6, 0x74,
                     0xe1, 0xe1, 0x9b, 0xd5]
    S_AU_RAND = [0x0e, 0xfa, 0xd5, 0x21, 0x1a, 0x35, 0x03, 0x20, 0xd9, 0xfc, 0x14,
                     0xfe, 0x41, 0xe9,  0xab, 0x23]
    M_SRES = [0x89, 0xef, 0x46, 0x6e]
    S_SRES = [0xa6, 0x78, 0xdf, 0x62]

    def setUp(self):
#        self.session = sniffcommon.SniffSession(sniff.State(), 
#                                                self.MASTER_ADD, 
#                                                self.SLAVE_ADD, 
#                                                'hci0', None) 
        self.pincrackdata = crack.PinCrackData()
        self.pincrackdata.in_rand  = self.IN_RAND
        self.pincrackdata.m_comb_key = self.M_COMB_KEY
        self.pincrackdata.s_comb_key = self.S_COMB_KEY
        self.pincrackdata.m_au_rand = self.M_AU_RAND
        self.pincrackdata.s_au_rand = self.S_AU_RAND
        self.pincrackdata.m_sres = self.M_SRES
        self.pincrackdata.s_sres = self.S_SRES
        
    def tearDown(self):
        del self.pincrackdata

class pincrackrunnerInternalTest(CrackTest):
    
#    pcr = crack._pincrackrunner(self.pincrackdata, self.MASTER_ADD, self.SLAVE_ADD)
    
    def testRuncrack(self):
        
        import tempfile
        tmpfile = tempfile.TemporaryFile()
#        self.pcr.runcrack(self.pincrackdata, self.MASTER_ADD, self.SLAVE_ADD, 
#                          tmpfile)
        self.pcr = crack._pincrackrunner(self.pincrackdata, self.MASTER_ADD, self.SLAVE_ADD)
        self.pcr.run()
        i = 0
        while not self.pcr.is_done():
            i += 1
            if i < 3:
                _show("Sleep")
                import time
                time.sleep(5)
        pin = self.pcr.getpin()
        _show("testRuncrack: pin: %s" % pin)
        self.assertEqual(pin, '1234')


class PinCrackRunnerTest(CrackTest):
    
    def setUp(self):
        super(PinCrackRunnerTest, self).setUp()
        self.pcr = crack.PinCrackRunner(self.MASTER_ADD, self.SLAVE_ADD)
        lp1 = BtRaw()
        lp1.rawdata = self.IN_RAND
        lp2 = BtRaw()
        lp2.rawdata = self.M_COMB_KEY
        lp3 = BtRaw()
        lp3.rawdata = self.S_COMB_KEY
        lp4 = BtRaw()
        lp4.rawdata = self.M_AU_RAND
        lp5 = BtRaw()
        lp5.rawdata = self.S_AU_RAND
        lp6 = BtRaw()
        lp6.rawdata = self.M_SRES
        lp7 = BtRaw()
        lp7.rawdata = self.S_SRES
        self.payloads = [lp1, lp2, lp3, lp4, lp5, lp7, lp6]
 
        lh1 = LMPHeader(tid=1, op1=8)
        lh2 = LMPHeader(tid=1, op1=9)
        lh3 = LMPHeader(tid=1, op1=9)
        lh4 = LMPHeader(tid=1, op1=11)
        lh5 = LMPHeader(tid=1, op1=11)
        lh6 = LMPHeader(tid=1, op1=12)
        lh7 = LMPHeader(tid=1, op1=12)
        
        self.headers = [lh1, lh2, lh3, lh4, lh5, lh7, lh6]
        self.sources = ['M', 'M', 'S', 'M', 'S', 'S', 'M']
        self.lmps = []
        for header, payload in zip(self.headers, self.payloads):
            self.lmps.append(LMP(header = header, payload = payload))

    
    def test_try_crack(self):
        for i, lmp in zip(range(len(self.lmps)), self.lmps):
            _show('LMP %d' % i)
            if self.pcr.try_crack(lmp, True if self.sources[i] == 'M' else False):
                pin = self.pcr.getpin()
                _show('try_crack_test: Done! Pin: %s' % pin)
                self.assertEqual(pin, '1234')
            else:
                time.sleep(1)
        # First time failed
        # Keep trying for 30 seconds
        if self.pcr.pincrackdata is not None:
            _show("test_try_crack: pincrackdata ready")
            self.assertEqual(self.pincrackdata.in_rand, self.pcr.pincrackdata.in_rand)
            self.assertEqual(self.pincrackdata.s_comb_key, self.pcr.pincrackdata.s_comb_key)
            self.assertEqual(self.pincrackdata.m_comb_key, self.pcr.pincrackdata.m_comb_key)
            self.assertEqual(self.pincrackdata.s_au_rand, self.pcr.pincrackdata.s_au_rand)
            self.assertEqual(self.pincrackdata.m_au_rand, self.pcr.pincrackdata.m_au_rand)
            self.assertEqual(self.pincrackdata.m_sres, self.pcr.pincrackdata.m_sres)
            self.assertEqual(self.pincrackdata.s_sres, self.pcr.pincrackdata.s_sres)

        else:
            _show("test_try_crack: pincrackdata not ready")
            assert False
            
        while not self.pcr.try_crack(None, None):
            _show('Sleep')
            time.sleep(3)
        
        pin = self.pcr.getpin()
        _show("PIN! %s" % pin)
        self.pcr.terminate()
        self.assertEqual(pin, '1234')
        self.assertTrue(self.pcr.pincrackdata is not None, 'PCD is None')
            
    
    def tearDown(self):
        super(PinCrackRunnerTest, self).tearDown()
        del self.lmps
        del self.payloads
        del self.headers


if __name__ == "__main__":
    print 'running testcrack'
    unittest.main()