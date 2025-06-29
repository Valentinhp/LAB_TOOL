# modules/shortcuts.py

from __future__ import annotations
import os
import glob
import shutil
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

logger = logging.getLogger(__name__)


def _scan_shortcuts() -> dict[str, str]:
    """
    Busca todos los .lnk en Menú Inicio (ProgramData y AppData)
    y devuelve un dict: { "Nombre": ruta_al_lnk }.
    """
    roots = [
        os.path.join(os.getenv("ProgramData", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.getenv("APPDATA", ""),    "Microsoft\\Windows\\Start Menu\\Programs"),
    ]
    mapping: dict[str, str] = {}
    for root in roots:
        pattern = os.path.join(root, "**", "*.lnk")
        for path in glob.glob(pattern, recursive=True):
            name = os.path.splitext(os.path.basename(path))[0]
            if name not in mapping:
                mapping[name] = path
    return dict(sorted(mapping.items()))


def create_shortcuts() -> None:
    """
    Ventana con dos paneles:
      • Disponibles: todos los .lnk filtrables.
      • Seleccionados: los que elijas.
    Luego:
      • Elegir carpeta destino.
      • Botón “Crear accesos” copia los .lnk allí y abre la carpeta.
    """
    mapping = _scan_shortcuts()
    if not mapping:
        messagebox.showinfo("Vacío", "No se encontraron accesos .lnk en el Menú Inicio.")
        return

    root = tk.Toplevel()
    root.title("Crear accesos directos")
    root.resizable(False, False)
    root.grab_set()

    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0)

    # Búsqueda
    ttk.Label(frm, text="Buscar:").grid(row=0, column=0, sticky="w")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(frm, textvariable=search_var)
    search_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0, 10))
    frm.columnconfigure(1, weight=1)

    # Paneles disponibles / seleccionados
    ttk.Label(frm, text="Disponibles").grid(row=1, column=0, padx=(0,5))
    ttk.Label(frm, text="Seleccionados").grid(row=1, column=2, padx=(15,0))

    lb_avail = tk.Listbox(frm, height=16, width=30,
                          selectmode="extended", exportselection=False)
    lb_sel   = tk.Listbox(frm, height=16, width=30,
                          selectmode="extended", exportselection=False)
    sb_a = ttk.Scrollbar(frm, orient="vertical", command=lb_avail.yview)
    sb_s = ttk.Scrollbar(frm, orient="vertical", command=lb_sel.yview)
    lb_avail.configure(yscrollcommand=sb_a.set)
    lb_sel.configure(yscrollcommand=sb_s.set)

    lb_avail.grid(row=2, column=0, sticky="nsew")
    sb_a.grid(row=2, column=1, sticky="ns")
    lb_sel.grid(row=2, column=2, sticky="nsew", padx=(15,0))
    sb_s.grid(row=2, column=3, sticky="ns")

    all_names = list(mapping.keys())
    def update_available(*_):
        query = search_var.get().lower()
        lb_avail.delete(0, "end")
        for name in all_names:
            if query in name.lower():
                lb_avail.insert("end", name)
    search_var.trace_add("write", update_available)

    update_available()  # inicial poblado

    # Botones de mover
    def _move(src: tk.Listbox, dst: tk.Listbox):
        sel = list(src.curselection())
        for i in reversed(sel):
            item = src.get(i)
            if item not in dst.get(0, "end"):
                dst.insert("end", item)
            src.delete(i)

    btns = ttk.Frame(frm)
    btns.grid(row=2, column=4, padx=(10,0))
    ttk.Button(btns, text="► Añadir", command=lambda: _move(lb_avail, lb_sel)).pack(pady=5)
    ttk.Button(btns, text="◄ Quitar", command=lambda: _move(lb_sel, lb_avail)).pack(pady=5)
    lb_avail.bind("<Double-Button-1>", lambda e: _move(lb_avail, lb_sel))
    lb_sel.bind("<Double-Button-1>",   lambda e: _move(lb_sel, lb_avail))

    # Seleccionar carpeta destino
    dest_var = tk.StringVar()
    dest_lbl = ttk.Label(frm, text="Destino: (ninguno)")
    dest_lbl.grid(row=3, column=0, columnspan=4, sticky="w", pady=(10,0))

    def choose_folder():
        folder = filedialog.askdirectory(title="Selecciona carpeta destino", mustexist=True)
        if folder:
            dest_var.set(folder)
            dest_lbl.config(text=f"Destino: {folder}")

    ttk.Button(frm, text="Elegir carpeta destino…", command=choose_folder)\
        .grid(row=4, column=0, columnspan=2, sticky="w", pady=(5,10))

    # Crear y abrir
    def do_create():
        selected = list(lb_sel.get(0, "end"))
        dest = dest_var.get()
        if not selected:
            messagebox.showwarning("Nada seleccionado", "Marca al menos un acceso.")
            return
        if not dest:
            messagebox.showwarning("Sin destino", "Selecciona la carpeta destino antes.")
            return

        errors = []
        for name in selected:
            src = mapping[name]
            dst = os.path.join(dest, os.path.basename(src))
            try:
                shutil.copy2(src, dst)
                logger.info("Copiado: %s → %s", src, dst)
            except Exception as ex:
                logger.exception("Error copiando %s", src)
                errors.append(f"{name}: {ex}")

        if errors:
            messagebox.showerror("Errores al copiar", "\n".join(errors), parent=root)
        else:
            messagebox.showinfo("Hecho", f"{len(selected)} accesos copiados en:\n{dest}", parent=root)
            try:
                os.startfile(dest)
            except Exception:
                pass
            root.destroy()

    bottom = ttk.Frame(frm)
    bottom.grid(row=5, column=0, columnspan=5, pady=(0,5))
    ttk.Button(bottom, text="Crear accesos", command=do_create).pack(side="left", padx=5)
    ttk.Button(bottom, text="Cancelar",       command=root.destroy).pack(side="left")

    root.mainloop()
