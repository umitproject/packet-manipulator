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

from PM.Gui.Pages.PacketPage import PacketPage
from PM.Gui.Pages.SequencePage import SequencePage

class SequenceSession(Session):
    def create_ui(self, show_packet=True, show_sequence=True):
        self.vpaned = gtk.VPaned()

        self.sequence_page = SequencePage(self)
        self.packet_page = PacketPage(self)

        self.perspectives = [self.sequence_page, self.packet_page]

        self.packet_expander   = AnimatedExpander(self.packet_page.title,
                                                  self.packet_page.icon)
        self.sequence_expander = AnimatedExpander(self.sequence_page.title,
                                                  self.sequence_page.icon)

        self.vpaned.pack1(self.sequence_expander, True, False)
        self.vpaned.pack2(self.packet_expander, True, False)

        self.packet_expander.add_widget(self.packet_page, show_packet)
        self.sequence_expander.add_widget(self.sequence_page, show_sequence)

        self.pack_start(self.vpaned)
        self.show_all()

        self.reload()

    def reload_editor(self):
        self.packet_page.reload()

    def reload_container(self, packet=None):
        self.sequence_page.reload(packet)

    def save_session(self, fname):
        if not fname.lower().endswith(".pms"):
            fname += ".pms"

        # Reinsert the values into the sequence
        self.context.set_sequence(self.sequence_page.get_current_tree())
        return super(SequenceSession, self).save_session(fname)
