import time
from datetime import datetime,timezone
import sys
import board
import adafruit_sht4x
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import asyncio
from kasa import SmartPlug
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['Highland']

i2c = board.I2C()
sensor = adafruit_sht4x.SHT4x(i2c)
sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

# Custom Values Below
whurl = config['WebhookURL']
kasa_ip = config['CoolingPumpIP']
interval = int(config['ReadingInterval'])
humidity_alert_min = int(config['MinHumidityAlert'])
Hthreshold = int(config['AlertHumidityThreshold'])
temp_alert_min = int(config['AlertMinTemp'])
temp_alert_max = int(config['AlertMaxTemp'])
Tthreshold = int(config['AlertTempThreshold'])
maxNotifH = int(config['MaxNotificationsHumidity'])
timeBetweenH = int(config['NotificationIntervalHumidity'])
maxNotifT = int(config['MaxNotificationsTemp'])
timeBetweenT = int(config['NotificationIntervalTemp'])

light_on_time = int(config['LightsOnTime'])
light_off_time = int(config['LightsOffTime'])
day_target_temp = int(config['DayTargetTemp'])
night_target_temp = int(config['NightTargetTemp'])
target_threshold = int(config['TargetTempThreshold'])
cooling_offset = int(config['CoolingTimeOffset'])

#InfluxDB Client Settings
host = config['IP']
port = config['Port']
user = config['User']
password = config['Password']
dbname = config['DatabaseName']
location = config['Location']
measurement = config['DatatypeName']

client = InfluxDBClient(host, port, user, password, dbname)

plugError = False

async def kasa_setup():
    global plugError
    global plug
    try:
        plug = SmartPlug(kasa_ip)
        await plug.update()
        if plugError is True:
            webhook = DiscordWebhook(url=whurl, content="ATTN: Cooling Pump plug reconnected.")
            plugError = False
        return plug
    except:
        if plugError is False:
            webhook = DiscordWebhook(url=whurl, content="ATTN: Unable to connect to Cooling Pump plug.")
            response = webhook.execute()
            plugError = True

async def toggle_plug(str):
    global plugError
    global plug
    try:
        if str == "on" or str == "On" or str == "ON":
            await plug.turn_on()
        elif str == "off" or str == "Off" or str == "OFF":
            await plug.turn_off()
        else:
            print("Error: Invalid state")
        if plugError is True:
            webhook = DiscordWebhook(url=whurl, content="ATTN: Cooling Pump plug reconnected.")
            plugError = False
    except:
        if plugError is False:
            webhook = DiscordWebhook(url=whurl, content="ATTN: Unable to connect to Cooling Pump plug.") #Message can be changed if desired
            response = webhook.execute()
            plugError = True

async def main():
    #Finish initializing values
    HnotifSent = 0 #initialize number of notifications sent
    TnotifSent = 0 #initialize number of notifications sent
    notifBetweenH = (timeBetweenH * 60) // interval
    notifBetweenT = (timeBetweenT * 60) // interval
    Hiter = -1 #initialize for num readings between notifications
    Titer = -1 #initialize for num readings between notifications
    global plugError


    plug = await kasa_setup()

    while True:
        try:
            if plugError is True:
                plug = await kasa_setup()
            currTime = datetime.now()
            iso = datetime.now(timezone.utc)
            tempC, humidity = sensor.measurements
            tempF = (1.8 * tempC) + 32

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
            try:
                client.write_points(data)
            except:
                print("InfluxDB timed out")
                pass

            # if humidity > 85: # Reduce condensation in high humidity environments
            #     sensor.mode = adafruit_sht4x.Mode.LOWHEAT_100MS

            if humidity > (humidity_alert_min + Hthreshold):
                HnotifSent = 0
                Hiter = -1

            if humidity < humidity_alert_min and HnotifSent < maxNotifH:
                Hiter += 1
                if (Hiter % notifBetweenH) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Highland humidity has fallen to %0.1f%%" % humidity) #Message can be changed if desired
                    response = webhook.execute()
                    HnotifSent += 1

            if tempF < (temp_alert_max - Tthreshold) and tempF > (temp_alert_min + Tthreshold):
                TnotifSent = 0
                Titer = -1

            if (tempF < temp_alert_min or tempF > temp_alert_max) and TnotifSent < maxNotifT:
                Titer += 1
                if (Titer % notifBetweenT) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Highland temperature has reached %0.1fF" % tempF) #Message can be changed if desired
                    response = webhook.execute()
                    TnotifSent += 1


            if config.getboolean('Cooling') == True:
                if currTime.hour >= light_on_time and currTime.hour < light_off_time and config.getboolean('DayCooling') == True:
                    if tempF > day_target_temp + target_threshold:
                        await toggle_plug("on")
                    elif tempF <= day_target_temp:
                        await toggle_plug("off")

                elif currTime.hour >= light_on_time-cooling_offset and currTime.hour < light_off_time+cooling_offset and config.getboolean('DayCooling') == False and plug.is_on:
                    await toggle_plug("off")

                elif currTime.hour < light_on_time-cooling_offset or currTime.hour >= light_off_time+cooling_offset:
                    if tempF > night_target_temp + target_threshold:
                        await toggle_plug("on")
                    elif tempF <= night_target_temp:
                        await toggle_plug("off")

        except RuntimeError:
            pass #ignore and retry
        except TimeoutError:
            print("Timed out")
            pass
        except:
            try:
                await plug.turn_off()
            except:
                webhook = DiscordWebhook(url=whurl, content="ATTN: Could not reconnect to plug. Service stopped without ensuring plug turned off.") #Message can be changed if desired
                response = webhook.execute()
            sys.exit(1)

        time.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
