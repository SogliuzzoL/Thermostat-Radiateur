from flask import Flask, render_template, jsonify, request
import time
import board
import adafruit_dht
import psutil
import math
import os
import threading
import sys
from datetime import datetime

# Configuration initiale
sensor = adafruit_dht.DHT11(board.D4)
code_on = 2388100096
code_off = 2169996288
user = "sogliuzzo-loris"
cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"
temp_consigne = 20
temp_u = 1

# Initialisation des variables globales
last_temp = 0
radiator_state = False
data = {"temperature": None, "temperature_ressentie": None, "humidity": None, "radiator_state": radiator_state, "temperature_consigne": temp_consigne, "timestamp": 0}

# Arrêt de tout processus libgpiod s'il existe
for proc in psutil.process_iter():
    if proc.name() in ['libgpiod_pulsein', 'libgpiod_pulsei']:
        proc.kill()

def eteindre():
    global radiator_state
    t0 = time.time()
    while(time.time() - t0 < 3):
        os.system(cmd_off)
    radiator_state = False
    print("Radiateur éteint")

def allumer():
    global radiator_state
    t0 = time.time()
    while(time.time() - t0 < 3):
        os.system(cmd_on)
    radiator_state = True
    print("Radiateur allumé")

# Fonction modifiée pour monitor_temperature
def monitor_temperature():
    global last_temp, data, temp_consigne
    while True:
        try:
            temp = sensor.temperature
            humidity = sensor.humidity
            temp_rosee = 1 / (0.072655 / (math.log(humidity / 100) + 17.27 * temp / (237.7 + temp)) - 1 / 237.7)
            temp_ressentie = temp + 0.5555 * (6.11 * math.exp(5417.7530 * (1 / 273.16 - 1 / (273.16 + temp_rosee))) - 10)
            now = datetime.now()
            timestamp = now.isoformat()

            data.update({
                "temperature": temp,
                "temperature_ressentie": round(temp_ressentie, 2),
                "humidity": humidity,
                "radiator_state": radiator_state,
                "temperature_consigne": temp_consigne,
                "timestamp": timestamp
            })

            if last_temp != temp_ressentie:
                print("Temperature: {}*C   Humidity: {}%  Temperature ressentie: {}*C   Temperature rosee: {}*C".format(temp, humidity, round(temp_ressentie, 2), round(temp_rosee, 2)))
                last_temp = temp_ressentie

                if temp_consigne - temp_u >= temp:
                    allumer()
                elif temp_consigne + temp_u <= temp:
                    eteindre()
        except RuntimeError as error:
            print(f"RuntimeError: {error.args[0]}")
        except Exception as error:
            sensor.exit()
            print(f"Exception: {error}")
        sys.stdout.flush()
        time.sleep(2)

# Démarrage du serveur Flask
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', data=data)

@app.route('/data')
def get_data():
    return jsonify(data)

@app.route('/set_temperature', methods=['POST'])
def set_temperature():
    global temp_consigne
    new_temp = request.json.get('temp_consigne')
    if new_temp is not None:
        temp_consigne = round(new_temp)
        data["temperature_consigne"] = temp_consigne
        return jsonify({"message": "Température de consigne mise à jour", "temp_consigne": temp_consigne}), 200
    return jsonify({"message": "Donnée invalide"}), 400

# Lancer le monitoring de température dans un thread séparé
threading.Thread(target=monitor_temperature, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
