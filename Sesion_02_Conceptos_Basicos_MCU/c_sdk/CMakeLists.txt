cmake_minimum_required(VERSION 3.13)

# Inicializar el Pico SDK
include(pico_sdk_import.cmake)

project(memory_map_demo C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Inicializar entorno del SDK
pico_sdk_init()

# Definir el ejecutable a partir de tu archivo fuente
add_executable(memory_map_demo
    memory_map_demo.c
)

# Vincular las librerías estándar del SDK de la Pico
target_link_libraries(memory_map_demo
    pico_stdlib
)

# Habilitar salida serial por USB (CDC) y deshabilitar UART física
pico_enable_stdio_usb(memory_map_demo 1)
pico_enable_stdio_uart(memory_map_demo 0)

# Generar archivos extra (como el archivo .uf2 listo para flashear)
pico_add_extra_outputs(memory_map_demo)
