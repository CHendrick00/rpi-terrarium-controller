#!/bin/bash

cd ~
FILE=./tmp

# install circuitpython, or skip this section if tmp file present
if [ ! -f "$FILE" ]; then

  # create tmp file when done to avoid running this section on second run
  touch tmp

  sudo apt-get update
  sudo apt-get upgrade
  sudo apt-get install python3-pip
  sudo pip3 install --upgrade setuptools

  sudo pip3 install --upgrade adafruit-python-shell
  wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
  sudo python3 raspi-blinka.py

fi

# ensure CircuitPython install was successful
sudo wget https://raw.githubusercontent.com/Night-Raider/rpi-terrarium-controller/main/blinkatest.py
python3 blinkatest.py
pip3 install --upgrade adafruit_blinka

# install required libraries
sudo pip3 install adafruit-circuitpython-hcsr04
sudo pip3 install adafruit-circuitpython-htu31d
sudo pip3 install discord-webhook
sudo pip3 install influxdb

# download sensor files
wget https://raw.githubusercontent.com/Night-Raider/rpi-terrarium-controller/main/HcsrHumidifier.py

sudo rm ./tmp

echo "ATTENTION: Before running, you MUST open each hardware-specific file and change the parameters listed at the top to fit your specific situation if needed."
echo "To do this, use the command <sudo nano \"filename\">, change the values as needed, then save with ctrl+s, ctrl+x"
echo "To view all files installed, use the command <ls>"
echo "To delete an unneeded file, use command <rm ./filename>"
echo "To run a script automatically at startup, run the command <crontab -e>, select option 1, then at the bottom of the file add the line:"
echo "<@reboot python3 ~/filename.py>, replacing filename with the name of the file to be ran"
echo "Additional files can be added to run on reboot simply by adding another line and changing the filename to match"

echo "All of these instructions can be found again in the README on my Github repository"
echo "Note: do not include the <> characters in the commands above"
