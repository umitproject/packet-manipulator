'''
Created on Jul 22, 2009

@author: qsy
'''

import  btsniff
import sniffer
import crack
import btlayers

from sniffcommon import * 


## This code for taking out of PM, so we do not need to change any code
try:
    from packet import BtMetaPacket
except ImportError:
    class BtMetaPacket(object):
        
        def _init__(self, unit):
            self.pkt = unit 

        def __getattr__(self, name):
            return getattr(self.pkt, name)

class CollectHandler(btsniff.SniffHandler):
    
    def __init__(self):
        self.data = []

    def recvgenevt(self, unit):
        self.data.append(BtMetaPacket(unit))
    
    def recvlmp(self, unit):
        self.recvgenevt(unit)
    
    def recvdv(self, unit):
        self.recvgenevt(unit)
    
    def recvl2cap(self, unit):
        self.recvgenevt(unit)

    def clear_data(self):
        self.data = []


class PinCrackCollectHandler(CollectHandler):
    
    def __init__(self, master_add, slave_add):
        super(PinCrackCollectHandler, self).__init__()
        self._capstate = btsniff.CaptureState()
        self._pcr = crack.PinCrackRunner(master_add, slave_add, self._capstate)
        self._pin = None
    
    def recvlmp(self, unit):
         super(PinCrackCollectHandler, self).recvlmp(unit)
         # Optimize for more speed
         lmp = unit.payload
         if lmp.header.op1 in crack.LMP_PINCRACK_OPCODES \
            and self._pcr.try_crack(lmp):
             self._pin = self._pcr.getpin()
        

class TextHandler(btsniff.SniffHandler):
    '''
        This handler duplicates the functionality of Frontline. 
        Allows the calculation of a pin   
    '''
    def __init__(self, do_pin = False, 
                 master_add = None, slave_add = None, writer = None):
        
        super(TextHandler, self).__init__()
        self._state = btsniff.CaptureState()
        if do_pin:
            print 'do_pin'
            self._state.pinstate = 1
            self._pcr = crack.PinCrackRunner(master_add, slave_add)
            if master_add is None or slave_add is None:
                raise Exception('Error: cannot do_pin without master/slave addresses')
        else:
            self._pcr = None
#        if not writer:
#            writer = sfio.HCIWriter()
        self._writer = writer
#        if session:
#            self._session = session
#            self._write_file = session.dump
#        else:
#            raise sniff.SniffError("FrontlineHandler: Session not given. session is %s" 
#                                   % session)
         

    def _writetofile(self, type, packet):
        pass
#        self._writer.writetofile(hcipkttype = type, llid = self._session.state.llid,
#                                 ismaster = self._session.state.master, packet = packet, filename = self._write_file)
        
    def _printpktdetails(self, packet):
        """
            Parameters:
            packet    -    sniff.SniffPacket
        """
        master = not (packet.clock & FP_SLAVE_MASK)
        header_len = packet.header_len
        channel = packet.chan
        clock = packet.clock
        status = packet.status
        hdr0 = packet.header_byte0
        type = packet.type
        address = packet.address
        llid = packet.llid
        length = packet.payload_len
        
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

    def _printpayload(self, payload):
        print ' '.join(['%.2x' % d for d in payload.rawdata])
    
    def recvlmp(self, packet):
        self._printpktdetails(packet)
        lmp = packet.payload
        if lmp:
            print 'LMP Tid %d, Op1 %d' % (lmp.header.tid, lmp.header.op1),
            if lmp.header.op1 >= 124 and lmp.header.op1 <= 127:
                print ', Op2 %d' % (lmp.header.op2),
            print ' '.join(['%.2x' % d for d in lmp.payload.rawdata])
            
            if self._pcr and self._pcr.try_crack(lmp):
                print 19 * '='
                print 'Pin: ', self._pcr.getpin()
                print 19 * '='
            
        else:
            print
        
#            pcd = crack._gen_pincrackdata(self._state, lmp.header.op1, lmp.payload.rawdata,
#                                 self._session.master, self._session.slave)
#            print '============== pindata state ============'
#            print self._session.state.pindata
#            print '========================================='
#            if pcd:
#                if pcd.ready_to_crack():
#                    print 'Pin: ', self.getpin(pcd)
#                else:
#                    raise StandardError('recvlmp: dopin: pairing process complete but no pin crack.')
    
    def getpin(self, pincrackdata):
        import tempfile
        tmpfile = tempfile.TemporaryFile()
        pcr = crack._pincrackrunner() # This is a thread. runcrack is actually thread.start()
        evt = pcr.runcrack(pincrackdata, self._session.master, 
                           self._session.slave, tmpfile)
        evt.wait()
        return pcr.getpin()
        
    
    def recvl2cap(self, packet):
        self._printpktdetails(packet)
        print "L2CAP:",
#        self._printgenpkt(packet.payload)
        self._printpayload(packet.payload)
    
    def recvdv(self, packet):
        self._printpktdetails(packet)
        print 'DV:',
        self._printgenpkt(packet.payload)
        
    
    def recvgenevt(self, packet):
        self._printpktdetails(packet)




