#!/bin/bash

pkill -f libgpiod_pulsein
exec -a Terrarium-HcsrHumidifier python3 ./sensors/HcsrHumidifier.py &
exec -a Terrarium-Htu31d python3 ./sensors/Htu31d.py &
