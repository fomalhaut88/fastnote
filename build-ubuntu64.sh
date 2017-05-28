#!/bin/bash

version=`cat version`

echo "Removing old build and dist..."
rm -rf build
rm -rf dist

echo "Pyinstaller packing..."
pyinstaller fastnote.spec --log-level WARN

echo "Compressing into .tar.gz format..."
tar -czvf dist/fastnote-ubuntu64-$version.tar.gz -C dist fastnote

echo "Creating .deb package..."
deb_pkg_dir=dist/fastnote-ubuntu64-$version
mkdir $deb_pkg_dir
mkdir $deb_pkg_dir/usr
mkdir $deb_pkg_dir/usr/bin
mkdir $deb_pkg_dir/usr/share
mkdir $deb_pkg_dir/usr/share/applications
mkdir $deb_pkg_dir/usr/share/pixmaps
mkdir $deb_pkg_dir/DEBIAN
cp dist/fastnote $deb_pkg_dir/usr/bin/
cp linux/control $deb_pkg_dir/DEBIAN/
cp linux/fastnote.desktop $deb_pkg_dir/usr/share/applications
cp fastnote.ico $deb_pkg_dir/usr/share/pixmaps
sed -i "s/Version:.*/Version: $version/" $deb_pkg_dir/DEBIAN/control
dpkg-deb --build $deb_pkg_dir
rm -r $deb_pkg_dir

echo "Completed."
