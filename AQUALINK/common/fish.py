# fish.py — Modelo del pez y de la pecera (lógica pura, sin hardware)
# Funciona igual en MicroPython (Pico) y en Python de PC (para pruebas).
#
# Coordenadas normalizadas: x e y van de 0.0 a 1.0 en CUALQUIER pantalla.
#   x = 0 borde izquierdo, x = 1 borde derecho
#   y = 0 arriba,          y = 1 abajo
# Así el mismo pez se puede dibujar en cualquier pantalla y con cualquier estilo.

import random
import json

SPEED = 0.12          # ancho de pantalla por segundo
MARGIN = 0.08         # medio largo del pez (no sale de la pantalla sin enlace)
Y_MIN, Y_MAX = 0.18, 0.80
HUNGER_RATE = 1 / 30  # +1 punto de hambre cada 30 s
HUNGRY_LEVEL = 70
FOOD_FALL = 0.15      # velocidad de caída de la comida
FOOD_LIFE = 25.0      # segundos que dura la comida en el fondo
EAT_DIST = 0.07
MAX_FOOD = 6
ARRIVE_COOLDOWN = 5.0  # tras llegar, el pez explora unos segundos antes de poder regresar

NAMES_OK = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def valid_name(name):
    if not name or len(name) > 10:
        return False
    for ch in name:
        if ch not in NAMES_OK:
            return False
    return True


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Fish:
    def __init__(self, name="Nemo", color=(255, 95, 162)):
        self.name = name
        self.color = color
        self.x = 0.5
        self.y = 0.5
        self.vx = SPEED if random.random() < 0.5 else -SPEED
        self.vy = 0.0
        self.hunger = 20.0
        self.age = 0.0
        self.gen = 0            # cuántas veces ha viajado (sirve para evitar duplicados)
        self.scared = 0.0       # segundos de susto restantes
        self.asleep = False
        self._wander = 0.0

    def to_dict(self):
        return {
            "name": self.name, "color": list(self.color),
            "x": round(self.x, 4), "y": round(self.y, 4),
            "vx": round(self.vx, 4), "vy": round(self.vy, 4),
            "hunger": round(self.hunger, 1), "age_s": int(self.age),
            "gen": self.gen,
        }

    @staticmethod
    def from_dict(d):
        f = Fish(d.get("name", "Nemo"), tuple(d.get("color", (255, 95, 162))))
        f.x = float(d.get("x", 0.5))
        f.y = _clamp(float(d.get("y", 0.5)), Y_MIN, Y_MAX)
        f.vx = float(d.get("vx", SPEED))
        f.vy = float(d.get("vy", 0.0))
        f.hunger = float(d.get("hunger", 20))
        f.age = float(d.get("age_s", 0))
        f.gen = int(d.get("gen", 0))
        return f

    @property
    def facing_right(self):
        return self.vx >= 0


