# sensors.py — Entradas y salidas simples (GPIO, IRQ, ADC, PWM)
# Temas del curso: GPIO/interrupciones, ADC y PWM.

from machine import Pin, ADC, PWM
import time

DEBOUNCE_MS = 40        # ms minimos para que una pulsacion cuente
LONG_MS = 800           # ms para considerarla pulsacion larga


class Button:
    """Boton activo en bajo con pull-up interno.

    La interrupcion solo guarda la hora del flanco (operacion barata y segura
    dentro de una IRQ). El bucle principal interpreta esos tiempos con update()
    y distingue pulsacion corta de pulsacion larga, con antirrebote.
    """

    def __init__(self, pin, name="", long_ms=LONG_MS):
        self.name = name
        self.long_ms = long_ms
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._t_down = 0
        self._t_up = 0
        self._edge_down = False
        self._edge_up = False
        self._long_fired = False
        self._last = 0
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._irq)

    def _irq(self, _p):
        now = time.ticks_ms()
        if self.pin.value() == 0:
            self._t_down = now
            self._edge_down = True
        else:
            self._t_up = now
            self._edge_up = True

    def update(self):
        """Llamar en cada vuelta del bucle. Devuelve "short", "long" o None."""
        ev = None
        if self._edge_up:
            self._edge_up = False
            held = time.ticks_diff(self._t_up, self._t_down)
            if self._long_fired:
                self._long_fired = False            # el largo ya se aviso
            elif DEBOUNCE_MS <= held < self.long_ms:
                if time.ticks_diff(self._t_up, self._last) > DEBOUNCE_MS:
                    self._last = self._t_up
                    ev = "short"
        elif self.is_down() and not self._long_fired:
            if time.ticks_diff(time.ticks_ms(), self._t_down) >= self.long_ms:
                self._long_fired = True
                ev = "long"
        return ev

    def pressed(self):
        """Compatibilidad: True una vez por pulsacion corta."""
        return self.update() == "short"

    def is_down(self):
        return self.pin.value() == 0


class HallSensor:
    """Sensor Hall digital (A3144 / KY-003) o reed switch.
    Salida en bajo cuando hay imán. El estado solo cambia si es estable `stable_ms`."""

    def __init__(self, pin, stable_ms=200):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.stable_ms = stable_ms
        self._raw = self.pin.value() == 0
        self._t = time.ticks_ms()
        self.state = False
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self._irq)

    def _irq(self, _p):
        self._t = time.ticks_ms()   # marca cuándo cambió la señal

    def active(self):
        raw = self.pin.value() == 0
        now = time.ticks_ms()
        if raw != self._raw:
            self._raw = raw
            self._t = now
        if raw != self.state and time.ticks_diff(now, self._t) >= self.stable_ms:
            self.state = raw
        return self.state


class LightSensor:
    """LDR en divisor de voltaje -> ADC. Media móvil + histéresis para día/noche."""

    def __init__(self, pin=26, night_below=25, day_above=35, invert=False, samples=16):
        self.adc = ADC(Pin(pin))
        self.night_below = night_below
        self.day_above = day_above
        self.invert = invert
        self._buf = []
        self._n = samples
        self.percent = 100
        self.night = False

    def update(self):
        v = self.adc.read_u16()
        self._buf.append(v)
        if len(self._buf) > self._n:
            self._buf.pop(0)
        pct = sum(self._buf) * 100 // (len(self._buf) * 65535)
        if self.invert:
            pct = 100 - pct
        self.percent = pct
        if not self.night and pct < self.night_below:
            self.night = True
        elif self.night and pct > self.day_above:
            self.night = False
        return self.night


_temp_adc = None


def read_temp_c():
    """Sensor de temperatura interno del RP2350 (canal ADC 4)."""
    global _temp_adc
    if _temp_adc is None:
        _temp_adc = ADC(4)
    v = _temp_adc.read_u16() * 3.3 / 65535
    return round(27 - (v - 0.706) / 0.001721, 1)


class Fader:
    """Salida PWM con transición suave (retroiluminación o lámpara)."""

    def __init__(self, pin, freq=1000, start=100):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.value = float(start)
        self.target = float(start)
        self.override_until = 0
        self._apply()

    def set_target(self, pct):
        self.target = max(0, min(100, pct))

    def force(self, pct, seconds=10):
        """Prueba manual desde la web: fija el brillo unos segundos."""
        self.value = self.target = max(0, min(100, pct))
        self.override_until = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        self._apply()

    def overridden(self):
        return time.ticks_diff(self.override_until, time.ticks_ms()) > 0

    def update(self, dt):
        step = 120 * dt          # % por segundo
        if abs(self.target - self.value) <= step:
            self.value = self.target
        elif self.target > self.value:
            self.value += step
        else:
            self.value -= step
        self._apply()

    def _apply(self):
        self.pwm.duty_u16(int(self.value * 65535 / 100))


class Buzzer:
    """Buzzer pasivo con PWM. play() no bloquea: update() avanza las notas."""
    EAT = [(880, 60), (1320, 80)]
    ARRIVE = [(523, 80), (659, 80), (784, 140)]
    SEND = [(784, 70), (523, 90)]
    HUNGRY = [(330, 150), (0, 80), (330, 150)]
    LINK = [(1047, 40)]
    ERROR = [(220, 200)]

    def __init__(self, pin, volume=30, enabled=True):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)
        self.volume = volume
        self.enabled = enabled
        self._seq = []
        self._until = 0

    def play(self, seq):
        if self.enabled:
            self._seq = list(seq)
            self._until = 0

    def update(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._until) < 0:
            return
        if not self._seq:
            self.pwm.duty_u16(0)
            return
        freq, ms = self._seq.pop(0)
        if freq > 0:
            self.pwm.freq(freq)
            self.pwm.duty_u16(int(65535 * self.volume / 200))
        else:
            self.pwm.duty_u16(0)
        self._until = time.ticks_add(now, ms)
