# Receta de PyInstaller para generar el .exe.
#
# Para que sirve: que el cliente use el bot sin instalar Python ni dependencias.
# Se corre con
#
#     py -m PyInstaller bot_whatsapp.spec
#
# y deja `dist/Bot WhatsApp.exe`.
#
# Dos cosas que hay que hacer a mano y son las que rompen el empaquetado si
# faltan:
#
# 1. **customtkinter viaja con archivos propios** (temas y assets .json). No son
#    codigo, asi que PyInstaller no los ve siguiendo los imports: hay que
#    copiarlos explicitamente con collect_data_files.
# 2. **CHANGELOG.md se lee en tiempo de ejecucion** para la ventana de
#    novedades (ver version.py). Sin el, la ventana queda vacia y nadie se
#    entera de que cambio.
#
# El peso: sin pandas, el ejecutable ronda las decenas de megas en vez de
# cientos. Es la razon por la que se saco.

from PyInstaller.utils.hooks import collect_data_files

datos = [
    # El changelog, al lado de los modulos: version.py lo busca junto a si mismo.
    ('CHANGELOG.md', '.'),
]
datos += collect_data_files('customtkinter')

analisis = Analysis(
    ['bot_gui.py'],
    pathex=[],
    binaries=[],
    datas=datos,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Lo que no se usa y pesa. Si algun dia falla por un import faltante,
    # sacar de esta lista antes que agregar dependencias.
    excludes=['pandas', 'numpy', 'matplotlib', 'pytest'],
    noarchive=False,
)

pyz = PYZ(analisis.pure)

exe = EXE(
    pyz,
    analisis.scripts,
    analisis.binaries,
    analisis.datas,
    [],
    name='Bot WhatsApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Sin consola: es una aplicacion de ventana. Si hay que depurar el
    # arranque, poner console=True temporalmente y ejecutar desde una terminal.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
