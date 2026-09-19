from machine import Pin, Timer
import time

btn_a = Pin(16, Pin.IN, Pin.PULL_UP)
btn_b = Pin(17, Pin.IN, Pin.PULL_UP)

led_red = Pin(13, Pin.OUT)
led_yellow = Pin(14, Pin.OUT)
led_green = Pin(15, Pin.OUT)

BLOQUEADO = 0
ESPERANDO_B = 1
ACCESO = 2
SEGURIDAD = 3

estado = BLOQUEADO
intentos_fallidos = 0

ultimo_a_ms = 0
ultimo_b_ms = 0
DEBOUNCE_MS = 250

timer_sistema = Timer()

def set_leds(red, yellow, green):
    led_red.value(red)
    led_yellow.value(yellow)
    led_green.value(green)

def ir_bloqueado():
    global estado
    estado = BLOQUEADO
    set_leds(1, 0, 0)
    print("[BLOQUEO] Sistema listo. Presiona A para iniciar.")

def callback_timeout(t):
    global estado, intentos_fallidos
    if estado == ESPERANDO_B:
        print("[ERROR] Tiempo agotado esperando B (TIMEOUT)")
        registrar_fallo()

def callback_fin_acceso(t):
    print("[TIMER] Fin del acceso")
    ir_bloqueado()

def callback_fin_seguridad(t):
    global intentos_fallidos
    print("[TIMER] Fin del bloqueo de seguridad")
    intentos_fallidos = 0
    ir_bloqueado()

def registrar_fallo():
    global estado, intentos_fallidos
    intentos_fallidos += 1
    print(f"[FALLO] Intento fallido. Contador: {intentos_fallidos}")
    if intentos_fallidos >= 3:
        estado = SEGURIDAD
        set_leds(1, 0, 0)
        print("[SEGURIDAD] 3 errores detectados. Sistema bloqueado 10 segundos.")
        timer_sistema.init(mode=Timer.ONE_SHOT, period=10000, callback=callback_fin_seguridad)
    else:
        ir_bloqueado()

def ir_esperando_b():
    global estado
    estado = ESPERANDO_B
    set_leds(0, 1, 0)
    print("[ESPERANDO B] Boton A detectado. Tienes 5s para presionar B.")
    timer_sistema.init(mode=Timer.ONE_SHOT, period=5000, callback=callback_timeout)

def ir_acceso_concedido():
    global estado
    timer_sistema.deinit()
    estado = ACCESO
    set_leds(0, 0, 1)
    print("[ACCESO CONCEDIDO] Correcto. Abriendo por 3s...")
    timer_sistema.init(mode=Timer.ONE_SHOT, period=3000, callback=callback_fin_acceso)

def interruption_a(pin):
    global ultimo_a_ms
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_a_ms) < DEBOUNCE_MS:
        return
    ultimo_a_ms = ahora

    if estado == BLOQUEADO:
        ir_esperando_b()
    else:
        print("[A] Boton A presionado de nuevo, se ignora, ya esta en proceso.")

def interruption_b(pin):
    global ultimo_b_ms
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_b_ms) < DEBOUNCE_MS:
        return
    ultimo_b_ms = ahora

    if estado == BLOQUEADO:
        print("[ERROR] B fue presionado antes que A")
        registrar_fallo()
    elif estado == ESPERANDO_B:
        ir_acceso_concedido()
    else:
        print("[B] Boton B presionado, se ignora.")

btn_a.irq(trigger=Pin.IRQ_FALLING, handler=interruption_a)
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=interruption_b)

ir_bloqueado()

while True:
    time.sleep(1)
