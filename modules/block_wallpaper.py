r"""
block_wallpaper.py – Bloquea el cambio de fondo para el usuario actual.

• Lanza el script PowerShell `powershell\bloquear_fondo.ps1`.
• Pregunta confirmación al técnico.
• Muestra resultado claro: “Hecho” o “Error”.
• Nunca se cae: cualquier excepción queda registrada en labtool.log
  y se enseña al usuario de forma amigable.
"""

from __future__ import annotations
import logging
import tkinter as tk
from tkinter import messagebox
from utils.run_powershell import run_script

logger = logging.getLogger(__name__)


def block_wallpaper() -> None:
    """
    Ventana modal de confirmación ⇒ ejecuta el PS1 ⇒ notifica resultado.
    """
    if not messagebox.askyesno(
        title="Bloquear fondo",
        message="Esto impedirá que el usuario cambie su fondo.\n¿Continuar?"
    ):
        return  # usuario canceló

    stdout, stderr, code = run_script(r"powershell\bloquear_fondo.ps1")

    if code == 0:
        logger.info("Bloqueo de fondo completado: %s", stdout)
        messagebox.showinfo("Hecho", "Cambios de fondo bloqueados.")
    else:
        logger.error("block_wallpaper → %s | %s", stdout, stderr)
        messagebox.showerror(
            "Error",
            stderr or stdout or "No se pudo bloquear el fondo."
        )
