#!/bin/bash

#Installation for DS18B20 Probe
if ! grep -q dtoverlay=w1-gpio "/boot/config.txt"; then
  sudo echo "dtoverlay=w1-gpio" >> /boot/config.txt
  pip3 install python-kasa
  echo "The system needs to restart."
  echo "Please run this script one more time after the device restarts to finish installation."
  echo "To acknowledge and continue, press any key..."
  read -n 1 -s
  sudo reboot
else
  sudo modprobe w1-gpio
  sudo modprobe w1-therm
  kasa discover
fi
