"""
Tests de la normalizacion de telefonos.

Es la unica parte del bot que se puede probar sin abrir un navegador, y la mas
importante: un numero mal normalizado no falla, manda el mensaje a otra persona.
"""

from numeros import esta_marcado_para_saltear, normalizar_numero, solo_digitos


class TestNormalizarNumero:
    def test_numero_ya_completo_se_deja_igual(self):
        assert normalizar_numero("5492215424585") == "+5492215424585"

    def test_saca_espacios_guiones_y_simbolos(self):
        assert normalizar_numero("+54 9 2215 42-4585") == "+5492215424585"

    def test_agrega_el_codigo_de_pais_y_el_nueve(self):
        assert normalizar_numero("2215424585") == "+5492215424585"

    def test_saca_el_cero_de_la_caracteristica(self):
        assert normalizar_numero("02215424585") == "+5492215424585"

    def test_numero_de_capital(self):
        assert normalizar_numero("11 2345-6789") == "+5491123456789"


class TestLoQueSeRechaza:
    def test_celda_vacia(self):
        assert normalizar_numero("") is None
        assert normalizar_numero(None) is None

    def test_texto_sin_digitos(self):
        assert normalizar_numero("sin telefono") is None

    def test_demasiado_corto(self):
        assert normalizar_numero("123456") is None

    def test_telefono_guardado_como_numero_con_decimal(self):
        """El caso que mandaba el mensaje a otro numero.

        Excel guarda un telefono sin formato como numero y openpyxl lo entrega
        como float: str(1123456789.0) termina en '.0' y al quedarse con los
        digitos aparece un cero de mas al final.
        """
        assert normalizar_numero(1123456789.0) is None

    def test_formato_local_con_15_no_se_adivina(self):
        """'221 15 5424585' se rechaza en vez de mandarlo a otra persona.

        Sacar el 15 bien requiere saber cuantos digitos tiene la caracteristica,
        que en Argentina varia entre 2 y 4. Adivinar es peor que rechazar: el
        numero queda anotado en el registro y se corrige en la planilla.
        """
        assert normalizar_numero("221 15 5424585") is None


class TestAyudantes:
    def test_solo_digitos(self):
        assert solo_digitos("+54 (221) 542-4585") == "542215424585"
        assert solo_digitos(None) == ""

    def test_marca_para_saltear(self):
        assert esta_marcado_para_saltear("mandar") is True
        assert esta_marcado_para_saltear("MANDAR mañana") is True
        assert esta_marcado_para_saltear("2215424585") is False
