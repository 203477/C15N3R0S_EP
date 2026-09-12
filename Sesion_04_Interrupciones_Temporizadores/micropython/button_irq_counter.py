from machine import Pin
from time import ticks_ms, ticks_diff, sleep_ms

# GP16 conectado a botón a GND (Pull-Up interno activo)
button = Pin(16, Pin.IN, Pin.PULL_UP)
contador = 0
ultimo = 0

def boton_irq(pin):
    global contador, ultimo
    ahora = ticks_ms()
    # Filtro debounce por software (> 80 ms)
    if ticks_diff(ahora, ultimo) > 80:
        contador += 1
        ultimo = ahora

# Configurar interrupción en flanco de bajada (1 -> 0)
button.irq(trigger=Pin.IRQ_FALLING, handler=boton_irq)

print("Sistema listo. Presiona el botón...")
while True:
    print("clics:", contador)
    sleep_ms(500)
