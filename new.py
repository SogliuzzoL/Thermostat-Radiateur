from flask import Flask, jsonify, request
import time
import board
import adafruit_dht
import os
import threading

# --- Configuration Matérielle ---
sensor = adafruit_dht.DHT11(board.D4)
code_on, code_off = 2388100096, 2169996288
user = "sogliuzzo-loris"
cmd_on = f"/home/{user}/433Utils/RPi_utils/codesend {code_on}"
cmd_off = f"/home/{user}/433Utils/RPi_utils/codesend {code_off}"

# --- Variables d'État ---
temp_consigne = 19
hysteresis = 1
system_mode = "auto"
radiator_state = False
current_temp = 0
current_hum = 0

def piloter_hardware(state):
    """Envoie l'ordre RF433 immédiatement"""
    global radiator_state
    cmd = cmd_on if state else cmd_off
    print(f"[Hardware] Envoi du signal : {'ALLUMER' if state else 'ÉTEINDRE'}")
    # Envoi répété pour garantir la réception par le radiateur
    for _ in range(3):
        os.system(cmd)
        time.sleep(0.2)
    radiator_state = state

def monitor_temperature():
    """Boucle de sécurité et mise à jour des capteurs"""
    global current_temp, current_hum, radiator_state
    while True:
        try:
            temp = sensor.temperature
            hum = sensor.humidity
            if temp is not None:
                current_temp = temp
                current_hum = hum
                
                # Thermostat local en mode Auto (sécurité si HA est coupé)
                if system_mode == "auto":
                    if temp <= (temp_consigne - hysteresis) and not radiator_state:
                        piloter_hardware(True)
                    elif temp >= (temp_consigne + hysteresis) and radiator_state:
                        piloter_hardware(False)
        except RuntimeError:
            pass
        time.sleep(15)

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify({
        "temperature": current_temp,
        "humidity": current_hum,
        "radiator_state": radiator_state,
        "temperature_consigne": temp_consigne,
        "mode": system_mode
    })

@app.route('/config', methods=['POST'])
def set_config():
    global temp_consigne, system_mode
    req = request.json
    print(f"[API] Commande reçue : {req}")
    
    if 'temp_consigne' in req:
        temp_consigne = int(req['temp_consigne'])
    
    if 'mode' in req:
        new_mode = req['mode']
        system_mode = new_mode
        # ACTION IMMÉDIATE : On ne dépend plus de la boucle de 15s
        if new_mode == "on":
            piloter_hardware(True)
        elif new_mode == "off":
            piloter_hardware(False)
            
    return jsonify({"status": "ok", "radiator_state": radiator_state})

if __name__ == "__main__":
    threading.Thread(target=monitor_temperature, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
