# PASO 1 — ¿Funciona la OLED?
# Sube antes a la Pico:  ssd1306.py
# Conecta: VCC->3V3 (pin 36), GND->GND, SDA->GP4 (pin 6), SCL->GP5 (pin 7)
# Ejecuta este archivo desde Thonny (boton verde).
#
# Debes ver: un marco, el texto "OLED OK", un pez de caracteres y un contador
# que avanza del 1 al 10. Al final la pantalla baja y sube el brillo.

from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
print("Dispositivos I2C encontrados:", [hex(a) for a in i2c.scan()])

oled = ssd1306.detect(i2c, 128, 64)      # cambia a 128, 32 si tu OLED es chica
oled.fill(0)
oled.rect(0, 0, 128, 64, 1)
oled.text("OLED OK", 32, 10, 1)
oled.text("><(((>", 36, 28, 1)
oled.show()
print("PASO 1 OK si ves el marco, el texto y el pez")
time.sleep(2)

for n in range(1, 11):
    oled.fill_rect(20, 44, 90, 10, 0)
    oled.text("contador %d" % n, 22, 45, 1)
    oled.show()
    time.sleep(0.3)

for c in (255, 128, 20, 128, 255):
    oled.contrast(c)                      # asi se atenua en el modo noche
    time.sleep(0.5)
print("Listo. Si el contador avanzo y el brillo cambio, la pantalla sirve.")
