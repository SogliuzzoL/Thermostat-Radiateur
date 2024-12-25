import requests
from datetime import datetime
import time

temp_nuit = 19
temp_jour = 22
url = 'https://raspi.sogliuzzo.com/set_temperature'
debut_jour = 9
fin_jour = 23
statue_jour = False

while True:
    now = datetime.now()
    if now.hour >= debut_jour and now.hour < fin_jour:
        consigne = {'temp_consigne': temp_jour}
    else:
        consigne = {'temp_consigne': temp_nuit}
    request = requests.post(url, json = consigne)
    print(request)
    time.sleep(60)