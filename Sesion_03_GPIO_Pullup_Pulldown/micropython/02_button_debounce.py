from machine import Pin
from time import sleep_ms

# Entrada digital con pull-up
button = Pin(16, Pin.IN, Pin.PULL_UP)

last = 1
print("Sistema listo. Presiona el botón para registrar eventos...")

while True:
    now = button.value()
    
    # Detección de flanco de bajada (1 -> 0)
    if last == 1 and now == 0:
        sleep_ms(30)  # Ventana de estabilización (antirrebote)
        if button.value() == 0:
            print("CLICK válido")
            
            # WAIT FOR RELEASE: esperar a que el usuario suelte el botón
            # para no registrar múltiples eventos en pulsaciones largas
            while button.value() == 0:
                sleep_ms(10)
                
    last = now
    sleep_ms(10)
