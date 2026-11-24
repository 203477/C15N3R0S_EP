# link.py — Comunicación entre peceras
# Wi-Fi (modo STA) + UDP para descubrir a la otra pecera + TCP para mandar el pez con ACK.
# Plan B: el mismo protocolo por UART (cable) si el Wi-Fi falla.
#
# Mensajes (JSON, una línea terminada en \n):
#   HELLO  {"t":"HELLO","id":"A","ip":"...","hall":1,"fish":1,"gen":3,...}   cada 1 s
#   FISH   {"t":"FISH","seq":4,"enter":"left","fish":{...}}                   pez viajando
#   ACK    {"t":"ACK","seq":4}      /  NACK {"t":"NACK","seq":4,"why":"..."}
#   CMD    {"t":"CMD","cmd":"feed"|"send"|"scare"|"name","value":"..."}       órdenes desde la web

import time
import json

UDP_PORT = 5001
TCP_PORT = 5000
HELLO_EVERY_MS = 1000
PEER_TIMEOUT_MS = 3500


def wifi_connect(ssid, password, timeout_s=20, on_status=None):
    """Conecta en modo STA (igual que en la Sesión 11). Devuelve (wlan, ip) o (wlan, None)."""
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.config(pm=0xa11140)   # desactiva ahorro de energía: menos latencia
    except Exception:
        pass
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if on_status:
                on_status("Conectando a %s..." % ssid)
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
                return wlan, None
            time.sleep_ms(300)
    return wlan, wlan.ifconfig()[0]


def _broadcast_addr(ip, mask):
    a = [int(x) for x in ip.split(".")]
    m = [int(x) for x in mask.split(".")]
    return ".".join(str((a[i] & m[i]) | (255 - m[i])) for i in range(4))


