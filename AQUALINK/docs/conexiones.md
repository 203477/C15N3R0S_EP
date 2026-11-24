# Conexiones físicas paso a paso

**Las dos peceras se cablean exactamente igual.** Arma una, pruébala con `pasos/paso2_entradas.py`,
y repite la misma receta en la otra.

> Guía visual: abre `wokwi/pecera_a/diagram.json` en Wokwi (ver [wokwi/README.md](../wokwi/README.md)).
> Los colores de cable de esta guía son los mismos que en el diagrama.

## Antes de empezar

- **Desconecta el USB** antes de mover cables.
- Los números de pin físico se cuentan así: con el USB hacia arriba, el pin 1 es el de arriba a la
  izquierda (GP0) y el pin 40 es el de arriba a la derecha (VBUS). Lo más seguro es voltear la Pico:
  abajo vienen impresos los nombres (`GP22`, `3V3`, `GND`…). Guíate por los nombres, no por contar patitas.
- Hay 8 pines GND repartidos (3, 8, 13, 18, 23, 28, 33, 38). Si un GND de la tabla te queda incómodo,
  usa cualquier otro: son todos el mismo.

## Tabla de conexiones (igual para la pecera A y la B)

| # | Componente | Pata del componente | Pin de la Pico (n.º) | Cable |
|---|------------|---------------------|----------------------|-------|
| 1 | **OLED SSD1306** | VCC | **3V3(OUT)** (36) | rojo |
| 2 | | GND | GND (38) | negro |
| 3 | | SDA | **GP4** (6) | verde |
| 4 | | SCL | **GP5** (7) | amarillo |
| 5 | **Botón FEED** | una pata | **GP2** (4) | verde |
| 6 | | pata opuesta | GND (3) | negro |
| 7 | **Botón SEND** | una pata | **GP3** (5) | verde |
| 8 | | pata opuesta | GND (3) | negro |
| 9 | **Sensor Hall A3144** (cara con letras hacia ti: pines 1-2-3) | 1 VCC | **VBUS** (40) | rojo |
| 10 | | 2 GND | GND (28) | negro |
| 11 | | 3 OUT | **GP22** (29) | morado |
| 12 | **Fotorresistencia (LDR)** | una pata | **3V3(OUT)** (36) | rojo |
| 13 | | otra pata | **GP26** (31) | naranja |
| 14 | **Resistencia 10 kΩ** | de **GP26** (31) | a **AGND** (33) | negro |
| 15 | **Resistencia 100 Ω** | de **GP14** (19) | a la pata **+** del buzzer | azul |
| 16 | **Buzzer pasivo** | pata **−** | GND (18) | negro |
| 17 | **Resistencia 220 Ω** | de **GP16** (21) | al **ánodo** (pata larga) del LED | blanco |
| 18 | **LED blanco** | **cátodo** (pata corta) | GND (23) | negro |
| 19 | **Imán de neodimio** | — | pegado en el borde **izquierdo** de la carcasa | — |
| — | El sensor Hall | — | pegado por dentro en el borde **derecho** | — |

**Notas**

- El A3144 necesita unos 4.5–5 V, por eso va a **VBUS** (los 5 V del USB) y no a 3V3. Su salida es de
  colector abierto: solo jala a GND, así que con el pull-up interno de la Pico **es seguro** para GP22.
- Alternativa más simple al Hall: un **reed switch** entre GP22 y GND. No necesita alimentación y el
  código funciona igual.
- Si usas un **módulo** LDR de 3 o 4 pines (con AO/DO), conecta AO a GP26, VCC a 3V3 y GND a GND, y pon
  `LDR_INVERT = True` en `config.py`.
- La OLED solo necesita 3.3 V. **No la conectes a VBUS.**
- El LED blanco es la "luz de la pecera": se atenúa de noche por PWM. Colócalo apuntando a la OLED.

## ¿Por qué imán a la izquierda y sensor a la derecha en las DOS peceras?

Así el enlace funciona en cualquier orden:

```
  [ imán | PECERA A | Hall ] [ imán | PECERA B | Hall ]   -> el Hall de A ve el imán de B: B está a la derecha de A
  [ imán | PECERA B | Hall ] [ imán | PECERA A | Hall ]   -> el Hall de B ve el imán de A: A está a la derecha de B
```

Cada pecera avisa en su mensaje `HELLO` si su sensor está activo, y así ambas saben de qué lado está la otra.

## Plan B — cable UART entre peceras

| Pecera A | | Pecera B |
|----------|---|----------|
| GP0 (TX, pin 1) | → | GP1 (RX, pin 2) |
| GP1 (RX, pin 2) | ← | GP0 (TX, pin 1) |
| GND (pin 3) | — | GND (pin 3) |

En ambos `config.py`: `LINK_MODE = "uart"`. Si el Wi-Fi no conecta al arrancar, el código cambia solo a UART.

## Alimentación

Cada pecera con su cable USB a un power bank o cargador de 5 V. Para la demo, mejor dos power banks:
así las peceras se pueden mover y juntar libremente.
