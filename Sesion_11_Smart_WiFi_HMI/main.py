# ================================================================
# SESIÓN 11 - DO11
# SMART Wi-Fi HMI FINAL
# Raspberry Pi Pico W / Pico 2 W - MicroPython
# ================================================================
#
# Integra: Wi-Fi (STA) + servidor HTTP con sockets + PWM
#          + salida digital + OLED SSD1306 por I2C + API JSON
#
# ARCHIVOS EN LA RAÍZ DE LA PICO
# ------------------------------
# /secrets.py   (NO se sube a GitHub)
# /ssd1306.py
# /main.py      (este archivo)
#
# HARDWARE
# --------
# GP15 -> LED PWM (resistencia 220/330 ohm)
# GP14 -> LED 2 digital (resistencia 220/330 ohm)
# GP4  -> OLED SDA
# GP5  -> OLED SCL
# 3V3  -> OLED VCC
# GND  -> OLED GND / cátodos de los LEDs
#
# ENDPOINTS
# ---------
# GET /                    -> Dashboard HTML
# GET /api/status          -> Estado en JSON
# GET /api/pwm?value=N     -> PWM 0..100 (400 si N es inválido)
# GET /api/led2/toggle     -> Alterna LED 2
# GET /api/leds?state=on   -> BONUS: ambos LEDs ON/OFF
# cualquier otra ruta      -> 404
# ================================================================

import network
import socket
import json

from machine import (
    Pin,
    PWM,
    I2C,
    ADC
)

from time import (
    sleep_ms,
    ticks_ms,
    ticks_diff,
    localtime,
    time
)

from secrets import (
    WIFI_SSID,
    WIFI_PASSWORD
)

from ssd1306 import SSD1306_I2C


# ================================================================
# CONFIGURACIÓN
# ================================================================

PIN_LED_PWM = 15
PIN_LED2 = 14
PIN_SDA = 4
PIN_SCL = 5
OLED_ADDR = 0x3C

PWM_FREQ = 1000          # Hz
HTTP_PORT = 80
UTC_OFFSET_H = -6        # Hora de Puebla / CDMX (UTC-6)
OLED_REFRESH_MS = 5000   # refresco periódico de la OLED (reloj)


# ================================================================
# BLOQUE 1 - Wi-Fi (modo STA)
# ================================================================

def get_sta_interface():

    try:
        return network.WLAN(
            network.WLAN.IF_STA
        )

    except AttributeError:
        return network.WLAN(
            network.STA_IF
        )


def connect_wifi(
    ssid,
    password,
    timeout_ms=20000
):

    wlan = get_sta_interface()
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    try:
        wlan.disconnect()
        sleep_ms(200)
    except Exception:
        pass

    print("Conectando a:", ssid)

    wlan.connect(
        ssid,
        password
    )

    start = ticks_ms()

    while not wlan.isconnected():

        if ticks_diff(
            ticks_ms(),
            start
        ) >= timeout_ms:

            raise RuntimeError(
                "Timeout Wi-Fi"
            )

        sleep_ms(250)

    print(
        "Wi-Fi conectado | IP:",
        wlan.ifconfig()[0]
    )

    return wlan


# ================================================================
# BLOQUE 2 - SERVIDOR TCP
# ================================================================

def create_server(port=80):

    addr = socket.getaddrinfo(
        "0.0.0.0",
        port
    )[0][-1]

    server = socket.socket()

    try:
        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )
    except Exception:
        pass

    server.bind(addr)
    server.listen(2)

    try:
        # accept() lanza OSError cada 1 s si no llega nadie:
        # así el loop sigue vivo y puede imprimir/refrescar.
        server.settimeout(1)
    except Exception:
        pass

    return server


# ================================================================
# BLOQUE 3 - HARDWARE
# ================================================================

# LED 1: brillo variable por PWM.
led_pwm = PWM(
    Pin(PIN_LED_PWM)
)

led_pwm.freq(PWM_FREQ)


# LED 2: solo ON / OFF.
led2 = Pin(
    PIN_LED2,
    Pin.OUT
)


# Sensor de temperatura interno (ADC canal 4) - BONUS ADC real.
try:
    temp_adc = ADC(4)
except Exception:
    temp_adc = None


# OLED de la sesión I2C.
i2c = I2C(
    0,
    sda=Pin(PIN_SDA),
    scl=Pin(PIN_SCL),
    freq=400000
)

devices = i2c.scan()

print(
    "I2C scan:",
    [hex(d) for d in devices]
)

oled = None

if OLED_ADDR in devices:

    oled = SSD1306_I2C(
        128,
        64,
        i2c
    )

