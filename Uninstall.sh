#!/bin/bash
sudo systemctl disable terrarium-monitor
sudo rm -r ~/rpi-terrarium-controller /var/lib/rpi-terrarium-controller
sudo rm /etc/systemd/system/terrarium-monitor.service
sudo systemctl daemon-reload
