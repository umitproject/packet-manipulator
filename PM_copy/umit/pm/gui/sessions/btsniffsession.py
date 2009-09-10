
import gtk

from umit.pm import backend

from umit.pm.gui.sessions import SniffSession 
from umit.pm.gui.pages import BtSniffPage, BtPacketPage


class BtSniffSession(SniffSession):
    session_id = 3
    session_name = "BTSNIFF"

    def create_ui(self):
        self.sniff_page = self.add_perspective(BtSniffPage, True,
                                               True, False)

        self.btpacket_page = self.add_perspective(BtPacketPage, False,
                                                True, False)

        self.editor_cbs.insert(0, self.btpacket_page.reload)
        self.container_cbs.insert(0, self.reload_container)

        self.btpacket_page.reload()

        self.pack_start(self.paned)
        self.show_all()

    def reload_container(self, packet=None):
        # FIXME: check packet and emit a row-changed
        if not isinstance(self.context, Backend.TimedContext):
            self.sniff_page.clear()
        self.sniff_page.reload()

    def save_session(self, fname, async=True):
        # Probably hated check
        if not fname.lower().endswith('.pcap') and \
           not fname.lower().endswith('.pcap.gz'):

            log.debug('Appending .pcap.gz suffix to %s before saving.' % fname)
            fname += '.pcap.gz'

        ret = super(SniffSession, self).save_session(fname)

#        if not async:
#            if ret:
#                self.sniff_page.statusbar.image = gtk.STOCK_HARDDISK
#            else:
#                self.sniff_page.statusbar.image = gtk.STOCK_DIALOG_ERROR
#
#            self.sniff_page.statusbar.label = "<b>%s</b>" % self.context.summary
#        else:
#            self.sniff_page.statusbar.image = gtk.STOCK_HARDDISK
#            self.sniff_page.statusbar.label = "<b>Saving to %s</b>" % fname
#
#        self.sniff_page.statusbar.start_animation(True)

        return ret


  