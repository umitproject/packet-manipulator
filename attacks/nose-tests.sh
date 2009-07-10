#!/bin/sh
# Simple bash script to run nosetest on targets

export PYTHONPATH="$(dirname `pwd`):$PYHONPATH"
echo "Masking pm-prefs.xml"
mv ~/.PacketManipulator/pm-prefs.xml ~/.PacketManipulator/pm-prefs.xml.bak
echo "Running tests"
find . -name "main.py" | xargs nosetests --with-doctest
echo "Restoring pm-prefs.xml"
mv ~/.PacketManipulator/pm-prefs.xml.bak ~/.PacketManipulator/pm-prefs.xml
