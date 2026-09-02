import os, gc, machine

# Información básica del sistema
print("Sistema:", os.uname())
print("Frecuencia CPU:", machine.freq())

# Recolectar basura y medir memoria libre inicial
gc.collect()
print("Memoria libre inicial:", gc.mem_free())

# Reservar memoria (buffer de 10,000 bytes)
# Nota: La guía pide comparar también cambiando este valor a 20000 bytes
buffer = bytearray(10000)
print("Memoria después de reservar buffer:", gc.mem_free())

# Eliminar referencia y forzar recolección de basura
del buffer
gc.collect()
print("Memoria después de liberar y gc.collect():", gc.mem_free())
