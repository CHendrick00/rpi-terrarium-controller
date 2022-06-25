#!/bin/bash

cd ~
FILE=./tmp

# install circuitpython, or skip this section if tmp file present
if [ ! -f "$FILE" ]; then

  # create tmp file when done to avoid running this section on second run
  sudo touch tmp

  sudo apt update
  sudo apt install python3-pip -y
  sudo pip3 install --upgrade setuptools

  sudo pip3 install --upgrade adafruit-python-shell
  wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
  echo "The system will restart after completing the following step."
  echo "Please run this script one more time after the device restarts to finish installation."
  echo "To acknowledge and continue, press any key..."
  read -n 1 -s
  sudo python3 raspi-blinka.py

fi

if [ ! -f "/etc/systemd/system/terrarium-monitor.target" ] && [ -d ~/rpi-terrarium-controller ]; then
  # ensure CircuitPython install was successful
  cd ~
  sudo rm ./tmp
  sudo rm ./raspi-blinka.py
  cd ~/rpi-terrarium-controller
  python3 blinkatest.py
  sudo rm ./blinkatest.py
  pip3 install --upgrade adafruit_blinka

  # install required libraries
  if [ ! -d /usr/share/doc/libgpiod2 ]; then
    sudo apt install libgpiod2 -y
  fi
  if [ ! -f /usr/local/lib/python3.7/dist-packages/adafruit_hcsr04.py ]; then
    sudo pip3 install adafruit-circuitpython-hcsr04
  fi
  if [ ! -f /usr/local/lib/python3.7/dist-packages/adafruit_htu31d.py ]; then
    sudo pip3 install adafruit-circuitpython-htu31d
  fi
  if [ ! -d /usr/local/lib/python3.7/dist-packages/discord_webhook ]; then
    sudo pip3 install discord-webhook
  fi
  if [ ! -d /usr/local/lib/python3.7/dist-packages/influxdb ]; then
    sudo pip3 install influxdb
  fi

  cd ~
  sudo rm -r /var/lib/rpi-terrarium-controller
  sudo mv ./rpi-terrarium-controller /var/lib/rpi-terrarium-controller
  cd /var/lib/rpi-terrarium-controller
  sudo chmod u+x Uninstall.sh
  find /etc/systemd/system/ -name "terrarium-*" -exec sudo rm -r {} \;
  sudo mkdir /etc/systemd/system/terrarium-monitor.target.wants
  find /var/lib/rpi-terrarium-controller/services/ -name "terrarium-*" -exec sudo ln '{}' /etc/systemd/system/ \;
  find /var/lib/rpi-terrarium-controller/services/ -name "terrarium-*.service" -exec sudo ln '{}' /etc/systemd/system/terrarium-monitor.target.wants/ \;
  cd ~
  sudo ln -s /var/lib/rpi-terrarium-controller "$(pwd)/rpi-terrarium-controller"

  sudo systemctl daemon-reload
  find /etc/systemd/system/ -name "terrarium-*.service" -exec sudo systemctl enable {} \;
  sudo systemctl start terrarium-monitor.target

elif [ -f "/etc/systemd/system/terrarium-monitor.target" ]; then
  echo "All installation steps have been run previously. If you wish to reinstall, please run the uninstall script first."

elif [ ! -d ~/rpi-terrarium-controller ]; then
  echo "Required files could not be found at ~/rpi-terrarium-controller. Please redownload or move them to this location."
fi


echo "ATTENTION: Before finishing installation, you MUST open each hardware-specific file you plan to use and change the parameters listed at the top to fit your specific situation as needed."
echo "To do this, use the command <sudo nano ~/rpi-terrarium-controller/sensors/FILENAME>, change the values as needed, then save with ctrl+s, ctrl+x"
echo "To view all sensor files installed, use the commands <cd ~/rpi-terrarium-controller/sensors>, then <ls>"
echo "To run a sensor on startup, run the command <sudo nano ~/rpi-terrarium-controller/monitor-startup.sh> and add another line using the filename of the sensor you plan to use"
echo "After adding a sensor to the startup file, simply reboot or run the command <sudo systemctl restart terrarium-monitor>"
echo "To start/stop/enable on boot/disable on boot/restart the monitoring service, run <sudo systemctl (start/stop/enable/disable/restart) terrarium-monitor>"
echo "If your Pi uses a username other than the default <pi>, you need to change the <User> field in ./rpi-terrarium-controller/terrarium-monitor.service"

echo "All of these instructions can be found again in the README on my Github repository"
echo "Note: do not include the <> characters in the commands above"