else:
    # Si la OLED falla, el dashboard web puede continuar.
    print(
        "AVISO: OLED 0x3C no encontrada; "
        "el servidor sigue sin OLED"
    )


# Estado del sistema.
pwm_percent = 0
led2_state = 0
request_count = 0
ntp_ok = False


# ================================================================
# TODO 1 - PWM  (RESUELTO)
# ================================================================

def set_pwm(percent):

    global pwm_percent

    # 1) limitar percent a 0..100
    percent = max(
        0,
        min(100, int(percent))
    )

    # 2) convertir 0..100 % -> 0..65535
    duty = int(
        percent * 65535 / 100
    )

    # 3) aplicar al hardware
    led_pwm.duty_u16(duty)

    # 4) guardar el estado
    pwm_percent = percent


# ================================================================
# TODO 2 - LED 2  (RESUELTO)
# ================================================================

def set_led2(value):

    global led2_state

    led2_state = 1 if value else 0
    led2.value(led2_state)


def toggle_led2():

    # 0 -> 1  /  1 -> 0
    set_led2(
        1 - led2_state
    )


# ================================================================
# BONUS - TEMPERATURA (ADC) Y HORA (NTP)
# ================================================================

def read_temp_c():

    if temp_adc is None:
        return None

    try:
        volts = temp_adc.read_u16() * 3.3 / 65535
        # Fórmula del datasheet RP2040 / RP2350
        temp = 27 - (volts - 0.706) / 0.001721
        return round(temp, 1)

    except Exception:
        return None


def sync_ntp():

    global ntp_ok

    try:
        import ntptime
        ntptime.settime()
        ntp_ok = True
        print("NTP sincronizado")

    except Exception as exc:
        # NTP es opcional: si falla, todo lo demás sigue.
        ntp_ok = False
        print("NTP no disponible:", exc)


def local_time_text():

    if not ntp_ok:
        return "--:--"

    t = localtime(
        time() + UTC_OFFSET_H * 3600
    )

    return "{:02d}:{:02d}".format(
        t[3],
        t[4]
    )


def wifi_rssi(wlan):

    try:
        return wlan.status("rssi")
    except Exception:
        return None


# ================================================================
# TODO 3 - OLED  (RESUELTO)
# ================================================================

def show_oled(ip):

    if oled is None:
        return

    try:
        oled.fill(0)

        # Encabezado invertido
        oled.fill_rect(0, 0, 128, 10, 1)
        oled.text("SMART WIFI HMI", 8, 1, 0)

        oled.text(ip, 0, 14)

        oled.text(
            "PWM: {}%".format(pwm_percent),
            0,
            26
        )

        oled.text(
            "LED2: {}".format(
                "ON" if led2_state else "OFF"
            ),
            0,
            36
        )

        oled.text(
            "REQ: {}".format(request_count),
            0,
            46
        )

        # Barra del PWM a la derecha
        oled.rect(88, 26, 40, 8, 1)
        oled.fill_rect(
            88,
            26,
            int(40 * pwm_percent / 100),
            8,
            1
        )

        # Indicador LED2 (cuadro relleno = ON)
        if led2_state:
            oled.fill_rect(88, 36, 8, 8, 1)
        else:
            oled.rect(88, 36, 8, 8, 1)

        # Hora NTP (bonus)
        oled.text(
            local_time_text(),
            88,
            56
        )

        oled.show()

    except Exception as exc:
        # Un error de I2C no debe tumbar el servidor.
        print("OLED ERROR:", exc)


# ================================================================
# BLOQUE 4 - ESTADO JSON
# ================================================================

def status_dict(ip):

    return {
        "ip": ip,
        "pwm": pwm_percent,
        "led2": led2_state,
        "requests": request_count,
        "temp_c": read_temp_c(),
        "rssi": wifi_rssi(wlan),
        "time": local_time_text(),
    }


# ================================================================
# BLOQUE 5 - HTML
# ================================================================

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Pico Smart HMI</title>

<style>
body {
    font-family: Arial, sans-serif;
    background: #08131f;
    color: #eef7ff;
    margin: 0;
    padding: 18px;
}

.card {
    max-width: 620px;
    margin: auto;
    background: #13263a;
    padding: 24px;
    border-radius: 18px;
}

h1 {
    margin-top: 0;
    color: #62e6f0;
}

.panel {
    background: #0d1d2d;
    padding: 16px;
    margin: 14px 0;
    border-radius: 14px;
}

input[type=range] {
    width: 100%;
}

