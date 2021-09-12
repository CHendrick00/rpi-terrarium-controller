import time
import board
import adafruit_hcsr04
import requests
from discord_webhook import DiscordWebhook

#ATTN: Set custom user values below
whurl = 'your-url-here' #url of your discord webhook
msg = 'your-message-here' #contents of message sent
sample = 30 #number of readings to average for reported value
interval = 10 #time between full readings (minutes)
dist = 5 #distance to refill level (inches)
threshold = 2 #distance above refill level when tank is considered filled (inches) (set this somewhere between the refill level and completely filled)
numNotif = 1 #how many notifications you recieve each time humidifier falls below refill level
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.D5, echo_pin=board.D6) #update pins if necessary


#initializing empty values
distances = [] #empty array to store <sample> number of readings
i = 0 #initialize counter to 0 values in array
sum = 0 #initialize sum
notifiedFlag = 0 #initialize notification sent flag
flag = 0 #set when full (avg) reading attained
interval = interval * 60 #convert to seconds for program usage

while True:
    while flag == 0:
        try:
            distIn = sonar.distance / 2.54 #distance in inches
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
                print(str(round(avg,2)) + " Inches") #print average value of filtered readings to 2 decimal places

                #allow notifications again once refilled
                if avg < (dist-threshold):
                    notifiedFlag = 0

                if avg > dist and notifiedFlag < numNotif:
                    webhook = DiscordWebhook(url=whurl, content=msg)
                    response = webhook.execute()
                    notifiedFlag += 1

                #reset values
                distances = []
                i = 0
                sum = 0
                avg = 0
                flag = 1 #set flag to wait <interval> for next full reading


        except RuntimeError:
            pass #ignore and retry
        time.sleep(0.1) #interval between individual readings
    time.sleep(interval) #interval between full readings
    flag = 0 #reset flag to take a full reading
