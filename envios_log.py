"""
Registro de envios, una fila por contacto y un archivo por tanda.

El problema que resuelve: el bot manda mensajes de a uno, despacio, durante
horas. Si se corta a mitad -- se cierra WhatsApp Web, se corta internet, se
apaga la maquina -- no queda ninguna forma de saber a quien le llego y a quien
no. La consola se pierde al cerrar la ventana, y volver a mandarle a todos es
peor que no mandar.

Cada corrida abre un archivo CSV propio, identificado por la fecha y hora de
arranque. Cada linea se escribe y se baja a disco en el momento, no al final:
si el proceso muere, lo ya escrito sigue estando.

Uso:

    registro = RegistroDeTanda(origen="contactos.xlsx")
    registro.enviado("+5492211234567", pestana="Hoja1", fila=3)
    registro.fallido("+5492217654321", "no existe el chat", pestana="Hoja1", fila=4)
    print(registro.resumen())
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

# Al lado del estado de version (~/.bot_whatsapp), no en la carpeta del
# programa: sobrevive a reinstalar o mover el bot.
CARPETA_REGISTROS = Path.home() / ".bot_whatsapp" / "envios"

COLUMNAS = ["id_tanda", "fecha_hora", "origen", "pestana", "fila", "numero", "estado", "detalle"]

# Estados posibles de un contacto dentro de una tanda.
ENVIADO = "enviado"
FALLIDO = "fallido"
SALTEADO = "salteado"


def _ahora() -> str:
    """Fecha y hora con la diferencia horaria incluida (ISO 8601).

    Con la zona escrita, el dato sigue siendo interpretable si el archivo se
    lee desde otra maquina o despues de un cambio de horario.
    """
    return datetime.now().astimezone().isoformat(timespec="seconds")


class RegistroDeTanda:
    """Una tanda de envios y su archivo CSV."""

    def __init__(self, origen: str = "", carpeta: Path | None = None) -> None:
        self.id_tanda = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.origen = Path(origen).name if origen else ""
        self.enviados = 0
        self.fallidos = 0
        self.salteados = 0

        carpeta = carpeta or CARPETA_REGISTROS
        self.ruta: Path | None = None
        self._archivo = None
        self._csv = None

        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            self.ruta = carpeta / f"{self.id_tanda}.csv"
            self._archivo = self.ruta.open("w", encoding="utf-8-sig", newline="")
            self._csv = csv.writer(self._archivo)
            self._csv.writerow(COLUMNAS)
            self._archivo.flush()
        except OSError:
            # No poder escribir el registro no puede impedir el envio: se pierde
            # la trazabilidad, pero el trabajo se hace igual.
            self.ruta = None
            self._archivo = None
            self._csv = None

    # -- escritura -----------------------------------------------------------

    def _anotar(self, numero, estado: str, detalle: str = "", pestana: str = "", fila=None) -> None:
        if estado == ENVIADO:
            self.enviados += 1
        elif estado == FALLIDO:
            self.fallidos += 1
        else:
            self.salteados += 1

        if self._csv is None or self._archivo is None:
            return

        try:
            self._csv.writerow(
                [
                    self.id_tanda,
                    _ahora(),
                    self.origen,
                    pestana,
                    "" if fila is None else fila,
                    numero,
                    estado,
                    detalle,
                ]
            )
            # Bajar a disco en el momento: si el proceso muere, lo escrito queda.
            self._archivo.flush()
        except (OSError, ValueError):
            pass

    def enviado(self, numero, pestana: str = "", fila=None) -> None:
        self._anotar(numero, ENVIADO, "", pestana, fila)

    def fallido(self, numero, error, pestana: str = "", fila=None) -> None:
        self._anotar(numero, FALLIDO, str(error), pestana, fila)

    def salteado(self, numero, motivo: str, pestana: str = "", fila=None) -> None:
        self._anotar(numero, SALTEADO, motivo, pestana, fila)

    def cerrar(self) -> None:
        if self._archivo is not None:
            try:
                self._archivo.close()
            except OSError:
                pass
            self._archivo = None
            self._csv = None

    # -- lectura -------------------------------------------------------------

    def resumen(self) -> str:
        partes = [f"Tanda {self.id_tanda}: {self.enviados} enviados"]
        if self.fallidos:
            partes.append(f"{self.fallidos} con error")
        if self.salteados:
            partes.append(f"{self.salteados} salteados")
        texto = ", ".join(partes)
        if self.ruta is not None:
            texto += f"\nRegistro: {self.ruta}"
        return texto

    def __enter__(self) -> "RegistroDeTanda":
        return self

    def __exit__(self, *_) -> None:
        self.cerrar()
