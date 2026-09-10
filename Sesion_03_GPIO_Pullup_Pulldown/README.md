# Sesión 03 — GPIO, pull-up/pull-down y debounce

### Contenido

| Carpeta / Archivo | Contenido | Descripción |
| --- | --- | --- |
| `micropython/01_button_read.py` | MicroPython (DO 01: Lectura de botón) | Lectura digital con resistencia pull-up interna |
| `micropython/02_button_debounce.py` | MicroPython (DO 02: Debounce) | Algoritmo antirrebote y retención *wait-for-release* |
| `micropython/03_semaforo_peatonal.py` | MicroPython (Challenge 03: Semáforo) | Control semafórico interactivo con máquina de estados finitos |
| `cpp/button_read/button_read.c` | C/C++ Pico SDK (DO 01: Lectura de botón) | Configuración y lectura de GPIO en bajo nivel |
| `cpp/traffic_light/traffic_light.c` | C/C++ Pico SDK (Challenge 03: Semáforo) | Implementación equivalente en C con invariante de seguridad |
| `wokwi/diagram.json` | Simulación Wokwi | Esquemático virtual para validación previa en wokwi.com |
| `evidence/` | Capturas y multimedia | Registros visuales en Wokwi, fotos y video del hardware |

---

### 📝 Objetivo de la Práctica

Comprender y aplicar la interfaz GPIO como el límite funcional entre el software y el mundo físico (Entrada $\rightarrow$ Decisión $\rightarrow$ Salida) sobre la Raspberry Pi Pico. Se abordan problemas eléctricos inherentes como el estado de alta impedancia (*pin flotante*) y el rebote mecánico (*contact bounce*), implementando un semáforo peatonal reactivo mediante una máquina de estados finitos que garantice el cumplimiento estricto de la invariante de seguridad (autos y peatones jamás comparten la señal verde).

---

### 📦 Materiales Utilizados

* 1x Raspberry Pi Pico 2 W (RP2350) o Raspberry Pi Pico (RP2040)
* 1x Pulsador de cuatro terminales (*pushbutton*)
* 2x Diodos LED rojos (Auto y Peatón)
* 1x Diodo LED amarillo (Auto)
* 2x Diodos LED verdes (Auto y Peatón)
* 5x Resistores de $330\,\Omega$ (limitación de corriente para LEDs)
* 1x Protoboard y jumpers de conexión
* 1x Cable Micro-USB compatible con líneas de datos
* Software: VS Code (Pico SDK / extensión MicroPico) o Thonny, simulador Wokwi

---

### 🔌 Diagrama y Conexión del Circuito

El circuito se construyó por fases modulares:

* **Etapa A (Entrada):** Conexión directa del pulsador entre **GP16** y **GND**, aprovechando la resistencia pull-up interna del microcontrolador.
* **Etapa B (Salidas):** Cinco LEDs en configuración cátodo común conectados a tierra, con resistencias individuales de $330\,\Omega$ en el ánodo.

| Elemento | Pin GPIO | Componente | Conexión física |
| --- | --- | --- | --- |
| **Auto: Rojo** | GP15 | LED Rojo | GPIO $\rightarrow$ Resistor $330\,\Omega$ $\rightarrow$ Ánodo LED / Cátodo $\rightarrow$ GND |
| **Auto: Amarillo** | GP14 | LED Amarillo | GPIO $\rightarrow$ Resistor $330\,\Omega$ $\rightarrow$ Ánodo LED / Cátodo $\rightarrow$ GND |
| **Auto: Verde** | GP13 | LED Verde | GPIO $\rightarrow$ Resistor $330\,\Omega$ $\rightarrow$ Ánodo LED / Cátodo $\rightarrow$ GND |
| **Peatón: Rojo** | GP12 | LED Rojo | GPIO $\rightarrow$ Resistor $330\,\Omega$ $\rightarrow$ Ánodo LED / Cátodo $\rightarrow$ GND |
| **Peatón: Verde** | GP11 | LED Verde | GPIO $\rightarrow$ Resistor $330\,\Omega$ $\rightarrow$ Ánodo LED / Cátodo $\rightarrow$ GND |
| **Botón Peatón** | GP16 | Pulsador | GP16 $\rightarrow$ Terminal 1 Pulsador / Terminal 2 $\rightarrow$ GND |

