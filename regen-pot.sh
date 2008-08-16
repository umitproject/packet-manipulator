#!/bin/sh
echo -n "Regenerating packetmanipulator.pot ... "
python scripts/i18n/pygettext.py -o packetmanipulator.pot \
PM/ PM/Backend/ PM/Backend/Abstract PM/Backend/Abstract/BaseContext \
PM/Backend/Abstract/Context PM/Backend/Scapy PM/Backend/Scapy/Context \
PM/Manager PM/Core PM/Gui PM/Gui/Core PM/Gui/Tab PM/Gui/Pages \
PM/Gui/Dialogs PM/Gui/Widgets PM/higwidgets
echo "done"
