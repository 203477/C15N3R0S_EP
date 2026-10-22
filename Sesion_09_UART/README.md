Challenge 09 — UART Command Center con Thonny

Este proyecto implementa un centro de comandos y control de actuadores (LEDs) utilizando comunicación serial asíncrona (UART) sobre una Raspberry Pi Pico con MicroPython, empleando un esquema de prueba por loopback físico y Thonny IDE como consola de operador.

1. Fundamentos Teóricos

¿Qué es UART?

UART (Universal Asynchronous Receiver-Transmitter) es un protocolo de comunicación serie punto a punto. Se denomina asíncrono porque no cuenta con una línea de reloj (clock) compartida entre el transmisor y el receptor. En su lugar, ambos extremos acuerdan previamente los parámetros temporales y de formato de trama.

Líneas TX y RX

TX (Transmitter): Pin encargado de serializar los datos y enviarlos bit a bit hacia el receptor.

RX (Receiver): Pin encargado de muestrear la línea y reconstruir los bytes recibidos.

En una conexión estándar entre dos dispositivos independientes, el pin TX del dispositivo A se conecta al RX del dispositivo B, y viceversa, compartiendo siempre una referencia común de tierra (GND).

Baud Rate

El Baud Rate es la velocidad de modulación o número de símbolos transferidos por segundo en la línea serie. Para señales binarias estándar TTL/CMOS, equivale a bits por segundo (bps).

En este proyecto se configuró a $9600\text{ bps}$.

Cada bit tiene una duración aproximada de:

$$T_{\text{bit}} = \frac{1}{9600} \approx 104.16\,\mu\text{s}$$

Es indispensable que emisor y receptor operen exactamente a la misma velocidad para evitar errores de desfase o muestreo erróneo.

Formato de Trama Estándar: 8N1

La configuración por defecto empleada es 8N1, lo que define la estructura de cada byte transmitido:

1 Bit de Start: Transición a nivel bajo ($0\text{ V}$) que alerta al receptor del inicio de la trama.

8 Bits de Datos: Longitud de la carga útil (1 byte, típicamente codificado en ASCII).

No Paridad (N): No se incluye bit de redundancia o verificación de paridad.

1 Bit de Stop: Transición a nivel alto ($3.3\text{ V}$) para marcar el fin del byte y permitir el reposo de la línea.

Separación de Interfaces: USB/REPL vs UART0 Físico

USB / REPL (CDC): La Raspberry Pi Pico se comunica con la computadora anfitriona mediante emulación de puerto serie USB (USB CDC). A través de este canal, Thonny controla el entorno interactivo REPL de MicroPython, permitiendo usar input() y print().

UART0 Físico: Es el periférico de hardware dedicado de la RP2040 mapeado en los pines GP0 (TX) y GP1 (RX). Es independiente de la interfaz USB.

Loopback Físico: ¿Cómo comprobar UART sin adaptador externo?

Normalmente, para probar un puerto UART se requeriría un convertidor USB-Serial (FTDI, CP2102) externo conectado a la computadora.

El loopback físico consiste en puentear directamente el pin de transmisión con el de recepción (GP0 $\rightarrow$ GP1 con un cable jumper). De este modo:

El programa toma la instrucción ingresada por USB.

La transmite por el hardware UART0 TX.

La señal viaja físicamente por el jumper e ingresa inmediatamente por UART0 RX.

El programa lee la entrada de hardware, la procesa y reporta el resultado por USB.

Esto permite validar el funcionamiento del transceptor de hardware, buffers internos y parsers de software con cero instrumental externo adicional.

2. Arquitectura y Flujo de Datos

[Operador / Thonny]
       │  (USB Serial CDC)
       ▼
   input()  ───► uart.write() ───► GP0 (TX)
                                      │
                                [Jumper Físico]
                                      │
  LEDs (GP13, GP14) ◄─── Parser ◄─── GP1 (RX) ◄─── uart.read()
       │
       ▼
   print() (Consola USB)



3. Conexiones y Hardware

Componente

Pin Raspberry Pi Pico

