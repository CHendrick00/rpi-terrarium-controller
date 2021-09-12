# rpi-terrarium-controller
CircuitPython files for my highland terrarium sensors

HcsrHumidifierTemplate.py:

Use case: measure water level in humidifer and send an alert via a discord webhook when the tank is almost empty (or at a specified level)

Hardware: Adafruit HC-SR04 or RCWL-1601 sensor

Prerequisites: Raspberry Pi with CircuitPython and HCSR library installed, discord-webhook installed via pip3

Features: 
Discord alert with custom message when water level reaches user-specified refill level
Specify number of alerts to be sent after consecutive measurements before going silent
Alerts become active again when the water level reading rises by a specified amount
Extremely precise with default sample sizes (individual readings have extreme variation/outliers)
Specifiable sample size for each aggregate (reported) reading
Specifiable interval between readings

Not implemented:
Alerts for multiple different water levels / report % capacity
Logging values to a database
