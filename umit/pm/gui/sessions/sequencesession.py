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

from base import Session

from umit.pm import backend
from umit.pm.core.i18n import _
from umit.pm.gui.widgets.expander import AnimatedExpander

from umit.pm.gui.pages.packetpage import PacketPage
from umit.pm.gui.pages.sequencepage import SequencePage

class SequenceSession(Session):
    session_id = 0
    session_name = "SEQUENCE"

    def create_ui(self):
        self.sequence_page = self.add_perspective(SequencePage, True, True)
        self.packet_page = self.add_perspective(PacketPage, True, True)

        self.editor_cbs.insert(0, self.reload_editor)
        self.container_cbs.insert(0, self.reload_container)

        self.reload()
        super(SequenceSession, self).create_ui()

    def reload_editor(self):
        self.packet_page.reload()

    def reload_container(self, packet=None):
        self.sequence_page.reload(packet)

    def save_session(self, fname):
        if not fname.lower().endswith(".pms") and \
           not fname.lower().endswith(".pcap") and \
           not fname.lower().endswith(".pcap.gz"):
            fname += ".pms"

        # Reinsert the values into the sequence
        self.context.set_sequence(self.sequence_page.get_current_tree())
        return super(SequenceSession, self).save_session(fname)
