"""
Normalizacion de telefonos argentinos al formato que espera WhatsApp.

Por que existe: esta funcion estaba escrita dos veces, una en la ventana y otra
en la version de consola, con el mismo cuerpo copiado. Duplicada, cualquier
arreglo se aplicaba en un lado y no en el otro. Ademas es la unica parte del bot
que se puede probar sin abrir un navegador, asi que separarla es lo que permite
tener tests de verdad.

Lo que hace, en orden:

1. Se queda solo con los digitos.
2. Saca el 0 inicial de la caracteristica (0221 -> 221).
3. Si no empieza con 54, antepone 549 (Argentina, movil).
4. Rechaza lo que no tenga largo plausible.

Lo que NO hace, a proposito: sacar el 15 de los numeros escritos en formato
local ("221 15 5424585"). Para hacerlo bien hay que saber cuantos digitos tiene
la caracteristica, que en Argentina varia entre 2 y 4, y adivinarlo manda el
mensaje a otra persona. Esos numeros se rechazan y quedan anotados en el
registro de la tanda, que es lo que permite corregirlos en la planilla.
"""

from __future__ import annotations

import re

# Un numero argentino completo es 549 + caracteristica (2 a 4) + abonado (6 a 8):
# entre 12 y 13 digitos, nunca mas.
#
# El tope no es decoracion. Un telefono guardado como numero en el Excel llega
# como 1123456789.0, y quedarse con los digitos suma un cero al final: 14
# digitos y un destinatario equivocado. `contactos.py` ya lo corrige al leer;
# esto es la segunda red, por si el numero entra por otro lado.
LARGO_MINIMO = 12
LARGO_MAXIMO = 13

# Lo que se escribe en la columna del telefono para saltear una fila a proposito.
MARCA_SALTEAR = "mandar"


def solo_digitos(valor: object) -> str:
    """Los digitos de lo que sea que haya en la celda."""
    return re.sub(r"\D", "", str(valor))


def esta_marcado_para_saltear(valor: object) -> bool:
    """La fila se saltea si en el telefono dice 'mandar'."""
    return MARCA_SALTEAR in str(valor).lower()


def normalizar_numero(valor: object) -> str | None:
    """Devuelve el numero en formato internacional, o None si no sirve.

    None significa "no le mandes a este": puede ser una celda vacia, un texto,
    o un numero con un largo que no cierra. Quien llama lo anota como salteado.
    """
    limpio = solo_digitos(valor)

    if len(limpio) < 10:
        return None

    # 0221 4241234 -> 221 4241234. El 0 es para llamar desde adentro del pais.
    if limpio.startswith("0"):
        limpio = limpio[1:]

    if not limpio.startswith("54"):
        limpio = "549" + limpio

    if not (LARGO_MINIMO <= len(limpio) <= LARGO_MAXIMO):
        return None

    return "+" + limpio
