#!/bin/sh
# Simple bash script to run nosetest on targets

trap bashtrap INT

bashtrap()
{
    mv ~/.PacketManipulator/pm-prefs.xml.bak ~/.PacketManipulator/pm-prefs.xml
}

export PYTHONPATH="$PYTHONPATH:$(dirname `pwd`)"
echo "Masking pm-prefs.xml"
mv ~/.PacketManipulator/pm-prefs.xml ~/.PacketManipulator/pm-prefs.xml.bak

if [ "$1" = "" ]; then
    echo "Running tests"
    find . -name "main.py" | xargs nosetests --with-doctest
    echo "Restoring pm-prefs.xml"
else
    echo "Running selected test ($1)"
    nosetests --with-doctest $1
fi

bashtrap
