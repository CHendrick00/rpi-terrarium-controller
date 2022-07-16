import os
import re
import time
import sys
import asyncio
from discord_webhook import DiscordWebhook
from kasa import SmartPlug
import configparser

config = configparser.ConfigParser()
config.read('heartbeatConfig.ini')
config = config['Heartbeat']

whurl = config['WebhookURL']
pump_ip = config['CoolingPumpIP']
cooler_ip = config['CoolerPlugIP']
interval = int(config['TestInterval'])
maxTimeouts = int(config['maxTimeouts'])

plugError = False

async def kasa_setup(ip):
    global plugError
    try:
        plug = SmartPlug(ip)
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

async def poll():
    stream = os.popen('ssh rpi systemctl list-units --all --type=service | grep "terrarium-*"')
    response = stream.read().strip()
    return response

async def main():
    global plugError
    offline = False
    count = 0
    services = {}
    if(pump_ip != ""):
        pumpPlug = await kasa_setup(pump_ip)
    if(cooler_ip != ""):
        coolerPlug = await kasa_setup(cooler_ip)

    while True:
        try:
            pollFunc = poll()
            output = await pollFunc

            # Alert if unable to reach Pi
            if output == "" and offline == False:
                count+=1
                if count >= maxTimeouts:
                    webhook = DiscordWebhook(url=whurl, content="Pi is offline. Disabling cooling system.")
                    response = webhook.execute()
                    await pumpPlug.turn_off()
                    await coolerPlug.turn_off()
                    offline = True
            # Check sensor statuses
            else:
                if offline == True:
                    webhook = DiscordWebhook(url=whurl, content="Pi is back online.")
                    offline = False
                    count = 0
                lines = output.split('\n')
                regex = r'[" "]+'
                for line in range(len(lines)):
                    svc = re.split(regex, lines[line].strip(), maxsplit=4)[0].replace("terrarium-", "").replace(".service", "")
                    if svc not in services.keys():
                        services[re.split(regex, lines[line].strip(), maxsplit=4)[0].replace("terrarium-", "").replace(".service", "")] = [re.split(regex, lines[line].strip())[3], False, 0]
                    else:
                        tmp = services[svc]
                        services[svc] = [re.split(regex, lines[line].strip())[3], tmp[1], tmp[2]]

                for svc in services:
                    print("%s - %s" % (svc, services[svc][0]))
                    # Alert if sensor goes offline
                    if services[svc][0] != "running" and services[svc][1] == False:
                        services[svc][2]+=1
                        if services[svc][2] >= maxTimeouts:
                            services[svc][1] = True
                            webhook = DiscordWebhook(url=whurl, content="%s has stopped running. Status: %s" % (svc, services[svc][0]))
                            response = webhook.execute()
                            # Turn off any relevant plugs
                            if 'HL' in svc and pumpPlug.is_on:
                                await pumpPlug.turn_off()
                            elif 'DS18B20' in svc and coolerPlug.is_on:
                                await coolerPlug.turn_off()
                    # Reset alerts if sensor comes back online
                    elif services[svc][0] == "running" and services[svc][1] == True:
                        webhook = DiscordWebhook(url=whurl, content="%s has come back online." % svc)
                        response = webhook.execute()
                        services[svc][1] = False
                        services[svc][2] = 0

            time.sleep(interval)
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
