import time
from datetime import datetime,timezone
import board
from adafruit_htu31d import HTU31D
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook

i2c = board.I2C()
sensor = HTU31D(i2c)
sensor.temp_resolution = "0.040"
sensor.humidity_resolution = "0.020%"

#ATTN: Set custom user values below
whurl = 'your-url-here'
interval = 30 #time between full readings (seconds)
humidity_alert_min = 85 #minimum humidity level before sending alert (percent)
threshold = 2 #percent above minimum humidity level when alert counter will be reset and resume
maxNotif = 3 #how many notifications to recieve each time humidity falls below minimum level
notifBetween = 3 #number of readings between sending another notification
#InfluxDB Client Settings
host = "127.0.0.1" # Influxdb Server Address; set to 127.0.0.1 if installed on same machine
port = 8086 # Default port; SHOULD NOT NEED TO BE CHANGED
user = "user" # InfluxDB user/pass for pi; CHANGE THIS to whatever you set during InfluxDB install
password = "your-password-here"
dbname = "sensor_data" #database created for this terrarium; should not need changed

measurement = "rpi-HTU31D" #tag for sensor; should not need changed
location = "Terrarium" #tag for location of sensor; change if desired
#END custom values


client = InfluxDBClient(host, port, user, password, dbname)

iter = -1 #initialize for num readings between notifications
notifSent = 0 #initialize number of notifications sent
while True:
    try:
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
        print("data logged")

        if humidity > 90: #Prevent condensation in high humidity environments
            sensor.heater = True
            time.sleep(1)
            sensor.heater = False

        if humidity > (humidity_alert_min + threshold): #reset notifications if humidity rises above threshold
            notifSent = 0
            iter = -1

        if humidity < humidity_alert_min and notifSent < maxNotif:
            iter += 1
            if (iter % notifBetween) == 0:
                webhook = DiscordWebhook(url=whurl, content="ATTN: Humidity has fallen to %0.1f%%" % humidity) #change message if desired
                response = webhook.execute()
                notifSent += 1


    except RuntimeError:
        pass #ignore and retry


    time.sleep(interval)



    '''print("\nTemperature: %0.1f C" % sensor.temperature)
    print("Humidity: %0.1f %%" % sensor.relative_humidity)
    time.sleep(2)'''
