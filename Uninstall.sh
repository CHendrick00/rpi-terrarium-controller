#!/bin/bash
sudo systemctl disable terrarium-monitor.service
cd ~
sudo rm -r "$(pwd)/rpi-terrarium-controller" /var/lib/rpi-terrarium-controller
sudo rm /etc/systemd/system/terrarium-monitor.service
sudo systemctl daemon-reload


sudo killall -u username
sudo userdel -r terrarium-monitor
