# Emulador plc mfc Python
Este código sirve para levantar un emulador que permita hacer pruebas en mfc al conectarlo con los módulos de SGA

## Que hace
El programa, al ejecutarse, levanta un servidor web en el  puerto 50001 y crea un hilo para cada conexión socket necesaria.
La idea es ejecutarlo en el mismo srv en el que esté el módulo en preproducción, o ejecutarlo en un servidor de preproducción al que se tenga acceso desde OCP para poder realizar pruebas.
Permite emular varios plcs en el mismo programa, de diferentes proveedores.
Cada socket permite al módulo conectarse y mantiene esa conexión enviando los acks y kal necesarios.
Permite enviar 4 tipos de mensaje predefinido:
DR - > petición de destino por parte del plc
DR con peso y medidas -> petición de destino por parte del plc informado de peso y medidas
TR -> Destino alcanzado
KAL -> keep alive, para pruebas.
Ahora mismo sólo funciona con Aberle, Commander y dft.

## Que NO hace
No comprueba la gramática de los mensajes, no comprueba si llegan o no keepalives, sólo manda y recibe mensajería, no utiliza la biblioteca de ITX.

## Cómo funciona
Copiarlo a una carpeta en el srv de pre (dentro de soporteSGA?), hace falta instalar algunas librerías, como no tenemos permiso para hacerlo system wide hay un script main/libs(/installlibs.sh) que instalará lo necesario en la carpeta libs.
Ya podemos ir a main/ y editar config.xml con los datos de nuestro[s] plc[s].  Se puede añadir tantos plcs como sea necesario.
Una vez configurado, desde main, podemos arrancar con start.sh, para parar, usaremos stop.sh, los logs se registran en main/logs.
una vez arrancado, podremos acceder a la interfaz web desde http://<dirección del srv de pre>:50001

## Desarrollos futuros
La idea original era poder emular todo el mfc de una instalación, pasándole al programa un mapa de las posiciones y sus conexiones y permitiendo que los escáneres enviasen autónomamente mensajes según la matrícula pasada va avanzando por el sistema.
La primera fase era conseguir la funcionalidad de enviar / recibir en, al menos, 4 protocolos, aberle, dft, commander y tim, pero no ha sido posible aún, por tanto hago público el código para quien pueda encontrarlo útil.

## Autoría
Rodrigo Santos Gallego, T-Systems ,para Inditex, 2025/2026
