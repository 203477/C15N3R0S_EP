# Sesión 10: Smart I2C HMI Monitor
---

## Descripción de la Práctica
Este proyecto implementa una Interfaz Hombre-Máquina (HMI) embebida de 3 pantallas en una pantalla OLED SSD1306 (128x64) mediante comunicación I2C con una Raspberry Pi Pico.

El sistema monitorea una señal analógica (ADC), gestiona estados del sistema mediante clasificación por umbrales, despliega un indicador gráfico en tiempo real, controla un indicador físico (LED de alarma) y permite navegar entre las distintas pantallas mediante un botón con detección de flancos.

---

## Configuración del Bus I2C
* **Microcontrolador:** Raspberry Pi Pico
* **Periférico I2C:** I2C(0)
* **Línea de Datos (SDA):** GP4
* **Línea de Reloj (SCL):** GP5
* **Frecuencia del Bus:** $400\text{ kHz}$ (Fast-mode)
* **Dispositivo Principal (OLED SSD1306):**
  * Dirección Decimal: 60
  * Dirección Hexadecimal: 0x3C

---
## Diagnóstico del Bus (i2c.scan())
Al ejecutar el diagnóstico con i2c.scan(), el controlador escanea el bus de $7\text{ bits}$ en búsqueda de confirmaciones ACK.
* **Formato Decimal:** [60] (o [60, 104] si se conecta opcionalmente un MPU6050 en 0x68).
* **Formato Hexadecimal:** ['0x3c'] (o ['0x3c', '0x68']).

---

## Arquitectura de la HMI (3 Pantallas)
La navegación entre páginas se realiza mediante la pulsación de un botón (detección de flanco de bajada 1 -> 0), alternando la variable page = (page + 1) % 3.

### 1. Page 0: LIVE (Monitoreo en Tiempo Real)
* Muestra el porcentaje actual del ADC ($0 - 100\%$).
* Clasificación del estado del sistema:
  * NORMAL ($\text{ADC} < 50\%$): LED de alarma APAGADO.
  * WARNING ($50\% \le \text{ADC} < 75\%$): LED de alarma APAGADO.
  * ALARM ($\text{ADC} \ge 75\%$): LED de alarma ENCENDIDO.
* Dibujo dinámico de una barra de progreso proporcional en la OLED.

### 2. Page 1: I2C (Diagnóstico del Bus)
* Muestra los pines asignados (SDA = GP4, SCL = GP5).
* Muestra la frecuencia configurada ($400\text{ kHz}$).
* Lista interactiva con las direcciones I2C detectadas activamente en el bus.

### 3. Page 2: STATS (Estadísticas de Adquisición)
* Registra el valor mínimo registrado ($\text{Min \%}$).
* Registra el valor máximo registrado ($\text{Max \%}$).
* Muestra el número total de muestras procesadas ($N$).


| ID Prueba | Acción | Resultado Esperado | Estado |
| :--- | :--- | :--- | :--- |
| **P-01: SCAN** | Ejecutar script inicial de escaneo | OLED detectada en dirección 0x3C (60 decimal) | PASS |
| **P-02: LIVE NORMALy** | Ajustar ADC al $20\%$ | Pantalla muestra NORMAL, barra corta, LED OFF | PASS |
| **P-03: LIVE WARNING** | Ajustar ADC al $60\%$ | Pantalla muestra WARNING, barra media, LED OFF. | PASS |

---

## ¿Por qué varios dispositivos comparten SDA y SCL?
A diferencia de protocolos punto a punto como UART (que requieren un par dedicado de líneas $TX/RX$ para cada periférico extra), el bus I2C es un bus compartido basado en topología de líneas bidireccionales con configuración de drenador abierto (open-drain) y resistencias pull-up.
Gracias a esta arquitectura:
* Direccionamiento Único: Cada periférico responde únicamente cuando el controlador envía su dirección específica ($7\text{ bits}$) seguida del bit de operación ($R/\bar{W}$) y obtiene un bit de confirmación ($ACK$).
* Ahorro masivo de pines GPIO: Es posible conectar múltiples sensores (ej. MPU6050 0x68, RTC 0x68/0x57, OLED 0x3C) utilizando únicamente dos pines físicos en la Raspberry Pi Pico (GP4 y GP5).

---
## Conclusiones
El uso del bus I2C en la Raspberry Pi Pico permitió conectar de forma eficiente la pantalla OLED y los sensores usando solo dos pines (GP4 y GP5). Esto facilitó el desarrollo de una HMI interactiva de tres páginas con navegación por botón y visualización de datos en tiempo real, confirmando la escalabilidad de los sistemas embebidos.

Jiji, este proyecto me gustó bastantito 
---
