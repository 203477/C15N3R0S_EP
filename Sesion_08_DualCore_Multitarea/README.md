# Práctica 08 — Procesamiento Concurrente y Arquitectura Dual-Core

**Desafío 08 — Implementación de un Sistema Multitarea**
*Ana Nickole Cisneros Herrera · Laboratorio de Elementos Programables*

---

## 1. Propósito del Proyecto

El objetivo central es desarrollar una arquitectura de software en la que un proceso se dedique exclusivamente a la **lectura de un sensor de misión crítica a alta frecuencia**, mientras que otros procesos paralelos gestionan las interfaces de usuario (LEDs, botones, alertas y consola serial) **sin generar cuellos de botella ni bloqueos** en el microcontrolador.

En sesiones previas, el flujo de ejecución era lineal y dependía de pausas prolongadas (`sleep_ms(300)`), lo que dejaba al sistema "ciego" ante cambios rápidos. En esta iteración, el código se fragmenta en **rutinas independientes con frecuencias de actualización específicas**:

```text
[Adquisición 20 ms] ──▶ [Suavizado] ──▶ [Evaluación] ──▶ (Datos Compartidos) ──▶ [Indicadores Visuales 200 ms]
                                                                   ▲             [Salida Serial 1000 ms]
                                                     [Interrupción ACK 50 ms] ──┘

```

Este esquema se aborda mediante dos enfoques distintos:

* **Entorno Wokwi (`main_wokwi.py`):** Simulación en un solo núcleo que demuestra **concurrencia**, alternando tareas mediante la evaluación de tiempo con `ticks_ms()`.
* **Hardware Real (`main_dualcore_physical.py`):** Ejecución en una Raspberry Pi Pico 2 W utilizando **paralelismo puro**, asignando el monitoreo del sensor al Core 1 y el manejo de la interfaz al Core 0, coordinados mediante la librería `_thread` y semáforos (`lock`).

## 2. Principios de Ejecución Simultánea

La **concurrencia** es la capacidad del sistema para administrar múltiples hilos de ejecución en un mismo periodo, intercalando sus procesos en una sola unidad de procesamiento. Por otro lado, el **paralelismo** implica la ejecución de tareas exactamente en el mismo instante a través de hardware multinúcleo. Wokwi nos permite simular el primer concepto, mientras que la placa física ejecuta ambos.

### 2.1 Enfoque Cooperativo (Simulación en Wokwi)

En este modelo, cada subrutina calcula **su próxima ventana de ejecución** (por ejemplo, `next_sensor`, `next_ui`). El bucle principal (`while True`) monitorea constantemente el reloj del sistema y solo dispara las funciones cuyo tiempo límite ha expirado:

```python
def tiempo_cumplido(actual, objetivo):
    return ticks_diff(actual, objetivo) >= 0

while True:
    reloj_actual = ticks_ms()
    if tiempo_cumplido(reloj_actual, next_sensor):
        rutina_sensor()
        next_sensor = reloj_actual + intervalo_sensor
    # ... evaluación de interfaz, botones y consola ...
    sleep_ms(2) # Pausa mínima para no saturar el procesador

```

La regla de oro aquí es evitar bloqueos prolongados. Ninguna función utiliza pausas largas; todas deben operar y liberar el control inmediatamente.

**Frecuencias establecidas:**

* **Muestreo (20 ms / 50 Hz):** Vital para reaccionar ante fluctuaciones inmediatas de la señal analógica.
* **Pulsador (50 ms / 20 Hz):** Supera la velocidad de reacción humana y mitiga problemas eléctricos de rebote.
* **Interfaz (200 ms / 5 Hz):** Fluidez visual adecuada para el usuario, ideal para el efecto de parpadeo en las alertas.
* **Consola (1000 ms / 1 Hz):** Frecuencia de lectura humana; evita retrasar el procesador con operaciones pesadas de I/O.

### 2.2 Multiprocesamiento Físico (Raspberry Pi Pico)

Mediante la instrucción `_thread.start_new_thread(sensor_core, ())`, delegamos toda la carga de lectura analógica al **Core 1**. El **Core 0** mantiene el control del flujo principal administrando los LEDs, la consola y el botón (utilizando un planificador idéntico al cooperativo).

Para evitar corrupciones de memoria, ambos núcleos acceden a un diccionario global (`shared`) protegido por un mecanismo de exclusión mutua (`lock`):

```python
lock.acquire()
shared["raw"] = lectura_cruda
shared["state"] = estado_actual
# ...
lock.release()

```

**Criterios de arquitectura para el dual-core:**

