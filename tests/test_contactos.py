"""
Tests de la lectura del Excel.

Se arma una planilla de verdad en un archivo temporal: es la unica forma de
probar que openpyxl devuelve lo que el bot espera.
"""

from openpyxl import Workbook

from contactos import PRIMERA_FILA_DE_DATOS, leer_excel


def _planilla(tmp_path, filas, titulos=("Nombre", "Tel"), hoja="Contactos"):
    libro = Workbook()
    ws = libro.active
    ws.title = hoja
    ws.append(list(titulos))
    for fila in filas:
        ws.append(list(fila))
    ruta = tmp_path / "contactos.xlsx"
    libro.save(ruta)
    return str(ruta)


class TestLeerExcel:
    def test_lee_titulos_y_filas(self, tmp_path):
        ruta = _planilla(tmp_path, [("Juan", "2215424585"), ("Maria", "1123456789")])

        hojas = leer_excel(ruta)

        assert list(hojas) == ["Contactos"]
        hoja = hojas["Contactos"]
        assert hoja.columnas == ["Nombre", "Tel"]
        assert len(hoja.filas) == 2
        assert hoja.filas[0]["Nombre"] == "Juan"

    def test_numera_las_filas_como_el_excel(self, tmp_path):
        """La fila 2 de la planilla es la primera con datos: la 1 son titulos."""
        ruta = _planilla(tmp_path, [("Juan", "2215424585")])

        hoja = leer_excel(ruta)["Contactos"]
        numeros = [n for n, _ in hoja.numeradas()]

        assert numeros == [PRIMERA_FILA_DE_DATOS]

    def test_convierte_los_telefonos_guardados_como_numero(self, tmp_path):
        """Sin esto, str(1123456789.0) suma un cero y el mensaje va a otro lado."""
        ruta = _planilla(tmp_path, [("Juan", 1123456789)])

        hoja = leer_excel(ruta)["Contactos"]

        assert hoja.filas[0]["Tel"] == 1123456789
        assert str(hoja.filas[0]["Tel"]) == "1123456789"

    def test_ignora_las_filas_vacias_del_final(self, tmp_path):
        ruta = _planilla(tmp_path, [("Juan", "2215424585"), (None, None), (None, None)])

        hoja = leer_excel(ruta)["Contactos"]

        assert len(hoja.filas) == 1

    def test_tiene_dice_si_esta_la_columna(self, tmp_path):
        ruta = _planilla(tmp_path, [("Juan", "2215424585")])

        hoja = leer_excel(ruta)["Contactos"]

        assert hoja.tiene("Tel") is True
        assert hoja.tiene("Telefono") is False

    def test_la_columna_del_nombre_es_la_primera_que_no_es_el_telefono(self, tmp_path):
        ruta = _planilla(tmp_path, [("Juan", "2215424585")])

        hoja = leer_excel(ruta)["Contactos"]

        assert hoja.primera_columna_distinta_de("Tel") == "Nombre"
