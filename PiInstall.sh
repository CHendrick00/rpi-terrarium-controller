#!/bin/bash

cd ~
FILE=./tmp

# install circuitpython, or skip this section if tmp file present
if [ ! -f "$FILE" ]; then

  # create tmp file when done to avoid running this section on second run
  sudo touch tmp

  sudo apt-get update
  sudo apt-get upgrade
  sudo apt-get install python3-pip
  sudo pip3 install --upgrade setuptools

  sudo pip3 install --upgrade adafruit-python-shell
  wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
  echo "The system will restart after completing the following step."
  echo "Please run this script one more time after the device restarts to finish installation."
  echo "To acknowledge and continue, press any key..."
  read -n 1 -s
  sudo python3 raspi-blinka.py

fi

# ensure CircuitPython install was successful
cd ~
sudo rm ./tmp
sudo rm ./raspi-blinka.py
cd ~/rpi-terrarium-controller
python3 blinkatest.py
sudo rm ./blinkatest.py
pip3 install --upgrade adafruit_blinka

# install required libraries
sudo pip3 install adafruit-circuitpython-hcsr04
sudo pip3 install adafruit-circuitpython-htu31d
sudo pip3 install discord-webhook
sudo pip3 install influxdb

cd ~
mv ./rpi-terrarium-controller /var/lib/rpi-terrarium-controller
cd /var/lib/rpi-terrarium-controller
sudo chmod u+x monitor-startup.sh
ln ./terrarium-monitor.service /etc/systemd/system/terrarium-monitor.service
cd /var/lib
sudo ln -s ./rpi-terrarium-controller ~/rpi-terrarium-controller
cd ~

sudo systemctl daemon-reload
sudo systemctl enable terrarium-monitor.service
sudo systemctl start terrarium-monitor.service


echo "ATTENTION: Before finishing installation, you MUST open each hardware-specific file you plan to use and change the parameters listed at the top to fit your specific situation as needed."
echo "To do this, use the command <sudo nano ~/rpi-terrarium-controller/sensors/FILENAME>, change the values as needed, then save with ctrl+s, ctrl+x"
echo "To view all sensor files installed, use the commands <cd ~/rpi-terrarium-controller/sensors>, then <ls>"
echo "To run a sensor on startup, run the command <sudo nano ~/rpi-terrarium-controller/monitor-startup.sh> and add another line using the filename of the sensor you plan to use"
echo "After adding a sensor to the startup file, simply reboot or run the command <sudo systemctl restart terrarium-monitor>"
echo "To start/stop/enable on boot/disable on boot/restart the monitoring service, run <sudo systemctl (start/stop/enable/disable/restart) terrarium-monitor>"
echo "If your Pi uses a username other than the default <pi>, you need to change the <User> field in ./rpi-terrarium-controller/terrarium-monitor.service"

echo "All of these instructions can be found again in the README on my Github repository"
echo "Note: do not include the <> characters in the commands above"
