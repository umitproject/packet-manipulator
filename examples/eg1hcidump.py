import umit.bluetooth.sniff_fileio as sfio
import umit.bluetooth.sniff as sniff
import umit.bluetooth.sniffer as sniffer
import umit.bluetooth.handlers as handlers

class HCIDumpHandler(sniff.SniffHandler):
    
    def __init__(self, state, write_file, writer = None):
        super(sniff.SniffHandler, self).__init__()
        if not writer:
            writer = sfio.HCIWriter()
        self._writer = writer
        self._lmpbasehandler = handlers.BTSniffHandler()
        if state and write_file:
            self._state = state
            self._write_file = write_file
        else:
            raise sniff.SniffError("HCIDumpHandler: State or write_filename not given. state is %s, write_file is %s" 
                                   % (state, write_file))
    def _writetofile(self, type, packet):
        self._writer.writetofile(type, self._state.llid,
                                 self._state.master, packet, self._write_file)
    
    def recvgenevt(self, packet):
        self._lmpbasehandler.recvgenevt(packet)
    
    def recvlmp(self, packet):
        self._lmpbasehandler.recvlmp(packet)
        self._writetofile(sniff.HCI_EVENT_PKT, packet)
    
    def recvdv(self, packet):
        pass
    
    def recvl2cap(self, packet):
        self._writetofile(sniff.HCI_ACLDATA_PKT, packet)


if __name__=='__main__':
#    sniffer.run(handler = HCIDumpHandler(state = start_state, write_file = 'eg1hcidump.cap'),
#                state = start_state)
    hcihandler = handlers.BTSniffHandler()
    start_state = sniff.State()
    #hcihandler = HCIDumpHandler(start_state, "eg1.cap") 
    sniffer.run(handler = hcihandler, state = start_state)