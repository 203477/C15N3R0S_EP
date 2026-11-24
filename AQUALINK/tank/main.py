# main.py — AQUALINK. El MISMO archivo corre en las dos peceras.
# Lo que cambia entre una y otra esta en config.py (copiado de config_a.py o config_b.py).
#
# Pecera A: crea el pez, sirve el dashboard y dibuja el pez con figuras. Usa los dos nucleos.
# Pecera B: espera al pez y lo dibuja con caracteres.

import time
import gc
import config
from machine import Pin, I2C, UART
from ssd1306 import detect
from render_oled import Scene
from fish import Aquarium
from sensors import Button, HallSensor, LightSensor, Fader, Buzzer, read_temp_c
from tank import TankBrain
from link import wifi_connect, Link
from web import WebServer, json_resp

try:
    from secrets import WIFI_SSID, WIFI_PASSWORD
except ImportError:
    WIFI_SSID = WIFI_PASSWORD = None
try:
    from secrets import PEER_IP
except ImportError:
    PEER_IP = None

DUAL = config.USE_DUAL_CORE
if DUAL:
    import _thread

# ---------------------------------------------------------------- pantalla
i2c = I2C(0, sda=Pin(config.PIN_SDA), scl=Pin(config.PIN_SCL), freq=config.I2C_FREQ)
oled = detect(i2c, config.OLED_WIDTH, config.OLED_HEIGHT)
scene = Scene(oled, config.FISH_STYLE)


def boot_msg(*lines):
    scene.boot(lines)


boot_msg("Pecera " + config.TANK_ID, "Iniciando...")

# ---------------------------------------------------------------- pecera y cerebro
lock = _thread.allocate_lock() if DUAL else None
aq = Aquarium(config.TANK_ID)
aq.load()
buzzer = Buzzer(config.PIN_BUZZER, enabled=config.BUZZER_ON)
brain = TankBrain(config.TANK_ID, aq, buzzer, lock, create_fish=config.CREATE_FISH)
lamp = Fader(config.PIN_LAMP, start=config.LAMP_DAY)

# ---------------------------------------------------------------- entradas
btn_feed = Button(config.PIN_BTN_FEED, "FEED")
btn_send = Button(config.PIN_BTN_SEND, "SEND")
hall = HallSensor(config.PIN_HALL)
light = LightSensor(config.PIN_LDR, config.NIGHT_BELOW, config.DAY_ABOVE, config.LDR_INVERT)

# ---------------------------------------------------------------- red
mode = config.LINK_MODE
wlan, ip, uart = None, None, None
if mode == "wifi":
    if WIFI_SSID is None:
        boot_msg("Falta secrets.py", "copia la plantilla")
        time.sleep(3)
    else:
        wlan, ip = wifi_connect(WIFI_SSID, WIFI_PASSWORD,
                                on_status=lambda s: boot_msg("Pecera " + config.TANK_ID, "Wi-Fi..."))
    if ip is None:
        boot_msg("Sin Wi-Fi", "uso cable UART")
        time.sleep(2)
        mode = "uart"
if mode == "uart":
    uart = UART(0, baudrate=115200, tx=Pin(config.PIN_UART_TX), rx=Pin(config.PIN_UART_RX))

link = Link(config.TANK_ID, brain.status, brain.on_fish, brain.on_cmd,
            mode=mode, wlan=wlan, peer_ip=PEER_IP, uart=uart)
brain.attach(link)

# ---------------------------------------------------------------- web (solo la pecera A)
def _peer_view():
    if not link.peer_alive():
        return None
    p = dict(link.peer)
    p["last_seen_ms"] = link.peer_age_ms()
    return p


def api_status(q):
    me = brain.status()
    me["ip"] = ip
    me["id"] = config.TANK_ID
    peer = _peer_view()
    mine = config.TANK_ID
    other = peer.get("id") if peer else None
    fish_in = mine if me.get("fish") else (other if peer and peer.get("fish") else None)
    return json_resp({
        "fish_in": fish_in,
        "link": brain.linked(),
        "link_side": aq.link_side,
        "mode": mode,
        "transfers_ok": brain.transfers_ok,
        "transfers_failed": brain.transfers_failed,
        "A": me if mine == "A" else peer,
        "B": peer if mine == "A" else me,
        "uptime_s": time.ticks_ms() // 1000,
    })


def _cmd(cmd, value=None):
    code, body = brain.cmd_anywhere(cmd, value)
    return json_resp(body, code)


def api_feed(q):
    return _cmd("feed")


def api_send(q):
    return _cmd("send")


def api_scare(q):
    return _cmd("scare")


def api_name(q):
    return _cmd("name", q.get("value", ""))


