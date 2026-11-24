# web.py — Servidor HTTP mínimo y no bloqueante (como en la Sesión 11)
# - Responde con Content-Length y Connection: close
# - Rutas desconocidas -> 404, parámetros inválidos -> 400, el servidor nunca se detiene

import socket
import json

REASONS = {200: "OK", 400: "Bad Request", 404: "Not Found",
           409: "Conflict", 500: "Internal Server Error", 503: "Service Unavailable"}


def json_resp(obj, code=200):
    return code, "application/json", json.dumps(obj)


def text_resp(text, code=200):
    return code, "text/plain; charset=utf-8", text


def _unquote(s):
    s = s.replace("+", " ")
    out = ""
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            try:
                out += chr(int(s[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        out += s[i]
        i += 1
    return out


def parse_query(qs):
    q = {}
    if not qs:
        return q
    for part in qs.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            q[_unquote(k)] = _unquote(v)
        elif part:
            q[_unquote(part)] = ""
    return q


class WebServer:
    def __init__(self, routes, port=80, files=None):
        """routes: {"/ruta": funcion(query_dict) -> (codigo, content_type, cuerpo)}
        files:  {"/": ("index.html", "text/html")} archivos estáticos"""
        self.routes = routes
        self.files = files or {}
        self.requests = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(3)
        self.sock.setblocking(False)

    def poll(self):
        try:
            conn, addr = self.sock.accept()
        except OSError:
            return False
        try:
            conn.settimeout(2.0)
            req = conn.recv(1024)
            if not req:
                return True
            first = req.split(b"\r\n", 1)[0].decode()
            parts = first.split(" ")
            if len(parts) < 2:
                self._send(conn, *text_resp("Bad Request", 400))
                return True
            target = parts[1]
            path, _, qs = target.partition("?")
            self.requests += 1
            if path in self.files:
                fname, ctype = self.files[path]
                self._send_file(conn, fname, ctype)
            elif path in self.routes:
                try:
                    code, ctype, body = self.routes[path](parse_query(qs))
                except Exception as e:          # un error en una ruta no tumba el servidor
                    print("web: error en", path, e)
                    code, ctype, body = json_resp({"error": str(e)}, 500)
                self._send(conn, code, ctype, body)
            elif path == "/favicon.ico":
                self._send(conn, 404, "text/plain", "")
            else:
                self._send(conn, *json_resp({"error": "not found", "path": path}, 404))
        except OSError as e:
            print("web: conexión fallida:", e)
        finally:
            conn.close()
        return True

    def _send(self, conn, code, ctype, body):
        if isinstance(body, str):
            body = body.encode()
        head = ("HTTP/1.1 %d %s\r\nContent-Type: %s\r\nContent-Length: %d\r\n"
                "Access-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n"
                % (code, REASONS.get(code, "OK"), ctype, len(body)))
        conn.sendall(head.encode())
        if body:
            conn.sendall(body)

    def _send_file(self, conn, fname, ctype):
        try:
            with open(fname, "rb") as fp:
                body = fp.read()
        except OSError:
            self._send(conn, *text_resp("Falta el archivo " + fname, 500))
            return
        self._send(conn, 200, ctype, body)
