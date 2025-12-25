from flask import Flask, jsonify, request
import time
import board
import adafruit_dht
import os
import threading

# --- Configuration Matérielle ---
# Le DHT11 est capricieux, on initialise le capteur une seule fois
sensor = adafruit_dht.DHT11(board.D4)
code_on, code_off = 2388100096, 2169996288
user = "sogliuzzo-loris"
cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"

# --- Variables d'État ---
temp_consigne = 19
hysteresis = 1  # Adapté à la précision du DHT11
system_mode = "auto"  # "auto", "on", "off"
radiator_state = False

# Dictionnaire de données pour l'API
current_data = {
    "temperature": 0,
    "humidity": 0,
    "radiator_state": False,
    "temperature_consigne": temp_consigne,
    "mode": system_mode
}

def piloter_hardware(state):
    """Envoie l'ordre RF433 et met à jour l'état local"""
    global radiator_state
    cmd = cmd_on if state else cmd_off
    # On envoie la commande plusieurs fois pour être sûr que le radiateur capte le signal
    for _ in range(3):
        os.system(cmd)
        time.sleep(0.5)
    radiator_state = state

def monitor_temperature():
    """Boucle principale de régulation"""
    global temp_consigne, radiator_state, system_mode, current_data
    while True:
        try:
            temp = sensor.temperature
            hum = sensor.humidity
            
            if temp is not None:
                # Logique de décision selon le mode choisi sur le téléphone
                if system_mode == "on":
                    if not radiator_state: piloter_hardware(True)
                elif system_mode == "off":
                    if radiator_state: piloter_hardware(False)
                elif system_mode == "auto":
                    # Thermostat avec hystérésis de 1 degré pour compenser le DHT11
                    if temp <= (temp_consigne - hysteresis) and not radiator_state:
                        piloter_hardware(True)
                    elif temp >= (temp_consigne + hysteresis) and radiator_state:
                        piloter_hardware(False)

                # Mise à jour des données pour Home Assistant
                current_data.update({
                    "temperature": temp, 
                    "humidity": hum,
                    "radiator_state": radiator_state,
                    "temperature_consigne": temp_consigne,
                    "mode": system_mode
                })
        except RuntimeError:
            # Erreur de lecture fréquente avec le DHT11, on ignore simplement
            pass
        except Exception as e:
            print(f"Erreur critique : {e}")
            
        time.sleep(15) # Lecture toutes les 15 secondes pour ne pas chauffer le capteur

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def get_data():
    """Endpoint utilisé par Home Assistant pour lire l'état"""
    return jsonify(current_data)

@app.route('/config', methods=['POST'])
def set_config():
    """Endpoint utilisé par Home Assistant pour piloter le radiateur"""
    global temp_consigne, system_mode
    req = request.json
    if 'temp_consigne' in req: 
        temp_consigne = int(req['temp_consigne'])
    if 'mode' in req: 
        system_mode = req['mode']
    return jsonify(current_data)

if __name__ == "__main__":
    # Démarrage du thread de régulation
    threading.Thread(target=monitor_temperature, daemon=True).start()
    # Démarrage de l'API Flask
    app.run(host="0.0.0.0", port=5000)
