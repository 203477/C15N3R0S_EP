from machine import Pin
from time import sleep_ms

# Constantes de tiempo (en milisegundos)
TRANSITION_MS = 1500  # Duración luz amarilla autos
CROSSING_MS = 4000    # Duración verde peatonal fijo
BLINK_TIMES = 4       # Cantidad de parpadeos de desalojo peatonal
BLINK_MS = 300        # Duración de cada fase de parpadeo
RECOVERY_MS = 1000    # Pausa de seguridad antes de reactivar verde autos

# Mapeo de pines (Etapa A y B)
car_red = Pin(15, Pin.OUT)
car_yellow = Pin(14, Pin.OUT)
car_green = Pin(13, Pin.OUT)

ped_red = Pin(12, Pin.OUT)
ped_green = Pin(11, Pin.OUT)

button = Pin(16, Pin.IN, Pin.PULL_UP)

def set_lights(car_r, car_y, car_g, ped_r, ped_g):
    """
    Controlador de salidas con guarda de seguridad (Invariante).
    Verifica que autos y peatones NUNCA tengan verde simultáneamente.
    """
    if car_g and ped_g:
        print("[ALERTA CRÍTICA] Invariante violada: ambos verdes activos. Cambio descartado.")
        return
    
    car_red.value(car_r)
    car_yellow.value(car_y)
    car_green.value(car_g)
    ped_red.value(ped_r)
    ped_green.value(ped_g)

# Capa de abstracción
def cars_go():
    # Autos Verde / Peatones Rojo (S0 Reposo)
    set_lights(0, 0, 1, 1, 0)

def cars_prepare_to_stop():
    # Autos Amarillo / Peatones Rojo (S1 Transición)
    set_lights(0, 1, 0, 1, 0)

def pedestrians_go():
    # Autos Rojo / Peatones Verde (S2 Cruce)
    set_lights(1, 0, 0, 0, 1)

def pedestrians_hurry():
    # Autos Rojo / Peatones Verde parpadeando (S3 Fin/Desalojo)
    for _ in range(BLINK_TIMES):
        ped_green.value(0)
        sleep_ms(BLINK_MS)
        ped_green.value(1)
        sleep_ms(BLINK_MS)
    ped_green.value(0)
    ped_red.value(1)

def crossing_sequence():
    """Ejecución secuencial de la máquina de estados"""
    print(">> S1: Autos frenan (Amarillo)")
    cars_prepare_to_stop()
    sleep_ms(TRANSITION_MS)
    
    print(">> S2: Cruce peatonal habilitado (Verde)")
    pedestrians_go()
    sleep_ms(CROSSING_MS)
    
    print(">> S3: Advertencia de fin de cruce (Parpadeo)")
    pedestrians_hurry()
    
    # Tiempo de guarda de seguridad
    sleep_ms(RECOVERY_MS)
    
    print(">> S0: Retorno a reposo vehicular")
    cars_go()

# Inicialización en S0
cars_go()
last = 1
print("Semáforo operativo en S0 (Reposo). Esperando peatón...")

while True:
    now = button.value()
    
    # Detección con debounce por software
    if last == 1 and now == 0:
        sleep_ms(30)
        if button.value() == 0:
            print("\n[EVENTO] Petición de cruce detectada.")
            crossing_sequence()
            
            # Esperar a que suelte el botón
            while button.value() == 0:
                sleep_ms(10)
                
    last = now
    sleep_ms(10)
