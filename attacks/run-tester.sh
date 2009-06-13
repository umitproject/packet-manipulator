#!/bin/sh
# Simple bash script to run attacktester without touching by hand PYTHONPATH

export PYTHONPATH="$(dirname `pwd`):$PYHONPATH"
python attacktester.py $*
