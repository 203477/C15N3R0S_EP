#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "hardware/timer.h"

#define PIN_SIGNAL 15
#define PIN_WAIT 14
#define PIN_BUTTON 16

typedef enum {
    IDLE,
    WAITING_SIGNAL,
    SIGNAL_ACTIVE,
    ROUND_OVER
} game_state_t;

volatile game_state_t state = IDLE;
volatile uint32_t start_ms = 0;
volatile uint32_t reaction_ms = 0;
volatile bool early_press = false;
volatile bool result_ready = false;
volatile uint32_t last_irq_ms = 0;
alarm_id_t current_alarm = 0;

int64_t signal_alarm_callback(alarm_id_t id, void *user_data) {
    gpio_put(PIN_WAIT, false);
    gpio_put(PIN_SIGNAL, true);
    start_ms = to_ms_since_boot(get_absolute_time());
    state = SIGNAL_ACTIVE;
    return 0; // Alarma One-shot
}

void gpio_callback(uint gpio, uint32_t events) {
    if (gpio != PIN_BUTTON) return;

    uint32_t now = to_ms_since_boot(get_absolute_time());
    if (now - last_irq_ms < 100) return; // Debounce
    last_irq_ms = now;

    if (state == WAITING_SIGNAL) {
        cancel_alarm(current_alarm);
        early_press = true;
        result_ready = true;
        state = ROUND_OVER;
    } else if (state == SIGNAL_ACTIVE) {
        reaction_ms = now - start_ms;
        result_ready = true;
        state = ROUND_OVER;
    }
}

void schedule_round(void) {
    early_press = false;
    result_ready = false;
    gpio_put(PIN_SIGNAL, false);
    gpio_put(PIN_WAIT, true);
    state = WAITING_SIGNAL;

    uint32_t delay_ms = 2000 + (rand() % 3000);
    printf("\n--- Preparate... La senal aparecera pronto ---\n");
    current_alarm = add_alarm_in_ms(delay_ms, signal_alarm_callback, NULL, false);
}

int main(void) {
    stdio_init_all();
    sleep_ms(1500); // Pausa para conexión serial USB

    gpio_init(PIN_SIGNAL);
    gpio_set_dir(PIN_SIGNAL, GPIO_OUT);
    gpio_put(PIN_SIGNAL, false);

    gpio_init(PIN_WAIT);
    gpio_set_dir(PIN_WAIT, GPIO_OUT);
    gpio_put(PIN_WAIT, false);

    gpio_init(PIN_BUTTON);
    gpio_set_dir(PIN_BUTTON, GPIO_IN);
    gpio_pull_up(PIN_BUTTON);

    gpio_set_irq_enabled_with_callback(PIN_BUTTON, GPIO_IRQ_EDGE_FALL, true, &gpio_callback);

    printf("Juego de Reflejos en C / Pico SDK\n");
    schedule_round();

    while (true) {
        if (result_ready) {
            gpio_put(PIN_SIGNAL, false);
            gpio_put(PIN_WAIT, false);

            if (early_press) {
                printf("[FOUL] Salida falsa! Oprimiste antes de tiempo.\n");
            } else {
                printf("[EXITO] Tiempo de reaccion: %lu ms\n", reaction_ms);
            }

            // Esperar liberación del botón
            while (!gpio_get(PIN_BUTTON)) {
                sleep_ms(10);
            }

            sleep_ms(1500);
            schedule_round();
        }
        tight_loop_contents();
    }
    return 0;
}
