from machine import Pin, Timer
import time

btn_a = Pin(16, Pin.IN, Pin.PULL_UP)
btn_b = Pin(17, Pin.IN, Pin.PULL_UP)

led_red = Pin(13, Pin.OUT)
led_yellow = Pin(14, Pin.OUT)
led_green = Pin(15, Pin.OUT)

STATE_BLOQUEADO = 0
STATE_ESPERA_B = 1
STATE_ACCESO = 2
STATE_SEGURIDAD = 3

estado_actual = STATE_BLOQUEADO
intentos_fallidos = 0

ultimo_tiempo_a = 0
ultimo_tiempo_b = 0
DEBOUNCE_MS = 250

timer_sistema = Timer()

def set_leds(red, yellow, green):
    led_red.value(red)
    led_yellow.value(yellow)
    led_green.value(green)

def mostrar_pantalla_bloqueado():
    print("[LISTO] SISTEMA BLOQUEADO")
    print("Secuencia correcta: A -> B")

def callback_timeout(t):
    global estado_actual, intentos_fallidos
    if estado_actual == STATE_ESPERA_B:
        print("[ERROR] Tiempo agotado esperando B (TIMEOUT)")
        intentos_fallidos += 1
        print(f"[ERROR] Intentos fallidos: {intentos_fallidos}")
        verificar_intentos()

def callback_fin_acceso(t):
    global estado_actual
    print("[TIMER] Fin del acceso")
    estado_actual = STATE_BLOQUEADO
    set_leds(1, 0, 0)
    mostrar_pantalla_bloqueado()

def callback_fin_bloqueo(t):
    global estado_actual, intentos_fallidos
    print("[TIMER] Fin del bloqueo")
    intentos_fallidos = 0
    print("[RESET] Intentos fallidos = 0")
    estado_actual = STATE_BLOQUEADO
    set_leds(1, 0, 0)
    mostrar_pantalla_bloqueado()

def verificar_intentos():
    global estado_actual, intentos_fallidos
    if intentos_fallidos >= 3:
        estado_actual = STATE_SEGURIDAD
        set_leds(1, 0, 0)
        print("[BLOQUEO] 3 errores detectados")
        print("[BLOQUEO] Sistema bloqueado 10 segundos")
        timer_sistema.init(mode=Timer.ONE_SHOT, period=10000, callback=callback_fin_bloqueo)
    else:
        estado_actual = STATE_BLOQUEADO
        set_leds(1, 0, 0)
        print("[LISTO] Intenta nuevamente con A -> B")

def handle_btn_a(pin):
    global estado_actual, ultimo_tiempo_a
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_tiempo_a) < DEBOUNCE_MS:
        return
    ultimo_tiempo_a = ahora

    if estado_actual == STATE_SEGURIDAD:
        print("[INFO] A ignorado: bloqueo de seguridad")
        return
    
    if estado_actual == STATE_ACCESO:
        return

    if estado_actual == STATE_ESPERA_B:
        return

    if estado_actual == STATE_BLOQUEADO:
        print("[A] Boton A detectado")
        print("[ESPERA] Presiona B antes de 5 segundos")
        estado_actual = STATE_ESPERA_B
        set_leds(0, 1, 0)
        timer_sistema.init(mode=Timer.ONE_SHOT, period=5000, callback=callback_timeout)

def handle_btn_b(pin):
    global estado_actual, intentos_fallidos, ultimo_tiempo_b
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_tiempo_b) < DEBOUNCE_MS:
        return
    ultimo_tiempo_b = ahora

    if estado_actual == STATE_SEGURIDAD:
        print("[INFO] B ignorado: bloqueo de seguridad")
        return

    if estado_actual == STATE_ACCESO:
        return

    if estado_actual == STATE_BLOQUEADO:
        print("[ERROR] B fue presionado antes que A")
        intentos_fallidos += 1
        print(f"[ERROR] Intentos fallidos: {intentos_fallidos}")
        verificar_intentos()

    elif estado_actual == STATE_ESPERA_B:
        timer_sistema.deinit()
        print("[B] Boton B detectado")
        print("[OK] ACCESO CONCEDIDO")
        print("[TIMER] Acceso activo durante 3 segundos")
        estado_actual = STATE_ACCESO
        set_leds(0, 0, 1)
        timer_sistema.init(mode=Timer.ONE_SHOT, period=3000, callback=callback_fin_acceso)

btn_a.irq(trigger=Pin.IRQ_FALLING, handler=handle_btn_a)
btn_b.irq(trigger=Pin.IRQ_FALLING, handler=handle_btn_b)

set_leds(1, 0, 0)
mostrar_pantalla_bloqueado()

while True:
    time.sleep(1)