def api_light(q):
    try:
        v = int(q.get("value", ""))
    except ValueError:
        return json_resp({"error": "value debe ser un entero 0-100"}, 400)
    if not 0 <= v <= 100:
        return json_resp({"error": "value fuera de rango 0-100"}, 400)
    lamp.force(v, seconds=10)
    return json_resp({"ok": True, "lamp": v, "for_s": 10})


web = None
if ip and config.SERVE_DASHBOARD:
    web = WebServer({
        "/api/status": api_status,
        "/api/feed": api_feed,
        "/api/send": api_send,
        "/api/scare": api_scare,
        "/api/name": api_name,
        "/api/light": api_light,
    }, files={"/": ("index.html", "text/html; charset=utf-8")})
    print("Dashboard: http://%s/" % ip)

boot_msg("IP " + (ip or "UART"), "Dashboard en A" if not config.SERVE_DASHBOARD else "http://%s/" % ip)
time.sleep(2)

# ---------------------------------------------------------------- estado compartido
ui = {"info": False, "msg": "", "tank": config.TANK_ID, "ip": ip, "peer_ip": None,
      "peer_fish": False, "peer_id": None, "light": 100, "temp": 0.0, "ok": 0, "fail": 0}
pending = []


class _NoLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


L = lock or _NoLock()


def snapshot():
    f = aq.fish
    return {
        "night": aq.night,
        "link_side": aq.link_side,
        "food": [(x, y) for (x, y, _) in aq.food],
        "fish": None if f is None else {
            "x": f.x, "y": f.y, "right": f.facing_right, "asleep": f.asleep,
            "hunger": f.hunger, "name": f.name, "gen": f.gen},
    }


def frame(dt):
    with L:
        ev = aq.update(dt)
        if ev:
            pending.extend(ev)
        snap = snapshot()
    if ui["info"]:
        scene.info(ui, snap)
    else:
        scene.draw(snap, ui)


def render_loop():
    period = 1000 // config.TARGET_FPS
    last = time.ticks_ms()
    while True:
        t0 = time.ticks_ms()
        frame(time.ticks_diff(t0, last) / 1000)
        last = t0
        spent = time.ticks_diff(time.ticks_ms(), t0)
        if spent < period:
            time.sleep_ms(period - spent)


if DUAL:
    _thread.start_new_thread(render_loop, ())

# ---------------------------------------------------------------- bucle principal
last = time.ticks_ms()
last_frame = last
last_temp = 0
msg_until = 0
was_night = None

while True:
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last) / 1000
    last = now

    # --- botones: corto y largo (GPIO + interrupciones) ---
    ev = btn_feed.update()
    if ev == "short":
        with L:
            aq.drop_food()
    elif ev == "long":
        brain.local_cmd("scare")                 # golpe al vidrio
    ev = btn_send.update()
    if ev == "short":
        ok, why = brain.local_cmd("send")
        if not ok:
            brain.message = why
    elif ev == "long":
        ui["info"] = not ui["info"]              # pantalla de datos

    # --- sensores ---
    brain.hall = hall.active()
    night = light.update()
    brain.light_pct = light.percent
    with L:
        aq.night = night
    if time.ticks_diff(now, last_temp) > 2000:
        last_temp = now
        brain.temp_c = read_temp_c()

    # --- salidas PWM y brillo de la OLED ---
    if not lamp.overridden():
        lamp.set_target(config.LAMP_NIGHT if night else config.LAMP_DAY)
    lamp.update(dt)
    if night != was_night:
        was_night = night
        oled.contrast(config.OLED_CONTRAST_NIGHT if night else config.OLED_CONTRAST_DAY)
    buzzer.update()

    # --- red ---
    link.poll()
    if web:
        web.poll()
        brain.web_requests = web.requests
    brain.update_link()
    brain.resolve_conflict()
    brain.maybe_create_fish()

    # --- eventos de la simulacion ---
    with L:
        evs = pending[:]
        del pending[:]
    if evs:
        brain.handle_events(evs)
    brain.periodic()

    # --- datos para la pantalla ---
    if brain.message:
        ui["msg"] = brain.message
        brain.message = ""
        msg_until = time.ticks_add(now, 2500)
    elif ui["msg"] and time.ticks_diff(now, msg_until) > 0:
        ui["msg"] = ""
    ui["peer_ip"] = link.peer_ip if link.peer_alive() else None
    ui["peer_fish"] = bool(link.peer_alive() and link.peer.get("fish"))
    ui["peer_id"] = link.peer.get("id")
    ui["light"] = light.percent
    ui["temp"] = brain.temp_c
    ui["ok"], ui["fail"] = brain.transfers_ok, brain.transfers_failed

    # --- si no hay doble nucleo, dibujamos aqui mismo ---
    if not DUAL and time.ticks_diff(now, last_frame) >= 1000 // config.TARGET_FPS:
        frame(time.ticks_diff(now, last_frame) / 1000)
        last_frame = now
        gc.collect()

    time.sleep_ms(5)
