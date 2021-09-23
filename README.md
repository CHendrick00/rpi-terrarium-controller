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
ATTENTION: Before running, you MUST open each hardware-specific file and change the parameters listed at the top to fit your specific situation if needed.
To do this, use the command <sudo nano "filename\", change the values as needed, then save with ctrl+s, ctrl+x
To view all files installed, use the command <ls>
To delete an unneeded file, use command <rm ./filename>
To run a script automatically at startup, run the command <crontab -e>, select option 1, then at the bottom of the file add the line:
<@reboot python3 ~/filename.py>, replacing filename with the name of the file to be ran
Additional files can be added to run on reboot simply by adding another line and changing the filename to match

All of these instructions can be found again in the README on my Github repository
Note: do not include the <> characters in the commands above
```
- Be sure to follow the instructions above to finish installation
## HcsrHumidifierTemplate.py

**Use case:** measure water level in humidifer and send an alert via a discord webhook when the tank is almost empty (or falls below a specified level)

**Hardware:** 
- Adafruit HC-SR04 or RCWL-1601 sensor
- female-female jumper wires OR 22ga wire + soldering iron

**Prerequisites:** 
- Raspberry Pi with CircuitPython and HCSR library installed [Instructions by Adafruit](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
- discord-webhook library installed via pip3 [Instructions and documentation](https://opensourcelibs.com/lib/python-discord-webhook)
- **NOTE:** above requirements can be satisfied by using PiInstall.sh
- Discord server with webhook

**Features:** 
- Discord alert with custom message when water level reaches user-specified refill level
- Specify number of alerts to be sent after consecutive measurements before going silent
- Alerts become active again when the water level reading rises by a specified amount
- Extremely consistent readings when using default sample size (individual readings have extreme variation/outliers)
- Specifiable sample size for each aggregate (reported) reading
- Specifiable interval between readings

**Not implemented:**
- Alerts for multiple different water levels / report % capacity
- Logging values to a database
- Led indicator when taking readings

## TODO:
- HTU31 sensor file
- Test PiInstall.sh
- Write and test an InfluxDB/Grafana install script
- Link to hardware in README
- Grafana/Influxdb install file, walkthrough (reverse proxy w/ apache2, port forwarding, ufw/firewalld, db initialization, etc)
