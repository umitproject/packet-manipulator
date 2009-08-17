#!/bin/sh
# Be sure to run this script from a clean svn trunk

python setup.py sdist
cd dist
tar zvxf PacketManipulator*.tar.gz > extract.log
cd PacketManipulator*
cp -R ../../scripts/linux/ubuntu/debian .
dpkg-buildpackage
cd ../../..
