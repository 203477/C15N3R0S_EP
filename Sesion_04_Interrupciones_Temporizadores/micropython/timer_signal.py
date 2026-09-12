from machine import Pin, Timer
from time import sleep_ms

signal = Pin(15, Pin.OUT)
timer = Timer(-1)

def encender(t):
    signal.on()
    print("-> Timer disparado: LED encendido!")

signal.off()
print("Espera 3 segundos...")
timer.init(mode=Timer.ONE_SHOT, period=3000, callback=encender)

while True:
    print("programa vivo")
    sleep_ms(500)
