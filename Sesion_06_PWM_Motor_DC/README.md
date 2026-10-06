# Sesión 06 — PWM, puente H y control de motor DC

**Reto 06 — Control Motor Intelligente**
Ana Nickole Cisneros Herrera· Lab. de Elementos Programables*

---

## 1. Objetivo

Desarrollar un controlador de motor DC con la Raspberry Pi Pico utilizando PWM y un puente H L298N. El objetivo principal es lograr que el motor no solo gire, sino controlar **cómo llega a cada estado**: hacia dónde gira, a qué velocidad, y cómo acelera y frena progresivamente mediante rampas para evitar cambios bruscos de inercia que puedan dañar los componentes físicos.

Para lograr esto, se utilizan dos tipos de señales en pines distintos:

| Pregunta | Pin | Tipo de señal |
| --- | --- | --- |
| **¿Hacia dónde?** | `IN1`, `IN2` | Lógica: `0` / `1` |
| **¿Qué tan rápido?** | `ENA` | PWM: duty cycle 0–100 % |

## 2. Circuito

Las conexiones entre la Raspberry Pi Pico y el L298N son directas:

| Pico | L298N | Función |
| --- | --- | --- |
| GP2 | IN1 | Dirección |
| GP3 | IN2 | Dirección |
| GP4 | ENA | Velocidad (PWM a 1000 Hz) |
| GND | GND | Tierra común |

El motor se conecta a `OUT1/OUT2` del L298N. El L298N se alimenta de una fuente de voltaje externa, y el jumper por defecto del pin `ENA` debe ser retirado para permitir la inyección de la señal PWM. Es crucial que la tierra (GND) sea compartida entre la Pico y el puente H para que las señales de control tengan una referencia común.

## 3. Qué es PWM

**PWM (Pulse Width Modulation)** es una técnica para simular un voltaje analógico encendiendo y apagando una señal digital a gran velocidad. La **frecuencia** define qué tan rápido ocurre este ciclo (en este código, `1000 Hz`), y el **duty cycle** (ciclo de trabajo) define qué porcentaje del tiempo la señal permanece en alto:

$$D = \frac{t_{on}}{T} \qquad V_{avg} = D \cdot 3.3\ \text{V}$$

En MicroPython, el duty cycle no se ingresa directamente como porcentaje, sino como un valor de 16 bits que va de $0$ a $65535$. A mayor valor, mayor tiempo de pulso en alto, y en consecuencia, el motor recibe más energía promedio y gira más rápido.

## 4. Qué hacen IN1, IN2 y ENA

La combinación de estados lógicos determina el comportamiento del puente H:

| IN1 | IN2 | Motor |
| --- | --- | --- |
| 0 | 0 | STOP (Detenido) |
| 1 | 0 | FORWARD (Adelante) |
| 0 | 1 | REVERSE (Reversa) |

Las funciones `forward()`, `reverse()` y `stop()` encapsulan el comportamiento de los pines lógicos `IN1` e `IN2`. Esto permite que en el flujo principal del programa solo nos preocupemos por llamar acciones claras en lugar de configurar estados de pines directamente.

## 5. Velocidad: Porcentaje lógico a Duty de 16 bits

Para que sea más intuitivo trabajar con la velocidad, la función `set_speed(percent)` acepta un porcentaje de 0 a 100. La función incluye una medida de seguridad utilizando `max(0, min(100, percent))` para "saturar" el valor y garantizar que nunca se le pida a la Pico un porcentaje fuera de rango.

Una vez validado el porcentaje, se convierte a su equivalente en resolución de 16 bits mediante una regla de tres simple:

```python
def set_speed(percent):
  percent=max(0, min(100, percent))
  duty = int(percent * 65535 /100)
  ENA.duty_u16(duty)

```

## 6. Cómo funciona la rampa

Acelerar de golpe un motor requiere picos altos de corriente y causa estrés mecánico. La función `ramp_to()` resuelve esto incrementando o disminuyendo el PWM de forma gradual.

