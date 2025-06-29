# main.py – LabTool 3.2
# ─────────────────────────────────────────────────────────────
# Centro gráfico de tareas administrativas para Windows
#  • Ventana siempre centrada
#  • Botones agrupados con ancho uniforme
#  • Tooltips y atajos (Alt+letra)
#  • Log reiniciado en cada ejecución
# ─────────────────────────────────────────────────────────────

from __future__ import annotations
import os, sys, ctypes, logging, tkinter as tk
from tkinter import ttk, messagebox

# ────────────────────── Configurar logging ───────────────────
logging.basicConfig(
    filename="labtool.log",
    filemode="w",                 # sobrescribe en cada inicio
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
console = logging.StreamHandler(sys.stdout)          # eco en terminal
console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logging.getLogger().addHandler(console)
logger = logging.getLogger("main")

APP_NAME  = "LabTool"
BASE_DIR  = os.path.abspath(os.path.dirname(__file__))

# ────────────────────── Utilidades comunes ───────────────────
def resource(rel: str) -> str:
    """Devuelve la ruta a un archivo (soporta PyInstaller)."""
    return os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), rel)

def is_admin() -> bool:
    """¿El proceso corre como administrador?  Necesario para todas las acciones."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        logger.exception("No se pudo comprobar privilegios")
        return False

def elevate() -> None:
    """Re-lanza el script con privilegios elevados (UAC)."""
    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(  # type: ignore
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit()

def open_log() -> None:
    """Abre labtool.log con el visor asociado."""
    try:
        os.startfile("labtool.log")  # type: ignore
    except Exception as e:
        logger.exception("Error abriendo log")
        messagebox.showerror("Error", str(e))

# ──────────────────── Importar acciones reales ───────────────
from modules.create_user       import create_user
from modules.delete_user       import delete_user
from modules.replace_user      import replace_user
from modules.batch_delete      import batch_delete_folders, has_residuals
from modules.wallpaper         import apply_and_lock_wallpaper
from modules.block_wallpaper   import block_wallpaper
from modules.unblock_wallpaper import unblock_wallpaper
from modules.shortcuts         import create_shortcuts

# ───────────────────────── Tooltip simple ────────────────────
class ToolTip(tk.Toplevel):
    """Ventana tipo tip que sigue al ratón."""
    def __init__(self, widget: tk.Widget, text: str):
        super().__init__(widget)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        ttk.Label(self, text=text, padding=6,
                  style="ToolTip.TLabel").pack()
        widget.bind("<Enter>", self._show, add=True)
        widget.bind("<Leave>", lambda *_: self.withdraw(), add=True)

    def _show(self, e):
        self.geometry(f"+{e.x_root+20}+{e.y_root+20}")
        self.deiconify()

# ───────────────────── Construir la interfaz ─────────────────
def build_ui() -> tuple[tk.Tk, callable]:
    root = tk.Tk()
    root.title(APP_NAME)
    root.resizable(False, False)

    # Ícono (ignorar error si falta)
    try:
        root.iconbitmap(resource("resources/app.ico"))
    except Exception:
        pass

    # Ajustar a Hi-DPI para monitores 125 % / 150 % / 175 %
    try:
        scaling = root.winfo_fpixels("1i") / 72  # puntos por pulgada
        root.tk.call("tk", "scaling", scaling)
    except Exception:
        pass

    # ───── Estilos ttk ────────────────────────────────────────
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".",            font=("Segoe UI", 11))
    style.configure("TButton",      padding=(12, 6))
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure("ToolTip.TLabel",
                    background="#ffffe0", relief="solid", borderwidth=1)

    # ───── Menú (Ayuda + log) ─────────────────────────────────
    menubar = tk.Menu(root)
    helpm   = tk.Menu(menubar, tearoff=False)
    helpm.add_command(label="Ver log", command=open_log)
    helpm.add_separator()
    helpm.add_command(
        label="Acerca de…",
        command=lambda: messagebox.showinfo(
            "Acerca de", "LabTool 3.2\n© 2025")
    )
    menubar.add_cascade(label="Ayuda", menu=helpm)
    root.config(menu=menubar)

    # ───── Marco principal ───────────────────────────────────
    main = ttk.Frame(root, padding=24)
    main.pack()

    ttk.Label(main, text="LabTool – Centro de tareas",
              style="Title.TLabel").grid(column=0, row=0, pady=(0, 12))

    # ───── Definir acciones: (texto, tooltip, grupo, fn, habilita?) ────
    ACTIONS: list[tuple[str, str, str, callable, callable | None]] = [
        # Usuarios
        ("Crear nuevo usuario",   "Crea una cuenta local vacía.",
         "Usuarios", create_user, None),
        ("Borrar usuario(s)",     "Elimina cuentas y sus carpetas.",
         "Usuarios", delete_user, None),
        ("Reemplazar usuario",    "Borra uno y crea otro con accesos.",
         "Usuarios", replace_user, None),

        # Fondos
        ("Aplicar y bloquear fondo", "Fija un fondo y evita cambios.",
         "Fondos", apply_and_lock_wallpaper, None),
        ("Bloquear fondo",        "Impide cambiar el fondo.",
         "Fondos", block_wallpaper, None),
        ("Desbloquear fondo",     "Vuelve a permitir cambios.",
         "Fondos", unblock_wallpaper, None),

        # Limpieza
        ("Borrado en lote de carpetas", "Elimina perfiles huérfanos.",
         "Limpieza", batch_delete_folders, has_residuals),

        # Miscelánea
        ("Shortcuts (accesos)",   "Copia accesos útiles al Escritorio.",
         "Otros", create_shortcuts, None),
        ("Ver log",               "Abre labtool.log.",
         "Otros", open_log, None),
    ]

    # ───── Crear frames por grupo ─────────────────────────────
    groups: dict[str, ttk.LabelFrame] = {}
    buttons: dict[str, ttk.Button]    = {}
    used_shortcuts: set[str]          = set()

    def next_shortcut(text: str) -> str:
        """Elige una letra libre para Alt+letra."""
        for ch in text.lower():
            if ch.isalpha() and ch not in used_shortcuts:
                used_shortcuts.add(ch)
                return ch
        # fallback (poco probable)
        return "x"

    col = 0  # columnas para distribuir grupos (2 por fila máx.)
    row = 1
    for txt, tip, grp, fn, cond in ACTIONS:
        if grp not in groups:
            # cada 2 grupos saltamos de fila p/ distribución limpia
            if col == 2:
                col = 0
                row += 1
            grp_frame = ttk.LabelFrame(main, text=grp, padding=12)
            grp_frame.grid(column=col, row=row, padx=6, pady=6, sticky="nsew")
            groups[grp] = grp_frame
            col += 1

        shortcut = next_shortcut(txt)
        btn = ttk.Button(
            groups[grp],
            text=txt,
            underline=txt.lower().index(shortcut),
            command=lambda f=fn, n=txt: launch(f, n, root, refresh)
        )
        # mismo ancho para todos
        btn.pack(fill="x", pady=3, ipadx=10)
        ToolTip(btn, tip)
        root.bind_all(f"<Alt-{shortcut}>",
                      lambda e, b=btn: b.invoke(), add=True)
        buttons[txt] = btn

    # ───── Refresco dinámico (habilitar / deshabilitar) ──────
    def refresh():
        for txt, _, _grp, _fn, cond in ACTIONS:
            state = "normal"
            if cond and not cond():
                state = "disabled"
            buttons[txt].config(state=state)

    refresh()  # estado inicial

    # ───── Centrar ventana ───────────────────────────────────
    root.update_idletasks()  # calcula tamaño real
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth()  // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")

    # al cerrar, pedir confirmación
    root.protocol("WM_DELETE_WINDOW", lambda:
        root.destroy() if messagebox.askokcancel(
            "Salir", "¿Cerrar LabTool?") else None)

    return root, refresh

# ─────────────────── Despachador genérico ───────────────────
def launch(fn: callable, name: str, parent: tk.Tk, refresh_cb):
    """Lanza una acción, muestra los mensajes y refresca botones."""
    logger.debug("→ %s", name)
    try:
        fn()
    except Exception as err:
        logger.exception("Error en %s", name)
        messagebox.showerror(f"Error – {name}", str(err), parent=parent)
    else:
        logger.info("%s completada sin errores", name)
        messagebox.showinfo("Listo", f"{name} finalizado.", parent=parent)
    finally:
        refresh_cb()

# ─────────────────────────── Main ────────────────────────────
def main():
    if not is_admin():
        if messagebox.askretrycancel(
            APP_NAME,
            "Debes ejecutar como administrador.\n"
            "Pulsa Reintentar y acepta la UAC."
        ):
            elevate()
        sys.exit()

    root, _ = build_ui()
    root.mainloop()

if __name__ == "__main__":
    main()
