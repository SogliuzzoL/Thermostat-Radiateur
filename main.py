import time
import board
import adafruit_dht
import psutil
import math
import os
import sys

def eteindre():
    t0 = time.time()
    while(time.time() - t0 < 3):
        os.system(cmd_off)

def allumer():
    t0 = time.time()
    while(time.time() - t0 < 3):
        os.system(cmd_on)

# We first check if a libgpiod process is running. If yes, we kill it!
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
sensor = adafruit_dht.DHT11(board.D4)

# A configurer
code_on = 2388100096 
code_off = 2169996288
user = "sogliuzzo-loris"

cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"

last_temp = 0
eteindre()
print("Radiateur étient")
sys.stdout.flush()

temp_consigne = 22
temp_u = 1

time.sleep(2)

while True:
    try:
        temp = sensor.temperature
        humidity = sensor.humidity
        temp_rosee = 1 / ( 0.072655 / ( math.log(humidity / 100) + 17.27 * temp / ( 237.7 + temp ) ) - 1 / 237.7 )
        temp_ressentie = temp + 0.5555 * ( 6.11 * math.exp( 5417.7530 * (1 / 273.16 - 1 / ( 273.16 + temp_rosee )) ) - 10 )
        if last_temp != temp_ressentie:
            print("Temperature: {}*C   Humidity: {}%  Temperature ressentie: {}*C   Temperature rosee: {}*C".format(temp, humidity, round(temp_ressentie, 2), round(temp_rosee, 2)))
            last_temp = temp_ressentie
            if temp_consigne - temp_u >= temp:
                allumer()
                print("Radiateur allumé")
            elif temp_consigne + temp_u <= temp:
                eteindre()
                print("Radiateur éteint")
            
    except RuntimeError as error:
        print(error.args[0])
        sys.stdout.flush()
        time.sleep(2.0)
        continue
    except Exception as error:
        sensor.exit()
        raise error
    time.sleep(2.0)
