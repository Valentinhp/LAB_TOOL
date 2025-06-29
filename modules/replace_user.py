# modules/replace_user.py

from __future__ import annotations
import os
import subprocess
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from utils.run_powershell import run_powershell_script as run_script

logger = logging.getLogger(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _local_users() -> list[str]:
    """
    Devuelve la lista de usuarios locales habilitados,
    excluyendo cuentas de sistema.
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
            text=True, encoding="utf-8"
        )
    except subprocess.CalledProcessError as e:
        logger.error("Error listando usuarios locales: %s", e)
        return []
    return sorted(u.strip() for u in out.splitlines() if u.strip())


def replace_user() -> None:
    """
    Abre un diálogo con:
      1. Combo de usuarios actuales.
      2. Campo para el nuevo nombre.
    Al confirmar, borra la cuenta antigua y crea la nueva sin contraseña.
    """
    users = _local_users()
    if not users:
        messagebox.showinfo("Vacío", "No hay usuarios locales habilitados para reemplazar.")
        return

    modal = tk.Toplevel()
    modal.title("Reemplazar usuario")
    modal.resizable(False, False)
    modal.grab_set()

    frm = ttk.Frame(modal, padding=20)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)

    ttk.Label(frm, text="Usuario a reemplazar:")\
        .grid(row=0, column=0, sticky="w", pady=4)
    user_cb = ttk.Combobox(frm, values=users, state="readonly")
    user_cb.grid(row=0, column=1, sticky="ew", pady=4)
    user_cb.current(0)

    ttk.Label(frm, text="Nuevo nombre:")\
        .grid(row=1, column=0, sticky="w", pady=4)
    new_var = tk.StringVar()
    ttk.Entry(frm, textvariable=new_var).grid(row=1, column=1, sticky="ew", pady=4)

    btn_frame = ttk.Frame(frm)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=(10,0))

    def on_confirm():
        old = user_cb.get()
        new = new_var.get().strip()
        if not new:
            messagebox.showwarning("Atención", "Escribe el nuevo nombre de usuario.", parent=modal)
            return
        modal.destroy()
        _run_replace_user(old, new)

    ttk.Button(btn_frame, text="Cancelar", command=modal.destroy)\
        .pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Reemplazar", command=on_confirm)\
        .pack(side="right")

    modal.transient()
    modal.wait_window()


def _run_replace_user(old_username: str, new_username: str) -> None:
    """
    1) Borra la cuenta antigua y su perfil completo.
    2) Crea la cuenta nueva sin contraseña y la marca never-expire.
    """
    # 1) Borrar cuenta antigua y perfil
    delete_script = os.path.abspath(
        os.path.join(BASE_DIR, os.pardir, "powershell", "borrar_usuario_completo.ps1")
    )
    logger.debug("Borrando usuario: %s", old_username)
    out, err, code = run_script(delete_script, "-Username", old_username)
    if code != 0:
        msg = err.strip() or out.strip()
        logger.error("Error borrando %s: %s", old_username, msg)
        raise RuntimeError(f"No se pudo borrar '{old_username}': {msg}")

    # 2) Crear usuario nuevo sin contraseña, con passwordreq:no y never expire
    create_script = os.path.abspath(
        os.path.join(BASE_DIR, os.pardir, "powershell", "crear_usuario.ps1")
    )
    logger.debug("Creando usuario: %s sin contraseña", new_username)
    out, err, code = run_script(
        create_script,
        "-Username", new_username,
        "-NoPassword",
        "-NeverExpire"
    )
    if code != 0:
        msg = err.strip() or out.strip()
        logger.error("Error creando %s: %s", new_username, msg)
        raise RuntimeError(f"No se pudo crear '{new_username}': {msg}")

    logger.info("Usuario '%s' eliminado y '%s' creado.", old_username, new_username)
    messagebox.showinfo(
        "Éxito",
        f"Usuario '{old_username}' eliminado\ny se ha creado '{new_username}' sin contraseña."
    )


__all__ = ["replace_user"]
