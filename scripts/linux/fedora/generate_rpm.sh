#!/bin/sh
python setup.py bdist_rpm --spec-only \
    --packager="Francesco Piccinno <stack.box@gmail.com>" \
    --requires="python2 pygtk2" \
    --build-requires="gtk2-devel pango-devel python2-devel" \
    --group="Applications/Internet"
sed -ie 's/UNKNOWN/PacketManipulator is a graphical frontend really useful\
for advanced users and easy to use for newbies. With\
PacketManipulator, network admin can forge custom\
packets and send them over the wire to analyze the\
network, sniff on a selected interface or simply edit\
a pcap file for further replay./' dist/PacketManipulator.spec
sed -ie '/BuildArch/d' dist/PacketManipulator.spec

echo '%_unpackaged_files_terminate_build 0' >> ~/.rpmmacros

python setup.py sdist

cd dist
mkdir -p ~/rpmbuild/SOURCES
cp PacketManipulator-*.tar.gz ~/rpmbuild/SOURCES

rpmbuild -vv -bb PacketManipulator.spec --clean

echo
echo "################################################################################"
echo "# Your RPM package is under ~/rpmbuild/RPMS/"
echo "################################################################################"
echo
