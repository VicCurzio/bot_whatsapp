# Changelog

Todos los cambios del Bot de WhatsApp, contados para quien lo usa.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
las versiones siguen [SemVer](https://semver.org/lang/es/).

Lo que esta en `Sin publicar` se muestra recien cuando se corre
`python scripts/release.py`.

## [Sin publicar]

### Agregado

- Registro de envios: cada tanda deja un archivo con a quien se le mando, a que hora y que paso con cada numero. Si el envio se corta a la mitad, queda escrito hasta donde llego.
- Al terminar (o al cortarse), el bot muestra el resumen de la tanda y donde quedo el archivo.

### Cambiado

- El bot se instala con `pip install -e .` y las dependencias quedan con version fija, para que funcione igual en otra maquina.
- El Excel se lee directamente con openpyxl. Se saco pandas, que eran ~50 MB de libreria de analisis de datos para leer una columna de telefonos: el bot arranca mas rapido y el dia que se empaquete como .exe va a pesar mucho menos.

### Arreglado

- Un telefono guardado como numero en el Excel podia terminar con un cero de mas y el mensaje se mandaba a un numero equivocado.
- Los telefonos escritos en formato local con 15 ("221 15 5424585") se mandaban a otro numero. Ahora se rechazan y quedan anotados en el registro de la tanda para corregirlos en la planilla.

## [1.0.0] - 2026-08-07

### Agregado

- Ventana de novedades: al abrir el bot despues de una actualizacion, cuenta que cambio.
- Boton "Novedades" y numero de version visibles en la ventana principal.
- `python ejecutar_bot.py --version` muestra la version, y `--novedades` el historial completo.

### Arreglado

- La ventana no abria: faltaba cerrar un parentesis en el editor de mensajes.

### Cambiado

- Se sacaron los emojis de la interfaz y de los mensajes de la consola.

## [0.9.0] - 2026-08-05

### Agregado

- Interfaz de escritorio: cargar Excel, elegir pestana y columna, editar el mensaje y ver el registro de envio.
- Envio con esperas al azar entre mensajes para no parecer automatico.
- Boton de detener sin cerrar el programa.
- Version por consola (`ejecutar_bot.py`) para el envio directo.
