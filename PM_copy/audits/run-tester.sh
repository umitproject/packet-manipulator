#!/bin/sh
# Simple bash script to run attacktester without touching by hand PYTHONPATH

trap bashtrap INT

bashtrap()
{
    mv ~/.PacketManipulator/pm-prefs.xml.bak ~/.PacketManipulator/pm-prefs.xml
}

export PYTHONPATH="$PYTHONPATH:$(dirname `pwd`)"
echo "Masking pm-prefs.xml"
mv ~/.PacketManipulator/pm-prefs.xml ~/.PacketManipulator/pm-prefs.xml.bak
python audittester.py $*
bashtrap
