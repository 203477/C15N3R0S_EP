# Sesión 11: Smart Wi-Fi HMI

## Descripción de la Práctica

Este proyecto implementa una **Interfaz Hombre-Máquina (HMI) web** servida directamente desde una **Raspberry Pi Pico W / Pico 2 W** conectada en **modo STA** a la misma red Wi-Fi que la laptop.

La Pico levanta un **servidor HTTP con sockets TCP** en el puerto 80. Desde el navegador se puede:

- controlar el brillo de un LED con un **slider PWM de 0 a 100 %** (GP15),
- encender/apagar un **segundo LED** con un botón virtual `TOGGLE LED 2` (GP14),
- consultar el estado del sistema mediante una **API JSON**.

Al mismo tiempo, una **OLED SSD1306 por I2C** funciona como HMI local y muestra la IP, el PWM actual, el estado del LED 2 y el número de requests atendidos.

Integra: **Wi-Fi + HTTP + PWM + salida digital + I2C/OLED**.

---

## Estructura del Repositorio

```text
Sesion_11_Smart_WiFi_HMI/
├── main.py               # Servidor HTTP + HMI web + OLED
├── ssd1306.py            # Driver de la OLED 128x64 por I2C
├── secrets_template.py   # Plantilla de credenciales (sin datos reales)
├── .gitignore            # Excluye secrets.py
├── README.md
└── evidence/             # Capturas y fotos de las pruebas
```

> ⚠️ `secrets.py` **no está en el repositorio**: está listado en `.gitignore`. Para ejecutar el proyecto, copia `secrets_template.py`, renómbralo como `secrets.py`, escribe tu SSID y contraseña y guárdalo en la raíz de la Pico.

---

## Hardware y Conexiones

| Componente | Pin Pico | Notas |
|---|---|---|
| LED PWM | GP15 | Con resistencia de 220/330 Ω, brillo variable |
| LED 2 (digital) | GP14 | Con resistencia de 220/330 Ω, ON/OFF |
| OLED SDA | GP4 | I2C(0) |
| OLED SCL | GP5 | I2C(0) |
| OLED VCC | 3V3 | |
| OLED GND | GND | |

**Configuración del bus I2C**

- Periférico: `I2C(0)`
- Frecuencia: **400 kHz** (Fast-mode)
- OLED SSD1306: dirección **0x3C** (60 decimal)

**Configuración del PWM**

- Frecuencia: **1000 Hz**
- Resolución: `duty_u16()` → 0 a 65535

**Archivos en la raíz de la Pico**

```text
/
├── secrets.py
├── ssd1306.py
└── main.py
```

---

## Arquitectura de Red (modo STA)

```text
                 ROUTER / WI-FI (2.4 GHz)
                    /              \
                   /                \
            LAPTOP / PC         PICO W / PICO 2 W
            Chrome               servidor HTTP :80
         http://192.168.x.x/     PWM + LED2 + OLED
```

La laptop **no cambia de red**: sigue teniendo Internet y accede a la Pico por su IP local.

---

## Endpoints de la API

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/` | Dashboard HTML |
| GET | `/api/status` | JSON con el estado actual |
| GET | `/api/pwm?value=N` | Ajusta el PWM a N (0–100) y devuelve JSON. Si N es inválido → **400** |
| GET | `/api/led2/toggle` | Alterna LED 2 (OFF → ON → OFF…) y devuelve JSON |
| GET | `/api/leds?state=on\|off` | **Bonus:** enciende/apaga ambos LEDs |
| GET | `/favicon.ico` | 204 No Content |
| GET | cualquier otra ruta | **404** Not Found |

**Ejemplo de `/api/status`:**

```json
{
  "ip": "192.168.1.75",
  "pwm": 63,
  "led2": 1,
  "requests": 12,
  "temp_c": 27.6,
  "rssi": -55,
  "time": "20:45"
}
```

**Ejemplo de error 400 (`/api/pwm?value=150`):**

```json
{"error": "value debe ser un entero entre 0 y 100"}
```

### Robustez HTTP

- Todas las respuestas incluyen `Content-Length` y `Connection: close`.
- El valor del PWM se valida: solo se aceptan enteros de 0 a 100 (`150`, `-5`, `abc` o vacío → 400).
- Rutas desconocidas → 404.
- Cualquier excepción se imprime en consola y el `while True` continúa: **el servidor no se detiene después de un error**.
- Si la OLED no se detecta o falla, el servidor web sigue funcionando.

---

## Arquitectura de la HMI

### HMI Web (navegador)

1. **IP** de la Pico + indicador de conexión (punto verde = en línea, rojo = sin respuesta).
2. **Slider 0–100 %** para el LED PWM, con el valor numérico en tiempo real.
3. **Botón `TOGGLE LED 2`** con indicador visual ON/OFF.
4. **Botones ALL ON / ALL OFF** (bonus).
5. **Contador de requests**, temperatura interna, RSSI y hora.
6. **Botón REFRESH STATUS**.

### HMI Local (OLED 128x64)

```text
SMART WIFI HMI        <- encabezado invertido
192.168.1.75
PWM: 37%     [███   ] <- barra proporcional
LED2: ON     [■]      <- cuadro relleno = ON
REQ: 15
             20:45    <- hora NTP (bonus)
