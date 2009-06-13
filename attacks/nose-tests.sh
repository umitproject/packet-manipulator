#!/bin/sh
# Simple bash script to run nosetest on targets

export PYTHONPATH="$(dirname `pwd`):$PYHONPATH"
find . -name "main.py" | xargs nosetests --with-doctest
