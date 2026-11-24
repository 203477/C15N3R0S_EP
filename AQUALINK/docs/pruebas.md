# Plan de pruebas y evidencias

Marca cada prueba y guarda la evidencia en `evidence/` con el nombre indicado.

## 0. Pruebas en la PC (sin hardware)

```bash
python3 tests/test_logic.py
```
Comprueba: nombres válidos, parseo de URLs, rebote sin enlace, viaje A→B y B→A,
5 minutos de cruces sin pérdidas ni duplicados, envío fallido, duplicado tras reinicio,
comida/hambre y órdenes web 200/400/409.

## 1. Por módulo (semana 1–2)

| # | Prueba | Cómo | Esperado | Evidencia |
|---|--------|------|----------|-----------|
| 1 | Entradas | `pasos/paso2_entradas.py` en cada Pico | Cada botón se imprime una vez; Hall SI/no; luz cambia | `io_test.png` |
| 2 | OLED A | `pasos/paso1_pantalla.py` | Marco, texto y contador del 1 al 10 | `oled_a.jpg` |
| 3 | OLED B | `pasos/paso1_pantalla.py` | Lo mismo en la segunda Pico | `oled_b.jpg` |
| 4 | PWM | Tapar el LDR | Baja el brillo de la OLED y de la lámpara, en las dos | `night_mode.jpg` |
| 5 | Wi-Fi | `pasos/paso3_wifi.py` | Ambas obtienen IP en la misma red | `ips.jpg` |
| 5b | Pantalla de datos | Mantener **SEND** 1 s | Sale IP, enlace, luz y envíos | `info.jpg` |

## 2. Integración (semana 3)

| # | Prueba | Esperado | Evidencia |
|---|--------|----------|-----------|
| 6 | Juntar peceras | Aparece `<>` arriba y la flecha hacia la otra | `link.jpg` |
| 7 | A → B | El pez sale de la OLED de A y entra en la de B | `transfer_a_b.mp4` |
| 8 | B → A | Regresa a la pecera A | `transfer_b_a.mp4` |
| 9 | Separadas | El pez rebota en el borde | — |
| 10 | Dashboard | `http://IP_A/` muestra al pez donde está | `dashboard.png` |
| 11 | API | `/api/status` JSON | `api_status.png` |
| 12 | Errores | `/api/light?value=150` → 400, `/xyz` → 404, `/api/send` separadas → 409 | `err_400_404.png` |

## 3. Robustez (semana 4)

| # | Prueba | Esperado |
|---|--------|----------|
| 13 | 20 transferencias seguidas | 20/20 sin pérdida ni duplicado (ver contador en dashboard) |
| 14 | Apagar Wi-Fi de B durante un envío | El pez se queda en A ("Envio fallido") |
| 15 | Desconectar una Pico y volver a conectar | El pez sigue en la misma pecera (`fish.json`) |
| 16 | Plan B UART | Con `LINK_MODE="uart"` y el cable cruzado, el pez viaja igual — `uart_planb.mp4` |
