#!/bin/sh
grep -n "TODO\|FIXME" PM/* -R | grep -v [.]svn
