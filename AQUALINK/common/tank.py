# tank.py — "Cerebro" compartido por ambas peceras
# Une la pecera (fish.Aquarium), la comunicación (link.Link) y el buzzer.
# Decide cuándo hay enlace, manda/recibe el pez con ACK y atiende órdenes de la web.

import time
from fish import Fish, valid_name

SAVE_EVERY_MS = 60000


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TankBrain:
    def __init__(self, tank_id, aq, buzzer=None, lock=None, create_fish=False):
        self.id = tank_id
        self.aq = aq
        self.buzzer = buzzer
        self.lock = lock or _NoLock()
        self.create_fish = create_fish
        self.link = None
        self.web_requests = 0
        # lecturas de sensores (las actualiza main.py)
        self.hall = False
        self.light_pct = 100
        self.temp_c = 0.0
        # estadísticas
        self.transfers_ok = 0
        self.transfers_failed = 0
        self.last_seq_in = -1
        self._boot = time.ticks_ms()
        self._last_save = time.ticks_ms()
        self._was_linked = False
        self.message = ""          # texto corto para mostrar en pantalla

    def attach(self, link):
        self.link = link

    def _beep(self, seq):
        if self.buzzer:
            self.buzzer.play(seq)

    # ------------------------------------------------------------ estado
    def linked(self):
        return self.aq.link_side is not None

    def status(self):
        """Lo que mando en cada HELLO (y uso en /api/status)."""
        f = self.aq.fish
        d = {"hall": 1 if self.hall else 0, "fish": 1 if f else 0,
             "night": 1 if self.aq.night else 0, "light": self.light_pct,
             "temp_c": self.temp_c, "req": self.web_requests,
             "link": 1 if self.linked() else 0}
        if f:
            d.update({"gen": f.gen, "name": f.name, "hunger": round(f.hunger),
                      "x": round(f.x, 3), "y": round(f.y, 3), "age_s": int(f.age),
                      "asleep": 1 if f.asleep else 0, "right": 1 if f.facing_right else 0})
        return d

    # ------------------------------------------------------------ enlace
    def update_link(self):
        """Decide de qué lado está la otra pecera.
        Mi sensor Hall detecta el imán de la otra -> está a mi DERECHA.
        El Hall de la otra detecta MI imán      -> está a mi IZQUIERDA."""
        side = None
        if self.link and self.link.peer_alive():
            if self.hall:
                side = "right"
            elif self.link.peer.get("hall"):
                side = "left"
        with self.lock:
            self.aq.link_side = side
        if side and not self._was_linked:
            self._beep(self.buzzer.LINK if self.buzzer else None)
            self.message = "Enlace con la otra pecera"
        self._was_linked = side is not None

    def resolve_conflict(self):
        """Si por un reinicio ambas peceras creen tener el pez, se queda el de mayor gen."""
        if not (self.link and self.link.peer_alive() and self.aq.fish):
            return
        p = self.link.peer
        if not p.get("fish"):
            return
        mine, theirs = self.aq.fish.gen, p.get("gen", 0)
        if theirs > mine or (theirs == mine and self.id > p.get("id", "")):
            print("tank: pez duplicado detectado, me quedo sin pez (gen %d vs %d)" % (mine, theirs))
            with self.lock:
                self.aq.fish = None
            self.aq.save()

    def maybe_create_fish(self):
        """La primera vez (sin fish.json) la pecera A crea al pez."""
        if not self.create_fish or self.aq.fish:
            return
        age = time.ticks_diff(time.ticks_ms(), self._boot)
        if age < 8000:
            return                               # da tiempo a escuchar a la otra pecera
        if self.link and self.link.peer_alive() and self.link.peer.get("fish"):
            self.create_fish = False             # el pez ya vive en la otra pecera
            return
        if self.link and self.link.peer_alive() or age > 15000:
            with self.lock:
                self.aq.fish = Fish()
            self.aq.save()
            self.create_fish = False
            self.message = "Nacio un pez!"

    # ------------------------------------------------------------ pez que llega
    def on_fish(self, msg):
        seq = msg.get("seq", 0)
        with self.lock:
            if self.aq.fish is not None:
                if seq <= self.last_seq_in:
                    return True, ""              # reintento de algo que ya recibí
                return False, "ya tengo un pez"
            if seq <= self.last_seq_in:
                return True, ""
            fish = Fish.from_dict(msg["fish"])
            fish.gen = seq
            self.aq.receive(fish, msg.get("enter", "left"))
            self.last_seq_in = seq
        self.aq.save()
        self._beep(self.buzzer.ARRIVE if self.buzzer else None)
        self.message = "Llego " + fish.name
        print("tank: llegó el pez", fish.name, "seq", seq)
        return True, ""

    # ------------------------------------------------------------ pez que se va
    def do_transfer(self, side):
        with self.lock:
            fish = self.aq.fish
            if fish is None:
                return False
            if side != self.aq.link_side or not self.link:
                self.aq.transfer_failed()
                return False
            seq = fish.gen + 1
            data = fish.to_dict()
        msg = {"t": "FISH", "seq": seq, "enter": "left" if side == "right" else "right",
               "fish": data}
        reply = self.link.send(msg)          # puede tardar hasta 1.5 s
        ok = bool(reply and reply.get("t") == "ACK" and reply.get("seq") == seq)
        with self.lock:
            if ok:
                self.aq.transfer_ok()
            else:
                self.aq.transfer_failed()
        if ok:
            self.transfers_ok += 1
            self.aq.save()
            self._beep(self.buzzer.SEND if self.buzzer else None)
            self.message = "Pez enviado"
        else:
            self.transfers_failed += 1
            self._beep(self.buzzer.ERROR if self.buzzer else None)
            self.message = "Envio fallido"
            print("tank: transferencia fallida, respuesta:", reply)
        return ok

    def handle_events(self, events):
        for ev in events:
            if ev == "eat":
                self._beep(self.buzzer.EAT if self.buzzer else None)
            elif ev == "hungry":
                self._beep(self.buzzer.HUNGRY if self.buzzer else None)
                self.message = "Tengo hambre!"
            elif ev == "exit_right":
                self.do_transfer("right")
            elif ev == "exit_left":
                self.do_transfer("left")

    def periodic(self):
        if time.ticks_diff(time.ticks_ms(), self._last_save) > SAVE_EVERY_MS:
            self._last_save = time.ticks_ms()
            if self.aq.fish:
                self.aq.save()

    # ------------------------------------------------------------ órdenes
    def local_cmd(self, cmd, value=None):
        """Ejecuta una orden en ESTA pecera. Devuelve (ok, motivo)."""
        with self.lock:
            if cmd == "feed":
                return (self.aq.drop_food(), "demasiada comida")
            if self.aq.fish is None:
                return False, "el pez no esta aqui"
            if cmd == "send":
                return (self.aq.request_send(), "las peceras no estan juntas")
            if cmd == "scare":
                self.aq.scare()
                return True, ""
            if cmd == "name":
                if not valid_name(value or ""):
                    return False, "nombre invalido"
                self.aq.fish.name = value
                return True, ""
        return False, "orden desconocida"

    def on_cmd(self, msg):
        ok, why = self.local_cmd(msg.get("cmd"), msg.get("value"))
        return {"t": "OK"} if ok else {"t": "ERR", "why": why}

    def cmd_anywhere(self, cmd, value=None):
        """Para la web: ejecuta la orden donde esté el pez. Devuelve (código HTTP, dict)."""
        if cmd == "name" and not valid_name(value or ""):
            return 400, {"error": "nombre invalido (1-10 letras o numeros)"}
        if cmd == "send" and not self.linked():
            return 409, {"error": "las peceras no estan juntas"}
        if self.aq.fish is not None or (cmd == "feed" and not self._peer_has_fish()):
            ok, why = self.local_cmd(cmd, value)
            return (200, {"ok": True, "tank": self.id}) if ok else (409, {"error": why})
        if not (self.link and self.link.peer_alive()):
            return 503, {"error": "la otra pecera no responde"}
        reply = self.link.send({"t": "CMD", "cmd": cmd, "value": value})
        if reply and reply.get("t") == "OK":
            return 200, {"ok": True, "tank": self.link.peer.get("id")}
        return 409, {"error": (reply or {}).get("why", "sin respuesta")}

    def _peer_has_fish(self):
        return bool(self.link and self.link.peer_alive() and self.link.peer.get("fish"))
