from machine import Pin, ADC
from time import sleep_ms

# --- Configuración de Hardware ---
sensor = ADC(Pin(26))           # Entrada del ADC0 conectada al pin AOUT del sensor
white = Pin(13, Pin.OUT)        # Indicador de estado SEGURO
yellow = Pin(14, Pin.OUT)       # Indicador de estado de PRECAUCIÓN
red = Pin(15, Pin.OUT)          # Indicador de estado de PELIGRO

# --- Variables Globales y Parámetros ---
VREF = 3.3          # Tensión de operación del ADC en la Raspberry Pi Pico
WARNING = 50        # Límite para detectar incremento de gas (Advertencia)
ALARM = 75          # Límite para detectar niveles críticos (Emergencia)
WINDOW_SIZE = 10    # Número de muestras en el buffer para el filtro de señal
PERIODO_MS = 300    # Intervalo de muestreo (10 muestras * 300ms = 3 segundos de historial)

# Buffer dinámico para almacenar las lecturas recientes del filtro
window = []


# --- Bloque de Adquisición ---
def read_raw():
    return sensor.read_u16()    # Devuelve el valor digitalizado de 16 bits (0 a 65535)


# Conversión de la lectura digital cruda a su equivalente eléctrico en voltios
def to_voltage(raw):
    return raw * VREF / 65535


# Conversión de la lectura digital a un porcentaje de escala (0% - 100%)
def to_percent(raw):
    return raw * 100 / 65535


# --- Bloque de Filtrado ---
# Filtro de promedio móvil:
# Inserta la nueva muestra al final y expulsa la más antigua si el buffer está lleno.
# Se divide por la longitud actual de la lista para evitar valores artificialmente bajos
# durante los primeros ciclos de llenado del buffer.
def filter_average(raw):
    window.append(raw)
    if len(window) > WINDOW_SIZE:
        window.pop(0)
    return sum(window) / len(window)


# --- Bloque de Evaluación ---
# Verifica los límites de mayor a menor gravedad.
# Si se evaluara primero WARNING, un valor extremo de 80% se quedaría
# atrapado en esa condición y nunca lograría activar la ALARMA.
def classify(percent):
    if percent >= ALARM:
        return "ALARM"
    elif percent >= WARNING:
        return "WARNING"
    else:
        return "NORMAL"


# Activa el LED correspondiente apoyándose en operaciones de evaluación (True=1, False=0)
def update_outputs(state):
    white.value(state == "NORMAL")
    yellow.value(state == "WARNING")
    red.value(state == "ALARM")


# --- Bloque de Salida/Monitoreo ---
def print_status(raw, filtered, voltage, percent, state):
    print("raw:", raw, "| filtered:", int(filtered), "| V:", round(voltage, 2), "| %:", round(percent, 1), "| state:", state)


# --- Bucle Principal (Main) ---
print("RETO 07 (BONUS) - Smart Analog Monitor con sensor de gas")
print("Sensor: gas, AOUT -> GP26 (ADC0) | LEDs: GP13 verde, GP14 amarillo, GP15 rojo")
print("Umbrales: WARNING >=", WARNING, "% | ALARM >=", ALARM, "% | Filtro:", WINDOW_SIZE, "lecturas")

# Aseguramos que los indicadores luminosos estén apagados antes de procesar el primer dato
update_outputs("")

# Ciclo infinito del sistema: Extraer -> Suavizar -> Escalar -> Clasificar -> Actuar -> Informar
while True:
    raw = read_raw()
    filtered = filter_average(raw)
    voltage = to_voltage(filtered)
    percent = to_percent(filtered)
    state = classify(percent)
    update_outputs(state)
    print_status(raw, filtered, voltage, percent, state)
    sleep_ms(PERIODO_MS)