```

La OLED se actualiza después de cada request y cada 5 s para el reloj.

---

## Preguntas

### 1. ¿Qué significa STA?

**STA (Station)** es el modo en el que la Pico se comporta como un cliente más de una red Wi-Fi existente, igual que un celular o una laptop. El router le asigna una IP local (por ejemplo `192.168.1.75`). Lo contrario es el modo **AP (Access Point)**, donde la Pico crea su propia red; eso obligaría a la laptop a desconectarse de su Wi-Fi normal y perder Internet. Con STA, la laptop y la Pico conviven en la misma red local.

### 2. ¿Qué hacen `bind()`, `listen()` y `accept()`?

- **`bind(("0.0.0.0", 80))`**: asocia el socket a una dirección IP y un puerto. `0.0.0.0` significa "escuchar en todas las interfaces" y el puerto 80 es el estándar de HTTP.
- **`listen(2)`**: convierte el socket en un socket servidor que espera conexiones; el número indica cuántas conexiones pendientes puede mantener en cola.
- **`accept()`**: espera a que un cliente (el navegador) se conecte y devuelve un **socket nuevo** para hablar con ese cliente, junto con su dirección. Con `settimeout(1)`, si nadie se conecta en 1 s lanza `OSError`, lo que permite al programa seguir vivo, imprimir `Servidor vivo` y refrescar la OLED.

### 3. ¿Cómo se transforma 0–100 % a `duty_u16()`?

`duty_u16()` recibe un valor de 16 bits (0 a 65535). Se hace una regla de tres:

$$duty = \frac{porcentaje \times 65535}{100}$$

```python
percent = max(0, min(100, int(percent)))
duty = int(percent * 65535 / 100)
led_pwm.duty_u16(duty)
```

| % | duty_u16 |
|---|---|
| 0 | 0 |
| 25 | 16383 |
| 37 | 24247 |
| 50 | 32767 |
| 75 | 49151 |
| 100 | 65535 |

### 4. ¿Qué hace el slider HTML?

`<input type="range" min="0" max="100" step="1">` permite elegir **cualquier entero entre 0 y 100**. Usa dos eventos:

- **`oninput`**: mientras se arrastra, solo actualiza el número en pantalla (no envía nada a la Pico).
- **`onchange`**: al soltarlo, envía `GET /api/pwm?value=N` a la Pico.

Así se evita mandar decenas de requests por segundo mientras se mueve el control.

### 5. ¿Por qué se usa `fetch()`?

`fetch()` permite que el JavaScript haga peticiones HTTP **en segundo plano sin recargar la página**. El navegador llama a `/api/pwm`, `/api/led2/toggle` o `/api/status`, recibe el JSON y actualiza solo los elementos necesarios (valor del PWM, estado del LED 2, contador). Esto hace la interfaz más rápida, reduce los datos transferidos y la Pico no tiene que generar todo el HTML en cada clic. Además, si `fetch()` falla, el indicador de conexión se pone en rojo.

### 6. ¿Qué diferencia existe entre HTML y JSON?

| HTML | JSON |
|---|---|
| Lenguaje de marcado para **presentar** información a una persona | Formato de **datos** para que lo lea un programa |
| Incluye estructura, estilos y scripts | Solo pares clave–valor |
| `Content-Type: text/html` | `Content-Type: application/json` |
| Lo entrega `/` | Lo entregan las rutas `/api/...` |

El HTML se carga una sola vez (la "cara" del sistema) y el JSON se pide muchas veces para actualizar los datos.

### 7. ¿Cómo se integra I2C/OLED con el servidor web?

Ambos comparten las mismas **variables de estado** (`pwm_percent`, `led2_state`, `request_count`). Cada vez que llega un request:

1. el router modifica el estado (`set_pwm()` o `toggle_led2()`),
2. se envía la respuesta HTTP al navegador,
3. se llama a `show_oled(ip)`, que redibuja la pantalla por I2C (GP4/GP5).

Así la HMI local (OLED) y la HMI web muestran siempre la misma información. La función `show_oled()` está protegida con `try/except`, de modo que un fallo del bus I2C no detiene el servidor.

---

## Tabla de Pruebas

| ID | Acción | Resultado esperado | Evidencia | Estado |
|---|---|---|---|---|
| P-01: WIFI | Ejecutar `main.py` | Thonny imprime `Wi-Fi conectado` e IP local | `wifi_ip.png` | PASS |
| P-02: DASHBOARD | Abrir `http://IP/` | Dashboard visible con slider, botones y contador | `dashboard.png` | PASS |
| P-03: SLIDER 0 | Mover slider a 0 % | LED PWM apagado | — | PASS |
| P-04: SLIDER 37 | Mover slider a 37 % | Brillo intermedio, duty = 24247 | `slider_37.png` | PASS |
| P-05: SLIDER 100 | Mover slider a 100 % | Brillo máximo, duty = 65535 | `slider_100.png` | PASS |
| P-06: TOGGLE | Clic en `TOGGLE LED 2` | GP14 cambia OFF → ON → OFF | `led2_on.png` | PASS |
| P-07: OLED | Observar pantalla | OLED refleja IP, PWM, LED2 y REQ | `oled_status.jpg` | PASS |
| P-08: API | Abrir `/api/status` | JSON con `ip`, `pwm`, `led2`, `requests` | `api_status.png` | PASS |
| P-09: ERROR 400 | Abrir `/api/pwm?value=150` | `400 Bad Request` + JSON de error | `error_400.png` | PASS |
| P-10: ERROR 404 | Abrir `/ruta-que-no-existe` | `404 Not Found` | `error_404.png` | PASS |
| P-11: ROBUSTEZ | Después de P-09 y P-10 usar el slider | El servidor sigue respondiendo | — | PASS |

