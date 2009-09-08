#!/bin/sh
echo -n "Regenerating packetmanipulator.pot ... "
python scripts/i18n/pygettext.py -o packetmanipulator.pot PM
echo "done"
