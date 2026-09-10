#include <stdio.h>
#include "pico/stdlib.h"

// Pines asignados
#define CAR_RED      15
#define CAR_YELLOW   14
#define CAR_GREEN    13
#define PED_RED      12
#define PED_GREEN    11
#define BUTTON       16

// Tiempos (ms)
#define TRANSITION_MS  1500
#define CROSSING_MS    4000
#define BLINK_TIMES    4
#define BLINK_MS       300
#define RECOVERY_MS    1000

// Invariante de seguridad
void set_lights(bool car_r, bool car_y, bool car_g, bool ped_r, bool ped_g) {
    if (car_g && ped_g) {
        printf("[ALERTA] Invariante violada: no se permite doble verde.\n");
        return;
    }
    gpio_put(CAR_RED, car_r);
    gpio_put(CAR_YELLOW, car_y);
    gpio_put(CAR_GREEN, car_g);
    gpio_put(PED_RED, ped_r);
    gpio_put(PED_GREEN, ped_g);
}

// Funciones de estado
void cars_go(void) {
    set_lights(false, false, true, true, false);
}

void cars_prepare_to_stop(void) {
    set_lights(false, true, false, true, false);
}

void pedestrians_go(void) {
    set_lights(true, false, false, false, true);
}

void pedestrians_hurry(void) {
    for (int i = 0; i < BLINK_TIMES; i++) {
        gpio_put(PED_GREEN, 0);
        sleep_ms(BLINK_MS);
        gpio_put(PED_GREEN, 1);
        sleep_ms(BLINK_MS);
    }
    gpio_put(PED_GREEN, 0);
    gpio_put(PED_RED, 1);
}

void crossing_sequence(void) {
    printf(">> S1: Autos en amarillo\n");
    cars_prepare_to_stop();
    sleep_ms(TRANSITION_MS);

    printf(">> S2: Peatones en verde\n");
    pedestrians_go();
    sleep_ms(CROSSING_MS);

    printf(">> S3: Parpadeo de desalojo\n");
    pedestrians_hurry();

    sleep_ms(RECOVERY_MS);

    printf(">> S0: Retorno a reposo vehicular\n");
    cars_go();
}

int main() {
    stdio_init_all();

    uint leds[] = {CAR_RED, CAR_YELLOW, CAR_GREEN, PED_RED, PED_GREEN};
    for (int i = 0; i < 5; i++) {
        gpio_init(leds[i]);
        gpio_set_dir(leds[i], GPIO_OUT);
    }

    gpio_init(BUTTON);
    gpio_set_dir(BUTTON, GPIO_IN);
    gpio_pull_up(BUTTON);

    cars_go();
    sleep_ms(2000);
    printf("Sistema en C listo. Esperando boton...\n");

    int last = 1;

    while (true) {
        int now = gpio_get(BUTTON);

        if (last == 1 && now == 0) {
            sleep_ms(30); // Debounce
            if (gpio_get(BUTTON) == 0) {
                printf("\n[EVENTO] Cruce solicitado.\n");
                crossing_sequence();

                // Wait for release
                while (gpio_get(BUTTON) == 0) {
                    sleep_ms(10);
                }
            }
        }
        last = now;
        sleep_ms(10);
    }

    return 0;
}