button {
    padding: 12px 18px;
    margin: 4px 4px 4px 0;
    border: 0;
    border-radius: 10px;
    background: #1b9aaa;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

.dot {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #666;
    vertical-align: middle;
}

code {
    color: #8be9fd;
}

.small {
    color: #9fb3c8;
    font-size: 14px;
}

#msg {
    color: #ff7b7b;
    min-height: 18px;
}
</style>
</head>

<body>
<div class='card'>

<h1>Pico Smart HMI</h1>

<p>
IP:
<code>__IP__</code>
&nbsp;
<span id='connDot' class='dot'></span>
<span id='connText' class='small'>conectando...</span>
</p>


<div class='panel'>

<h3>LED PWM - GP15</h3>

<p>
Valor:
<b id='pwmValue'>__PWM__%</b>
</p>

<input
    id='pwmSlider'
    type='range'
    min='0'
    max='100'
    step='1'
    value='__PWM__'
    oninput='previewPWM(this.value)'
    onchange='applyPWM(this.value)'
>

</div>


<div class='panel'>

<h3>LED 2 - GP14</h3>

<p>
<span id='led2Dot' class='dot'></span>
Estado:
<b id='led2State'>__LED2_TEXT__</b>
</p>

<button onclick='toggleLed2()'>TOGGLE LED 2</button>

</div>


<div class='panel'>

<h3>Ambos LEDs (bonus)</h3>

<button onclick="allLeds('on')">ALL ON</button>
<button onclick="allLeds('off')">ALL OFF</button>

</div>


<div class='panel'>

<p>
Requests:
<b id='requestValue'>__REQ__</b>
</p>

<p class='small'>
Temp. interna: <b id='tempValue'>--</b> &deg;C
&nbsp;|&nbsp;
RSSI: <b id='rssiValue'>--</b> dBm
&nbsp;|&nbsp;
Hora: <b id='timeValue'>--:--</b>
</p>

<button onclick='refreshStatus()'>REFRESH STATUS</button>

<p id='msg'></p>

</div>


<script>

function byId(id) {
    return document.getElementById(id);
}


function setConnection(ok) {

    byId('connDot').style.background = ok ? '#43e97b' : '#ff5c5c';
    byId('connText').textContent = ok ? 'en linea' : 'sin respuesta';
}


function previewPWM(value) {

    byId('pwmValue').textContent = value + '%';
}


function updateStatus(data) {

    byId('pwmSlider').value = data.pwm;
    byId('pwmValue').textContent = data.pwm + '%';

    byId('led2State').textContent = data.led2 ? 'ON' : 'OFF';
    byId('led2Dot').style.background = data.led2 ? '#43e97b' : '#666';

    byId('requestValue').textContent = data.requests;

    byId('tempValue').textContent =
        (data.temp_c === null) ? '--' : data.temp_c;

    byId('rssiValue').textContent =
        (data.rssi === null) ? '--' : data.rssi;

    byId('timeValue').textContent = data.time;
}


function callApi(url) {

    fetch(url, {cache: 'no-store'})
    .then(function(response) {

        return response.json().then(function(data) {
            return {ok: response.ok, data: data};
        });
    })
    .then(function(result) {

        setConnection(true);

        if (result.ok) {
            byId('msg').textContent = '';
            updateStatus(result.data);
        } else {
            byId('msg').textContent = 'Error: ' + result.data.error;
        }
    })
    .catch(function() {

        setConnection(false);
        byId('msg').textContent = 'La Pico no respondio';
    });
}


function applyPWM(value) {
    callApi('/api/pwm?value=' + value);
}

function toggleLed2() {
    callApi('/api/led2/toggle');
}

function allLeds(state) {
    callApi('/api/leds?state=' + state);
}

function refreshStatus() {
    callApi('/api/status');
}


refreshStatus();

// Indicador de conexion: consulta el estado cada 10 s.
setInterval(refreshStatus, 10000);

</script>

