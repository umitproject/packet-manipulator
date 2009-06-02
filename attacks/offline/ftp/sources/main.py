"""
FTP protocol dissector (Offline attack)
"""

from PM.Core.Logger import log
from PM.Gui.Plugins.Engine import Plugin
from PM.Manager.AttackManager import *

@coroutine
def tcp_decoder():
    while True:
        try:
            mpkt = yield

            log.debug("I've received a metapacket %s" % mpkt)
        except GeneratorExit:
            pass

class TCPDissector(Plugin, OfflineAttack):
    def start(self, reader):
        self._decoders = (tcp_decoder, )

    def stop(self):
        pass

    def register_decoders(self):
        AttackManager().add_decoder(LINK_LAYER, IL_TYPE_ETH, tcp_decoder())

__plugins__ = [TCPDissector]