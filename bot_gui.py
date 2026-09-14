import customtkinter as ctk
from tkinter import filedialog, messagebox
import pywhatkit as kit
import threading
import time
import random
import os

from contactos import leer_excel
from envios_log import RegistroDeTanda
from numeros import esta_marcado_para_saltear, normalizar_numero
from version import __version__, format_releases, get_releases, pending_notes, write_last_seen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class WhatsAppBotGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title(f"Bot WhatsApp v{__version__}")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)

        self.running = False
        self.stop_requested = False
        self.df_contactos = None
        self.archivo_actual = ""

        self._build_ui()

        # Si el bot se actualizo desde la ultima vez, contar que cambio.
        self.root.after(400, self._mostrar_novedades_si_hay)

    def _build_ui(self):
        # Main container
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Title
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        title = ctk.CTkLabel(
            header, text="Bot de WhatsApp",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left", expand=True)

        ctk.CTkButton(
            header, text=f"v{__version__}  ·  Novedades", width=150, height=28,
            fg_color="transparent", border_width=1,
            font=ctk.CTkFont(size=11),
            command=self._mostrar_historial
        ).pack(side="right")

        # Content: left (contacts + config) + right (message + log)
        content = ctk.CTkFrame(main)
        content.pack(fill="both", expand=True)

        content.grid_columnconfigure(0, weight=1, minsize=450)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        right = ctk.CTkFrame(content)
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent):
        # File selection
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(file_frame, text="Archivo Excel:",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        file_row = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_row.pack(fill="x", padx=10, pady=(0, 10))

        self.file_entry = ctk.CTkEntry(file_row, placeholder_text="contactos.xlsx")
        self.file_entry.insert(0, "contactos.xlsx")
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(file_row, text="Buscar", width=90,
                       command=self._seleccionar_archivo).pack(side="left")
        ctk.CTkButton(file_row, text="Cargar", width=90,
                       command=self._cargar_excel).pack(side="left", padx=(5, 0))

        # Sheet selector
        sheet_frame = ctk.CTkFrame(parent)
        sheet_frame.pack(fill="x", pady=(0, 10))

        sheet_row = ctk.CTkFrame(sheet_frame, fg_color="transparent")
        sheet_row.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(sheet_row, text="Pestaña:").pack(side="left", padx=(0, 5))
        self.sheet_var = ctk.StringVar(value="Todas")
        self.sheet_menu = ctk.CTkOptionMenu(sheet_row, variable=self.sheet_var,
                                             values=["Todas"], width=150)
        self.sheet_menu.pack(side="left")

        ctk.CTkLabel(sheet_row, text="Columna Tel:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(15, 5))
        self.col_entry = ctk.CTkEntry(sheet_row, width=80)
        self.col_entry.insert(0, "Tel")
        self.col_entry.pack(side="left")

        # Contact count
        self.contactos_label = ctk.CTkLabel(
            sheet_frame, text="Contactos: 0",
            font=ctk.CTkFont(size=12))
        self.contactos_label.pack(anchor="w", padx=10, pady=(0, 5))

        # Contact table
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(table_frame, text="Vista previa de contactos",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # Scrollable table
        self.table_scroll = ctk.CTkScrollableFrame(table_frame)
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Config at bottom of left panel
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="x")

        ctk.CTkLabel(config_frame, text="Configuración de envío",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        config_grid = ctk.CTkFrame(config_frame, fg_color="transparent")
        config_grid.pack(fill="x", padx=10, pady=(0, 10))
        config_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(config_grid, text="Espera inicio (s):", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.wait_start = ctk.CTkEntry(config_grid, width=70)
        self.wait_start.insert(0, "10")
        self.wait_start.grid(row=1, column=0, sticky="w", padx=(0, 5))

        ctk.CTkLabel(config_grid, text="Espera carga (s):", font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w")
        self.wait_load = ctk.CTkEntry(config_grid, width=70)
        self.wait_load.insert(0, "25")
        self.wait_load.grid(row=1, column=1, sticky="w", padx=(0, 5))

        ctk.CTkLabel(config_grid, text="Delay min (s):", font=ctk.CTkFont(size=11)).grid(row=0, column=2, sticky="w")
        self.delay_min = ctk.CTkEntry(config_grid, width=70)
        self.delay_min.insert(0, "25")
        self.delay_min.grid(row=1, column=2, sticky="w", padx=(0, 5))

        ctk.CTkLabel(config_grid, text="Delay max (s):", font=ctk.CTkFont(size=11)).grid(row=0, column=3, sticky="w")
        self.delay_max = ctk.CTkEntry(config_grid, width=70)
        self.delay_max.insert(0, "40")
        self.delay_max.grid(row=1, column=3, sticky="w")

    def _build_right_panel(self, parent):
        # Message editor
        msg_frame = ctk.CTkFrame(parent)
        msg_frame.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(msg_frame, text="Mensaje a enviar",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.msg_text = ctk.CTkTextbox(msg_frame, wrap="word", font=ctk.CTkFont(size=12))
        self.msg_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.msg_text.insert(
            "1.0",
            "Hola, ¿cómo estás?\nEscribí acá tu mensaje personalizado.",
        )

        # Controls
        ctrl_frame = ctk.CTkFrame(parent)
        ctrl_frame.pack(fill="x", pady=(0, 10))

        ctrl_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(
            ctrl_row, text="INICIAR ENVÍO", fg_color="#2ea043",
            hover_color="#1f7a34", height=40, font=ctk.CTkFont(size=14, weight="bold"),
            command=self._iniciar_envio
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.stop_btn = ctk.CTkButton(
            ctrl_row, text="DETENER", fg_color="#da3633",
            hover_color="#b02625", height=40, font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled", command=self._detener_envio
        )
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Progress
        self.progress_bar = ctk.CTkProgressBar(ctrl_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(ctrl_frame, text="0 / 0", font=ctk.CTkFont(size=12))
        self.progress_label.pack(anchor="e", padx=10, pady=(0, 5))

        # Log
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(log_frame, text="Registro de actividad",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, wrap="word", font=ctk.CTkFont(size=11), state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.root, text="Listo. Carga un archivo Excel para comenzar.",
            font=ctk.CTkFont(size=11), anchor="w",
            fg_color=("#d9d9d9", "#2b2b2b"))
        self.status_bar.pack(side="bottom", fill="x", padx=15, pady=(0, 15), ipady=2)

    # ---- Novedades ----

    def _mostrar_novedades_si_hay(self):
        """Se muestra una sola vez por version, al abrir despues de actualizar."""
        notas = pending_notes()
        write_last_seen()
        if notas:
            self._ventana_notas("Novedades", notas)

    def _mostrar_historial(self):
        releases = get_releases()
        texto = format_releases(releases) if releases else "Todavia no hay novedades registradas."
        self._ventana_notas("Historial de versiones", texto)

    def _ventana_notas(self, titulo, texto):
        ventana = ctk.CTkToplevel(self.root)
        ventana.title(titulo)
        ventana.geometry("620x520")
        ventana.transient(self.root)

        ctk.CTkLabel(
            ventana, text=titulo, font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 4))

        ctk.CTkLabel(
            ventana, text="Esto es lo que cambio en el bot.",
            font=ctk.CTkFont(size=12), text_color=("#555555", "#aaaaaa")
        ).pack(anchor="w", padx=20, pady=(0, 12))

        caja = ctk.CTkTextbox(ventana, wrap="word", font=ctk.CTkFont(size=12))
        caja.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        caja.insert("1.0", texto)
        caja.configure(state="disabled")

        ctk.CTkButton(ventana, text="Entendido", command=ventana.destroy).pack(
            pady=(0, 20)
        )

        # Traer al frente sin robar el foco de forma permanente.
        ventana.after(100, ventana.lift)
        ventana.after(150, ventana.focus)

    # ---- Logic ----

    def _seleccionar_archivo(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos", "*.*")]
        )
        if archivo:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, archivo)
            self._cargar_excel()

    def _cargar_excel(self):
        archivo = self.file_entry.get().strip()
        if not archivo:
            messagebox.showwarning("Sin archivo", "Seleccioná un archivo Excel primero.")
            return

        if not os.path.isabs(archivo):
            archivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo)

        try:
            excel = leer_excel(archivo)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el Excel:\n{e}")
            return

        self.archivo_actual = archivo
        sheets = list(excel.keys())
        self.sheet_menu.configure(values=sheets)
        self.sheet_var.set("Todas")

        self._actualizar_tabla(excel)
        self._log(f"Excel cargado: {os.path.basename(archivo)} ({len(sheets)} pestañas)")
        self._set_status(f"Cargado: {os.path.basename(archivo)}")

    def _actualizar_tabla(self, excel_dict):
        for w in self.table_scroll.winfo_children():
            w.destroy()

        col = self.col_entry.get().strip()
        total = 0

        for sheet_name, hoja in excel_dict.items():
            if hoja.tiene(col):
                validos = sum(1 for f in hoja.filas if normalizar_numero(f[col]))
                total += validos

        self.contactos_label.configure(text=f"Contactos válidos: {total}")
        self._actualizar_progreso(0, total)

        # Show header
        header = ctk.CTkFrame(self.table_scroll, fg_color=("#e0e0e0", "#333333"))
        header.pack(fill="x", pady=(0, 2))

        cols_config = [("Pestaña", 0.2), ("Nombre", 0.35), ("Teléfono", 0.25), ("Estado", 0.2)]
        for c_name, c_w in cols_config:
            lbl = ctk.CTkLabel(header, text=c_name, font=ctk.CTkFont(size=11, weight="bold"))
            lbl.pack(side="left", fill="x", expand=True, padx=2, pady=2)

        for sheet_name, hoja in excel_dict.items():
            if not hoja.tiene(col):
                continue

            # Para mostrar al lado del teléfono: la primera columna que no sea
            # la de teléfonos, que en la práctica es la del nombre.
            columna_nombre = hoja.primera_columna_distinta_de(col)

            for row in hoja.filas:
                num = normalizar_numero(row[col])
                if not num:
                    continue

                row_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=1)

                name_col = row[columna_nombre] if columna_nombre else None
                name_str = str(name_col) if name_col is not None else ""

                vals = [sheet_name, name_str[:30], num, "Pendiente"]
                for v in vals:
                    lbl = ctk.CTkLabel(row_frame, text=v, font=ctk.CTkFont(size=10))
                    lbl.pack(side="left", fill="x", expand=True, padx=2)

    def _iniciar_envio(self):
        if not self.archivo_actual:
            messagebox.showwarning("Sin datos", "Cargá un archivo Excel primero.")
            return

        self.running = True
        self.stop_requested = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._log("Envío iniciado...")
        self._set_status("Enviando mensajes...")

        threading.Thread(target=self._ejecutar_bot, daemon=True).start()

    def _detener_envio(self):
        self.stop_requested = True
        self._log("Deteniendo envío... (esperá al mensaje actual)")
        self._set_status("Deteniendo...")

    def _ejecutar_bot(self):
        registro = None
        try:
            col = self.col_entry.get().strip()
            wait_start = int(self.wait_start.get())
            wait_load = int(self.wait_load.get())
            d_min = int(self.delay_min.get())
            d_max = int(self.delay_max.get())
            mensaje = self.msg_text.get("1.0", "end-1c")

            excel = leer_excel(self.archivo_actual)

            total = sum(
                sum(1 for f in hoja.filas if normalizar_numero(f[col]))
                for hoja in excel.values() if hoja.tiene(col)
            )
            enviados = 0

            # Una tanda, un archivo. Si esto se corta a la mitad -- se cierra
            # WhatsApp Web, se corta internet -- el registro dice hasta donde
            # llego. El log de la ventana se pierde al cerrarla.
            registro = RegistroDeTanda(origen=self.archivo_actual)
            if registro.ruta:
                self.root.after(0, self._log, f"Registro de la tanda: {registro.ruta}")

            self.root.after(0, self.progress_bar.set, 0)
            self.root.after(0, self._actualizar_progreso, 0, total)
            self.root.after(0, lambda: self._log(f"Total a enviar: {total} mensajes"))
            self.root.after(0, lambda: self._log(f"Arrancando en {wait_start}s..."))

            time.sleep(wait_start)

            for sheet_name, hoja in excel.items():
                if not hoja.tiene(col) or self.stop_requested:
                    continue

                for row in hoja.filas:
                    if self.stop_requested:
                        self._log("Envío detenido por el usuario.")
                        break

                    tel_original = row[col]
                    numero = normalizar_numero(tel_original)
                    if not numero:
                        registro.salteado(tel_original, "numero invalido", sheet_name)
                        continue

                    if esta_marcado_para_saltear(tel_original):
                        registro.salteado(tel_original, "marcado como 'mandar'", sheet_name)
                        continue

                    try:
                        kit.sendwhatmsg_instantly(
                            numero, mensaje,
                            wait_time=wait_load, tab_close=True
                        )
                        registro.enviado(numero, sheet_name)
                        enviados += 1
                        self.root.after(0, self._log, f"[{enviados}/{total}] Enviado a {numero}")
                        self.root.after(0, self.progress_bar.set, enviados / total)
                        self.root.after(0, self._actualizar_progreso, enviados, total)
                        self.root.after(0, self._set_status,
                                        f"Enviado {enviados}/{total} - {numero}")

                        if enviados < total and not self.stop_requested:
                            espera = random.randint(d_min, d_max)
                            self.root.after(0, self._log, f"Esperando {espera}s...")
                            if not self._esperar_con_stop(espera):
                                break
                    except Exception as e:
                        registro.fallido(numero, e, sheet_name)
                        self.root.after(0, self._log, f"Error con {numero}: {e}")

            if not self.stop_requested:
                self._log("Tarea completada.")
                self.root.after(0, self._set_status, "Envío completado")
            else:
                self.root.after(0, self._set_status, "Envío detenido")

        except Exception as e:
            self.root.after(0, self._log, f"Error general: {e}")
            self.root.after(0, self._set_status, "Error")
        finally:
            # Va en el finally para que el resumen y la ruta del registro
            # aparezcan tambien cuando la tanda se corta por un error.
            if registro is not None:
                for linea in registro.resumen().splitlines():
                    self.root.after(0, self._log, linea)
                registro.cerrar()

            self.running = False
            self.root.after(0, self.start_btn.configure, {"state": "normal"})
            self.root.after(0, self.stop_btn.configure, {"state": "disabled"})

    def _esperar_con_stop(self, segundos):
        for _ in range(segundos):
            if self.stop_requested:
                return False
            time.sleep(1)
        return True

    def _actualizar_progreso(self, actual, total):
        self.progress_label.configure(text=f"{actual} / {total}")

    def _log(self, mensaje):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} {mensaje}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_status(self, mensaje):
        self.status_bar.configure(text=f"  {mensaje}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WhatsAppBotGUI()
    app.run()
