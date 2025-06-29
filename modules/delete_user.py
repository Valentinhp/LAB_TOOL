# modules/delete_user.py

from __future__ import annotations
import subprocess
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from utils.run_powershell import run_powershell_script as run_script

logger = logging.getLogger(__name__)

def _local_users() -> list[str]:
    """
    Obtiene usuarios locales habilitados (excluye cuentas de sistema)
    usando PowerShell inline con subprocess.check_output.
    """
    ps_cmd = (
        'Get-LocalUser | Where-Object { $_.Enabled -eq $true } | '
        'Where-Object { $_.Name -notin @("Administrator","DefaultAccount","Guest","WDAGUtilityAccount") } | '
        'Select-Object -ExpandProperty Name'
    )
    try:
        out = subprocess.check_output(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8"
        )
    except subprocess.CalledProcessError as e:
        logger.error("Error listando usuarios con PowerShell: %s", e)
        return []

    users = [line.strip() for line in out.splitlines() if line.strip()]
    return sorted(users)


def delete_user() -> None:
    """Ventana de borrado múltiple de usuarios con check-buttons."""
    users = _local_users()
    if not users:
        messagebox.showinfo("Vacío", "No hay usuarios locales habilitados para borrar.")
        return

    modal = tk.Toplevel()
    modal.title("Borrar usuario(s)")
    modal.resizable(False, False)
    modal.grab_set()

    frm = ttk.Frame(modal, padding=20)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="Marca las cuentas que deseas eliminar:")\
        .pack(anchor="w", pady=(0, 4))

    # Botones de selección rápida
    btn_sel = ttk.Frame(frm)
    btn_sel.pack(fill="x", pady=(0, 8))
    def select_all():
        for var in vars_.values():
            var.set(True)
    def deselect_all():
        for var in vars_.values():
            var.set(False)
    ttk.Button(btn_sel, text="Seleccionar todo", command=select_all).pack(side="left")
    ttk.Button(btn_sel, text="Deseleccionar todo", command=deselect_all).pack(side="left", padx=4)

    # Canvas + Scrollable frame
    canvas = tk.Canvas(frm, height=200, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frm, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Crear los checkbuttons
    vars_: dict[str, tk.BooleanVar] = {}
    for idx, user in enumerate(users):
        var = tk.BooleanVar(value=False)
        vars_[user] = var
        row, col = divmod(idx, 2)
        ttk.Checkbutton(
            inner,
            text=user,
            variable=var
        ).grid(row=row, column=col, sticky="w", padx=4, pady=2)

    # Botones de acción
    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill="x", pady=(10,0))

    def on_delete():
        sel = [u for u, v in vars_.items() if v.get()]
        if not sel:
            messagebox.showwarning("Nada seleccionado",
                                   "Marca al menos una cuenta.",
                                   parent=modal)
            return
        if not messagebox.askyesno("Confirmar",
                                   f"¿Borrar {len(sel)} cuenta(s)?",
                                   parent=modal):
            return

        errors = []
        for user in sel:
            out, err, code = run_script(
                r"powershell\borrar_usuario_completo.ps1",
                "-Username", user,
                "-Force"
            )
            if code != 0:
                msg = err.strip() or out.strip()
                errors.append(f"{user}: {msg}")
                logger.error("Error borrando %s → %s", user, msg)
            else:
                logger.info("Usuario %s eliminado.", user)

        if errors:
            messagebox.showerror("Errores",
                                 "\n".join(errors),
                                 parent=modal)
        else:
            messagebox.showinfo("Hecho",
                                "Usuarios eliminados correctamente.",
                                parent=modal)
            modal.destroy()

    ttk.Button(btn_frame, text="Borrar", command=on_delete)\
        .pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Cancelar", command=modal.destroy)\
        .pack(side="right")

    # Esperar cierre
    modal.transient()
    modal.wait_window()
