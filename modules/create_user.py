# modules/create_user.py

from __future__ import annotations
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from utils.run_powershell import run_powershell_script as run_script

logger = logging.getLogger(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_user() -> None:
    """
    Abre un Toplevel para pedir solo:
      • Usuario
      • “Sin contraseña” (checkbox)
      • “Password nunca expira” (checkbox)

    Al confirmar, llama al script PS que usa -NoPassword si corresponde.
    """
    modal = tk.Toplevel()
    modal.title("Crear nuevo usuario")
    modal.resizable(False, False)
    modal.grab_set()

    username_var     = tk.StringVar()
    no_password_var  = tk.BooleanVar(value=True)
    never_expire_var = tk.BooleanVar(value=False)

    frm = ttk.Frame(modal, padding=20)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)

    # Usuario
    ttk.Label(frm, text="Usuario:").grid(row=0, column=0, sticky="w", pady=2)
    ttk.Entry(frm, textvariable=username_var).grid(row=0, column=1, sticky="ew", pady=2)

    # Sin contraseña
    ttk.Checkbutton(
        frm,
        text="Sin contraseña",
        variable=no_password_var
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)

    # Nunca expira
    ttk.Checkbutton(
        frm,
        text="Password nunca expira",
        variable=never_expire_var
    ).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)

    # Botones
    btn_frame = ttk.Frame(frm)
    btn_frame.grid(row=3, column=0, columnspan=2, pady=(10,0))

    def on_confirm():
        user   = username_var.get().strip()
        no_pwd = no_password_var.get()
        nexp   = never_expire_var.get()

        if not user:
            messagebox.showwarning("Atención", "El nombre de usuario no puede estar vacío.", parent=modal)
            return

        modal.destroy()
        _run_create_user(user, no_pwd, nexp)

    ttk.Button(btn_frame, text="Cancelar", command=modal.destroy).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Crear",   command=on_confirm).pack(side="right")

    modal.transient()
    modal.wait_window()


def _run_create_user(username: str,
                     no_password: bool,
                     never_expire: bool) -> None:
    """
    Ejecuta el script PowerShell para crear el usuario:
      - Si no_password=True usa -NoPassword
      - Si never_expire=True usa -NeverExpire
    """
    script_path = os.path.abspath(
        os.path.join(BASE_DIR, os.pardir, "powershell", "crear_usuario.ps1")
    )

    ps_args = ["-Username", username]
    if no_password:
        ps_args += ["-NoPassword"]
    if never_expire:
        ps_args += ["-NeverExpire"]

    logger.debug("Lanzando PowerShell: %s %s", script_path, ps_args)
    out, err, code = run_script(script_path, *ps_args)

    if code != 0:
        logger.error("PowerShell terminó con error %s: %s", code, err)
        raise RuntimeError(err or f"Exit code {code}")

    logger.info("Usuario '%s' creado con éxito.", username)
    messagebox.showinfo("Éxito", f"Usuario '{username}' creado correctamente.")


__all__ = ["create_user"]
