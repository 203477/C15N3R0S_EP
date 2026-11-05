from machine import Pin, I2C, ADC
from ssd1306 import SSD1306_I2C
from time import ticks_ms, ticks_diff, sleep_ms

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400_000)
devices = i2c.scan()
oled = SSD1306_I2C(128, 64, i2c, addr=0x3C)
adc = ADC(26)
button = Pin(16, Pin.IN, Pin.PULL_UP)
led_alarm = Pin(15, Pin.OUT)

page = 0
last_button = 1
samples = 0
min_value = 100.00
max_value = 0.0

def classify(p):
    if p < 50: return "NORMAL"
    if p < 75: return "WARNING"
    return "ALARM"

def live_screen(p, state):
    oled.text("Page 1- Live", 0, 0)
    oled.text("ADC {:5.1f}%".format(p), 0, 18)
    oled.text(state, 0, 34)
    oled.rect(4, 50, 120, 10, 1)
    oled.fill_rect(6, 52, int(116 * p / 100), 6, 1)

def bus_screen():
    oled.text("PAGE2 - I2C", 0, 0)
    oled.text("SDA: GP4", 0, 17)
    oled.text("SDL:GP5", 0, 29)
    oled.text("DEV:" + ",".join(hex(x) for x in devices), 0, 43)

def stats_screen():
    oled.text("PAGE 3 - STATS", 0, 0)
    oled.text("MIN: {:5.1f}%".format(min_value), 0, 17)
    oled.text("MAX: {:5.1f}%".format(max_value), 0, 29)  
    oled.text("N: {}".format(samples), 0, 43)

while True:
    raw = adc.read_u16()
    percent = raw * 100 / 65535
    state = classify(percent)
    samples += 1
    min_value = min(min_value, percent)
    max_value = max(max_value, percent)
    led_alarm.value(state == "ALARM")

    current = button.value()
    if last_button == 1 and current == 0:
        page = (page + 1) % 3
        print("Cambio a PAGE", page + 1)
    last_button = current

    oled.fill(0)
    if page == 0:
        live_screen(percent, state)
    elif page == 1:
        bus_screen()
    else:
        stats_screen()
        
    oled.show()  
    sleep_ms(100)