</div>
</body>
</html>
"""


def html_page(ip):

    page = HTML_TEMPLATE

    page = page.replace("__IP__", ip)
    page = page.replace("__PWM__", str(pwm_percent))
    page = page.replace("__REQ__", str(request_count))
    page = page.replace(
        "__LED2_TEXT__",
        "ON" if led2_state else "OFF"
    )

    return page


# ================================================================
# FUNCIÓN AUXILIAR - QUERY STRING
# ================================================================

def split_target(target):
    """
    /api/pwm?value=73  ->  ("/api/pwm", {"value": "73"})
    """

    if "?" in target:
        path, query = target.split("?", 1)
    else:
        path = target
        query = ""

    params = {}

    for item in query.split("&"):

        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        params[key] = value

    return path, params


# ================================================================
# RESPUESTAS AUXILIARES
# ================================================================

JSON_TYPE = "application/json"


def json_ok(ip):

    return (
        "200 OK",
        JSON_TYPE,
        json.dumps(status_dict(ip))
    )


def json_error(status, message):

    return (
        status,
        JSON_TYPE,
        json.dumps({"error": message})
    )


def parse_percent(text):
    """
    Devuelve un entero 0..100 o None si es inválido.
    Acepta solo dígitos: "37" sí; "-5", "abc", "3.7", "150" no.
    """

    if text is None:
        return None

    text = text.strip()

    if not text or not text.isdigit():
        return None

    value = int(text)

    if value < 0 or value > 100:
        return None

    return value


# ================================================================
# TODO 4 - ROUTER  (RESUELTO)
# ================================================================

def route(target, ip):

    path, params = split_target(target)

    # El navegador pide el ícono automáticamente.
    if path == "/favicon.ico":
        return ("204 No Content", "text/plain", "")

    if path == "/":
        return (
            "200 OK",
            "text/html; charset=utf-8",
            html_page(ip)
        )

    if path == "/api/status":
        return json_ok(ip)

    if path == "/api/pwm":

        value = parse_percent(
            params.get("value")
        )

        if value is None:
            return json_error(
                "400 Bad Request",
                "value debe ser un entero entre 0 y 100"
            )

        set_pwm(value)
        return json_ok(ip)

    if path == "/api/led2/toggle":
        toggle_led2()
        return json_ok(ip)

    # BONUS: encender/apagar ambos LEDs
    if path == "/api/leds":

        state = params.get("state", "").lower()

        if state == "on":
            set_pwm(100)
            set_led2(1)
            return json_ok(ip)

        if state == "off":
            set_pwm(0)
            set_led2(0)
            return json_ok(ip)

        return json_error(
            "400 Bad Request",
            "state debe ser on u off"
        )

    return json_error(
        "404 Not Found",
        "ruta no encontrada: " + path
    )


# ================================================================
# BLOQUE 6 - RESPUESTA HTTP
# ================================================================

def send_response(
    client,
    status,
    content_type,
    body
):

    if isinstance(body, str):
        body = body.encode()

    header = (
        "HTTP/1.1 {}\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        "\r\n"
    ).format(
        status,
        content_type,
        len(body)
    )

    client.write(header.encode())

    if body:
        client.write(body)


# ================================================================
# BLOQUE 7 - ARRANQUE
# ================================================================

wlan = connect_wifi(
    WIFI_SSID,
    WIFI_PASSWORD
)

ip = wlan.ifconfig()[0]

# Estado inicial.
set_led2(0)
set_pwm(0)

sync_ntp()
show_oled(ip)

server = create_server(HTTP_PORT)

print()
print("====================================")
print(" DO11 - SMART Wi-Fi HMI")
print("====================================")
print("Abre:")
print("http://{}/".format(ip))
print()


# ================================================================
# BLOQUE 8 - LOOP HTTP
# ================================================================

def serve_forever():

    global request_count

    last_wait = ticks_ms()
    last_oled = ticks_ms()

    while True:

        client = None

        try:

            client, remote = server.accept()

            try:
                client.settimeout(3)
            except Exception:
                pass

            raw = client.recv(2048)

            if not raw:
                continue

            first_line = raw.split(
                b"\r\n",
                1
            )[0].decode()

            parts = first_line.split(" ")

            target = (
                parts[1]
                if len(parts) >= 2
                else "/"
            )

            request_count += 1

            status, content_type, body = route(
                target,
                ip
            )

            send_response(
                client,
                status,
                content_type,
                body
            )

            show_oled(ip)
            last_oled = ticks_ms()

            print(
                "{} -> {} -> {}".format(
                    remote,
                    target,
                    status
                )
            )

        except OSError:
            # Timeout de accept(): no llegó navegador.
            now = ticks_ms()

            if ticks_diff(now, last_wait) >= 5000:
                print(
                    "Servidor vivo: http://{}/".format(ip)
                )
                last_wait = now

            if ticks_diff(now, last_oled) >= OLED_REFRESH_MS:
                show_oled(ip)
                last_oled = now

        except Exception as exc:
            # Cualquier otro error se reporta y el servidor sigue.
            print("SERVER ERROR:", exc)

            if client:
                try:
                    send_response(
                        client,
                        "500 Internal Server Error",
                        JSON_TYPE,
                        json.dumps({"error": str(exc)})
                    )
                except Exception:
                    pass

        finally:

            if client:
                try:
                    client.close()
                except Exception:
                    pass


serve_forever()
