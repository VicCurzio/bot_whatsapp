"""
Lectura del Excel de contactos, con openpyxl y nada mas.

Por que existe: antes esto lo hacia pandas. Pandas es una libreria de analisis
de datos de ~50 MB que se traia numpy adentro, para leer una columna de
telefonos de una planilla. Openpyxl ya estaba instalado igual, porque es lo que
pandas usa por abajo para abrir un .xlsx: se saco el intermediario.

Lo que cambia en concreto: cuando esto se empaquete con PyInstaller, sacar
pandas es la diferencia entre un ejecutable de cientos de megas y uno chico.

La estructura que devuelve es a proposito la mas simple que sirve: un diccionario
de nombre de pestana a `Hoja`, y cada fila es un diccionario de columna a valor.
No hace falta nada mas: el bot lee una columna y recorre filas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openpyxl import load_workbook

# La primera fila del Excel son los titulos, asi que los datos arrancan en la 2.
# Se guarda el numero real de fila para que el registro de envios diga en que
# linea de la planilla estaba cada contacto.
PRIMERA_FILA_DE_DATOS = 2


def _limpiar(valor: Any) -> Any:
    """Normaliza lo que devuelve openpyxl antes de que lo vea el resto del bot.

    El caso que importa: Excel guarda un telefono sin formato como numero, y
    openpyxl lo entrega como float. `str(1123456789.0)` termina en '.0', y al
    quedarse con los digitos aparece un cero de mas al final: un numero
    equivocado, al que se le manda el mensaje igual. Los enteros disfrazados de
    float se convierten antes de que eso pase.
    """
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    if isinstance(valor, str):
        limpio = valor.strip()
        return limpio or None
    return valor


@dataclass
class Hoja:
    """Una pestana del Excel, ya leida."""

    nombre: str
    columnas: list[str] = field(default_factory=list)
    # Cada fila: {titulo de columna: valor}. Las columnas que faltan valen None.
    filas: list[dict[str, Any]] = field(default_factory=list)

    def tiene(self, columna: str) -> bool:
        return columna in self.columnas

    def numeradas(self):
        """Las filas con su numero real de fila en la planilla."""
        return enumerate(self.filas, start=PRIMERA_FILA_DE_DATOS)

    def primera_columna_distinta_de(self, columna: str) -> str | None:
        """Sirve para mostrar el nombre del contacto al lado del telefono."""
        for titulo in self.columnas:
            if titulo != columna:
                return titulo
        return None


def leer_excel(ruta: str) -> dict[str, Hoja]:
    """Lee todas las pestanas de un .xlsx.

    `read_only` evita cargar la planilla entera en memoria y `data_only` trae el
    ultimo valor calculado de las formulas en vez de la formula.
    """
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        hojas: dict[str, Hoja] = {}

        for pestana in libro.worksheets:
            iterador = pestana.iter_rows(values_only=True)

            encabezado = next(iterador, None)
            if encabezado is None:
                hojas[pestana.title] = Hoja(nombre=pestana.title)
                continue

            columnas = [
                str(titulo).strip() if titulo is not None else f"columna_{i + 1}"
                for i, titulo in enumerate(encabezado)
            ]

            filas: list[dict[str, Any]] = []
            for valores in iterador:
                # Una fila totalmente vacia no es un contacto: Excel las deja
                # al final de cualquier planilla que se edito alguna vez.
                if all(valor is None for valor in valores):
                    continue
                fila = {columna: None for columna in columnas}
                for columna, valor in zip(columnas, valores):
                    fila[columna] = _limpiar(valor)
                filas.append(fila)

            hojas[pestana.title] = Hoja(nombre=pestana.title, columnas=columnas, filas=filas)

        return hojas
    finally:
        # En modo read_only el archivo queda abierto hasta que se cierra a mano.
        libro.close()
