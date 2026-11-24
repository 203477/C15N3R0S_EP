# PASO 3 — ¿Se conecta al Wi-Fi?
# Necesita secrets.py en la Pico (copia de secrets_template.py con tu red de 2.4 GHz).
# Debe imprimir la IP. Hazlo en las DOS Pico: las IP deben empezar igual (misma red).
# No avances al paso 4 hasta que ambas tengan IP.

import network
import time
from secrets import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)
print("Conectando a", WIFI_SSID)
for _ in range(40):
    if wlan.isconnected():
        break
    print("  estado:", wlan.status())
    time.sleep_ms(500)

if wlan.isconnected():
    print("PASO 3 OK  -  IP:", wlan.ifconfig()[0])
else:
    print("NO conectó. Revisa: nombre y contraseña, que la red sea de 2.4 GHz,")
    print("y que no sea una red de invitados o institucional.")
