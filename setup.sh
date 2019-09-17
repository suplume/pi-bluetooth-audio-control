#!/bin/bash

cd $(dirname $0)

sudo apt-get install python-gobject pi-bluetooth bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y
sudo cp org.acontrol.bthidservice.conf /etc/dbus-1/system.d/
sudo service dbus restart

echo "Done!"
