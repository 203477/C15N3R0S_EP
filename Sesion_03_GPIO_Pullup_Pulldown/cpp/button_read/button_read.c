#include <stdbool.h>
#include <stdio.h>
#include "pico/stdlib.h"

#define BUTTON_PIN  16

int main(void) {
    stdio_init_all();

    gpio_init(BUTTON_PIN);
    gpio_set_dir(BUTTON_PIN, GPIO_IN);
    gpio_pull_up(BUTTON_PIN);

    printf("DO 01 - Lectura de boton en GP%d con pull-up interno\n", BUTTON_PIN);
    printf("Esperado -> boton libre = 1 | boton presionado = 0\n");
    printf("----------------------------------------------\n");

    while (true) {
        bool value = gpio_get(BUTTON_PIN);
        const char *estado = (value == 0) ? "PRESIONADO" : "libre";
        printf("GP%d = %d  (%s)\n", BUTTON_PIN, value, estado);
        sleep_ms(200);
    }

    return 0;
}