Función / Destino

UART0 TX

GP0 (Pin físico 1)

Salida serial transmitida

UART0 RX

GP1 (Pin físico 2)

Entrada serial (conectada con jumper a GP0)

LED 1

GP13 (Pin físico 17)

Ánodo LED 1 (a través de resistor $220\,\Omega$ / $330\,\Omega$ a GND)

LED 2

GP14 (Pin físico 19)

Ánodo LED 2 (a través de resistor $220\,\Omega$ / $330\,\Omega$ a GND)

GND

GND (Pin físico 18 o 3)

Referencia común de masa

4. Protocolo de Comandos

Todas las tramas enviadas terminan con el delimitador de fin de línea \n. Las respuestas son enviadas como confirmación o error de procesamiento.

Comando

Respuesta Esperada

Descripción

PING

ACK,PONG

Verificación de comunicación viva

SET,LED1,1

ACK,LED1,1

Enciende el LED 1

SET,LED1,0

ACK,LED1,0

Apaga el LED 1

SET,LED2,1

ACK,LED2,1

Enciende el LED 2

SET,LED2,0

ACK,LED2,0

Apaga el LED 2

SET,ALL,1

ACK,ALL,1

Enciende ambos LEDs simultáneamente

SET,ALL,0

ACK,ALL,0

Apaga ambos LEDs simultáneamente

GET,STATUS

STATUS,LED1,<val>,LED2,<val>

Devuelve el estado actual de los LEDs (0 o 1)

Comando inválido / mal formado

ERR,BAD_SET_FRAME / ERR,UNKNOWN_FRAME

Manejo de excepciones y campos erróneos

5. Matriz de Pruebas Realizadas

#

Comando Entrada

UART TX $\rightarrow$ RX

Respuesta Esperada

Resultado Observado

Estado

1

PING

PING

ACK,PONG

RESP: ACK,PONG

PASS

2

SET,LED1,1

SET,LED1,1

ACK,LED1,1

RESP: ACK,LED1,1 (LED1 ON)

PASS

3

SET,LED1,0

SET,LED1,0

ACK,LED1,0

RESP: ACK,LED1,0 (LED1 OFF)

PASS

4

SET,LED2,1

SET,LED2,1

ACK,LED2,1

RESP: ACK,LED2,1 (LED2 ON)

PASS

5

SET,ALL,1

SET,ALL,1

ACK,ALL,1

RESP: ACK,ALL,1 (LED1 y LED2 ON)

PASS

6

GET,STATUS

GET,STATUS

STATUS,LED1,1,LED2,1

RESP: STATUS,LED1,1,LED2,1

PASS

7

SET,LED3,1

SET,LED3,1

ERR,BAD_SET_FRAME

RESP: ERR,BAD_SET_FRAME

PASS

8

SET,LED1,9

SET,LED1,9

ERR,BAD_SET_FRAME

RESP: ERR,BAD_SET_FRAME

PASS

9

HOLA MUNDO

HOLA MUNDO

ERR,UNKNOWN_FRAME

RESP: ERR,UNKNOWN_FRAME

PASS

6. Estructura del Repositorio

Sesion_09_UART/
├── README.md               # Este documento
├── main.py                 # Código de control y parser en MicroPython
├── tabla_pruebas.csv       # Registro en CSV de los casos de prueba ejecutados
└── evidencia/so
    ├── thonny.png          # Captura de pantalla de la terminal en Thonny
    └── loopback_fisico.jpg # Fotografía del circuito y jumper GP0->GP1



7. Instrucciones de Ejecución

Conecta la Raspberry Pi Pico a la computadora por USB.

Abre Thonny IDE y selecciona el intérprete MicroPython (Raspberry Pi Pico).

Asegúrate de tener colocado el cable jumper entre GP0 (TX) y GP1 (RX).

Carga y ejecuta main.py.

En la consola inferior (Shell), ingresa los comandos en el prompt CMD> y observa la trazabilidad completa del ciclo USB $\rightarrow$ UART $\rightarrow$ Loopback $\rightarrow$ Parser.
