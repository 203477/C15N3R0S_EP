# Sesión 09 — Protocolo Serie UART y Arquitectura Loopback
**Reto 09 — UART Command Center**  
---

### 1. Objetivo y qué es UART
El propósito de la práctica es implementar un centro de control y monitoreo de periféricos por línea de comandos utilizando el periférico de hardware **UART0** de la Raspberry Pi Pico. El operador introduce tramas desde la consola USB en Thonny, la placa transmite la trama por su pin emisor físico (**GP0/TX**), la señal viaja por un puente de hardware (jumper) hacia su propio pin receptor (**GP1/RX**), la procesa un intérprete/parser de tramas y conmuta actuadores (**LED1 en GP13** y **LED2 en GP14**), devolviendo un acuse de recibo estructurado (`ACK`, `STATUS` o `ERR`) a la consola.

#### UART, TX/RX, Baud Rate y Formato 8N1
* **UART (Universal Asynchronous Receiver-Transmitter):** Protocolo asíncrono punto a punto que transmite datos de forma secuencial (bit a bit) a través de dos líneas independientes sin compartir una señal de reloj común: **TX** (transmisión) y **RX** (recepción).
* **Cruce de líneas (TX $\rightarrow$ RX):** La salida del emisor siempre debe ingresar a la entrada del receptor correspondiente. En esta práctica se implementó un **loopback físico**: un único cable puente directo entre GP0 y GP1 para cerrar el lazo sobre el mismo controlador.
* **Baud Rate (9600 bps):** Determina la velocidad de modulación (tiempo por bit: $T_{\text{bit}} \approx \frac{1}{9600} \approx 104.16\,\mu\text{s}$). Al no existir línea de reloj, ambos extremos deben estar sincronizados de forma rígida a la misma tasa de baudios para muestrear la línea en el instante central de cada bit.
* **Trama 8N1:** Configuración estándar de la capa de enlace asíncrona:
  * **1 bit de arranque (Start Bit):** Transición a nivel bajo (LOW) para sincronizar el temporizador receptor.
  * **8 bits de datos:** Carga útil transmitida desde el bit menos significativo (LSB).
  * **Sin paridad (No parity):** Sin bit adicional de comprobación de paridad.
  * **1 bit de parada (Stop Bit):** Retorno a nivel alto (HIGH) para delimitar el byte y permitir el reposo de la línea.

---

### 2. Arquitectura de Comunicación: USB/REPL vs UART y Loopback Físico
La Raspberry Pi Pico utiliza una arquitectura de doble canal en esta práctica:
1. **USB/REPL (Consola de Usuario):** El conector micro-USB implementa un puerto serie virtual (CDC) que transporta el flujo estándar de entrada y salida (`input()`, `print()`) administrado por MicroPython y renderizado en Thonny.
2. **UART0 de Hardware (Bus de Control):** El periférico interno independiente `UART(0)` opera sobre los pines de silicio GP0 y GP1.

```text
Consola Thonny (USB) → input() → uart.write() [GP0 TX] → JUMPER FÍSICO → uart.read() [GP1 RX] → handle_frame() → LEDs (GP13/GP14) → print() → Consola Thonny
```

| Canal | Medio Físico | Función en la Práctica |
| --- | --- | --- |
| **USB CDC** | Conector micro-USB | Interfaz hombre-máquina (HMI) e inyección manual de comandos en Thonny |
| **UART0** | Pines GPIO GP0 y GP1 | Enlace serial asíncrono real bajo prueba |
| **Loopback** | Jumper GP0 $\leftrightarrow$ GP1 | Permite validar transmisión y recepción física sin usar un conversor USB-UART externo |

El **loopback físico** permite diagnosticar el transmisor, receptor y buffer interno de la Pico utilizando su propio hardware: si el cable jumper se desconecta, `uart_roundtrip()` agota su tiempo límite de espera (`timeout_ms=1000`) y reporta `UART RX: SIN DATOS. Checar conexion`.

#### Asignación de Pines