class Aquarium:
    """Una pecera. Puede tener el pez (fish) o estar vacía (fish = None)."""

    def __init__(self, tank_id):
        self.tank_id = tank_id
        self.fish = None
        self.food = []            # [x, y, segundos_en_el_fondo]
        self.night = False
        self.link_side = None     # "left", "right" o None: dónde está la otra pecera
        self.leaving = None       # lado por el que el pez está saliendo (esperando ACK)
        self.go_to_edge = None    # el usuario pidió enviar el pez
        self.cooldown = 0.0       # segundos tras llegar en los que no puede volver a salir
        self._hungry_alert = 0.0

    # ---------- acciones del usuario ----------
    def drop_food(self, x=None):
        if len(self.food) >= MAX_FOOD:
            return False
        if x is None:
            x = 0.2 + random.random() * 0.6
        self.food.append([_clamp(x, 0.05, 0.95), 0.12, 0.0])
        return True

    def scare(self):
        if self.fish:
            self.fish.scared = 2.0
            self.fish.vx = -self.fish.vx
            self.fish.vy = (random.random() - 0.5) * SPEED * 2

    def request_send(self):
        """Pide que el pez nade hacia la otra pecera. Devuelve False si no hay enlace o pez."""
        if self.fish is None or self.link_side is None:
            return False
        self.go_to_edge = self.link_side
        return True

    # ---------- llegada y salida ----------
    def receive(self, fish, enter_side):
        """Coloca un pez que llega desde la otra pecera."""
        if enter_side == "left":
            fish.x = MARGIN + 0.005
            fish.vx = abs(fish.vx) or SPEED
        else:
            fish.x = 1 - MARGIN - 0.005
            fish.vx = -(abs(fish.vx) or SPEED)
        fish.scared = 0.0
        self.fish = fish
        self.cooldown = ARRIVE_COOLDOWN
        self.leaving = None
        self.go_to_edge = None

    def transfer_ok(self):
        self.fish = None
        self.leaving = None
        self.go_to_edge = None

    def transfer_failed(self):
        if self.fish:
            self.fish.vx = -self.fish.vx
        self.leaving = None
        self.go_to_edge = None

    # ---------- simulación ----------
    def update(self, dt):
        """Avanza la simulación dt segundos. Devuelve lista de eventos:
        'eat', 'hungry', 'exit_left', 'exit_right'."""
        events = []
        if dt > 0.5:
            dt = 0.5

        # comida cae y caduca
        for f in self.food:
            if f[1] < Y_MAX + 0.05:
                f[1] += FOOD_FALL * dt
            else:
                f[2] += dt
        self.food = [f for f in self.food if f[2] < FOOD_LIFE]

        fish = self.fish
        if fish is None:
            return events

        if self.cooldown > 0:
            self.cooldown -= dt
        fish.age += dt
        fish.hunger = min(100.0, fish.hunger + HUNGER_RATE * dt)
        fish.asleep = self.night and fish.scared <= 0 and not self.go_to_edge
        if fish.scared > 0:
            fish.scared -= dt

        if fish.hunger >= HUNGRY_LEVEL:
            self._hungry_alert -= dt
            if self._hungry_alert <= 0:
                events.append("hungry")
                self._hungry_alert = 60.0

        if self.leaving:              # quieto en el borde mientras llega el ACK
            return events

        # ----- decidir hacia dónde nadar -----
        target = None
        if self.go_to_edge:
            target = (1.2 if self.go_to_edge == "right" else -0.2, fish.y)
        elif self.food and fish.hunger > 5 and not fish.asleep:
            best = None
            for f in self.food:
                d = (f[0] - fish.x) ** 2 + (f[1] - fish.y) ** 2
                if best is None or d < best[0]:
                    best = (d, f)
            target = (best[1][0], best[1][1])

        if target:
            dx = target[0] - fish.x
            dy = target[1] - fish.y
            if abs(dx) > 0.01:
                fish.vx = SPEED if dx > 0 else -SPEED
            fish.vy = _clamp(dy * 1.5, -SPEED, SPEED)
        else:
            fish._wander -= dt
            if fish._wander <= 0:
                fish._wander = 2 + random.random() * 2
                fish.vy = (random.random() - 0.5) * SPEED * 0.6
                if random.random() < 0.15:
                    fish.vx = -fish.vx

        mult = 1.0
        if fish.scared > 0:
            mult = 3.0
        elif fish.asleep:
            mult = 0.12
        elif fish.hunger >= HUNGRY_LEVEL:
            mult = 0.6
        if self.go_to_edge:
            mult = max(mult, 1.8)

        fish.x += fish.vx * mult * dt
        fish.y += fish.vy * mult * dt

        if fish.y < Y_MIN:
            fish.y = Y_MIN
            fish.vy = abs(fish.vy)
        elif fish.y > Y_MAX:
            fish.y = Y_MAX
            fish.vy = -abs(fish.vy)

        # ----- bordes: rebota o sale hacia la otra pecera -----
        if fish.x > 1 - MARGIN and fish.vx > 0:
            if self.link_side == "right" and (self.cooldown <= 0 or self.go_to_edge):
                fish.x = 1 - MARGIN
                self.leaving = "right"
                events.append("exit_right")
            else:
                fish.x = 1 - MARGIN
                fish.vx = -abs(fish.vx)
                self.go_to_edge = None
        elif fish.x < MARGIN and fish.vx < 0:
            if self.link_side == "left" and (self.cooldown <= 0 or self.go_to_edge):
                fish.x = MARGIN
                self.leaving = "left"
                events.append("exit_left")
            else:
                fish.x = MARGIN
                fish.vx = abs(fish.vx)
                self.go_to_edge = None

        # ----- comer -----
        if not fish.asleep:
            for f in self.food:
                if (f[0] - fish.x) ** 2 + (f[1] - fish.y) ** 2 < EAT_DIST ** 2:
                    self.food.remove(f)
                    fish.hunger = max(0.0, fish.hunger - 30)
                    events.append("eat")
                    break
        return events

    # ---------- persistencia ----------
    def save(self, path="fish.json"):
        data = {"tank": self.tank_id, "fish": self.fish.to_dict() if self.fish else None}
        try:
            with open(path, "w") as fp:
                fp.write(json.dumps(data))
            return True
        except OSError:
            return False

    def load(self, path="fish.json"):
        try:
            with open(path) as fp:
                data = json.loads(fp.read())
            if data.get("fish"):
                self.fish = Fish.from_dict(data["fish"])
                self.fish.x = 0.5
            return True
        except (OSError, ValueError):
            return False
