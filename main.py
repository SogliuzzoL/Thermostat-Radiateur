import time
import board
import adafruit_dht
import psutil
import math
# We first check if a libgpiod process is running. If yes, we kill it!
for proc in psutil.process_iter():
    if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
        proc.kill()
sensor = adafruit_dht.DHT11(board.D4)
while True:
    try:
        temp = sensor.temperature
        humidity = sensor.humidity
        temp_rosee = 1 / ( 0.072655 / ( math.log(humidity / 100) + 17.27 * temp / ( 237.7 + temp ) ) - 1 / 237.7 )
        temp_ressentie = temp + 0.5555 * ( 6.11 * math.exp( 5417.7530 * (1 / 273.16 - 1 / ( 273.16 + temp_rosee )) ) - 10 )
        print("Temperature: {}*C   Humidity: {}%  Temperature ressentie: {}*C   Temperature rosee: {}*C".format(temp, humidity, round(temp_ressentie, 2), round(temp_rosee, 2)))
    except RuntimeError as error:
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        sensor.exit()
        raise error
    time.sleep(2.0)
