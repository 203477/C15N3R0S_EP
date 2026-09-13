# Sesión 04: Interrupciones y Temporizadores (Juego de Reflejos)

### Contenido
| Archivo | Contenido | Descripción |
| --- | --- | --- |
| [`micropython/button_irq_counter.py`]("./micropython/button_irq_counter.py") | MicroPython (DO 01: Interrupción por Botón)| Detección de flancos de bajada (`IRQ_FALLING`) con *pull-up* interno y filtro de rebote (*debounce*) por software.|
| [`micropython/timer_signal.py`]("./micropython/timer_signal.py") | MicroPython (SHOW 02: Temporizador Asíncrono)| Uso del hardware `Timer.ONE_SHOT` para disparar eventos sin bloquear el bucle principal de ejecución (`sleep_ms`).|
| [`micropython/reaction_game.py`]("./micropython/reaction_game.py") | MicroPython (CHALLENGE 04: Juego de Reflejos)| Juego interactivo no bloqueante con máquina de estados finitos, medición en ms (`ticks_diff`) y detección de salidas en falso (*foul*).|
| [`cpp/main.c`]("./cpp/main.c") | C/C++ Pico SDK (SHOW 03 & Reto Equivalente) | Configuración en bajo nivel con `gpio_set_irq_enabled_with_callback()`, alarmas de hardware (`add_alarm_in_ms`) y variables `volatile`. |
| [`cpp/CMakeLists.txt`]("./cpp/CMakeLists.txt") | Entorno de Compilación C/C++ Pico SDK | Script de configuración de CMake enlazando bibliotecas `hardware_gpio`, `hardware_timer` y salida USB serie. |
| [`wokwi/`]("./wokwi") | Diagrama y Simulación Wokwi (Circuito Común) | Esquema virtual unificado: LED blanco en GP15 (señal), LED azul en GP14 (espera) y botón a GP16/GND. |
| [`evidence/`]("evidence") | Capturas y Registros de Validación | Evidencias de terminal serie|

---

## 1. Objetivo
Comprender la diferencia fundamental entre la técnica de sondeo continuo (*polling*) y la respuesta orientada a eventos mediante interrupciones hardware (IRQ/ISR) y temporizadores asíncronos en microcontroladores Raspberry Pi Pico / RP2350, implementando y comparando soluciones funcionales en MicroPython y C/C++ (Pico SDK).

## 2. Circuito
El circuito implementado es común para ambas plataformas de desarrollo:
* **GP15:** Conectado al ánodo del LED blanco (Señal visual de reacción) a través de un resistor limitador de 330 Ω hacia GND.
* **GP14:** Conectado al ánodo del LED azul (Indicador de espera/alerta) a través de un resistor limitador de 300 Ω hacia GND.
* **GP16:** Conectado a un extremo del pulsador normalmente abierto; el otro extremo se conecta directamente a GND.
* **Configuración Eléctrica:** Resistencia interna de *Pull-Up* activada por software (`Pin.PULL_UP` / `gpio_pull_up()`), garantizando reposo en nivel lógico alto (1) y activación por flanco de bajada (`IRQ_FALLING` a 0).

## 3. ¿Qué es una interrupción?
Una interrupción (IRQ) es una señal enviada por un periférico al núcleo del microcontrolador que suspende momentáneamente el flujo principal del programa para atender un evento prioritario mediante una rutina de servicio (*ISR* o *callback*). 
A diferencia del *polling* (que desperdicia ciclos de reloj preguntando continuamente el estado de un pin), la interrupción permite que la CPU ejecute otras tareas o entre en bajo consumo hasta que ocurre una transición eléctrica física.

## 4. ¿Qué es un temporizador?
Un temporizador (*Timer* / *Alarm*) es un periférico de hardware independiente que cuenta pulsos de reloj de manera asíncrona. Al alcanzar un valor programado, genera un evento o interrupción sin requerir bucles de retardo bloqueantes (`sleep_ms()` o `delay()`). En esta práctica se utiliza en modo disparo único (*one-shot*) para desfasar la señal visual de manera no predecible manteniendo vivo el bucle principal.

## 5. Resultados en ms (Pruebas del Reto)
A continuación se muestran los resultados de las mediciones del tiempo de reacción:

| Intento | Tiempo (ms) | Observación |
| :---: | :---: | :--- |
| 1 | 248 ms | Respuesta limpia tras señal visual |
| 2 | 215 ms | Mejor tiempo registrado |
| 3 | FOUL | Salida en falso (pulsación antes de encender GP15) |
| 4 | 260 ms | Respuesta válida |
| 5 | 232 ms | Respuesta válida |

* **Mejor tiempo:** 215 ms
* **Peor tiempo:** 260 ms
* **Promedio válido:** 238.75 ms
* **Salidas falsas detectadas:** 1

## 6. Problemas encontrados y soluciones
1. **Rebote del botón (Bouncing):** Al presionar el switch mecánico se producían múltiples disparos de la ISR. Se solucionó agregando un umbral de tiempo (debounce) por software mayor a 80–100 ms usando marcas de tiempo (`ticks_diff` en MicroPython y `to_ms_since_boot` en C).
2. **Disparo múltiple por botón sostenido:** Si el usuario no soltaba el botón, la siguiente ronda se daba por completada inmediatamente. Se añadió un bucle de bloqueo posterior al resultado que espera la liberación del pin (`button.value() == 1` / `gpio_get()`).
3. **Manejo de salidas en falso:** Si se oprimía el botón mientras corría el timer de espera, este podía quedar flotando. Se implementó la cancelación explícita del timer/alarma (`game_timer.deinit()` / `cancel_alarm()`) al marcar el foul.

## 7. Conclusión
Se verificó que el uso de interrupciones y temporizadores por hardware desacopla la captura temporal de la lógica de presentación. Tanto MicroPython como C/C++ siguen el mismo principio físico: la ISR debe limitarse a marcar banderas o capturar tiempos breves, dejando la lógica pesada y la comunicación serie al hilo principal. C/C++ ofrece un determinismo superior y menor latencia en aplicaciones de tiempo real crítico.