> ⚠️ **Advertencia de seguridad eléctrica:** Los pines GPIO del microcontrolador operan bajo lógica de $3.3\,\text{V}$. Conectar fuentes directas de $5\,\text{V}$ daña de forma irreversible los puertos de entrada.

---

### ⚡ Fundamento: El Pin Flotante, Pull-up y Debounce

1. **Estado Flotante (*Floating Pin*):**
Una entrada digital sin referencia fija no está en $0\,\text{V}$ ni en $3.3\,\text{V}$; se comporta como una antena de alta impedancia captando ruido electromagnético. Su valor lógico es indeterminado.
2. **Referencia Eléctrica:**
* **Pull-up interno:** Se activa una resistencia interna conectada a $3.3\,\text{V}$. Cuando el botón está en reposo (abierto), el pin lee un nivel alto (`1`). Al presionarlo, el camino de menor resistencia drena a GND y la lectura cae a nivel bajo (`0`).
* **Pull-down:** Invierte la lógica (reposo en `0`, activo en `1`), pero requiere conectar una resistencia externa a tierra o soporte en silicio.


3. **Rebote Mecánico (*Bounce*):**
Las laminillas metálicas del botón vibran durante unos milisegundos antes de asentarse, produciendo múltiples transiciones $0 \leftrightarrow 1$. Por software se aplica una ventana de retardo ($30\,\text{ms}$) tras el primer flanco para confirmar el valor real, seguida de una condición *wait-for-release* (`while not btn.value(): pass`) que asegura la regla: **1 pulsación física = 1 sola petición aceptada**.

---

### 🐍 MicroPython (DO 01, DO 02 y Challenge 03)

📄 **Códigos fuente:**

* `micropython/01_button_read.py`
* `micropython/02_button_debounce.py`
* `micropython/03_semaforo_peatonal.py`

**Explicación de la implementación:**

* **DO 01:** Inicialización con `Pin(16, Pin.IN, Pin.PULL_UP)`. En bucle constante se confirma que la consola serial muestra `1` cuando el pulsador está libre y `0` cuando se mantiene presionado.
* **DO 02:** Detección de flanco de bajada con retardo de estabilización (`sleep_ms(30)`) y bucle de liberación para evitar que sostener el botón encadene ejecuciones fantasma.
* **Challenge 03 (FSM del Semáforo):** Se estructuró la secuencia mediante estados y funciones de abstracción de alto nivel (`cars_go()`, `cars_prepare_to_stop()`, `pedestrians_go()`, `pedestrians_hurry()`):
* **S0 (Reposo):** Vehículos en Verde, Peatón en Rojo. Estado pasivo a la espera del botón.
* **S1 (Transición):** Vehículos en Amarillo, Peatón en Rojo ($1500\,\text{ms}$).
* **S2 (Cruce):** Vehículos en Rojo, Peatón en Verde ($4000\,\text{ms}$).
* **S3 (Desalojo):** Vehículos en Rojo, Peatón en Verde parpadeante ($4 \times 300\,\text{ms}$).
* **Invariante de Seguridad:** La función `set_lights()` comprueba que `car_green && ped_green` nunca se activen a la vez; si esto se solicita, la actualización se bloquea y se reporta el incidente por UART.



---

### ⚙️ C/C++ (Pico SDK - DO 01 y Challenge 03)

📄 **Códigos fuente:**

* `cpp/button_read/button_read.c`
* `cpp/traffic_light/traffic_light.c`

**Explicación de la implementación en C/C++:**

