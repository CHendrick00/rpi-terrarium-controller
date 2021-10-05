#!/bin/bash
sudo systemctl disable terrarium-*.service
sudo systemctl stop terrarium-monitor.target
cd ~
sudo rm -r "$(pwd)/rpi-terrarium-controller" /var/lib/rpi-terrarium-controller
sudo rm /etc/systemd/system/terrarium-*
sudo systemctl daemon-reload
