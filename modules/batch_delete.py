# modules/batch_delete.py
from __future__ import annotations
import os
import shutil
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

logger = logging.getLogger(__name__)


def has_residuals() -> bool:
    """Siempre habilita el botón para mostrar el diálogo."""
    return True


def batch_delete_folders() -> None:
    """
    Diálogo con dos Listbox para mover carpetas disponibles a seleccionadas,
    con doble clic ilimitado y botones, y confirmación final antes de eliminar en lote.
    """
    # 1) Pedir carpeta raíz
    root_dir = filedialog.askdirectory(
        title="Selecciona la carpeta raíz para borrado en lote"
    )
    if not root_dir:
        return  # Cancelado

    # 2) Listar subcarpetas directas
    try:
        subdirs = sorted(
            d for d in os.listdir(root_dir)
            if os.path.isdir(os.path.join(root_dir, d))
        )
    except Exception as e:
        logger.exception("No se pudo listar %s: %s", root_dir, e)
        messagebox.showerror(
            "Error",
            f"No se pudo acceder a:\n{root_dir}\n\n{e}"
        )
        return

    if not subdirs:
        messagebox.showinfo(
            "Sin subcarpetas",
            f"No se encontraron subcarpetas en:\n{root_dir}"
        )
        return

    # 3) Construir ventana modal
    win = tk.Toplevel()
    win.title("Borrado en lote")
    win.geometry("700x450")
    win.minsize(500, 350)
    win.resizable(True, True)
    win.grab_set()

    # Etiqueta superior
    ttk.Label(
        win,
        text=f"Carpeta raíz:\n{root_dir}",
        anchor="w"
    ).pack(fill="x", padx=10, pady=(10, 5))

    # Frame central con dos Listbox y botones de mover
    mid = ttk.Frame(win)
    mid.pack(fill="both", expand=True, padx=10, pady=5)

    # Listbox de disponibles
    lbl_avail = ttk.Label(mid, text="Disponibles:")
    lbl_avail.grid(row=0, column=0, padx=5, pady=(0,5))
    avail_lb = tk.Listbox(mid, selectmode="extended", activestyle="none")
    avail_lb.grid(row=1, column=0, sticky="nsew", padx=5)
    sb_av = ttk.Scrollbar(mid, orient="vertical", command=avail_lb.yview)
    sb_av.grid(row=1, column=1, sticky="ns")
    avail_lb.config(yscrollcommand=sb_av.set)

    # Botones de movimiento
    btn_frame = ttk.Frame(mid)
    btn_frame.grid(row=1, column=2, padx=5)
    ttk.Button(
        btn_frame,
        text="≫",
        width=3,
        command=lambda: move_items(avail_lb, sel_lb)
    ).pack(pady=10)
    ttk.Button(
        btn_frame,
        text="≪",
        width=3,
        command=lambda: move_items(sel_lb, avail_lb)
    ).pack()

    # Listbox de seleccionadas
    lbl_sel = ttk.Label(mid, text="Seleccionadas:")
    lbl_sel.grid(row=0, column=3, padx=5, pady=(0,5))
    sel_lb = tk.Listbox(mid, selectmode="extended", activestyle="none")
    sel_lb.grid(row=1, column=3, sticky="nsew", padx=5)
    sb_sel = ttk.Scrollbar(mid, orient="vertical", command=sel_lb.yview)
    sb_sel.grid(row=1, column=4, sticky="ns")
    sel_lb.config(yscrollcommand=sb_sel.set)

    # Configurar grid para expandir Listboxes
    mid.columnconfigure(0, weight=1)
    mid.columnconfigure(3, weight=1)
    mid.rowconfigure(1, weight=1)

    # Rellenar disponibles
    for folder in subdirs:
        avail_lb.insert("end", folder)

    def move_items(src: tk.Listbox, dst: tk.Listbox):
        """Mueve ítems seleccionados de src a dst (mantiene orden)."""
        items = [src.get(i) for i in src.curselection()]
        for item in items:
            if item not in dst.get(0, "end"):
                dst.insert("end", item)
        for i in reversed(src.curselection()):
            src.delete(i)

    # 4) Doble clic ilimitado para mover
    def on_avail_dblclick(event):
        idx = avail_lb.nearest(event.y)
        if idx < 0:
            return
        item = avail_lb.get(idx)
        if item not in sel_lb.get(0, "end"):
            sel_lb.insert("end", item)
        avail_lb.delete(idx)

    def on_sel_dblclick(event):
        idx = sel_lb.nearest(event.y)
        if idx < 0:
            return
        item = sel_lb.get(idx)
        if item not in avail_lb.get(0, "end"):
            avail_lb.insert("end", item)
        sel_lb.delete(idx)

    avail_lb.bind("<Double-Button-1>", on_avail_dblclick, add=True)
    sel_lb.bind("<Double-Button-1>", on_sel_dblclick, add=True)

    # 5) Función de confirmación y borrado
    def on_confirm():
        selected = sel_lb.get(0, "end")
        if not selected:
            messagebox.showwarning(
                "Nada seleccionado",
                "Debes mover al menos una carpeta a 'Seleccionadas'.",
                parent=win
            )
            return

        lista = "\n".join(selected)
        if not messagebox.askyesno(
            "Confirmar BORRAR",
            f"Vas a borrar {len(selected)} carpeta(s):\n\n{lista}\n\n¿Seguro?",
            parent=win
        ):
            return

        errors: list[str] = []
        for folder in selected:
            path = os.path.join(root_dir, folder)
            try:
                shutil.rmtree(path)
                logger.info("Carpeta eliminada: %s", path)
            except Exception as e:
                errors.append(f"{folder}: {e}")
                logger.error("Error al borrar %s → %s", folder, e)

        if errors:
            messagebox.showerror(
                "Completado con errores",
                "\n".join(errors),
                parent=win
            )
        else:
            messagebox.showinfo(
                "Hecho",
                "Carpetas eliminadas correctamente.",
                parent=win
            )
            win.destroy()

    # 6) Botones de acción abajo
    bottom = ttk.Frame(win)
    bottom.pack(fill="x", padx=10, pady=10)
    ttk.Button(bottom, text="Cancelar", command=win.destroy)\
        .pack(side="right", padx=(0,5))
    ttk.Button(bottom, text="Eliminar seleccionadas", command=on_confirm)\
        .pack(side="right", padx=(0,10))

    win.mainloop()
