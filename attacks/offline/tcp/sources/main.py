"""
TCP protocol dissector
"""

from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *
from PM.Core.NetConst import *

@coroutine
def tcp_decoder():
    try:
        while True:
            mpkt = yield
    except GeneratorExit:
        pass

class TCPDecoder(Plugin, OfflineAttack):
    def start(self, reader):
        self._decoder = tcp_decoder()

    def stop(self):
        pass

    def register_decoders(self):
        AttackManager().add_decoder(PROTO_LAYER, NL_TYPE_TCP, self._decoder)

__plugins__ = [TCPDecoder]