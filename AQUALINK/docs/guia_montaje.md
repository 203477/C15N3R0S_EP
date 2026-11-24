# Guía de montaje, paso a paso

Regla de la Sesión 11: **una prueba a la vez**. Si un paso falla, no avances al siguiente.
Cada paso tiene su programa en la carpeta `pasos/` y dice exactamente qué debes ver.

Las dos peceras son **idénticas**: mismo cableado y mismo código. Solo cambia un archivo de configuración.

Tiempo estimado: 2 a 3 horas la primera vez.

| Paso | Qué se prueba | Programa | Debes ver |
|------|---------------|----------|-----------|
| 0 | MicroPython instalado | — | `>>>` en la consola de Thonny |
| 1 | Pantalla OLED | `paso1_pantalla.py` | Marco, texto y un contador |
| 2 | Botones, Hall, LDR, buzzer, PWM | `paso2_entradas.py` | Lecturas en la consola |
| 3 | Wi-Fi | `paso3_wifi.py` | La IP de cada Pico |
| 4 | Proyecto completo | `main.py` | El pez nadando y el dashboard |
| 5 | Viaje del pez | — | El pez cruza de una pantalla a la otra |

---

## Paso 0 — Preparar las dos Pico

1. Instala **Thonny** (<https://thonny.org>).
2. Descarga el firmware de MicroPython para **Pico 2 W**: <https://micropython.org/download/RPI_PICO2_W/> (archivo `.uf2`).
3. Mantén presionado el botón **BOOTSEL** de la Pico, conecta el cable USB y suelta. Aparece una unidad llamada `RP2350`.
4. Arrastra el `.uf2` a esa unidad. La Pico se reinicia sola.
5. En Thonny: *Ejecutar → Configurar intérprete → MicroPython (Raspberry Pi Pico)*.

✅ **Listo si** en la consola de Thonny aparece `>>>`.

Repite con la segunda Pico. Márcalas con cinta: **A** y **B**.

## Paso 1 — La pantalla OLED

Cablea la OLED (4 cables) siguiendo **[conexiones.md](conexiones.md)**, con el USB desconectado:
VCC a 3V3, GND a GND, SDA a GP4 y SCL a GP5.

1. Sube `common/ssd1306.py` a la Pico (*Archivo → Guardar como… → Raspberry Pi Pico*, con el mismo nombre).
2. Abre `pasos/paso1_pantalla.py` y presiona ▶.

✅ **Listo si** ves un marco, el texto `OLED OK`, un pez `><(((>`, un contador que avanza del 1 al 10
y al final la pantalla sube y baja de brillo.

| Si pasa esto | Haz esto |
|--------------|----------|
| `No encuentro la OLED en el bus I2C` y la lista sale vacía | Revisa los 4 cables. SDA y SCL se confunden con facilidad: pruébalos al revés. |
| La pantalla enciende pero no se ve nada | Puede ser de 128×32. En `config.py` pon `OLED_HEIGHT = 32`, y en el paso 1 cambia `detect(i2c, 128, 64)` por `detect(i2c, 128, 32)`. |
| Se ve pero con "nieve" o se corta | Baja la velocidad: `I2C_FREQ = 100_000` en `config.py`. |

## Paso 2 — Sensores, botones y buzzer

Cablea el resto siguiendo **[conexiones.md](conexiones.md)**. Hazlo con el USB desconectado.

1. Abre `pasos/paso2_entradas.py` y presiona ▶. No hay que cambiar nada: las dos peceras son iguales.
2. Mira la consola.

✅ **Listo si**:
- cada botón imprime su nombre **una sola vez** y suena un bip;
- al acercar el imán al sensor Hall dice `hall(imán): SI`, y al alejarlo `no`;
- al tapar el LDR el número de `luz` baja, dice `(noche)` y el LED se atenúa.

| Si pasa esto | Haz esto |
|--------------|----------|
| El Hall siempre dice `no` | Voltea el imán (solo detecta un polo). Revisa que VCC vaya a **VBUS** (pin 40), no a 3V3. |
| El Hall siempre dice `SI` | La salida está en corto a GND o el sensor está al revés. |
| La luz sube al tapar el LDR | En `config.py` pon `LDR_INVERT = True`. |
| Un botón no responde | Revisa que una pata vaya al GPIO y la **opuesta** a GND. |

## Paso 3 — Wi-Fi

1. Copia `common/secrets_template.py` con el nombre **`secrets.py`** y escribe tu red (2.4 GHz).
   Usa un **hotspot del celular**: las redes de la universidad suelen bloquear la comunicación entre dispositivos.
2. Sube `secrets.py` a **las dos** Pico.
3. Ejecuta `pasos/paso3_wifi.py` en cada una.

✅ **Listo si** ambas imprimen `PASO 3 OK - IP: ...` y las dos IP empiezan igual (por ejemplo `192.168.43.`).

## Paso 4 — Subir el proyecto

Sube a la **raíz** de cada Pico (sin carpetas) estos archivos. Son los mismos en las dos, salvo los dos últimos:

| Archivo | Pico A | Pico B |
|---------|--------|--------|
| `common/fish.py` | ✓ | ✓ |
| `common/tank.py` | ✓ | ✓ |
| `common/link.py` | ✓ | ✓ |
| `common/web.py` | ✓ | ✓ |
| `common/sensors.py` | ✓ | ✓ |
| `common/ssd1306.py` | ✓ | ✓ |
| `common/render_oled.py` | ✓ | ✓ |
| `secrets.py` | ✓ | ✓ |
| `tank/www/index.html` → guárdalo como **`index.html`** | ✓ | — |
| `tank/config_a.py` → guárdalo como **`config.py`** | ✓ | — |
| `tank/config_b.py` → guárdalo como **`config.py`** | — | ✓ |
| `tank/main.py` (**al final**) | ✓ | ✓ |

Sube `main.py` al final: en cuanto existe, la Pico lo ejecuta sola al encender.

> Atajo: con `pip install mpremote`, el comando `./scripts/deploy.sh a` (o `b`) sube todo de una vez.
> En Windows: `.\scripts\deploy.ps1 a`.

Desconecta y vuelve a conectar cada Pico.

✅ **Listo si**:
- las dos pantallas muestran su IP y luego el agua con algas;
- a los 10–15 segundos nace el pez en la pecera A;
- la pecera B dice `el pez esta en la otra`;
- desde el celular (en el mismo hotspot) abres `http://IP_DE_A/` y se ve el dashboard.

| Si pasa esto | Haz esto |
|--------------|----------|
| El dashboard no abre | Escribe `http://` completo (no `https://`). El celular debe estar en la misma red. Apaga la VPN. |
| El dashboard dice `¿B apagada?` | Las Pico no se ven entre sí. En `secrets.py` de A pon `PEER_IP = "IP de B"` y en el de B la IP de A. |
| La pecera A se congela o se reinicia | En `tank/config_a.py` pon `USE_DUAL_CORE = False`. |
| Va lento | Baja `TARGET_FPS` a 10, o sube `I2C_FREQ` a `1_000_000`. |

## Paso 5 — El viaje del pez

1. Pega un **imán en el borde izquierdo** de cada pecera y deja el **sensor Hall en el borde derecho** (por dentro).
2. Junta las peceras: el borde derecho de una contra el borde izquierdo de la otra.
3. En las dos pantallas aparece `<>` arriba a la derecha y una flecha hacia la otra pecera.
4. Presiona **SEND** en la pecera A (o **Enviar** en el dashboard).

✅ **Listo si** el pez nada hasta el borde, desaparece de una pantalla y entra por el borde de la otra.
Suena un tono al salir y otro al llegar.

Con las peceras juntas, el pez también cruza solo cuando llega al borde (5 segundos después de haber llegado).
Separadas, rebota.

### Los dos botones hacen cuatro cosas

| Botón | Pulsación corta | Pulsación larga (1 segundo) |
|-------|-----------------|------------------------------|
| **FEED** (GP2) | Tirar comida | Golpear el vidrio: el pez se asusta |
| **SEND** (GP3) | Enviar el pez a la otra pecera | Pantalla de datos (IP, enlace, luz, envíos) |

## Plan B — sin Wi-Fi

Si el Wi-Fi falla el día de la demo:

1. Une las peceras con 3 cables: **GP0 de A → GP1 de B**, **GP1 de A → GP0 de B**, **GND → GND**.
2. En los dos `config.py` pon `LINK_MODE = "uart"` y vuelve a subirlos.

El pez viaja igual por el cable. Lo único que no funciona en este modo es el dashboard web.

## Subir el proyecto a GitHub

```bash
cd AQUALINK
git init
git add .
git commit -m "AQUALINK: pecera distribuida con dos Pico 2 W"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/AQUALINK.git
git push -u origin main
```

`secrets.py` está en `.gitignore`, así que la contraseña del Wi-Fi no se sube. Compruébalo con `git status`
antes del `push`: no debe aparecer en la lista.