| Elemento | Pin GPIO | Modo | Función |
| --- | --- | --- | --- |
| **UART0 TX** | GP0 | Salida serie | Transmisión asíncrona de tramas |
| **UART0 RX** | GP1 | Entrada serie | Recepción asíncrona de tramas |
| **LED 1** | GP13 | Salida digital | Actuador 1 |
| **LED 2** | GP14 | Salida digital | Actuador 2 |
| **GND** | GND | Referencia | Plano común de tierra |

---

### 3. Protocolo de Comandos y Máquina de Validación

El parser procesa comandos estructurados delimitados por comas y finalizados con salto de línea (`\n`). Todas las entradas se convierten a mayúsculas con `.upper()`.

| Nivel | Comando Enviado | Condición / Validación | Respuesta Exitosa | Respuesta Error |
| --- | --- | --- | --- | --- |
| **1** | `PING` | Comprobación de enlace | `ACK,PONG` | — |
| **1** | `GET,STATUS` | Consulta de estados | `STATUS,LED1,<0|1>,LED2,<0|1>` | — |
| **1** | `SET,<LED1|LED2>,<0|1>` | Escritura individual | `ACK,<LED>,<0|1>` | `ERR,BAD_SET_FRAME` |
| **2** | `SET,ALL,<0|1>` | Escritura concurrente | `ACK,ALL,<0|1>` | `ERR,BAD_SET_FRAME` |
| **2** | Campos o datos inválidos | Número de campos $\neq 3$, actuador inexistente o valor distinto a `0/1` | — | `ERR,BAD_SET_FRAME` |
| **2** | Comando desconocido | Cabecera distinta a `PING`, `GET` o `SET` | — | `ERR,UNKNOWN_FRAME` |

---

### 4. Mecanismo de Recepción y Control de Buffer

El intercambio de datos seriales requiere gestionar el buffer FIFO del microcontrolador:

* **Limpieza de buffer (`clear_rx`):** Antes de enviar una nueva trama con `uart.write()`, se purga cualquier byte remanente o ruido parásito en el buffer circular con `uart.read()`.
* **Recepción delimitada sin bloqueo permanente (`receive_complete_line`):** Mediante `ticks_ms()` y `ticks_diff()`, el microcontrolador inspecciona la línea durante una ventana máxima de 1000 ms. Lee byte a byte acumulando en un `bytearray` hasta detectar el delimitador `\n`, devolviendo la cadena decodificada libre de retornos de carro (`\r`). Si el jumper no está colocado o la línea se interrumpe, la rutina no se cuelga y retorna `None` al alcanzar el timeout.

---

### 5. Resultados de la Tabla de Pruebas

| # | Comando Inyectado | UART RX | Respuesta Esperada | Resultado Observado | Estado LED1 | Estado LED2 | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **1** | `PING` | `PING` | `ACK,PONG` | `ACK,PONG` | Sin cambio | Sin cambio | ✅ |
| **2** | `SET,LED1,1` | `SET,LED1,1` | `ACK,LED1,1` | `ACK,LED1,1` | ON | Sin cambio | ✅ |
| **3** | `SET,LED1,0` | `SET,LED1,0` | `ACK,LED1,0` | `ACK,LED1,0` | OFF | Sin cambio | ✅ |
| **4** | `SET,LED2,1` | `SET,LED2,1` | `ACK,LED2,1` | `ACK,LED2,1` | Sin cambio | ON | ✅ |
| **5** | `SET,ALL,1` | `SET,ALL,1` | `ACK,ALL,1` | `ACK,ALL,1` | ON | ON | ✅ |
| **6** | `GET,STATUS` | `GET,STATUS` | `STATUS,LED1,1,LED2,1` | `STATUS,LED1,1,LED2,1` | ON | ON | ✅ |
| **7** | `SET,LED3,1` | `SET,LED3,1` | `ERR,BAD_SET_FRAME` | `ERR,BAD_SET_FRAME` | ON | ON | ✅ |
| **8** | `SET,LED1,9` | `SET,LED1,9` | `ERR,BAD_SET_FRAME` | `ERR,BAD_SET_FRAME` | ON | ON | ✅ |
| **9** | `HOLA_MUNDO` | `HOLA_MUNDO` | `ERR,UNKNOWN_FRAME` | `ERR,UNKNOWN_FRAME` | ON | ON | ✅ |
| **10** | `SET,ALL,0` | `SET,ALL,0` | `ACK,ALL,0` | `ACK,ALL,0` | OFF | OFF | ✅ |

