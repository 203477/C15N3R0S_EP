# Protocolo de comunicación entre peceras

Todo viaja como **JSON en una línea terminada en `\n`**. El mismo formato sirve por Wi-Fi y por UART (Plan B).

## 1. Descubrimiento — UDP puerto 5001 (cada 1 s)

Cada pecera manda un `HELLO` por broadcast a su subred (o a `PEER_IP` si se configuró en `secrets.py`):

```json
{"t":"HELLO","id":"A","ip":"192.168.43.20","hall":1,"fish":1,"gen":3,"name":"Nemo",
 "hunger":35,"x":0.61,"y":0.42,"night":0,"light":78,"temp_c":27.4,"link":1,"req":12}
```

- Si no llega un `HELLO` en **3.5 s**, la otra pecera se considera apagada y no hay enlace.
- `hall` le dice a la otra pecera si mi sensor ve su imán (para saber de qué lado está).

## 2. Transferencia del pez — TCP puerto 5000

```
Emisor  ->  {"t":"FISH","seq":4,"enter":"left","fish":{"name":"Nemo","x":0.92,"y":0.42,
             "vx":0.12,"vy":-0.01,"hunger":35,"age_s":812,"gen":3,"color":[255,95,162]}}
Receptor -> {"t":"ACK","seq":4}
         o  {"t":"NACK","seq":4,"why":"ya tengo un pez"}
```

**Reglas para que el pez nunca se pierda ni se duplique**

1. El pez solo sale si: está tocando el borde que da hacia la otra pecera **y** hay enlace (Hall + HELLO reciente).
2. Mientras espera respuesta, el pez se queda **quieto en el borde** (no se borra todavía).
3. Solo con `ACK` y el mismo `seq` el emisor lo borra. Sin respuesta en 1.5 s → el pez **rebota y se queda**.
4. `seq = gen + 1`. El receptor ignora un `seq` que ya recibió (contesta `ACK` sin crear otro pez).
5. El estado se guarda en `fish.json`. Si tras un reinicio **ambas** dicen tener pez, se queda el de mayor `gen`.
6. Tras llegar, el pez explora 5 s antes de poder regresar (evita que rebote de inmediato).

## 3. Órdenes desde la web — TCP puerto 5000

La pecera A sirve el dashboard. Si el pez está en B, A reenvía la orden:

```
A -> B   {"t":"CMD","cmd":"feed"}            ("feed" | "send" | "scare" | "name")
B -> A   {"t":"OK"}   o   {"t":"ERR","why":"el pez no esta aqui"}
```

## 4. API HTTP (pecera A, puerto 80)

| Ruta | Respuesta | Descripción |
|------|-----------|-------------|
| `/` | 200 text/html | Dashboard |
| `/api/status` | 200 JSON | Estado de A, de B (según su HELLO) y del pez |
| `/api/feed` | 200 / 409 / 503 | Alimenta donde esté el pez |
| `/api/send` | 200 / 409 | Envía el pez a la otra pecera (409 si no están juntas) |
| `/api/scare` | 200 / 409 | Golpe al vidrio |
| `/api/name?value=Nemo` | 200 / 400 | Cambia el nombre (1–10 letras o números) |
| `/api/light?value=N` | 200 / 400 | Prueba del PWM de la retroiluminación, N = 0–100, por 10 s |
| cualquier otra | 404 | `{"error":"not found"}` — el servidor sigue funcionando |

Todas las respuestas llevan `Content-Length` y `Connection: close` (como en la Sesión 11).
La pecera B también responde `/api/status` (solo su propio estado).
