# Sesión 02 — Conceptos básicos de microcontroladores
## Contenido

| Carpeta | Contenido |
|---|---|
| `infografia/` | Infografía técnica (Challenge 02) |
| `micropython/` | `memory_probe.py` — MicroPython (DO 01: Prueba de Memoria) |
| `c_sdk/` | `memory_map_demo.c` + `CMakeLists.txt` — C/C++ (Pico SDK - DO 02: Mapa de Memoria y Registros) |
| `wokwi/` | Enlaces de simulaciones |
| `evidence/` | Evidencia (virtual y física) |


## 📝 Objetivo de la Práctica
Comprender la relación entre el código de software, el mapa de memoria (Flash, SRAM, Stack, Heap) y los registros de hardware del microcontrolador (RP2040 / RP2350), verificando la gestión de memoria en MicroPython y la asignación de direcciones de memoria y manipulación de GPIO mediante registros en C/C++ (Pico SDK).

## 📦 Materiales Utilizados
* 1x Raspberry Pi Pico 2 W (o Raspberry Pi Pico W)
* 1x Cable Micro-USB con soporte de datos
* Computadora con VS Code (Pico SDK / MicroPico) o Thonny
* Simulador Wokwi

## 📊 Infografía técnica (Challenge 02)
📄 **Infografía de Arquitectura:** [Descargar PDF](./Infografia/Cisneros_Ana_S02_Infografia.pdf)
* Explica la diferencia entre RP2040 y RP2350, el mapa de memoria, el concepto de registros y la ruta de ejecución de MicroPython vs C/C++.

---

### 🐍 MicroPython (DO 01: Prueba de Memoria)
📄 **Código fuente:** [Ver archivo `memory_probe.py` aquí](./micropython/memory_probe.py)

**Explicación de la lógica en Python:**
* Se utilizó el módulo `gc` (Garbage Collector) y `os` para inspeccionar los recursos del microcontrolador en tiempo de ejecución.
* Con `gc.mem_free()` se verificó la memoria disponible antes y después de instanciar un buffer dinámico de tipo `bytearray(10000)` (y `20000`).
* Tras eliminar la referencia con `del` y ejecutar `gc.collect()`, se observó cómo la memoria asignada regresa al heap libre, evidenciando cómo MicroPython gestiona la memoria dinámica en la SRAM.

---

### ⚙️ C/C++ (Pico SDK - DO 02: Mapa de Memoria y Registros)
📄 **Código fuente:** [Ver archivo `memory_map_demo.c` aquí](./c_sdk/memory_map_demo.c)

**Explicación de la lógica en C/C++:**
* Se imprimieron las direcciones de memoria de diferentes variables para verificar su correspondencia con el mapa de direcciones del microcontrolador:
  * `const uint32_t flash_const` vive en la memoria Flash/XIP (`0x10000000`).
  * `uint32_t global_counter` se asigna a la SRAM estática (`0x20000000`).
  * `uint32_t stack_value` vive en el Stack (crece hacia abajo en la SRAM).
  * `uint8_t *heap_buffer` proviene de `malloc()`, ubicándose en el Heap.
* Para el control de hardware, se observó cómo las funciones del SDK abstraen el acceso al periférico SIO (`sio_hw->gpio_set` y `sio_hw->gpio_clr`), donde cambiar un bit a 1 o 0 traduce directamente un cambio de voltaje físico (0V o 3.3V) en el pin.

| Variable | Tipo / Ámbito | Dirección Observada (%p) | Región Probable |
| :--- | :--- | :--- | :--- |
| `flash_const` | `const uint32_t` (Global) | *(Ej. 0x1000...)* | Flash / XIP |
| `global_counter` | `uint32_t` (Global) | *(Ej. 0x2000...)* | SRAM |
| `stack_value` | `uint32_t` (Local) | *(Ej. 0x2004...)* | Stack |
| `heap_buffer` | Puntero dinámico (`malloc`) | *(Ej. 0x2001...)* | Heap |

---

## 🎥 Evidencia
* **Wokwi:** [`wokwi/Wokwi.md`](./wokwi/Wokwi.md) 
* **Captura(s):** [Ver captura](./evidence/serial_output.png)

---

## 🤔 Conclusiones o Retos Superados
* **Gestión de Memoria:** Comprender que en sistemas embebidos la memoria RAM es un recurso crítico y finito; a diferencia de una PC convencional, no se cuenta con memoria virtual ni sistema operativo para gestionar desbordamientos.
* **Abstracción del SDK:** En lugar de memorizar y configurar manualmente direcciones hexadecimales de registros (como `0xD0000000` para SIO), el Pico SDK nos da portabilidad para que el mismo código sea compatible entre un RP2040 y un RP2350.
* **Retos técnicos:** *(Asegurar el retardo `sleep_ms(3000)` para que el monitor serial alcanzara a capturar los primeros prints)*.