---

### 6. Preguntas de Análisis

1. **¿Por qué la comunicación UART requiere la misma velocidad (baud rate) en ambos extremos y qué ocurriría si fuera distinta?**
Al ser asíncrono, no hay una línea de reloj (SCLK) compartida que indique cuándo leer. El receptor calcula el momento de muestreo de cada bit dividiendo el tiempo según el baud rate acordado. Si las velocidades difieren, el receptor muestreará fuera de fase (drift temporal), leyendo ceros y unos en instantes erróneos y provocando fallos de enmarcado (*framing error*) o decodificando caracteres basura.
2. **¿Cuál es la función del jumper físico entre GP0 y GP1 y qué demuestra?**
Cierra el lazo eléctrico entre el módulo transmisor y el módulo receptor del periférico UART0 (*hardware loopback*). Demuestra que la señal lógica de voltaje generada por el periférico de silicio viaja físicamente fuera del chip por la pista del pin TX y reingresa íntegra por el pin RX, validando la integridad del hardware sin requerir un analizador lógico ni un segundo microcontrolador.
3. **¿Por qué se limpia el buffer (`clear_rx`) antes de transmitir?**
Durante el arranque o ante ruidos transitorios en las líneas de cobre pueden alojarse bytes residuales en la memoria FIFO del UART. Si no se purga antes de enviar, la lectura posterior tomará datos viejos desfasando la trama actual de su respuesta correspondiente.
4. **¿Por qué es necesario un timeout en la función de recepción?**
Si el cable jumper se desconecta o la señal sufre un falso contacto, `uart.any()` reportará 0 permanentemente. Un bucle `while` sin límite de tiempo congelaría por completo la ejecución del programa. El timeout permite detectar la falla de hardware y mantener el sistema interactivo.
5. **Diferencia entre la consola de Thonny y el bus UART0:**
Thonny interactúa mediante un canal USB virtual (emulación serie USB CDC) gestionado por el núcleo de MicroPython para depuración (REPL). El UART0 es un módulo de hardware dedicado con registros, temporizadores y pines físicos de voltaje (3.3V TTL).

---

### 7. Problemas Encontrados y Soluciones

* **Falso eco y retornos de carro residuales:** Al recibir cadenas desde Thonny o transmitirlas por UART, la presencia de caracteres `\r` (CR) provocaba que el método `.split(",")` no comparara adecuadamente los valores finales de las tramas. Se resolvió decodificando y aplicando `.rstrip("\r")` en `receive_complete_line()`.
* **Desincronización por caracteres fantasma en el buffer:** Si se ingresaba texto muy rápido en la consola, quedaban residuos en la cola del periférico. La inclusión explícita de `clear_rx()` antes de cada llamada a `uart.write()` garantizó que cada respuesta correspondiera estrictamente al comando recién transmitido.

---

### 8. Conclusión

El desarrollo de esta práctica permitió comprender la diferencia operativa entre la interfaz USB virtual de depuración y un puerto asíncrono UART por hardware. El diseño de protocolos basados en texto mediante delimitadores y códigos de retorno (`ACK`/`ERR`) sentó las bases para el control estructurado de actuadores y la validación de tramas bajo condiciones de error de sintaxis. Asimismo, la técnica de loopback físico demostró ser una herramienta fundamental de autodiagnóstico en sistemas embebidos antes de desplegar enlaces entre dispositivos independientes.

---

### Estructura de Entrega y Evidencias

```text
Sesion_09_UART/
├── README.md
├── main.py
├── tabla_pruebas.csv
└── evidencia/
    ├── thonny.png
    └── loopback_fisico.jpg

```

* **Ejecución en placa física:**
1. Conectar el jumper entre **GP0 (Pin 1)** y **GP1 (Pin 2)**.
2. Conectar LEDs con resistencia en **GP13** y **GP14**.
3. Conectar la Pico al puerto USB y abrir `main.py` en Thonny.
4. Ejecutar el script (F5) e ingresar los comandos de prueba en la consola interactiva.



```

```