1. **Cómputo fuera de la zona crítica:** Las operaciones matemáticas se realizan antes de solicitar el `lock`. Dentro de la exclusión mutua, solo se transfieren datos para minimizar tiempos de espera entre núcleos.
2. **Lectura atómica en el Core 0:** Toda la información necesaria se extrae en un solo bloque (`read_shared()`) para garantizar que la interfaz opere con datos del mismo instante temporal.
3. **Confirmación segura en `button_task()`:** La evaluación del estado y la activación de la bandera ACK se encapsulan en un solo acceso protegido. Si no estuvieran agrupados, el Core 1 podría modificar el estado general justo en medio de la evaluación.
4. **Aislamiento de hardware lento:** El Core 1 jamás interactúa con la terminal serial ni con la interfaz visual, garantizando su naturaleza como hilo de alta velocidad.

## 3. Alcance de las Validaciones

**Lo que comprobamos en Wokwi:**

* La lógica matemática: periodos de actualización, algoritmo de suavizado, ventanas de histéresis y reconocimiento de botones.
* Garantía de que ningún proceso obstaculiza a los demás en un entorno de un solo núcleo.

**Lo que comprobamos en la placa Pico 2 W:**

* Que el hardware multinúcleo procesa la señal analógica en estricto paralelo.
* La integridad de los datos compartidos gracias al uso correcto de `lock`.
* El comportamiento real frente al ruido eléctrico y el rebote físico de los interruptores.

## 4. Diseño del Circuito

* **Entrada Analógica (Sensor):** Potenciómetro en el pin GP26 (ADC0). Las terminales laterales van a 3.3V y GND.
* **Indicador Normal:** LED Verde conectado a GP13.
* **Indicador Precaución:** LED Amarillo conectado a GP14.
* **Indicador Peligro:** LED Rojo conectado a GP15 (modo intermitente si no hay ACK; estático al confirmarse).
* **Señal de Vida (Heartbeat):** LED Azul conectado a GP12.
* **Botonera:** Pulsador en GP16 conectado a tierra (Configurado con resistencia `PULL_UP` interna: lee 1 en reposo, 0 al accionar).

*Nota: Se debe instalar una resistencia limitadora de corriente en serie para cada diodo emisor de luz.*

## 5. Lógica de Activación (Umbrales)

El algoritmo `classify()` evalúa en orden descendente, similar a la lógica aplicada en prácticas anteriores.

* **Fase NORMAL:** De 0% a menos del 50% (Indicador verde activo).
* **Fase WARNING:** De 50% a menos del 75% (Indicador amarillo activo).
* **Fase ALARM:** De 75% al 100% (Indicador rojo activo).

*Las cotas 50 y 75 están definidas estáticamente en el código para su fácil calibración.*

## 6. Procesamiento de Señales (Filtro)

Para estabilizar las lecturas del ADC, implementamos una ventana móvil que promedia las últimas 8 muestras (`BUFFER_SIZE = 8`). Con el incremento en la velocidad de muestreo a 20 ms, la latencia de este filtro es extremadamente corta:

$$T_{ventana} = Muestras \cdot Tiempo_{muestreo} = 8 \cdot 20\ \text{ms} = 160\ \text{ms}$$

En contraste con los 3 segundos que tomaba este filtro en la sesión pasada, esta nueva frecuencia permite limpiar la señal de interferencias sin sufrir ningún retraso perceptible en la respuesta del sistema.

## 7. Sistema de Reconocimiento de Alarmas (ACK)

El comportamiento de la interfaz ante situaciones críticas obedece a la siguiente matriz:

* **ALARM activa, sin confirmar:** El indicador rojo parpadea y la bandera `ack` es `False`.
* **ALARM confirmada por operador:** El indicador rojo queda encendido permanentemente (`True`).
* **Desescalada (salida de fase ALARM):** El indicador rojo se apaga y el sistema resetea `ack` a `False` de manera autónoma.
* **Activación del botón en estado normal:** La pulsación se ignora operativamente (solo emite registro serial).

La lectura del botón se detecta por flanco de bajada (transición de 1 a 0). Comparar la lectura actual contra el registro previo (`last_button`) evita disparos múltiples si el operador deja pulsado el botón.

## 8. Protocolo de Pruebas

* [ ] Voltaje mínimo en potenciómetro -> Entra en NORMAL / Se enciende LED verde.
* [ ] Voltaje medio en potenciómetro -> Entra en WARNING / Se enciende LED amarillo.
* [ ] Voltaje máximo en potenciómetro -> Entra en ALARM / LED rojo empieza a destellar.
* [ ] Pulsar botón fuera de rango crítico -> El sistema lo reporta pero ignora el ACK.
* [ ] Pulsar botón en rango crítico -> El LED rojo deja de destellar y se queda estático.
* [ ] Reducir voltaje tras una alarma -> El estado ACK se reinicia correctamente.
* [ ] Indicador Heartbeat -> El LED azul destella rítmicamente sin sufrir congelamientos.
* [ ] Reporte de consola -> Los datos fluyen sin interrupción cada segundo.
* [ ] Tasa de adquisición -> El sensor captura cerca de 50 muestras por segundo.
* [ ] Efectividad del filtro -> Los brincos bruscos del sensor se suavizan en los datos crudos.
* [ ] Hardware (Solo Pico) -> El sistema no colapsa al correr operaciones visuales en paralelo al ADC.

