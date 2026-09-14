import sys
import pywhatkit as kit
import time
import random
import os

from contactos import leer_excel
from envios_log import RegistroDeTanda
from numeros import esta_marcado_para_saltear, normalizar_numero
from version import __version__, format_releases, get_releases, pending_notes, write_last_seen

# Configuración de carpeta
abspath = os.path.abspath(__file__)
os.chdir(os.path.dirname(abspath))

archivo = "contactos.xlsx"
columna_buscada = "Tel"

# Tu mensaje
mensaje_plantilla = """Hola, ¿cómo estás?
Escribí acá tu mensaje personalizado."""


def manejar_flags():
    """--version y --novedades salen sin enviar nada."""
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"Bot WhatsApp v{__version__}")
        sys.exit(0)

    if "--novedades" in sys.argv:
        releases = get_releases()
        print(format_releases(releases) if releases else "Todavía no hay novedades registradas.")
        write_last_seen()
        sys.exit(0)


manejar_flags()

# Si el bot se actualizó desde la última corrida, contar qué cambió.
notas = pending_notes()
if notas:
    print("=" * 60)
    print(f"NOVEDADES DE LA VERSION {__version__}")
    print("=" * 60)
    print(notas)
    print("=" * 60)
    print()
write_last_seen()

try:
    # Leemos todas las pestañas
    excel_completo = leer_excel(archivo)
    print("Excel cargado correctamente.")
except Exception as e:
    print(f"Error al cargar Excel: {e}")
    exit()

print("El bot comenzará en 10 segundos. Asegurate de tener WhatsApp Web abierto.")
time.sleep(10)

# Una tanda, un archivo. Si esto se corta a la mitad, el registro dice hasta
# donde llego: sin eso, la unica opcion es volver a mandarle a todos.
registro = RegistroDeTanda(origen=archivo)
if registro.ruta:
    print(f"Registro de la tanda: {registro.ruta}")

try:
    for pestana, hoja in excel_completo.items():
        if hoja.tiene(columna_buscada):
            print(f"--- Procesando pestaña: {pestana} ---")
            for i, fila in hoja.numeradas():
                tel_original = fila[columna_buscada]
                numero = normalizar_numero(tel_original)

                if not numero:
                    registro.salteado(tel_original, "numero invalido", pestana, i)
                    continue

                if esta_marcado_para_saltear(tel_original):
                    registro.salteado(tel_original, "marcado como 'mandar'", pestana, i)
                    continue

                print(f"Enviando a: {numero}")

                try:
                    # wait_time en 25 para dar tiempo a que cargue bien el chat
                    kit.sendwhatmsg_instantly(numero, mensaje_plantilla, wait_time=25, tab_close=True)
                    registro.enviado(numero, pestana, i)

                    # Intervalo aleatorio para parecer humano
                    espera = random.randint(25, 40)
                    print(f"Mensaje enviado. Esperando {espera}s...")
                    time.sleep(espera)
                except Exception as e:
                    registro.fallido(numero, e, pestana, i)
                    print(f"Error con {numero}: {e}")
        else:
            print(f"Pestaña '{pestana}' saltada (no tiene columna '{columna_buscada}')")

    print("Tarea completada.")
finally:
    # Tambien con Ctrl+C: el resumen y la ruta del registro son justo lo que hace
    # falta cuando la tanda se corta.
    print(registro.resumen())
    registro.cerrar()