---

## Evidencias

### Wi-Fi conectado + IP
![Wi-Fi IP](evidence/wifi_ip.png)

### Dashboard
![Dashboard](evidence/dashboard.png)

### Slider en 37 %
![Slider 37](evidence/slider_37.png)

### Slider en 100 %
![Slider 100](evidence/slider_100.png)

### LED 2 encendido
![LED2 ON](evidence/led2_on.png)

### OLED mostrando el estado
![OLED](evidence/oled_status.jpg)

### API `/api/status`
![API status](evidence/api_status.png)

### Error 400
![Error 400](evidence/error_400.png)

### Error 404
![Error 404](evidence/error_404.png)

---

## Bonus Implementados

- ✅ **Indicador visual de conexión** en la página (verde/rojo), consultando `/api/status` cada 10 s.
- ✅ **Endpoint para ambos LEDs:** `/api/leds?state=on` y `/api/leds?state=off`.
- ✅ **NTP y hora en la OLED** (UTC-6). Si NTP falla, se muestra `--:--` y el resto sigue funcionando.
- ✅ **ADC real en `/api/status`:** temperatura interna del microcontrolador (`ADC(4)`) en el campo `temp_c`, además del RSSI del Wi-Fi.

---

## Seguridad

- Las credenciales Wi-Fi viven en `secrets.py`, que **nunca** se sube a GitHub (está en `.gitignore`).
- En el repositorio solo está `secrets_template.py` con valores de ejemplo.

---

## Conclusiones

Con la Pico W en modo STA fue posible crear un servidor HTTP accesible desde cualquier navegador de la red local sin que la laptop perdiera Internet. Usando sockets (`bind`, `listen`, `accept`) y respuestas HTTP con `Content-Length` y `Connection: close`, el navegador carga correctamente y el servidor atiende un request tras otro sin detenerse, incluso ante rutas o valores inválidos (404/400).

Separar la interfaz (HTML) de los datos (JSON) y usar `fetch()` permitió controlar el PWM con un slider de 0–100 % y el segundo LED sin recargar la página. Finalmente, la OLED por I2C se integró como HMI local compartiendo el mismo estado del servidor, lo que muestra cómo se combinan en un solo sistema embebido los temas del curso: GPIO, PWM, ADC, I2C y Wi-Fi/HTTP.
