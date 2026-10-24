import _thread
from machine import ADC, PWM, Pin
from time import sleep_ms, ticks_ms, ticks_diff

led1 = Pin(13, Pin.OUT)
led1.value(0)

led2_pwm = PWM(Pin(15))
led2_pwm.freq(1000)
led2_pwm.duty_u16(0)

btn = Pin(16, Pin.IN, Pin.PULL_UP)
adc = ADC(Pin(26))

pwm_val = 0
adc_pct = 0
samples = 0

def tarea_adc():
    global adc_pct, samples
    while True:
        lectura = adc.read_u16()
        adc_pct = int((lectura * 100) / 65535)
        samples += 1
        sleep_ms(50)

_thread.start_new_thread(tarea_adc, ())

ultimo_click = 0
def irq_boton(p):
    global ultimo_click
    ahora = ticks_ms()
    if ticks_diff(ahora, ultimo_click) > 200:
        ultimo_click = ahora
        print("EVENT,BTN_PRESSED")
        print(status_frame())

btn.irq(trigger=Pin.IRQ_FALLING, handler=irq_boton)

def status_frame():
    btn_val = 1 if btn.value() == 0 else 0
    return "STATUS,LED={},PWM={},ADC={}%,BTN={},SAMPLES={}".format(
        led1.value(), pwm_val, adc_pct, btn_val, samples
    )

def imprimir_help():
    print("===================== HELP =====================")
    print("LED 1 = LED rojo -> solo encendido/apagado")
    print("LED 2 = LED naranja -> brillo por PWM 0-100 %")
    print("------------------------------------------------")
    print("comandos: PING        -> PONG")
    print("LED,1     Enciende LED 1 (rojo)")
    print("LED,0     Apaga LED 1 (rojo)")
    print("PWM,n     Brillo de LED 2 (naranja), n = 0..100")
    print("          Ej: PWM,0 apaga, PWM,50 medio, PWM,100 maximo")
    print("ALL,1     Enciende LED 1 y LED 2 (100 %) juntos")
    print("ALL,0     Apaga LED 1 y LED 2 juntos")
    print("STATUS    Estado: LED, PWM, ADC %, BTN, SAMPLES")
    print("TOGGLE    Invierte LED 1 (si esta prendido lo apaga)")
    print("HELP      Muestra esta ayuda")
    print("------------------------------------------------")
    print("Boton (GP16): al presionarlo muestra EVENT + STATUS")
    print("================================================")

def handle_frame(frame):
    global pwm_val

    frame = frame.strip()
    if not frame:
        return None

    if frame.upper() == "PING":
        return "PONG"

    if frame.upper() == "HELP":
        imprimir_help()
        return None

    if frame.upper() == "STATUS":
        return status_frame()

    if frame.upper() == "TOGGLE":
        nuevo = 0 if led1.value() == 1 else 1
        led1.value(nuevo)
        return "ACK,TOGGLE,{}".format(nuevo)

    parts = frame.split(",")
    cmd = parts[0].upper()

    if cmd == "LED":
        if len(parts) < 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        if parts[1] not in ("0", "1"):
            return "ERR,BAD_VALUE"
        v = int(parts[1])
        led1.value(v)
        return "ACK,LED,{}".format(v)

    if cmd == "PWM":
        if len(parts) < 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        try:
            v = int(parts[1])
        except ValueError:
            return "ERR,BAD_VALUE"
        if v < 0 or v > 100:
            return "ERR,PWM_RANGE"
        pwm_val = v
        led2_pwm.duty_u16(int((v * 65535) / 100))
        return "ACK,PWM,{}".format(v)

    if cmd == "ALL":
        if len(parts) < 2 or parts[1] == "":
            return "ERR,BAD_FORMAT"
        if parts[1] not in ("0", "1"):
            return "ERR,BAD_VALUE"
        v = int(parts[1])
        led1.value(v)
        if v == 1:
            pwm_val = 100
            led2_pwm.duty_u16(65535)
        else:
            pwm_val = 0
            led2_pwm.duty_u16(0)
        return "ACK,ALL,{}".format(v)

    return "ERR,UNKNOWN_COMMAND"

print("Escribe HELP para ver comandos")

while True:
    try:
        command = input().strip()
    except KeyboardInterrupt:
        break

    if not command:
        continue

    resp = handle_frame(command)
    if resp is not None:
        print(resp)