* Se empleó la API del Pico SDK para mapear los registros de entrada/salida: `gpio_init()`, `gpio_set_dir(pin, GPIO_IN/OUT)` y `gpio_pull_up(pin)`.
* La lectura directa mediante `gpio_get(BUTTON)` reproduce de forma determinista la lógica de polaridad invertida evaluada previamente en MicroPython.
* Se estructuró la misma FSM en `traffic_light.c` manteniendo constantes parametrizables (`TRANSITION_MS`, `CROSSING_MS`, `RECOVERY_MS`) para ajustar tiempos de ciclo sin alterar el algoritmo de seguridad.

| Acción funcional | MicroPython | C / C++ (Pico SDK) |
| --- | --- | --- |
| **Configurar entrada con Pull-up** | `Pin(16, Pin.IN, Pin.PULL_UP)` | `gpio_init(16); gpio_set_dir(16, GPIO_IN); gpio_pull_up(16);` |
| **Lectura de estado digital** | `btn.value()` | `gpio_get(16)` |
| **Configurar terminal de salida** | `Pin(15, Pin.OUT)` | `gpio_init(15); gpio_set_dir(15, GPIO_OUT);` |
| **Escritura digital (alto/bajo)** | `led.value(1)` | `gpio_put(15, 1)` |
| **Retardo temporal bloqueante** | `sleep_ms(30)` | `sleep_ms(30)` |

---

### 🧪 Plan de Validación y Pruebas

| Caso de prueba | Condición de entrada | Comportamiento esperado | Simulación (Wokwi) | Placa física |
| --- | --- | --- | --- | --- |
| **DO 01: Lectura reposo** | Botón abierto | Lectura lógica `1` estable | PASS | PASS |
| **DO 01: Lectura presionado** | Botón cerrado a GND | Lectura lógica `0` estable | PASS | PASS |
| **DO 02: Pulsación corta** | Clic rápido (<100 ms) | Emite un solo evento `CLICK válido` | PASS | PASS |
| **DO 02: Pulsación larga** | Botón presionado por 2 s | Emite 1 solo evento; no repite hasta soltar | PASS | PASS |
| **DO 02: Pulsación repetitiva** | Clics rápidos consecutivos | Sin falsos disparos ni bloqueos de lectura | PASS | PASS |
| **CHALLENGE: Inicialización** | Arranque en frío | Estado S0: Auto Verde / Peatón Rojo | PASS | PASS |
| **CHALLENGE: Ciclo completo** | Pulsación confirmada | Secuencia ordenada S0 $\rightarrow$ S1 $\rightarrow$ S2 $\rightarrow$ S3 $\rightarrow$ S0 | PASS | PASS |
| **CHALLENGE: Seguridad** | Inspección en cruce | Auto Verde y Peatón Verde jamás coinciden | PASS | PASS |
| **C/C++: Transferencia** | Binario C compilado | Misma lógica booleana y temporal que en Python | PASS | PASS |

---

### 🎥 Evidencia

* **Wokwi:** (capturas `evidence/wokwi_button.png` y `evidence/wokwi_semaforo.png`).
* **Hardware físico:** Fotografías del protoboard en operación en la carpeta `evidence/` (`hardware_photo.jpg`, `S0.jpg`, `S1.jpg`, `S2.jpg` y secuencias de parpadeo `S3_1.jpg` a `S3_4.jpg`).
* **Video demostrativo:** `evidence/RE03_video.mp4` que muestra la ejecución del ciclo autónomo en la Raspberry Pi Pico.

---

### 🤔 Conclusiones o Retos Superados

* **Entradas flotantes y acondicionamiento:** Dejar un pin en alta impedancia sin conexión definida causa fluctuaciones impredecibles en la lectura digital. El uso de la resistencia pull-up interna soluciona este comportamiento al mantener el pin acoplado a $3.3\,\text{V}$ en estado de reposo.
* **Portabilidad y compilación cruzada:** El hardware de prueba físico (Raspberry Pi Pico 2 W con chip RP2350) requiere binarios compilados específicamente para su arquitectura (`pico2_w`). Para validar el código C en Wokwi (emulador de RP2040), se mantuvo el código fuente idéntico pero ajustando el objetivo de compilación correspondiente a cada entorno.
