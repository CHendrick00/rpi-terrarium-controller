# rpi-terrarium-controller
CircuitPython files for my highland terrarium sensors

[Pi Header Pinout Diagram](https://i.stack.imgur.com/JtpG7.png)

## HcsrHumidifierTemplate.py

**Use case:** measure water level in humidifer and send an alert via a discord webhook when the tank is almost empty (or at a specified level)

**Hardware:** 
- Adafruit HC-SR04 or RCWL-1601 sensor
- female-female jumper wires OR 22ga wire + soldering iron

**Prerequisites:** 
- Raspberry Pi with CircuitPython and HCSR library installed [Instructions by Adafruit](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi)
- discord-webhook library installed via pip3 [Instructions and documentation](https://opensourcelibs.com/lib/python-discord-webhook)
- Discord server with webhook

**Features:** 
- Discord alert with custom message when water level reaches user-specified refill level
- Specify number of alerts to be sent after consecutive measurements before going silent
- Alerts become active again when the water level reading rises by a specified amount
- Extremely consistent reaings when using default sample size (individual readings have extreme variation/outliers)
- Specifiable sample size for each aggregate (reported) reading
- Specifiable interval between readings

**Not implemented:**
- Alerts for multiple different water levels / report % capacity
- Logging values to a database
- Led indicator when taking readings

## TODO:
- SHT4x sensor file
- install/setup bash script
