# PASO 2 — ¿Funcionan botones, sensor Hall, LDR, buzzer y PWM?
# Ejecútalo desde Thonny en cada Pico (o como main.py en Wokwi con el diagram.json).
# Las dos peceras se cablean igual, así que no hay nada que cambiar. Mira la consola:
#   - Cada botón imprime su nombre UNA vez y suena un bip.
#   - "hall(imán): SI" al acercar el imán al sensor.
#   - "luz" baja al tapar el LDR; debajo de 25 % dice (noche) y baja el brillo.
# Si la luz funciona al revés, en config.py pon LDR_INVERT = True.

from machine import Pin, ADC, PWM
import time

BUTTONS = {"FEED": 2, "SEND": 3}
LAMP = 16

pressed = []


def make_handler(name):
    def h(p):
        pressed.append(name)
    return h


pins = []
for name, gp in BUTTONS.items():
    p = Pin(gp, Pin.IN, Pin.PULL_UP)
    p.irq(trigger=Pin.IRQ_FALLING, handler=make_handler(name))
    pins.append(p)

hall = Pin(22, Pin.IN, Pin.PULL_UP)
ldr = ADC(Pin(26))
buzzer = PWM(Pin(14))
buzzer.duty_u16(0)
lamp = PWM(Pin(LAMP))
lamp.freq(1000)

print("PASO 2 - prueba de entradas")
last_print = 0
while True:
    while pressed:
        name = pressed.pop(0)
        print("boton:", name)
        buzzer.freq(880)
        buzzer.duty_u16(20000)
        time.sleep_ms(60)
        buzzer.duty_u16(0)

    luz = ldr.read_u16() * 100 // 65535
    lamp.duty_u16(int(65535 * (15 if luz < 25 else 100) / 100))

    if time.ticks_diff(time.ticks_ms(), last_print) > 1000:
        last_print = time.ticks_ms()
        print("hall(imán):", "SI" if hall.value() == 0 else "no",
              "| luz:", luz, "%", "(noche)" if luz < 25 else "(día)")
    time.sleep_ms(20)
