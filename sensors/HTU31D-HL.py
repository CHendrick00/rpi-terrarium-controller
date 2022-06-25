import time
from datetime import datetime,timezone
import board
from adafruit_htu31d import HTU31D
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import asyncio
from kasa import SmartPlug
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['HTU31D-HL']

i2c = board.I2C()
sensor = HTU31D(i2c)
sensor.temp_resolution = "0.040"
sensor.humidity_resolution = "0.020%"

# Custom Values Below
whurl = config['WebhookURL']
kasa_ip = config['CoolingPumpIP']
interval = int(config['ReadingInterval'])
humidity_alert_min = int(config['MinHumidityAlert'])
Hthreshold = int(config['AlertHumidityThreshold'])
temp_alert_min = int(config['AlertMinTemp'])
temp_alert_max = int(config['AlertMaxTemp'])
Tthreshold = int(config['AlertTempThreshold'])
maxNotif = int(config['MaxNotifications'])
timeBetween = int(config['NotificationInterval'])

light_on_time = int(config['LightsOnTime'])
light_off_time = int(config['LightsOffTime'])
day_target_temp = int(config['DayTargetTemp'])
night_target_temp = int(config['NightTargetTemp'])
target_threshold = int(config['TargetTempThreshold'])

#InfluxDB Client Settings
host = config['IP']
port = config['Port']
user = config['User']
password = config['Password']
dbname = config['DatabaseName']
location = config['Location']
measurement = config['DatatypeName']

client = InfluxDBClient(host, port, user, password, dbname)

async def kasa_setup():
    plug = SmartPlug(kasa_ip)
    await plug.update()
    return plug

async def main():
    #Finish initializing values
    HnotifSent = 0 #initialize number of notifications sent
    TnotifSent = 0 #initialize number of notifications sent
    notifBetween = (timeBetween * 60) // interval
    Hiter = -1 #initialize for num readings between notifications
    Titer = -1 #initialize for num readings between notifications

    plug = await kasa_setup()
    while True:
        try:
            currTime = datetime.now()
            iso = datetime.now(timezone.utc)
            tempF = (1.8 * sensor.temperature) + 32
            humidity = sensor.relative_humidity

            print("\nTemperature: %0.1f F" % tempF)
            print("Humidity: %0.1f %%" % humidity)

            data = [
            {
              "measurement": measurement,
                  "tags": {
                      "location": location,
                  },
                  "time": iso,
                  "fields": {
                      "temperature" : tempF,
                      "humidity": humidity
                  }
              }
            ]
            client.write_points(data)

            if humidity > 85: # Reduce condensation in high humidity environments
                sensor.heater = True

            if humidity > (humidity_alert_min + Hthreshold):
                HnotifSent = 0
                Hiter = -1

            if humidity < humidity_alert_min and HnotifSent < maxNotif:
                Hiter += 1
                if (Hiter % notifBetween) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Humidity has fallen to %0.1f%%" % humidity) #Message can be changed if desired
                    response = webhook.execute()
                    HnotifSent += 1

            if tempF < (temp_alert_max - Tthreshold) and tempF > (temp_alert_min + Tthreshold):
                TnotifSent = 0
                Titer = -1

            if tempF < temp_alert_min or tempF > temp_alert_max and TnotifSent < maxNotif:
                Titer += 1
                if (Titer % notifBetween) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Temperature has reached %0.1f%%" % tempF) #Message can be changed if desired
                    response = webhook.execute()
                    notifSent += 1

            if config.getboolean('Cooling'):
                if currTime.hour >= light_on_time and currTime.hour < light_off_time:
                    if tempF > day_target_temp + target_threshold:
                        await plug.turn_on()
                    elif tempF <= day_target_temp:
                        await plug.turn_off()

                elif currTime.hour < light_on_time or currTime.hour >= light_off_time:
                    if tempF > night_target_temp + target_threshold:
                        await plug.turn_on()
                    elif tempF <= night_target_temp:
                        await plug.turn_off()


        except RuntimeError:
            pass #ignore and retry

        if sensor.heater:
            time.sleep(5)
            sensor.heater = False
            time.sleep(interval-5)
        else:
            time.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
