# -*- coding: utf-8 -*-
"""
Hub da Bia - Suíte Pessoal de Produtividade & Ferramentas
Ponto de entrada da aplicação desktop.
"""

import sys
import os
import traceback
from pathlib import Path

# Garante que src/ está no path para importar hubbia
SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Importar paths após ajustar sys.path
from hubbia.core.paths import get_log_path

# Log de inicialização e diagnóstico
log_file = get_log_path()


def log_debug(msg):
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass


def global_excepthook(exc_type, exc_val, exc_tb):
    err = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
    log_debug(f"[FATAL ERROR] {err}")
    try:
        from PySide6.QtWidgets import QMessageBox, QApplication
        if QApplication.instance():
            QMessageBox.critical(None, "Erro - Hub da Bia", err)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_val, exc_tb)


sys.excepthook = global_excepthook

log_debug("--- Iniciando Hub da Bia ---")

# Ajustar diretório de trabalho
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    os.chdir(str(exe_dir))
    sys.path.insert(0, str(exe_dir))
    if (exe_dir / "_internal").exists():
        sys.path.insert(0, str(exe_dir / "_internal"))
else:
    current_dir = Path(__file__).resolve().parent
    os.chdir(str(current_dir))
    sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from hubbia.ui.main_window import MainWindow


def main():
    log_debug("Configurando AppUserModelID...")
    # Otimizações de renderização no Windows
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = 'bia.hub.suite.launcher.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            log_debug(f"Aviso AppUserModelID: {e}")

    log_debug("Instanciando QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Hub da Bia")
    app.setOrganizationName("BiaStudio")

    log_debug("Instanciando MainWindow...")
    window = MainWindow()
    window.show()
    log_debug("MainWindow exibida. Entrando no loop principal exec()...")

    ret = app.exec()
    log_debug(f"Loop finalizado com código: {ret}")
    sys.exit(ret)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        global_excepthook(*sys.exc_info())