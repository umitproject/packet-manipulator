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
    def create_ui(self):
        # FIXME: this should be set automatically
        self.type_id = 0

        self.sequence_page = self.add_perspective(SequencePage, True,
                                                  True, False)

        self.packet_page = self.add_perspective(PacketPage, True,
                                                True, False)

        self.reload()

        self.pack_start(self.paned)
        self.show_all()

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
