#!/bin/bash

pkill -f libgpiod_pulsein
exec -a Terrarium-HcsrHumidifier python3 /var/lib/rpi-terrarium-controller/sensors/HcsrHumidifier.py &
exec -a Terrarium-Htu31d python3 /var/lib/rpi-terrarium-controller/sensors/Htu31d.py &
