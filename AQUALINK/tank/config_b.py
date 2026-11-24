# config_b.py — Pecera B.  Cópialo a la Pico B con el nombre  config.py
#
# Las dos peceras son iguales por dentro. Solo cambian estas opciones:
#   la B espera al pez, no sirve el dashboard y dibuja el pez con caracteres.

TANK_ID = "B"
CREATE_FISH = False       # el pez nace en la pecera A
SERVE_DASHBOARD = False   # el dashboard vive en la pecera A
FISH_STYLE = "ascii"      # "pixel" (figuras) o "ascii" (caracteres)
USE_DUAL_CORE = False     # un solo bucle: esta pecera tiene menos trabajo
LINK_MODE = "wifi"        # "wifi" o "uart" (Plan B: cable GP0/GP1 cruzado)
TARGET_FPS = 20

# --- Pantalla OLED SSD1306 (I2C0) ---
PIN_SDA = 4
PIN_SCL = 5
OLED_WIDTH = 128
OLED_HEIGHT = 64          # pon 32 si tu OLED es de 128x32
I2C_FREQ = 400_000

# --- Botones (una pata al pin, la otra a GND) ---
PIN_BTN_FEED = 2          # alimentar
PIN_BTN_SEND = 3          # enviar el pez / mantener 1 s = pantalla de datos

# --- Sensores y salidas ---
PIN_HALL = 22             # sensor Hall A3144 o reed switch
PIN_LDR = 26              # ADC0, divisor LDR + 10k
PIN_BUZZER = 14           # PWM
PIN_LAMP = 16             # PWM, LED blanco + 220 ohm (luz de la pecera)
PIN_UART_TX = 0           # Plan B
PIN_UART_RX = 1

# --- Ajustes ---
LDR_INVERT = False        # True si de noche marca mucho y de dia poco
NIGHT_BELOW = 25          # % de luz para entrar en modo noche
DAY_ABOVE = 35            # % de luz para volver al modo dia
LAMP_DAY = 80
LAMP_NIGHT = 10
OLED_CONTRAST_DAY = 255   # brillo de la OLED de dia
OLED_CONTRAST_NIGHT = 20  # y de noche
BUZZER_ON = True
