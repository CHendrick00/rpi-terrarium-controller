#!/bin/bash
sudo systemctl disable terrarium-*.service
sudo systemctl stop terrarium-monitor.target
cd ~
sudo rm -r "$(pwd)/rpi-terrarium-controller" /var/lib/rpi-terrarium-controller
find /etc/systemd/system/ -name "terrarium-*" -exec sudo rm -r {} \;
sudo systemctl daemon-reload
