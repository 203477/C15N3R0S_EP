# render_oled.py — Dibuja la pecera en una OLED SSD1306 de 128x64 (blanco y negro)
#
# Las dos peceras usan este mismo archivo. Solo cambia el estilo del pez:
#   STYLE = "pixel"  -> pez dibujado con figuras (pecera A)
#   STYLE = "ascii"  -> pez de caracteres  ><(((>  (pecera B)
# Así se nota en la demo que el mismo pez se dibuja de dos maneras distintas.

import math
import random
import time
from array import array

W, H = 128, 64
BAR = 10                 # alto de la barra de arriba
SAND_Y = 56              # linea de la arena
WATER_TOP, WATER_BOTTOM = BAR + 3, SAND_Y - 4
ON, OFF = 1, 0


def _short_ip(ip):
    """192.168.43.21 -> .43.21, para que quepa en 16 caracteres."""
    if not ip:
        return "--"
    parts = ip.split(".")
    return "." + ".".join(parts[-2:]) if len(parts) == 4 else ip


class Scene:
    def __init__(self, oled, style="pixel"):
        self.oled = oled
        self.style = style
        self.bubbles = []
        self.weeds = [(10, 3), (30, 2), (100, 3), (118, 2)]
        self._t0 = time.ticks_ms()
        self._next_bubble = 0

    # ---------------------------------------------------------------- pantallas sueltas
    def center(self, s, y, c=ON):
        self.oled.text(s[:16], max(0, (W - len(s) * 8) // 2), y, c)

    def boot(self, lines):
        o = self.oled
        o.fill(OFF)
        o.rect(0, 0, W, H, ON)
        self.center("AQUALINK", 6)
        for i, s in enumerate(lines[:3]):
            self.center(s, 24 + i * 11)
        o.show()

    def info(self, ui, snap):
        """Pantalla de datos (boton INFO). Cabe justo en 128x64."""
        o = self.oled
        o.fill(OFF)
        o.text("AQUALINK  " + ui.get("tank", "?"), 0, 0, ON)
        o.hline(0, 9, W, ON)
        rows = [
            "IP %s" % (ui.get("ip") or "sin red"),
            "otra %s" % _short_ip(ui.get("peer_ip")),
            "enlace %s" % {"right": "der", "left": "izq"}.get(snap["link_side"], "no"),
            "luz %d%% %s" % (ui.get("light", 0), "noche" if snap["night"] else "dia"),
            "envios %d/%d" % (ui.get("ok", 0), ui.get("fail", 0)),
        ]
        for i, s in enumerate(rows):
            o.text(s[:16], 0, 13 + i * 10, ON)
        o.show()

    # ---------------------------------------------------------------- escena
    def draw(self, snap, ui):
        o = self.oled
        t = time.ticks_diff(time.ticks_ms(), self._t0) / 1000
        o.fill(OFF)

        fish = snap["fish"]
        self._top_bar(snap, fish)

        # arena
        o.hline(0, SAND_Y, W, ON)
        for x in range(2, W, 10):
            o.pixel(x, SAND_Y + 3, ON)
            o.pixel(x + 4, SAND_Y + 5, ON)

        # algas que se mecen
        for k, (bx, n) in enumerate(self.weeds):
            x0, y0 = bx, SAND_Y
            for j in range(1, n * 2 + 1):
                x1 = bx + int(math.sin(t * 1.5 + k + j * 0.6) * j * 0.8)
                y1 = SAND_Y - j * 4
                o.line(x0, y0, x1, y1, ON)
                x0, y0 = x1, y1

        # flecha hacia la otra pecera
        side = snap["link_side"]
        if side:
            ax = W - 3 if side == "right" else 2
            d = 1 if side == "right" else -1
            for k in range(4):
                o.vline(ax - k * d, 32 - k, 2 * k + 1, ON)

        # comida
        for (fx, fy) in snap["food"]:
            x = int(fx * W)
            y = WATER_TOP + int(fy * (WATER_BOTTOM - WATER_TOP))
            o.fill_rect(x - 1, y - 1, 2, 2, ON)

        # pez
        if fish:
            self._fish(fish, t)
        else:
            self.center("el pez esta", 26)
            self.center("en la otra", 36)

        # burbujas
        if random.random() < 0.25:
            self.bubbles.append([random.randint(8, W - 8), SAND_Y - 4])
        alive = []
        for b in self.bubbles:
            b[1] -= 2
            b[0] += random.randint(-1, 1)
            if b[1] > WATER_TOP:
                o.pixel(b[0], b[1], ON)
                o.pixel(b[0] + 1, b[1], ON)
                alive.append(b)
        self.bubbles = alive[-8:]

        # mensaje temporal
        msg = ui.get("msg")
        if msg:
            box = min(W, len(msg) * 8 + 6)
            x = (W - box) // 2
            o.fill_rect(x, 26, box, 12, OFF)
            o.rect(x, 26, box, 12, ON)
            self.center(msg, 28)

        o.show()

    # ---------------------------------------------------------------- partes
    def _top_bar(self, snap, fish):
        o = self.oled
        o.fill_rect(0, 0, W, BAR, ON)
        if fish:
            o.text(fish["name"][:6], 1, 1, OFF)            # texto en negro sobre blanco
            hunger = fish["hunger"]
            o.rect(56, 1, 44, 7, OFF)
            if hunger > 2:
                o.fill_rect(57, 2, int(42 * hunger / 100), 5, OFF)
        else:
            o.text("pecera", 1, 1, OFF)
        o.text("<>" if snap["link_side"] else "--", W - 17, 1, OFF)
        if snap["night"]:
            o.fill_rect(46, 2, 5, 5, OFF)

    def _fish(self, fish, t):
        o = self.oled
        x = int(fish["x"] * W)
        y = WATER_TOP + int(fish["y"] * (WATER_BOTTOM - WATER_TOP))
        right = fish["right"]
        d = 1 if right else -1
        wag = int(math.sin(t * (3 if fish["asleep"] else 9)) * 2)

        if self.style == "ascii":
            s = "><(((>" if right else "<)))><"
            x0 = max(0, min(W - len(s) * 8, x - len(s) * 4))
            o.text(s, x0, y - 4, ON)
        else:
            o.ellipse(x, y, 9, 5, ON, True)                # cuerpo
            tail = [x - 9 * d, y, x - 17 * d, y - 5 + wag, x - 17 * d, y + 5 + wag]
            o.poly(0, 0, _arr(tail), ON, True)             # cola
            o.poly(0, 0, _arr([x - 2 * d, y - 4, x + 4 * d, y - 4, x, y - 9]), ON, True)
            o.pixel(x + 5 * d, y - 2, OFF)                 # ojo
            o.pixel(x + 5 * d + d, y - 2, OFF)

        if fish["asleep"]:
            o.text("z", x + 11 * d, y - 14, ON)
            o.text("Z", x + 16 * d, y - 22, ON)


def _arr(coords):
    """framebuf.poly necesita un array de enteros con signo."""
    return array("h", [int(v) for v in coords])
