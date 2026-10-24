Examen Práctico 02: Sistema de Control Serial Inteligente
Sistema embebido desarrollado sobre Raspberry Pi Pico con MicroPython, integrando comunicación serial (UART), salidas digitales, control de brillo por PWM, lectura analógica (ADC) y procesamiento concurrente mediante Dual-Core.
Equipo
Integrantes: Ana Nickole Cisneros Herrera y Leslie Yoselin Sánchez Flores
Materia: Elementos programables
Fecha: 23 de Octubre de 2026
Institución: Universidad Iberoamericana Puebla
Propósito del examen
Construir y demostrar un único sistema embebido que integre los temas principales vistos en las sesiones recientes. La Raspberry Pi Pico deberá recibir comandos, controlar salidas, leer entradas y mantener una tarea de adquisición en segundo plano sin detener la comunicación.

Material y montaje mínimo
Raspberry Pi Pico / Pico W / Pico 2 / Pico 2 W con MicroPython.
Computadora con Thonny y cable USB de datos.
2 LEDs con resistencias (o shield de LEDs equivalente).
1 botón/pulsador.
1 fuente analógica de sesiones anteriores: potenciómetro, LDR, NTC u otro sensor analógico aprobado por el docente.
Jumpers y protoboard, si el shield no incluye los elementos necesarios.
Asignación de Pines y Hardware
Elemento	Pin Pico	Función / Configuración
LED Digital	GP13	Salida digital (Encendido / Apagado)
LED PWM	GP15	Salida PWM (Brillo 0–100 %)
Botón	GP16	Entrada digital con resistencia PULL_UP
ADC / Potenciómetro	GP26 (ADC0)	Entrada analógica (0 – 3.3 V)
Seguridad: La entrada ADC no supera los 3.3 V permitidos por el microcontrolador.

Arquitectura Dual-Core
El sistema aprovecha los dos núcleos de la Raspberry Pi Pico para garantizar la ejecución no bloqueante:

Core 0 (Procesador Principal): Atiende la comunicación serial, procesa y valida comandos entrantes, controla las salidas del LED digital y PWM, y envía las respuestas (ACK, ERR, STATUS, PONG).
Core 1 (Segundo Núcleo): Realiza la adquisición periódica del sensor en el ADC (0–100 %), actualiza variables compartidas e incrementa el contador de muestras (SAMPLES) en segundo plano sin interrumpir el flujo de comandos.
Protocolo de Comandos Seriales
Comandos Válidos
Comando	Acción	Respuesta Esperada
PING	Comprueba la comunicación serial	PONG
LED,1 / LED,0	Enciende (1) o apaga (0) el LED digital	ACK,LED,1 / ACK,LED,0
PWM,n	Ajusta el brillo del LED PWM (rango n = 0...100)	ACK,PWM,n
STATUS	Reporta el estado actual completo del sistema.	STATUS,LED=x,PWM=x,ADC=x,BTN=x,SAMPLES=x
ALL,1 / ALL,0	Comando compuesto que enciende/apaga el LED digital y pone PWM a 100% / 0%	ACK,ALL,1 / ACK,ALL,0
Manejo de Errores y Robustez
El parser valida las tramas para evitar interrupciones o bloqueos del programa:

Entrada de Prueba	Problema Identificado	Respuesta del Sistema
PWM,150	Valor PWM fuera del rango permitido (0-100).	ERR,PWM_RANGE
LED,7	Estado digital no válido (solo 0 o 1)	ERR,BAD_VALUE
PWM	Trama con formato incompleto	ERR,BAD_FORMAT
HOLA	Comando desconocido	ERR,UNKNOWN_COMMAND
