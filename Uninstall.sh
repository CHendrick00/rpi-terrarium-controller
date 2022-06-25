#!/bin/bash
for i in /etc/systemd/system/terrarium*.service; do
    sudo systemctl disable $i
done
sudo systemctl stop terrarium-monitor.target
cd ~
sudo rm -r "$(pwd)/rpi-terrarium-controller" /var/lib/rpi-terrarium-controller
find /etc/systemd/system/ -name "terrarium-*" -exec sudo rm -r {} \;
sudo systemctl daemon-reload
