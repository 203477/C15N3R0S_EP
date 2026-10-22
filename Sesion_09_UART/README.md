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
