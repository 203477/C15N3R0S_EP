PRIMER EXAMEN PARCIAL 

Laboratorio de Elementos Programables I 

Escape Room de Hardware 

Duración: 2 horas de clase completas 

 

Nombre(s): 

Ana Nickole Cisneros Herrera 

Leslie Yoselin Sánchez Flores 

Matrícula(s): 

203477 & 201831 

Modalidad: 

☐ Individual     ☐ Pareja 

 

Misión 

Durante el examen recibirán un archivo diagram.json para Wokwi. El circuito contiene algunos errores de conexión que deberán identificar y corregir. El profesor mostrará al inicio una versión funcional del sistema para que conozcan exactamente el comportamiento esperado. 

A partir del circuito, deberán desarrollar y/o corregir el programa en MicroPython, utilizando únicamente los conceptos trabajados hasta este momento: GPIO, entradas con PULL_UP, interrupciones, temporizadores y manejo de eventos. 

Comportamiento que debe tener el sistema 

• Al iniciar, el sistema está BLOQUEADO: LED rojo encendido; amarillo y verde apagados. 

• Al presionar el botón A, el evento debe detectarse mediante una interrupción. El LED amarillo se enciende y comienza una ventana de 5 segundos para presionar B. 

• Si B se presiona correctamente dentro de esos 5 segundos, se concede el acceso: LED verde encendido durante 3 segundos. Después, el sistema debe regresar automáticamente al estado BLOQUEADO. 

• Si se presiona B antes que A, se registra un intento fallido y el sistema vuelve al estado BLOQUEADO. 

• Si se presiona A pero B no se presiona dentro de 5 segundos, ocurre TIMEOUT, se registra un intento fallido y el sistema vuelve al estado BLOQUEADO. 

• Después de 3 intentos fallidos, el sistema entra en BLOQUEO DE SEGURIDAD durante 10 segundos. Durante ese tiempo los botones no deben modificar el funcionamiento. Al terminar, el contador de fallos vuelve a cero. 

• Mientras se espera B, una nueva detección de A no debe cancelar ni reiniciar incorrectamente la secuencia. 

• Mientras el acceso está concedido o durante el bloqueo de seguridad, las pulsaciones que no correspondan deben ser ignoradas. 

• El programa debe incluir protección contra rebote o eventos repetidos para evitar que una sola pulsación sea interpretada varias veces. 

Requisitos obligatorios 

• MicroPython. 

• Botón A en GP16 y botón B en GP17, ambos con PULL_UP. 

• LED rojo en GP13, LED amarillo en GP14 y LED verde en GP15. 

• Los botones deben generar los eventos mediante interrupciones; no se aceptará polling como método principal de detección. 

• Los tiempos de 5 s, 3 s y 10 s deben resolverse mediante temporizadores sin bloquear innecesariamente el programa. 

• Primero deberá funcionar en Wokwi y después deberá demostrarse el funcionamiento en la Raspberry Pi Pico física. 

Referencia visual del funcionamiento correcto 

El profesor ejecutará el sistema correcto antes de iniciar el examen. Las siguientes imágenes pueden utilizarse como referencia del resultado esperado: 

 
 
 
 

 

 

 

 

 

Entrega y demostración 

El examen debe completarse dentro de las 2 horas de clase. Al finalizar, cada alumno o equipo deberá: 

• Entregar el archivo main.py final. 

• Entregar el diagram.json corregido. 

• Entregar el enlace o proyecto de Wokwi funcionando. 

• Mostrar en vivo el funcionamiento completo del sistema y cada uno de los casos indicados. 

• Mostrar también el montaje físico funcionando en la Raspberry Pi Pico. 

• Ser capaz de explicar brevemente qué errores encontró y cómo los corrigió. 

La entrega de archivos no sustituye la demostración en vivo. El sistema debe ejecutarse correctamente durante la evaluación. 
