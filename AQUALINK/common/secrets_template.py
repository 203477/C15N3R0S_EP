# secrets_template.py
# 1) Copia este archivo como  secrets.py
# 2) Escribe tu red Wi-Fi (2.4 GHz). Ambas peceras y la laptop/celular deben usar LA MISMA red.
# 3) Guarda secrets.py en la raíz de cada Pico.  ¡NUNCA subas secrets.py a GitHub!

WIFI_SSID = "TU_RED_WIFI"
WIFI_PASSWORD = "TU_CONTRASENA"

# Opcional: si el descubrimiento automático (UDP broadcast) no funciona en tu red,
# escribe aquí la IP de LA OTRA pecera (la que muestra su pantalla al arrancar).
# En la pecera A pon la IP de B, y en la pecera B pon la IP de A.
PEER_IP = None          # ejemplo: "192.168.43.21"
