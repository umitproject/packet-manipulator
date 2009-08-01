

import unittest

import umit.bluetooth.sniff as sniff
import umit.bluetooth.crack as crack
import umit.bluetooth.sniffcommon as sniffcommon

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
        self.session = sniffcommon.SniffSession(sniff.State(), 
                                                self.MASTER_ADD, 
                                                self.SLAVE_ADD, 
                                                'hci0', None) 
        self.pincrackdata = sniffcommon.PinCrackData()
        self.pincrackdata.in_rand  = self.IN_RAND
        self.pincrackdata.m_comb_key = self.M_COMB_KEY
        self.pincrackdata.s_comb_key = self.S_COMB_KEY
        self.pincrackdata.m_au_rand = self.M_AU_RAND
        self.pincrackdata.s_au_rand = self.S_AU_RAND
        self.pincrackdata.m_sres = self.M_SRES
        self.pincrackdata.s_sres = self.S_SRES
        
    def tearDown(self):
        del self.session

class PinCrackRunnerTest(CrackTest):
    
    pcr = crack.PinCrackRunner()
    
    def testRuncrack(self):
        import tempfile
        tmpfile = tempfile.TemporaryFile()
        self.pcr.runcrack(self.pincrackdata, self.session.master, self.session.slave, 
                          tmpfile).wait()
        self.assertEqual(self.pcr.getpin(), '1234')



if __name__ == "__main__":
    unittest.main()