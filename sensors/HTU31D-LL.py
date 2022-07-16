import time
from datetime import datetime,timezone
import board
from adafruit_htu31d import HTU31D
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
from adafruit_extended_bus import ExtendedI2C as I2C
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['HTU31D-LL']

i2c = I2C(2)
sensor = HTU31D(i2c)
sensor.temp_resolution = "0.040"
sensor.humidity_resolution = "0.020%"
sensor.heater = False

# Custom Values Below
whurl = config['WebhookURL']
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

#InfluxDB Client Settings
host = config['IP']
port = config['Port']
user = config['User']
password = config['Password']
dbname = config['DatabaseName']
location = config['Location']
measurement = config['DatatypeName']

client = InfluxDBClient(host, port, user, password, dbname)

def main():
    #Finish initializing values
    HnotifSent = 0 #initialize number of notifications sent
    TnotifSent = 0 #initialize number of notifications sent
    notifBetweenH = (timeBetweenH * 60) // interval
    notifBetweenT = (timeBetweenT * 60) // interval
    Hiter = -1 #initialize for num readings between notifications
    Titer = -1 #initialize for num readings between notifications

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
            try:
                client.write_points(data)
            except:
                print("InfluxDB timed out")
                pass

            if humidity > 85: # Reduce condensation in high humidity environments
                sensor.heater = True

            if humidity > (humidity_alert_min + Hthreshold):
                HnotifSent = 0
                Hiter = -1

            if humidity < humidity_alert_min and HnotifSent < maxNotifH:
                Hiter += 1
                if (Hiter % notifBetweenH) == 0:
                    print("Hiter " + str(Hiter) + " % notifBetweenH " + str(notifBetweenH) + " = " + str(Hiter % notifBetweenH))
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Lowland humidity has fallen to %0.1f%%" % humidity) #Message can be changed if desired
                    response = webhook.execute()
                    print("Alert sent")
                    HnotifSent += 1

            if tempF < (temp_alert_max - Tthreshold) and tempF > (temp_alert_min + Tthreshold):
                TnotifSent = 0
                Titer = -1

            if (tempF < temp_alert_min or tempF > temp_alert_max) and TnotifSent < maxNotifT:
                Titer += 1
                if (Titer % notifBetweenT) == 0:
                    print("Titer " + str(Titer) + " % notifBetweenT " + str(notifBetweenT) + " = " + str(Titer % notifBetweenT))
                    webhook = DiscordWebhook(url=whurl, content="ATTN: Lowland temperature has reached %0.1fF" % tempF) #Message can be changed if desired
                    response = webhook.execute()
                    print("Alert sent")
                    TnotifSent += 1


        except RuntimeError:
            pass #ignore and retry

        if sensor.heater == True:
            time.sleep(5)
            sensor.heater = False
            time.sleep(interval-5)
        else:
            time.sleep(interval)

if __name__ == "__main__":
    main()