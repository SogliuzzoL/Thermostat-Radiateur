from flask import Flask, render_template, jsonify, request
import time
import board
import adafruit_dht
import psutil
import math
import os
import threading
import sys
import requests
from datetime import datetime
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = "GottaGras"
url = "http://192.168.1.101:8086"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

bucket="Radiateur"
write_api = write_client.write_api(write_options=SYNCHRONOUS)

# Configuration initiale
sensor = adafruit_dht.DHT11(board.D4)
code_on = 2388100096
code_off = 2169996288
user = "sogliuzzo-loris"
cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"
temp_consigne = 19
temp_u = 1
consigne_change = False

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

def get_outdoor_temperature(city="Marseille"):
    API_KEY = "16e18111216e4f1faf1123911252404"
    url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=no"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["current"]["temp_c"]
    except Exception as e:
        print(f"[WeatherAPI] Erreur lors de la récupération météo : {e}")
        return None


def monitor_temperature():
    global last_temp, data, temp_consigne, consigne_change, write_api, write_client

    while True:
        try:
            temp = sensor.temperature
            humidity = sensor.humidity
            temp_rosee = 1 / (0.072655 / (math.log(humidity / 100) + 17.27 * temp / (237.7 + temp)) - 1 / 237.7)
            temp_ressentie = temp + 0.5555 * (6.11 * math.exp(5417.7530 * (1 / 273.16 - 1 / (273.16 + temp_rosee))) - 10)
            now = datetime.now()
            timestamp = now.isoformat()
            temp_exterieure = get_outdoor_temperature()
            
            data.update({
                "temperature": temp,
                "temperature_ressentie": round(temp_ressentie, 2),
                "humidity": humidity,
                "radiator_state": radiator_state,
                "temperature_consigne": temp_consigne,
                "temperature_exterieure": temp_exterieure,
                "timestamp": timestamp
            })
            
            point = (
                Point("measurement1")
                .tag("Emplacement", "chambre")
                .field("radiator_state", radiator_state)
                .field("temperature_consigne", temp_consigne)
                .field("temperature", temp)
                .field("temperature_ressentie", round(temp_ressentie, 2))
                .field("humidity", humidity)
            )
            
            if temp_exterieure is not None:
                point.field("temperature_exterieure", temp_exterieure)

            try:
                write_api.write(bucket=bucket, org=org, record=point)
            except Exception as e:
                print(f"[InfluxDB] Erreur d'écriture : {e}")
                print("[InfluxDB] Tentative de reconnexion...")
                try:
                    write_client.__del__()  # Fermer proprement
                except:
                    pass
                time.sleep(2)
                write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
                write_api = write_client.write_api(write_options=SYNCHRONOUS)
                print("[InfluxDB] Reconnexion réussie.")

            if last_temp != temp_ressentie or consigne_change:
                print("Température: {}°C   Humidité: {}%  Temp. ressentie: {}°C   Temp. rosée: {}°C".format(
                    temp, humidity, round(temp_ressentie, 2), round(temp_rosee, 2)))
                last_temp = temp_ressentie
                consigne_change = False
                if temp_consigne - temp_u >= temp:
                    allumer()
                elif temp_consigne + temp_u <= temp:
                    eteindre()

        except RuntimeError as error:
            print(f"[Sensor] RuntimeError: {error.args[0]}")
        except Exception as error:
            sensor.exit()
            print(f"[Sensor] Exception: {error}")
        except OSError as error:
            print(f"[Sensor] OSError: {error}")
        except ValueError as error:
            print(f"[Sensor] ValueError: {error}")

        sys.stdout.flush()
        time.sleep(5)


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
    global temp_consigne, consigne_change
    new_temp = request.json.get('temp_consigne')
    if new_temp is not None:
        temp_consigne = round(new_temp)
        data["temperature_consigne"] = temp_consigne
        consigne_change = True
        return jsonify({"message": "Température de consigne mise à jour", "temp_consigne": temp_consigne}), 200
    return jsonify({"message": "Donnée invalide"}), 400

# Lancer le monitoring de température dans un thread séparé
threading.Thread(target=monitor_temperature, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
