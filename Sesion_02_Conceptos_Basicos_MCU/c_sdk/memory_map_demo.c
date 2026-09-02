#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"

// Variable constante: se almacena en memoria FLASH / XIP (0x10000000)
const uint32_t flash_const = 0x12345678;

// Variable global: se almacena en SRAM (0x20000000)
uint32_t global_counter = 0;

int main() {
    // Inicializar entradas/salidas estándar (consola serial por USB)
    stdio_init_all();
    
    // Pausa para dar tiempo a que el monitor serial se conecte
    sleep_ms(3000);

    // Variable local: se aloja en el STACK
    uint32_t stack_value = 0xABCDEF01;

    // Memoria dinámica: asignada en el HEAP
    uint8_t *heap_buffer = (uint8_t *)malloc(1024);

    // Impresión de las direcciones hexadecimales de cada región
    printf("flash const: %p\n", (void*)&flash_const);
    printf("global var : %p\n", (void*)&global_counter);
    printf("stack var  : %p\n", (void*)&stack_value);
    printf("heap ptr   : %p\n", (void*)heap_buffer);

    // Liberar la memoria solicitada dinámicamente
    free(heap_buffer);

    // Bucle infinito de espera
    while (true) {
        sleep_ms(1000);
    }

    return 0;
}
