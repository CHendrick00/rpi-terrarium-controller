import os
import glob
import time
from datetime import datetime,timezone
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import asyncio
from kasa import SmartPlug

#ATTN: Set custom user values below
whurl = 'your-url-here' # Discord alery webhook url
kasa_ip = '127.0.0.1' # IP address of smart plug
cooling_alert_time = 30 # Max amount of time for plug to be turned on if not hitting target temperature (off_temp). Set to -1 to disable.
plug_cooldown_time = 10 # Time for plug to be disabled
interval = 60 # Time between readings (seconds)
off_temp = 40 # Temp (F) to turn Kasa plug off
on_temp = 50 # Temp (F) to turn Kasa plug on
temp_alert_below = 34 # Minimum temperature before sending alert (F). Should be set between 32 and off_temp.
threshold = 4 # Degrees F above <temp_alert_below> when alert counter will be reset
maxNotif = 99 # How many notifications to recieve each time temperature falls below minimum level
timeBetween = 30 # Time between sending another notification (minutes) (may not be exact if not a multiple of <interval>)

#InfluxDB Client Settings
host = "127.0.0.1" # Influxdb Server Address; do not change if InfluxDB is running on the same device
port = 8086 # Default port; SHOULD NOT NEED CHANGED
user = "your-user-here" # InfluxDB user/pass for pi
password = "your-password-here"
dbname = "sensor_data" # database created for this device
measurement = "rpi-DS18B20" # unique table name for data from this sensor
location = "Terrarium"
#END custom values

client = InfluxDBClient(host, port, user, password, dbname)

#Finish initializing values
notifSent = 0 #initialize number of notifications sent
notifBetween = (timeBetween * 60) // interval #number of sensor sampling intervals between notifications
iter = -1 #initialize for num readings between notifications


base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    #subprocess.call(['sudo', 'rm', device_file])
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

async def kasa_setup():
    plug = SmartPlug(kasa_ip)
    await p.update()
    return plug

async def main():
    plug = kasa_setup()
    while True:
        try:
            iso = datetime.now(timezone.utc)
            tempC, tempF = read_temp()
            print("\nTemperature: %0.1f F" % tempF)

            data = [
            {
              "measurement": measurement,
                  "tags": {
                      "location": location,
                  },
                  "time": iso,
                  "fields": {
                      "temperature" : tempF,
                  }
              }
            ]
            client.write_points(data)

            # Send alert if reservoir was unable to be cooled to target temperature within <cooling_alert_time>
            # Only sent once each time process is started
            if cooling_alert_time != -1 and (time.time() - start_time) >= (cooling_alert_time * 60):
                webhook = DiscordWebhook(url=whurl, content="Cooling reservoir was unable to hit target temperature within " + max_runtime + " minutes. Temperature reached: %0.1f%%" % tempF")
                response = webhook.execute()

            if tempF <= off_temp:
                start_time = 0
                plug.turn_off()
            else if tempF >= on_temp:
                start_time = time.time()
                plug.turn_on()

            if tempF > (temp_alert_below + threshold):
                notifSent = 0
                iter = -1

            if tempF < temp_alert_below and notifSent < maxNotif:
                iter += 1
                if (iter % notifBetween) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Cooling reservoir temperature has fallen to %0.1f%%" % tempF) #Message can be changed if desired
                    response = webhook.execute()
                    notifSent += 1

        except RuntimeError:
            pass #ignore and retry

        time.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
