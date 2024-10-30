
# Thermostat-Radiateur

Ce projet permet de contrôler un radiateur via un thermostat connecté à un Raspberry Pi.

## Prérequis

- Un Raspberry Pi avec accès au GPIO.
- Un capteur compatible avec `adafruit-circuitpython-dht` pour mesurer la température.
- Connexions GPIO :
  - **Data** connecté sur GPIO 4 (modifiable dans le code si besoin).
  - **5V** pour l'alimentation.
  - **GND** pour la mise à la terre.

## Installation

1. **Configurer l'environnement virtuel :**
   ```bash
   python -m venv env/
   source env/bin/activate
   ```

2. **Installer les dépendances nécessaires :**
   ```bash
   sudo pip install adafruit-python-shell
   wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
   sudo python raspi-blinka.py
   pip install adafruit-circuitpython-dht
   pip install RPi.GPIO
   pip install psutil
   sudo apt-get install libgpiod2
   ```

## Lancer le programme

1. **Activer l'environnement virtuel :**
   ```bash
   source env/bin/activate
   ```

2. **Exécuter le programme principal :**
   ```bash
   python main.py
   ```

## Configuration

Par défaut, le capteur de température est connecté sur le GPIO 4. Pour changer cette configuration, modifiez le code dans `main.py` en remplaçant le numéro du GPIO.

## Dépendances

- `adafruit-circuitpython-dht` : pour la gestion du capteur de température et d'humidité.
- `RPi.GPIO` : pour contrôler les broches GPIO.
- `psutil` : pour obtenir des informations sur le système.
- `libgpiod2` : requis pour le contrôle des GPIO sur certaines versions de Raspbian.

## Troubleshooting

- **Le capteur ne fonctionne pas** : Assurez-vous que le câblage est correct et que la configuration du GPIO correspond au câblage physique.
- **Les permissions GPIO sont refusées** : Essayez d'exécuter les commandes avec `sudo` si nécessaire.

