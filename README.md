# Bot de WhatsApp

[![CI](https://github.com/VicCurzio/bot_whatsapp/actions/workflows/ci.yml/badge.svg)](https://github.com/VicCurzio/bot_whatsapp/actions/workflows/ci.yml)

Envía un mensaje de WhatsApp a una lista de contactos tomada de un Excel. Tiene
una ventana con interfaz gráfica y una versión de consola. Funciona sobre
WhatsApp Web: abre cada chat, escribe y manda.

## Requisitos

| | |
|---|---|
| Python | 3.11 o superior |
| Navegador | Google Chrome instalado |
| Cuenta | WhatsApp Web ya vinculado con el QR |

## Puesta en marcha (local, en cinco minutos)

```bash
git clone https://github.com/VicCurzio/bot_whatsapp.git
cd bot_whatsapp
py -m pip install -e .
py bot_gui.py
```

`pip install -e .` lee `pyproject.toml`, que fija las versiones exactas de las
dependencias. Es lo que hace que el bot funcione igual en otra máquina y no
"según lo que tuviera instalado".

## El archivo de contactos

Un Excel con una columna de teléfonos (por defecto se busca `Tel`). Los números
se normalizan solos al formato internacional argentino.

| Nombre | Tel |
|--------|-----|
| Juan   | 1123456789 |
| María  | 5491134567890 |

Una fila cuyo teléfono contenga la palabra "mandar" se saltea a propósito.

La lectura la hace `contactos.py` con openpyxl. Si el teléfono está guardado
como número en vez de texto, se normaliza antes de usarlo: un `1123456789`
numérico llega como `1123456789.0` y, al quedarse con los dígitos, aparecía un
cero de más al final. Es decir, se le mandaba el mensaje a otro número.

## Cómo se usa

### Con interfaz gráfica

```bash
py bot_gui.py
```

1. Cargar el Excel (**Buscar** y después **Cargar**).
2. Elegir la pestaña y la columna de teléfonos.
3. Escribir el mensaje.
4. Ajustar los tiempos de espera si hace falta.
5. **Iniciar envío**, con WhatsApp Web abierto y visible en el navegador.

| Parámetro | Qué hace | Por defecto |
|---|---|---|
| Espera inicio | Segundos antes de empezar | 10 |
| Espera carga | Tiempo para que cargue el chat | 25 |
| Delay min / max | Pausa entre mensajes, al azar dentro del rango | 25 / 40 |

La pausa al azar entre mensajes no es un detalle: mandar a intervalo fijo es el
patrón más fácil de detectar como automatizado.

### Por consola

```bash
py ejecutar_bot.py              # usa contactos.xlsx de la misma carpeta
py ejecutar_bot.py --version
py ejecutar_bot.py --novedades
```

Las variables del envío se editan al principio de `ejecutar_bot.py`: `archivo`,
`columna_buscada` y `mensaje_plantilla`.

## Registro de envíos

Cada corrida abre su propio archivo CSV en:

```text
C:\Users\<usuario>\.bot_whatsapp\envios\AAAAMMDD-HHMMSS.csv
```

Una fila por contacto, con la hora, el número, el estado (`enviado`, `fallido`,
`salteado`) y el detalle del error si lo hubo. Cada línea se baja a disco en el
momento, no al final.

Existe por un motivo concreto: el bot manda de a uno durante horas y se puede
cortar solo — se cierra WhatsApp Web, se corta internet, se apaga la máquina. Sin
registro no hay forma de saber a quién le llegó, y volver a mandarle a todos es
peor que no mandar. Al terminar (o al cortarse), el bot muestra el resumen y la
ruta del archivo.

## Verificación

```bash
py -m pip install -e ".[dev]"
py -m pytest
```

Cubren lo que se puede romper en silencio: la normalización de teléfonos y la
lectura del Excel. **Un número mal normalizado no falla, le manda el mensaje a
otra persona** — por eso es lo primero que se testeó.

El envío en sí no se puede probar automáticamente: depende de WhatsApp Web y de
un navegador abierto. Eso se prueba a mano, con una lista corta.

## Cómo están separadas las cosas

```text
numeros.py      normaliza teléfonos          <- testeado
contactos.py    lee el Excel con openpyxl    <- testeado
envios_log.py   registro de cada tanda
version.py      versión y novedades
bot_gui.py      la ventana
ejecutar_bot.py la versión de consola
```

La normalización estaba escrita dos veces, una en cada versión, con el mismo
cuerpo copiado: cualquier arreglo se aplicaba en un lado y no en el otro. Ahora
vive en un solo lugar y tiene tests.

**Un número que no se puede normalizar con seguridad se rechaza, no se adivina.**
El caso típico es el formato local con 15 ("221 15 5424585"): sacar ese 15 bien
requiere saber cuántos dígitos tiene la característica, que en Argentina varía
entre 2 y 4. Adivinar manda el mensaje a otra persona. Esos números quedan
anotados como salteados en el registro de la tanda, para corregirlos en la
planilla.

## Advertencias

- El envío masivo puede violar los términos de servicio de WhatsApp. Usar con
  criterio: listas propias, gente que espera el mensaje, volúmenes razonables.
- WhatsApp Web tiene que quedar abierto y visible durante todo el envío.
- No cerrar el navegador mientras corre.

## Entrega y versiones

Versiones semánticas, y `CHANGELOG.md` escrito para quien usa el bot: es lo
mismo que se muestra en la ventana de novedades.

```bash
py scripts/release.py minor --tag
```

La versión vive en `version.py` y `pyproject.toml` la lee de ahí, para que no
haya dos números que puedan quedar distintos.

## Empaquetar como .exe

Para entregarlo a alguien que no tiene Python:

```bash
py -m pip install -e ".[dev]"
py -m PyInstaller bot_whatsapp.spec
```

Queda `dist/Bot WhatsApp.exe`. La receta está en `bot_whatsapp.spec`, con las dos
cosas que hay que copiar a mano o el ejecutable arranca roto: los archivos de
tema de customtkinter y el `CHANGELOG.md`, que se lee en tiempo de ejecución
para la ventana de novedades.
