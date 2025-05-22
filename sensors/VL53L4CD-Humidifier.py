import time
from datetime import datetime,timezone
import sys
import board
from adafruit_vl53l4cd import VL53L4CD
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import asyncio
from adafruit_extended_bus import ExtendedI2C as I2C
import configparser

i2c = I2C(3)
sensor = VL53L4CD(i2c)

config = configparser.ConfigParser()
config.read('config.ini')
config = config['Humidifier']

# Custom Values Below
whurl = config['WebhookURL']
maxHeight = int(config['MaxHeight'])
sensorHeight = float(config['SensorHeight'])
interval = int(config['ReadingInterval'])
refillLevel = int(config['RefillLevel'])
filledThreshold = int(config['FilledLevel'])
numNotif = int(config['MaxNotifications'])
timeBetween = int(config['NotificationInterval'])

#InfluxDB Client Settings
host = config['IP']
port = config['Port']
user = config['User']
password = config['Password']
dbname = config['DatabaseName']
location = config['Location']
measurement = config['DatatypeName']

#Finish initializing values
notifSent = 0 #initialize number of notifications sent
currLevel = -1 #current water level
refillLevel = maxHeight * (refillLevel / 100) #convert percent to water level height
filledThreshold = maxHeight * (filledThreshold / 100) #convert percent to water level height
notifBetween = (timeBetween * 60) // interval
iter = -1 #initialize for num readings between notifications

#create reporting objects
client = InfluxDBClient(host, port, user, password, dbname)

#configure sensor
sensor.inter_measurement = 800
sensor.timing_budget = 200
sensor.start_ranging()

async def main():
    while True:
        try:
            while not sensor.data_ready:
                sensor.start_ranging()
                time.sleep(interval)
                pass
            sensor.clear_interrupt()            
            distIn = sensor.distance / 2.54 #distance in Inches
            currLevel = round((maxHeight + sensorHeight) - distIn,1) #compute current water level above empty
            currLevelPercent = round(100 * (currLevel / maxHeight),1) #compute water level percentage of maximum water level
            print(str(currLevel) + " Inches / " + str(currLevelPercent) + "%") #print current water level to 2 decimal places

            iso = datetime.now(timezone.utc)
            data = [
            {
                "measurement": measurement,
                    "tags": {
                        "location": location,
                    },
                    "time": iso,
                    "fields": {
                        "water level" : currLevelPercent,
                    }
                }
            ]
            try:
                client.write_points(data)
            except:
                print("InfluxDB timed out")
                pass
            #allow notifications again once refilled
            if currLevel > filledThreshold:
                notifSent = 0
                iter = -1

            if currLevel < refillLevel and notifSent <= numNotif:
                iter += 1
                if (iter % notifBetween) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Humidifier level is currently at %0.1f%%. Please refill soon." % currLevelPercent) #Message can be changed if desired
                    response = webhook.execute()
                    notifSent += 1
            
        except KeyboardInterrupt:
            sys.exit(0)
        except TimeoutError:
            print("Timed out")
            pass
        except:
            pass #ignore and retry

        time.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())