**Rendimiento (Muestras por Segundo):**
El parámetro `rate=` documentado en la consola serial nos ayuda a verificar el rendimiento de cada arquitectura.

| Arquitectura Evaluada | `rate=` (muestras por segundo) |
| --- | --- |
| Simulación Wokwi (Un solo núcleo cooperativo) |  |
| Placa Física Pico 2 W (Procesamiento en Core 1) |  |

En el entorno cooperativo, es común observar un rendimiento marginalmente inferior a 50 (aprox. 48 lecturas/s). Esto ocurre porque la verificación del reloj central se efectúa cada 2 ms, sumando pequeñas latencias de procesamiento en cada ciclo del `while True`.

## 9. Análisis Conceptual

**1. ¿En qué difiere el modelo cooperativo de Wokwi frente al esquema dual-core físico?**
En la simulación, existe un único hilo conductor. Las tareas deben ceder voluntariamente el control procesal; si una operación es ineficiente, paraliza a las demás. En el entorno físico con la Pico, la tarea analógica vive en un procesador completamente independiente, garantizando su ejecución continua sin importar cuán sobrecargada esté la interfaz visual.

**2. ¿Por qué se omitió el uso de `sleep_ms(1000)` en el hilo de captura de datos?**
Introducir un retardo de un segundo cegaría por completo al microcontrolador ante picos de señal ocurridos en esa ventana temporal. Además, en el esquema de Wokwi, una instrucción de reposo absoluto de 1 segundo congelaría los botones y las alertas, rompiendo por completo la arquitectura multitarea.

**3. ¿Cuál es la justificación de tener el sensor a 20 ms y la terminal a 1000 ms?**
La temporalidad debe coincidir con el caso de uso. El ADC debe monitorear variables dinámicas a alta resolución temporal. La consola serial, diseñada para depuración humana, colapsaría de información ilegible a esa velocidad; además, las operaciones de I/O sobre el puerto serial son computacionalmente costosas.

**4. ¿Por qué resulta imperativo usar candados (`lock`) al manejar variables globales entre núcleos?**
Al operar en paralelo puro, es altamente probable que el Core 0 intente leer un conjunto de variables globales en el exacto milisegundo en que el Core 1 está modificándolas. Sin un candado de exclusión mutua, la interfaz podría procesar una lectura corrupta (mezclando información de dos instantes distintos). El `lock` fuerza a un núcleo a esperar milisegundos hasta que el paquete de datos haya sido actualizado en su totalidad.

**5. Conceptualmente, ¿qué separa a "confirmar una alerta" de "extinguir una alerta"?**
La confirmación (ACK) es una respuesta humana que le indica a la computadora: "El evento anómalo ha sido detectado, desactiva la señal auditiva/visual invasiva". Sin embargo, la alarma persiste. El sistema solo extingue la alerta cuando la condición electromecánica (voltaje del sensor) vuelve a un estado operativo seguro.

**6. ¿Qué métricas físicas validan que nuestro código no sufre retardos por bloqueos?**
La prueba definitiva es observar el "Heartbeat" (LED azul) destellando a un ritmo matemáticamente perfecto, ver a la consola reportar consistentemente casi 50 ciclos por segundo, e interactuar con el pulsador notando una reactividad instantánea incluso cuando el procesador está bajo carga de reportes.

## 10. Documentación Visual

* **Enlace de proyecto en Wokwi:** Referirse a `wokwi/enlace.md`.
* **Captura Terminal Wokwi:** `evidence/serial_wokwi.png` (Muestra ACK y cambios lógicos).
* **Captura Terminal Placa:** `evidence/serial_pico.png` (Detalle de muestras de Core 1).
* **Evidencia de Ensamble Físico:** `evidence/circuito.png`.

## 11. Bitácora de Inconvenientes

## 12. Reflexiones Finales

---

## Estructura del Repositorio e Instrucciones de Uso

* `main_wokwi.py`: Variante concurrente para simulación web.
* `main_dualcore_physical.py`: Variante con librería `_thread` para test en hardware.
* `wokwi/diagram.json`: Tipología de pines y componentes.
* `wokwi/enlace.md`: URL del simulador.
* `evidence/`: Banco de capturas de pantalla.

**Para testear en plataforma web:**

1. Crear un nuevo proyecto "Raspberry Pi Pico + MicroPython" en wokwi.com.
2. Sobrescribir el esquemático con el código de `diagram.json`.
3. Pegar el contenido de `main_wokwi.py` en la pestaña de `main.py`.

**Para testear en la Raspberry Pi Pico (Terminal local):**

```bash
# Ejecutar directamente desde la terminal del IDE usando mpremote
mpremote run main_dualcore_physical.py

```
