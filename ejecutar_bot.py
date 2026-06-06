import pywhatkit as kit
import pandas as pd
import time
import random
import os
import re

# Configuración de carpeta
abspath = os.path.abspath(__file__)
os.chdir(os.path.dirname(abspath))

archivo = "contactos.xlsx"
columna_buscada = "Tel"

# Tu mensaje
mensaje_plantilla = """Hola, ¿cómo estás? 👋
Escribí acá tu mensaje personalizado."""

def limpiar_numero(num):
    # Deja solo los dígitos
    limpio = re.sub(r'\D', '', str(num))
    
    # Si el número es válido (ej. 549...)
    if len(limpio) >= 10:
        if limpio.startswith('0'): limpio = limpio[1:] # Quita 0 inicial
        if not limpio.startswith('54'):
            limpio = '549' + limpio
        return "+" + limpio
    return None

try:
    # Leemos todas las pestañas
    excel_completo = pd.read_excel(archivo, sheet_name=None)
    print("✅ Excel cargado correctamente.")
except Exception as e:
    print(f"❌ Error al cargar Excel: {e}")
    exit()

print("🚀 El bot comenzará en 10 segundos. ¡Asegúrate de tener WhatsApp Web abierto!")
time.sleep(10)

for pestana, df in excel_completo.items():
    if columna_buscada in df.columns:
        print(f"--- Procesando pestaña: {pestana} ---")
        for i, fila in df.iterrows():
            tel_original = fila[columna_buscada]
            numero = limpiar_numero(tel_original)
            
            if not numero or "mandar" in str(tel_original).lower():
                continue

            print(f"➡️ Enviando a: {numero}")
            
            try:
                # wait_time en 25 para dar tiempo a que cargue bien el chat
                kit.sendwhatmsg_instantly(numero, mensaje_plantilla, wait_time=25, tab_close=True)
                
                # Intervalo aleatorio para parecer humano (45-80 segundos)
                espera = random.randint(25, 40)
                print(f"✅ Mensaje enviado. Esperando {espera}s...")
                time.sleep(espera)
            except Exception as e:
                print(f"❌ Error con {numero}: {e}")
    else:
        print(f"⚠️ Pestaña '{pestana}' saltada (no tiene columna '{columna_buscada}')")

print("🏁 ¡Tarea completada!")