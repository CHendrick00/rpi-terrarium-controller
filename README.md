# rpi-terrarium-controller
CircuitPython files for my highland terrarium sensors

[Pi Header Pinout Diagram](https://i.stack.imgur.com/JtpG7.png)

## PiInstall.sh
**DO NOT USE**: this file is untested and likely will not run properly

**Instructions:**
- This file is to be run on the Raspberry Pi
- To begin, run the following commands in the Pi's terminal:
```
cd ~
wget https://raw.githubusercontent.com/Night-Raider/rpi-terrarium-controller/main/PiInstall.sh
sudo chmod u+x PiInstall.sh
sudo ./PiInstall.sh
```
- Note: this process may take a while
- After installing CircuitPython, the Pi will reboot. After it reboots, run the script again with the commands:
```
cd ~
sudo ./PiInstall.sh
```
- If the install is successful, you should see the following output:
```
echo "ATTENTION: Before finishing installation, you MUST open each hardware-specific file you plan to use and change the parameters listed at the top to fit your specific situation as needed."
echo "To do this, use the command <sudo nano ~/rpi-terrarium-controller/sensors/FILENAME>, change the values as needed, then save with ctrl+s, ctrl+x"
echo "To view all sensor files installed, use the commands <cd ~/rpi-terrarium-controller/sensors>, then <ls>"
echo "To run a sensor on startup, run the command <sudo nano ~/rpi-terrarium-controller/monitor-startup.sh> and add another line using the filename of the sensor you plan to use"
echo "After adding a sensor to the startup file, simply reboot or run the command <sudo systemctl restart terrarium-monitor>"
echo "To start/stop/enable on boot/disable on boot/restart the monitoring service, run <sudo systemctl (start/stop/enable/disable/restart) terrarium-monitor>"

All of these instructions can be found again in the README on my Github repository
Note: do not include the <> characters in the commands above
```
- Be sure to follow the instructions above to finish installation
## HcsrHumidifierTemplate.py

**Use case:** measure water level in humidifier, send alerts via discord when water level falls below a specified level, and log data to InfluxDB

**Hardware:** 
- Adafruit HC-SR04 or RCWL-1601 sensor
- 22ga jumper wires OR 22ga wire spool + soldering iron

**Prerequisites:** 
- Raspberry Pi with CircuitPython and HCSR library installed [Instructions by Adafruit](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
- discord-webhook library installed via pip3 [Instructions and documentation](https://opensourcelibs.com/lib/python-discord-webhook)
- **NOTE:** above requirements can be satisfied by using PiInstall.sh
- Discord server with webhook

**Features:** 
- Discord alert with custom message when water level falls to user-specified refill level
- Specify number of repeat alerts to be sent before going silent
- Specify time between repeated alerts
- Alerts become active again when humidifier is refilled above a specified amount
- Extremely consistent readings when using default sample size (individual readings have extreme variation/outliers)
- Specifiable sample size for each aggregate (reported) reading
- Specifiable interval between readings
- Readings logged to InfluxDB

**Not implemented:**
- Alerts for multiple different water levels

## HTU31D.py
**Use case:** measure temperature and humidity, send alerts via discord when humidity falls below a specified level, and log data to InfluxDB

**Hardware:** 
- Adafruit HTU31D sensor
- 22ga jumper wires OR 22ga wire spool + soldering iron
- Adafruit STEMMA QT connector (opt.)

**Prerequisites:** 
- Raspberry Pi with CircuitPython and HCSR library installed [Instructions by Adafruit](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
- discord-webhook library installed via pip3 [Instructions and documentation](https://opensourcelibs.com/lib/python-discord-webhook)
- **NOTE:** above requirements can be satisfied by using PiInstall.sh
- Discord server with webhook
- InfluxDB / Grafana server installed on Pi or local network computer

**Features:** 
- Discord alert with custom message when humidity falls below user-specified level
- Specify number of repeat alerts to be sent before going silent
- Specify time between repeated alerts
- Alerts become active again when humidity rises above specified amount
- Specifiable interval between readings
- Readings logged to InfluxDB

**Not (yet) implemented:**
- High humidity alerts
- High/Low temperature alerts
- Different day/night alert thresholds

## TODO:
- Test PiInstall.sh
- Link to hardware in README
- Grafana/Influxdb install file, walkthrough (reverse proxy w/ apache2, port forwarding, ufw/firewalld, InfluxDB initialization, etc)
