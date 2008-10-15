# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import gtk

from Base import Session

from PM import Backend
from PM.Core.I18N import _
from PM.Gui.Widgets.Expander import AnimatedExpander

from PM.Gui.Pages.SniffPage import SniffPage
from PM.Gui.Pages.PacketPage import PacketPage

class SniffSession(Session):
    def create_ui(self):
        self.type_id = 1

        self.sniff_page = self.add_perspective(SniffPage, True,
                                               True, False)

        self.packet_page = self.add_perspective(PacketPage, False,
                                                True, False)

        self.packet_page.reload()

        self.pack_start(self.paned)
        self.show_all()

    def reload_editor(self):
        self.packet_page.reload()

    def reload_container(self, packet=None):
        # FIXME: check packet and emit a row-changed
        if not isinstance(self.context, Backend.TimedContext):
            self.sniff_page.clear()
        self.sniff_page.reload()

    def save_session(self, fname):
        if not fname.lower().endswith('.pcap') or \
           not fname.lower().endswith('.pcap.gz'):
            fname += '.pcap.gz'

        ret = super(SniffSession, self).save_session(fname)

        if ret:
            self.sniff_page.statusbar.image = gtk.STOCK_HARDDISK
        else:
            self.sniff_page.statusbar.image = gtk.STOCK_DIALOG_ERROR

        self.sniff_page.statusbar.label = "<b>%s</b>" % self.context.summary
        self.sniff_page.statusbar.start_animation(True)

        return ret
