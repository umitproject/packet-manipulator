'''
Created on Jul 22, 2009

@author: qsy
'''

import sniff
import sniffer
import crack
import sniff_fileio as sfio

from sniffcommon import * 

class BTSniffHandler(sniff.SniffHandler):
    """
        Subclassed SniffHandler can be wired to handle recvpacket events
    """
    def __init__(self):
        super(sniff.SniffHandler, self).__init__()
    
    def recvgenevt(self, packet):
        """
            Parameters:
            packet    -    sniff.SniffPacket
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
    
    def recvdv(self, packet):
        pass
    def recvl2cap(self, packet):
        self.recvdv(packet)
        
    def recvlmp(self, packet):
        """
            Do duplicate printing as to the original frontline tool. Used to manually diff the 2 outputs
            This can be modified to do anything we wish with the received packet.
        """
        self.recvgenevt(packet)
        # Process payload. We watch for LMPs
        if packet.payload:
            paypkt = sniffer.LMPPacket(packet.payload)
            print str(paypkt)
        else: print 
    

class FrontlineHandler(sniff.SniffHandler):
    '''
        This handler duplicates the functionality of Frontline.    
    '''
    def __init__(self, session, writer = None):
        super(sniff.SniffHandler, self).__init__()
        if not writer:
            writer = sfio.HCIWriter()
        self._writer = writer
        if session:
            self._session = session
            self._write_file = session.dump
        else:
            raise sniff.SniffError("FrontlineHandler: Session not given. session is %s" 
                                   % session)
         

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
                            
    def _printgenpkt(self, genpkt):
        pstr = ''
        payloadstr = (len(genpkt.data) * '%.2X ' % tuple(genpkt.data)) if len(genpkt.data) else None
        print ' '.join([pstr, payloadstr if payloadstr else ''])

    
    def recvlmp(self, packet):
        self._printpktdetails(packet)
        paypkt = None
        if packet.payload:
            paypkt = sniffer.LMPPacket(packet.payload)
            print str(paypkt)
        else:
            print
            
        if self._session.state.pinstate:
            print 'do pin'
            pcd = crack._gen_pincrackdata(self._session.state, paypkt.op1, paypkt.data,
                                 self._session.master, self._session.slave)
#            print '============== pindata state ============'
#            print self._session.state.pindata
#            print '========================================='
            if pcd:
                if pcd.ready_to_crack():
                    print 'Pin: ', self.getpin(pcd)
                else:
                    raise StandardError('recvlmp: dopin: pairing process complete but no pin crack.')
        self._writetofile(sniff.HCI_EVENT_PKT, packet)
    
    def getpin(self, pincrackdata):
        import tempfile
        tmpfile = tempfile.TemporaryFile()
        pcr = crack.PinCrackRunner() # This is a thread. runcrack is actually thread.start()
        evt = pcr.runcrack(pincrackdata, self._session.master, 
                           self._session.slave, tmpfile)
        evt.wait()
        return pcr.getpin()
        
    
    def recvl2cap(self, packet):
        self._printpktdetails(packet)
        print "L2CAP:",
        self._printgenpkt(packet.payload)
        self._writetofile(sniff.HCI_ACLDATA_PKT, packet)
    
    def recvdv(self, packet):
        self._printpktdetails(packet)
        print 'DV:',
        self._printgenpkt(packet.payload)
        
    
    def recvgenevt(self, packet):
        self._printpktdetails(packet)



class SimpleHandler(sniff.SniffHandler):
    '''
        This handler duplicates the functionality of Frontline.    
    '''
    def __init__(self, session):
        super(sniff.SniffHandler, self).__init__()
        self._session = session

    
    def recvlmp(self, packet):
        print 'SimpleHandler::recvlmp::',
        if self._session.state.pinstate:
            print 'Will do pin' 
        
    
    def recvl2cap(self, packet):
        print 'SimpleHandler::recvl2cap::'
    
    def recvdv(self, packet):
        print "SimpleHandler::recvdv"
        
    
    def recvgenevt(self, packet):
        print "SimpleHandler::recvgenevt"


