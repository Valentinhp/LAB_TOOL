
from __future__ import annotations
import os
import sys
import time
import shutil
import logging
import subprocess
import tempfile
import shlex
from typing import Tuple, List, Optional, Mapping

logger = logging.getLogger(__name__)


def _powershell_exe() -> str:
    """Devuelve el ejecutable de PowerShell disponible (pwsh.exe o powershell.exe)."""
    for exe in ("pwsh.exe", "powershell.exe"):
        path = shutil.which(exe)
        if path:
            return path
    raise FileNotFoundError("No se encontró PowerShell ('pwsh.exe' ni 'powershell.exe') en PATH.")


def run_powershell_script(
    path: str,
    *args: str,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout: int = 300,
) -> Tuple[str, str, int]:
    """
    Ejecuta un .ps1 y devuelve (stdout, stderr, exit_code).

    Args:
        path:    Ruta al script .ps1.
        *args:   Argumentos para el script (cada uno sin comillas).
        cwd:     Directorio de trabajo (opcional).
        env:     Variables de entorno adicionales/override (opcional).
        timeout: Segundos antes de matar el proceso (300s por defecto).

    Returns:
        Tuple[str, str, int]: stdout, stderr, returncode
    """
    exe = _powershell_exe()

    # Extraer script temporal si está embebido en PyInstaller
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        embedded_path = os.path.join(base_path, path)
        if os.path.isfile(embedded_path):
            temp_dir = tempfile.mkdtemp()
            temp_script = os.path.join(temp_dir, os.path.basename(path))
            shutil.copyfile(embedded_path, temp_script)
            path = temp_script

    cmd: List[str] = [
        exe,
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", path,
        *args
    ]

    cmd_str = " ".join(shlex.quote(part) for part in cmd)
    logger.debug("⤷ Ejecutando PowerShell: %s", cmd_str)

    start = time.time()
    try:
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd or os.getcwd(),
            env=full_env,
            timeout=timeout
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        elapsed = time.time() - start
        logger.debug("⤶ Fin (%ss) ➜ exit=%s", round(elapsed, 2), proc.returncode)

        return stdout.strip(), stderr.strip(), proc.returncode

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        logger.error("Timeout (%ss) ejecutando: %s", round(elapsed, 2), cmd_str)
        return "", f"Timeout: el script superó {timeout}s", 1

    except FileNotFoundError as e:
        logger.exception("PowerShell no encontrado: %s", e)
        return "", str(e), 1

    except Exception as e:
        logger.exception("run_powershell_script falló inesperadamente")
        return "", str(e), 1


# ——— Compatibilidad hacia atrás ———
run_script = run_powershell_script
