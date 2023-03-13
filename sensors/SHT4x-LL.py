import time
from datetime import datetime,timezone
import board
from adafruit_sht4x import SHT4x
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
from adafruit_extended_bus import ExtendedI2C as I2C
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['Lowland']

i2c = I2C(2)
sensor = adafruit_sht4x.SHT4x(i2c)
sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

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
    ErrIter = 0 #initialize for num missing sensors errors

    while True:
        try:
            currTime = datetime.now()
            iso = datetime.now(timezone.utc)
            tempC, humidity = sensor.measurements
            tempF = (1.8 * tempC) + 32

            print("\nTemperature: %0.1f F" % tempF)
            print("Humidity: %0.1f %%" % humidity)
            errIter = 0 #clear missing device error counter on successful read

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
        except OSError as error:
            ErrIter += 1
            if ErrIter >= 5:
                exit(error)
            else:
                pass

        time.sleep(interval)

if __name__ == "__main__":
    main()