class Link:
    def __init__(self, my_id, get_status, on_fish, on_cmd,
                 mode="wifi", wlan=None, peer_ip=None, uart=None):
        self.my_id = my_id
        self.get_status = get_status      # función -> dict con mi estado (va en HELLO)
        self.on_fish = on_fish            # función(msg) -> True si acepto el pez
        self.on_cmd = on_cmd              # función(msg) -> dict de respuesta
        self.mode = mode
        self.peer = {}                    # último HELLO de la otra pecera
        self.peer_ip = peer_ip
        self.fixed_peer = peer_ip is not None
        self._last_seen = None
        self._last_hello = 0
        self.ip = None
        self.uart = uart
        self._ubuf = b""
        if mode == "wifi":
            self._setup_wifi(wlan)

    # ------------------------------------------------------------------ Wi-Fi
    def _setup_wifi(self, wlan):
        import socket
        self.socket = socket
        ip, mask = wlan.ifconfig()[0], wlan.ifconfig()[1]
        self.ip = ip
        self.bcast = _broadcast_addr(ip, mask)

        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp.setsockopt(socket.SOL_SOCKET, 0x20, 1)   # SO_BROADCAST en lwIP
        except Exception:
            pass
        self.udp.bind(("0.0.0.0", UDP_PORT))
        self.udp.setblocking(False)

        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("0.0.0.0", TCP_PORT))
        self.srv.listen(2)
        self.srv.setblocking(False)

    # ------------------------------------------------------------------ común
    def peer_alive(self):
        if self._last_seen is None:
            return False
        return time.ticks_diff(time.ticks_ms(), self._last_seen) < PEER_TIMEOUT_MS

    def peer_age_ms(self):
        if self._last_seen is None:
            return -1
        return time.ticks_diff(time.ticks_ms(), self._last_seen)

    def _hello(self):
        msg = {"t": "HELLO", "id": self.my_id, "ip": self.ip or "uart"}
        msg.update(self.get_status())
        return msg

    def _got_hello(self, msg, addr_ip=None):
        if msg.get("id") == self.my_id:
            return                      # mi propio broadcast
        self.peer = msg
        self._last_seen = time.ticks_ms()
        if addr_ip and not self.fixed_peer:
            self.peer_ip = addr_ip

    def _dispatch(self, msg):
        """Procesa un mensaje entrante y devuelve la respuesta (o None)."""
        t = msg.get("t")
        if t == "HELLO":
            self._got_hello(msg)
            return None
        if t == "FISH":
            ok, why = self.on_fish(msg)
            if ok:
                return {"t": "ACK", "seq": msg.get("seq")}
            return {"t": "NACK", "seq": msg.get("seq"), "why": why}
        if t == "CMD":
            return self.on_cmd(msg)
        return {"t": "NACK", "why": "tipo desconocido"}

    def poll(self):
        """Llamar seguido desde el bucle principal (no bloquea)."""
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_hello) >= HELLO_EVERY_MS:
            self._last_hello = now
            self._send_hello()
        if self.mode == "wifi":
            self._poll_wifi()
        else:
            self._poll_uart()

    def send(self, msg, timeout_s=1.5):
        """Envía FISH o CMD y espera la respuesta. Devuelve dict o None."""
        if self.mode == "wifi":
            return self._send_tcp(msg, timeout_s)
        return self._send_uart(msg, timeout_s)

    # ------------------------------------------------------------------ Wi-Fi: detalle
    def _send_hello(self):
        data = (json.dumps(self._hello()) + "\n").encode()
        if self.mode == "wifi":
            try:
                if self.fixed_peer:
                    self.udp.sendto(data, (self.peer_ip, UDP_PORT))
                else:
                    self.udp.sendto(data, (self.bcast, UDP_PORT))
            except OSError:
                pass
        else:
            self.uart.write(data)

    def _poll_wifi(self):
        for _ in range(4):                 # UDP: puede haber varios HELLO en cola
            try:
                data, addr = self.udp.recvfrom(1024)
            except OSError:
                break
            try:
                msg = json.loads(data.decode())
                if msg.get("t") == "HELLO":
                    self._got_hello(msg, addr[0])
            except (ValueError, UnicodeError):
                pass
        try:                               # TCP: ¿alguien nos manda el pez o una orden?
            conn, addr = self.srv.accept()
        except OSError:
            return
        try:
            conn.settimeout(2.0)
            line = self._readline(conn)
            if line:
                reply = self._dispatch(json.loads(line.decode()))
                if reply is not None:
                    conn.send((json.dumps(reply) + "\n").encode())
        except (OSError, ValueError) as e:
            print("link: error en conexión entrante:", e)
        finally:
            conn.close()

    def _readline(self, conn, maxlen=2048):
        buf = b""
        while not buf.endswith(b"\n") and len(buf) < maxlen:
            chunk = conn.recv(256)
            if not chunk:
                break
            buf += chunk
        return buf.strip()

    def _send_tcp(self, msg, timeout_s):
        if not self.peer_ip:
            return None
        s = self.socket.socket(self.socket.AF_INET, self.socket.SOCK_STREAM)
        try:
            s.settimeout(timeout_s)
            s.connect((self.peer_ip, TCP_PORT))
            s.send((json.dumps(msg) + "\n").encode())
            line = self._readline(s)
            return json.loads(line.decode()) if line else None
        except (OSError, ValueError) as e:
            print("link: no se pudo enviar:", e)
            return None
        finally:
            s.close()

    # ------------------------------------------------------------------ UART (Plan B)
    def _uart_lines(self):
        n = self.uart.any()
        if n:
            data = self.uart.read(n)
            if data:
                self._ubuf += data
        while b"\n" in self._ubuf:
            line, self._ubuf = self._ubuf.split(b"\n", 1)
            line = line.strip()
            if line:
                yield line

    def _poll_uart(self):
        for line in self._uart_lines():
            try:
                msg = json.loads(line.decode())
            except ValueError:
                continue
            reply = self._dispatch(msg)
            if reply is not None:
                self.uart.write((json.dumps(reply) + "\n").encode())

    def _send_uart(self, msg, timeout_s):
        self.uart.write((json.dumps(msg) + "\n").encode())
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_s * 1000:
            for line in self._uart_lines():
                try:
                    r = json.loads(line.decode())
                except ValueError:
                    continue
                if r.get("t") in ("ACK", "NACK", "OK", "ERR"):
                    return r
                reply = self._dispatch(r)        # HELLO u otro mensaje mientras esperamos
                if reply is not None:
                    self.uart.write((json.dumps(reply) + "\n").encode())
            time.sleep_ms(10)
        return None
