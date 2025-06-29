# modules/unblock_wallpaper.py

from __future__ import annotations
import os
import logging
from utils.run_powershell import run_powershell_script as run_script
from tkinter import messagebox

logger = logging.getLogger(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def unblock_wallpaper() -> None:
    """
    Desbloquea el cambio de fondo usando desbloquear_fondo.ps1.
    """
    script_path = os.path.abspath(
        os.path.join(BASE_DIR, os.pardir, "powershell", "desbloquear_fondo.ps1")
    )
    logger.debug("Desbloqueando fondo: %s", script_path)

    out, err, code = run_script(script_path)
    if code != 0:
        logger.error("unblock_wallpaper → %s", err or out)
        messagebox.showerror("Error", err or out)
        return

    messagebox.showinfo("Listo", "Cambio de fondo desbloqueado.")
