# modules/wallpaper.py

from __future__ import annotations
import os
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from utils.run_powershell import run_powershell_script as run_script

logger = logging.getLogger(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

try:
    from PIL import Image, ImageTk
    has_pillow = True
except ImportError:
    has_pillow = False


def apply_and_lock_wallpaper():
    """
    Abre un diálogo con:
      • Predeterminado: resources/fondo.jpg
      • Personalizado: elige otro archivo
    Muestra preview (si Pillow) y aplica/bloquea al pulsar.
    """
    dialog = tk.Toplevel()
    dialog.title("Aplicar y bloquear fondo")
    dialog.resizable(False, False)
    dialog.grab_set()

    choice_var = tk.StringVar(value="default")
    custom_path = tk.StringVar(value="")
    preview_img: ImageTk.PhotoImage | tk.PhotoImage | None = None

    default_path = os.path.abspath(
        os.path.join(BASE_DIR, os.pardir, "resources", "fondo.jpg")
    )

    # --- Definición de funciones internas antes de construir la UI ---

    def load_preview(path: str):
        nonlocal preview_img
        preview_lbl.config(text="", image="")

        if not has_pillow:
            preview_lbl.config(text="❗ Instala Pillow para preview")
            return

        try:
            img = Image.open(path)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            preview_img = ImageTk.PhotoImage(img)
            preview_lbl.config(image=preview_img)
        except Exception as ex:
            logger.exception("Error cargando preview %s: %s", path, ex)
            preview_lbl.config(text="(No se puede mostrar preview)")

    def on_mode_change():
        mode = choice_var.get()
        if mode == "default":
            btn_browse.state(["disabled"])
            load_preview(default_path)
        else:
            btn_browse.state(["!disabled"])
            p = custom_path.get()
            if p and os.path.exists(p):
                load_preview(p)
            else:
                preview_lbl.config(text="No hay imagen seleccionada", image="")

    def browse_file():
        p = filedialog.askopenfilename(
            title="Selecciona imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not p:
            return
        custom_path.set(p)
        load_preview(p)

    def apply_wallpaper():
        mode = choice_var.get()
        img_path = default_path if mode == "default" else custom_path.get()
        if mode == "custom" and not img_path:
            messagebox.showwarning(
                "Atención",
                "Selecciona primero una imagen personalizada.",
                parent=dialog
            )
            return

        script = os.path.abspath(
            os.path.join(BASE_DIR, os.pardir, "powershell", "aplicar_fondo.ps1")
        )
        args = ["-Image", img_path]
        if mode == "default":
            args += ["-Default", "-Current"]
        else:
            args += ["-Current"]

        logger.debug("Aplicando y bloqueando fondo: %s %s", script, args)
        out, err, code = run_script(script, *args)
        if code != 0:
            logger.error("aplicar_fondo → %s", err or out)
            messagebox.showerror("Error", err or out, parent=dialog)
        else:
            messagebox.showinfo("Listo", "Fondo aplicado y bloqueado.", parent=dialog)
            dialog.destroy()

    # --- Construcción de la UI ---

    # Contenedor de preview 300×200
    preview_frame = tk.Frame(dialog, width=300, height=200, relief="sunken", bd=1)
    preview_frame.grid(row=0, column=0, columnspan=3, pady=(10, 0), padx=10)
    preview_frame.grid_propagate(False)

    preview_lbl = tk.Label(preview_frame, text="(Preview)")
    preview_lbl.place(relx=0.5, rely=0.5, anchor="center")

    # Radiobuttons
    rb_def = ttk.Radiobutton(dialog, text="Predeterminado",
                             variable=choice_var, value="default",
                             command=on_mode_change)
    rb_cus = ttk.Radiobutton(dialog, text="Personalizado",
                             variable=choice_var, value="custom",
                             command=on_mode_change)
    rb_def.grid(row=1, column=0, sticky="w", padx=10, pady=5)
    rb_cus.grid(row=1, column=1, sticky="w", padx=10, pady=5)

    # Examinar personalizado
    btn_browse = ttk.Button(dialog, text="Examinar…", command=browse_file)
    btn_browse.grid(row=1, column=2, sticky="e", padx=10, pady=5)

    # Botón aplicar
    btn_apply = ttk.Button(dialog, text="Aplicar y bloquear", command=apply_wallpaper)
    btn_apply.grid(row=2, column=0, columnspan=3, pady=(10, 10))

    dialog.columnconfigure(0, weight=1)
    dialog.columnconfigure(1, weight=1)
    dialog.columnconfigure(2, weight=1)

    # Inicialización
    if not has_pillow:
        messagebox.showwarning(
            "Preview deshabilitado",
            "Instala Pillow (`pip install pillow`) para ver la previsualización.",
            parent=dialog
        )
    load_preview(default_path)
    on_mode_change()

    dialog.transient()
    dialog.wait_window()
