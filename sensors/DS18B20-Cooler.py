import os
import glob
import time
import sys
from datetime import datetime,timezone
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import asyncio
from kasa import SmartPlug
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['DS18B20-Cooler']

# Custom Values Below
whurl = config['WebhookURL']
kasa_ip = config['CoolerPlugIP']
cooling_alert_time = int(config['CoolingAlertTime'])
interval = int(config['ReadingInterval'])
off_temp = int(config['OffTemp'])
on_temp = int(config['OnTemp'])
temp_alert_below = int(config['AlertBelowTemp'])
threshold = int(config['AlertResetThreshold'])
maxNotif = int(config['MaxNotifications'])
timeBetween = int(config['NotificationInterval'])
light_on_time = int(config['LightsOnTime'])
light_off_time = int(config['LightsOffTime'])
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

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

plugError = False

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
    global plugError
    global plug
    try:
        plug = SmartPlug(kasa_ip)
        await plug.update()
        plugError = False
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
    notifSent = 0 #initialize number of notifications sent
    notifBetween = (timeBetween * 60) // interval #number of sensor sampling intervals between notifications
    iter = -1 #initialize for num readings between notifications
    start_time = 0
    global plugError

    plug = await kasa_setup()

    while True:
        try:
            if plugError is True:
                plug = await kasa_setup()
            iso = datetime.now(timezone.utc)
            currTime = datetime.now()
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
            try:
                client.write_points(data)
            except:
                print("InfluxDB timed out")
                pass

            if config.getboolean('Cooling'):
                # Send alert if reservoir was unable to be cooled to target temperature within <cooling_alert_time>
                # Only sent once each time process is started
                if cooling_alert_time != -1 and (time.time() - start_time) >= (cooling_alert_time * 60) and start_time is not 0:
                    webhook = DiscordWebhook(url=whurl, content="Cooling reservoir was unable to hit target temperature within " + max_runtime + " minutes. Temperature reached: %0.1f%%" % tempF)
                    response = webhook.execute()

                if currTime.hour < light_on_time-1 or currTime.hour >= light_off_time+1:
                    if tempF <= off_temp:
                        await toggle_plug("off")
                        start_time = 0
                    elif tempF >= on_temp:
                        await toggle_plug("on")
                        start_time = time.time()

                elif currTime.hour >= light_on_time-1 and currTime.hour < light_off_time+1 and plug.is_on:
                    await toggle_plug("off")

            if tempF > (temp_alert_below + threshold):
                notifSent = 0
                iter = -1

            if tempF < temp_alert_below and notifSent < maxNotif:
                iter += 1
                if (iter % notifBetween) == 0:
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Cooling reservoir temperature has fallen to %0.1fF" % tempF) #Message can be changed if desired
                    response = webhook.execute()
                    notifSent += 1

        except RuntimeError:
            pass #ignore and retry
        except TimeoutError:
            print("Timed out")
            pass
        except Exception as e:
            print(e)
            try:
                await plug.turn_off()
            except:
                webhook = DiscordWebhook(url=whurl, content="ATTN: Could not reconnect to plug. Service stopped without ensuring plug turned off.") #Message can be changed if desired
                response = webhook.execute()
            sys.exit(1)

        time.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