```python
def ramp_to(start, end, step=10, delay_ms=100):
  if end >= 100:
    end = 101
  elif end <= 0:
    end = -1
  ...

```

Dado que la función `range(start, end, step)` de Python **excluye** el valor límite final, el algoritmo cuenta con un bloque de ajustes:

1. Si el objetivo (`end`) es 100%, se modifica internamente a 101.
2. Si el objetivo es 0%, se modifica a -1.

Esto garantiza que el ciclo `for` iterará hasta tocar los valores extremos reales. Además, para prevenir que un valor de `-1` se envíe por accidente a `set_speed()`, dentro del ciclo de la rampa se corrige: `if speed == -1: speed = 0`.

Dependiendo de si `start <= end`, el código utiliza un paso positivo (`step`) para acelerar, o un paso negativo (`-step`) para desacelerar.

## 7. Cambio seguro de dirección

Invertir la polaridad de un motor cuando este gira a alta velocidad genera un retroceso eléctrico (fuerza contraelectromotriz) que puede dañar el driver L298N.

En este código, la seguridad se implementa de forma explícita en el ciclo principal (`while True`). Antes de pasar de FORWARD a REVERSE, el código realiza una secuencia de frenado progresivo y añade un descanso con el motor apagado:

1. Desacelera progresivamente: `ramp_to(100, 0)`
2. Permite que el eje se detenga por completo: `sleep_ms(500)`
3. Invierte la polaridad: `reverse()`

## 8. Secuencia del controlador

El bloque principal del programa se ejecuta en un bucle infinito que demuestra las capacidades del controlador, combinando las funciones de dirección, las rampas y los tiempos de mantenimiento.

| Acción | Código | Propósito |
| --- | --- | --- |
| Inicia hacia adelante | `forward()` | Establece los pines para giro horario. |
| Acelera progresivamente | `ramp_to(0, 100)` | Sube de 0% a 100% en pasos de 10%. |
| Sostiene vel. máxima | `sleep_ms(2000)` | Mantiene el motor al máximo por 2 segundos. |
| Frena progresivamente | `ramp_to(100, 0)` | Baja de 100% a 0% suavemente. |
| Pausa de seguridad | `sleep_ms(500)` | Espera medio segundo para perder la inercia. |
| Inicia en reversa | `reverse()` | Invierte el puente H. |
| Acelera progresivamente | `ramp_to(0, 75)` | Sube la velocidad en sentido antihorario hasta 75%. |
| Frena progresivamente | `ramp_to(75, 0)` | Se detiene por completo sin sostener velocidad. |
| Cierre del ciclo | `stop()` | Confirma pines de dirección en 0. |

## 9. Pruebas

Se probó el código validando la lógica de las rampas a través de los `print()` de la consola y analizando las señales.

| Prueba | Resultado esperado | Resultado obtenido |
| --- | --- | --- |
| FORWARD / REVERSE | Cambio en polaridad de la señal. | Correcto. |
| Aceleración | Impresión en consola subiendo de 10 en 10. | Llega exacto a 100% por ajuste `end = 101`. |
| Desaceleración | Impresión en consola bajando de 10 en 10. | Llega exacto a 0% por ajuste de `speed == -1`. |
| Cambio de dirección | Paso obligatorio por velocidad 0. | El motor se detiene por completo antes de `reverse()`. |

## 10. Evidencias

| Evidencia | Archivo |
| --- | --- |
| Simulación Wokwi | "./wokwi/enlace.md" |
| Montaje físico | *./evidence/hardware.jpeg* |


## 11. Conclusión

Este código demuestra cómo controlar actuadores de potencia desde una placa de 3.3V usando abstracciones. El L298N separa el control de la potencia, y la modulación de ancho de pulso (PWM) convierte una señal digital pura en un mecanismo capaz de alterar la velocidad mecánica de un motor DC. Más importante aún, la creación de funciones modulares como `ramp_to()`, `forward()` y `set_speed()` convierte un simple encendido de transistores en un verdadero "Controlador Inteligente", delegando al software la tarea de proteger el hardware.
