import time
import board
import adafruit_dht
import psutil
import math
import os

# We first check if a libgpiod process is running. If yes, we kill it!
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
sensor = adafruit_dht.DHT11(board.D4)

# A configurer
code_on = 0
code_off = 0
user = "user"

cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"

radiateur_on = False
print(os.system(cmd_off))

temp_consigne = 23
temp_u = 1

while True:
    try:
        temp = sensor.temperature
        humidity = sensor.humidity
        temp_rosee = 1 / ( 0.072655 / ( math.log(humidity / 100) + 17.27 * temp / ( 237.7 + temp ) ) - 1 / 237.7 )
        temp_ressentie = temp + 0.5555 * ( 6.11 * math.exp( 5417.7530 * (1 / 273.16 - 1 / ( 273.16 + temp_rosee )) ) - 10 )
        print("Temperature: {}*C   Humidity: {}%  Temperature ressentie: {}*C   Temperature rosee: {}*C".format(temp, humidity, round(temp_ressentie, 2), round(temp_rosee, 2)))

        if not radiateur_on and temp_consigne - temp_u >= temp:
            radiateur_on = True
            print(os.system(cmd_on), "- Radiateur allumé")
        elif radiateur_on and temp_consigne + temp_u <= temp:
            radiateur_on = False
            print(os.system(cmd_off), "- Radiateur éteint")
            
    except RuntimeError as error:
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        sensor.exit()
        raise error
    time.sleep(2.0)
