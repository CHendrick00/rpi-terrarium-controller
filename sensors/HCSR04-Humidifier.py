import time
from datetime import datetime,timezone
import subprocess
import sys
import signal
from contextlib import contextmanager
import board
import adafruit_hcsr04
from influxdb import InfluxDBClient
import requests
from discord_webhook import DiscordWebhook
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
config = config['HCSR04-Humidifier']

# Custom Values Below
whurl = config['WebhookURL']
maxHeight = int(config['MaxHeight'])
sensorHeight = float(config['SensorHeight'])
trigger_pin=eval('board.D' + config['TriggerPin'])
echo_pin=eval('board.D' + config['EchoPin'])

#InfluxDB Client Settings
host = config['IP']
port = config['Port']
user = config['User']
password = config['Password']
dbname = config['DatabaseName']
location = config['Location']
measurement = config['DatatypeName']

interval = int(config['ReadingInterval'])
sample = int(config['Samples'])
refillLevel = int(config['RefillLevel'])
filledThreshold = int(config['FilledLevel'])
numNotif = int(config['MaxNotifications'])
timeBetween = int(config['NotificationInterval'])


# Initialize values
distances = [] #empty array to store <sample> number of readings
i = 0 #initialize counter to 0 values in array
sum = 0 #initialize sum
notifSent = 0 #initialize number of notifications sent
flag = 0 #set when full (avg) reading attained
currLevel = -1 #current water level
interval = interval * 60 #convert to seconds for program usage
refillLevel = maxHeight * (refillLevel / 100) #convert to water level height
filledThreshold = maxHeight * (filledThreshold / 100) #convert to water level height
notifBetween = (timeBetween * 60) // interval
iter = -1 #initialize for num readings between notifications

#create Timeout module
class TimeoutException(Exception): pass
@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

#create reporting objects
client = InfluxDBClient(host, port, user, password, dbname)
sonar = adafruit_hcsr04.HCSR04(trigger_pin, echo_pin)

while True:
    while flag == 0:
        try:
            try:
                with time_limit(10): #timeout and kill bad libgpiod process if it fails ; systemd will automatically restart process
                    distIn = sonar.distance / 2.54 #distance in Inches
            except TimeoutException as e:
                print("Killing faulty libgpiod process")
                subprocess.run(["pkill", "-f", "libgpiod_pulsein"]) #kill active libgpiod process
                sys.exit(1)
            distances.append(distIn) #append distance value to array
            i += 1 #increment counter on valid reading

            if i == sample: #if array contains <sample> number of readings
                #trim lowest half of values (most likely bad readings)
                distances.sort() #sort values by acsending
                cutoff = sample // 2
                distances = distances[cutoff:] #trim lowest half of values (makes next step faster)

                #find closest 50% of values in top half of <sample>
                lowIndex = 0
                highOffset = len(distances) // 2 #static value offset for 25% of original values
                range = 0
                bestRange = 100 #arbitrarily high number
                bestIndex = 0 #low (starting) index of closest range of values
                while (lowIndex+highOffset) < len(distances):
                    range = distances[lowIndex+highOffset] - distances[lowIndex]
                    if range < bestRange:
                        bestRange = range
                        bestIndex = lowIndex
                    lowIndex += 1
                distances = distances[bestIndex:bestIndex+highOffset]

                for val in distances: #for each value in the array, add to find the total sum
                    sum += val
                avg = sum / len(distances) #find the average of the <sample> number of readings
                currLevel = (maxHeight + sensorHeight) - avg #compute current water level above empty
                currLevelPercent = 100 * (currLevel / maxHeight) #compute water level percentage of maximum water level
                print(str(round(currLevel,2)) + " Inches / " + str(round(currLevelPercent,2)) + "%") #print current water level to 2 decimal places

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
                client.write_points(data)

                #allow notifications again once refilled
                if currLevel > filledThreshold:
                    notifSent = 0
                    iter = -1

                if currLevel < refillLevel and notifSent < numNotif:
                    iter += 1
                    if (iter % notifBetween) == 0:
                        webhook = DiscordWebhook(url=whurl, content="ATTN: Humidifier level is currently at %0.1f%%. Please refill soon." % currLevelPercent) #Message can be changed if desired
                        response = webhook.execute()
                        notifSent += 1

                #reset values
                distances = []
                i = 0
                sum = 0
                avg = 0
                currLevel = -1
                flag = 1 #set flag to wait <interval> for next full reading

            time.sleep(0.25) #interval between individual readings

        except RuntimeError as e:
            e = str(e)
            if "Timed out" in e:
                pass #ignore and retry
            else:
                print("Killing faulty libgpiod process")
                subprocess.run(["pkill", "-f", "libgpiod_pulsein"]) #kill active libgpiod process
                sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(0)
        except:
            sys.exit(1)

        time.sleep(0.25) #interval between individual readings
    time.sleep(interval) #interval between full readings
    flag = 0 #reset flag to take a full reading
