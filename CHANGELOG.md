# Changelog

Todos los cambios del Bot de WhatsApp, contados para quien lo usa.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
las versiones siguen [SemVer](https://semver.org/lang/es/).

Lo que esta en `Sin publicar` se muestra recien cuando se corre
`python scripts/release.py`.

## [Sin publicar]

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
