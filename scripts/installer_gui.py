# -*- coding: utf-8 -*-
"""
Instalador Simples e Limpo - Hub da Bia
Instala em %LOCALAPPDATA%\Programs\HubDaBia e fixa na Barra de Tarefas.
"""

import os
import sys
import time
import shutil
import subprocess
import ctypes
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame, QMessageBox,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6.QtCore import Qt, QTimer, QThread, Signal


def get_installer_version():
    """Lê versão do version.json embutido no instalador"""
    try:
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(base_path, "version.json")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f).get("version", "2.6.0")
    except Exception:
        pass
    return "2.6.0"


INSTALLER_VERSION = get_installer_version()


class InstallWorker(QThread):
    progress_changed = Signal(int, str)
    step_completed = Signal(int, str)
    finished = Signal(bool, str)

    def run(self):
        try:
            target_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\HubDaBia")
            exe_name = f"HubDaBia-v{INSTALLER_VERSION}.exe"
            exe_target = os.path.join(target_dir, exe_name)
            icon_target = os.path.join(target_dir, "_internal", "assets", "hub_icon.ico")

            # Passo 1: Encerrar instâncias anteriores
            self.progress_changed.emit(10, "Encerrando processos ativos do Hub...")
            time.sleep(0.5)
            subprocess.run(["taskkill", "/F", "/IM", "HubDaBia*.exe", "/T"], capture_output=True)
            time.sleep(0.8)
            self.step_completed.emit(1, "Instâncias anteriores finalizadas.")

            # Passo 2: Copiar / Extrair arquivos
            self.progress_changed.emit(30, "Preparando e instalando os arquivos do Hub...")
            os.makedirs(target_dir, exist_ok=True)

            installed_ok = False

            # Estratégia A: Arquivo ZIP embutido no instalador (_MEIPASS)
            if getattr(sys, "frozen", False):
                embedded_zip = os.path.join(sys._MEIPASS, "HubDaBia_Suite.zip")
                if os.path.exists(embedded_zip):
                    self.progress_changed.emit(40, "Extraindo arquivos do pacote integrado...")
                    import zipfile
                    with zipfile.ZipFile(embedded_zip, "r") as zf:
                        zf.extractall(target_dir)
                    installed_ok = os.path.exists(os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))

            # Estratégia B: Payload descompactado (_MEIPASS/payload)
            if not installed_ok and getattr(sys, "frozen", False):
                meipass_payload = os.path.join(sys._MEIPASS, "payload")
                if os.path.exists(meipass_payload):
                    self.progress_changed.emit(45, "Copiando arquivos internos...")
                    subprocess.run(
                        ["robocopy", meipass_payload, target_dir, "/E", "/NP", "/R:2", "/W:1"],
                        capture_output=True
                    )
                    installed_ok = os.path.exists(os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))

            # Estratégia C: Arquivo ZIP local próximo ao executável ou no Google Drive
            if not installed_ok:
                local_zips = [
                    os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "HubDaBia_Suite.zip"),
                    r"F:\Meu Drive\.AntigravityGoogle\HubDaBia\HubDaBia_Suite.zip",
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "HubDaBia_Suite.zip"),
                ]
                for z_path in local_zips:
                    if os.path.exists(z_path):
                        self.progress_changed.emit(45, "Extraindo pacote local de instalação...")
                        import zipfile
                        with zipfile.ZipFile(z_path, "r") as zf:
                            zf.extractall(target_dir)
                        installed_ok = os.path.exists(os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))
                        if installed_ok:
                            break

            # Estratégia D: Pasta dist local (versão versionada)
            if not installed_ok:
                candidates = [
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", f"HubDaBia-v{INSTALLER_VERSION}"),
                    r"F:\Meu Drive\.AntigravityGoogle\HubDaBia\dist\HubDaBia-v{}".format(INSTALLER_VERSION),
                    r"C:\temp_hub_build\dist\HubDaBia-v{}".format(INSTALLER_VERSION)
                ]
                for c in candidates:
                    exe_path = os.path.join(c, f"HubDaBia-v{INSTALLER_VERSION}.exe")
                    if os.path.exists(exe_path):
                        self.progress_changed.emit(50, f"Instalando arquivos a partir de {c}...")
                        subprocess.run(
                            ["robocopy", os.path.abspath(c), target_dir, "/E", "/NP", "/R:2", "/W:1"],
                            capture_output=True
                        )
                        installed_ok = os.path.exists(os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))
                        if installed_ok:
                            break

            # Estratégia E: Download da nuvem oficial (Dropbox Cloud)
            if not installed_ok:
                self.progress_changed.emit(35, f"Conectando à nuvem para baixar os arquivos do Hub (v{INSTALLER_VERSION})...")
                import urllib.request
                import tempfile
                cloud_zip_url = "https://www.dropbox.com/scl/fi/p9oubha0cr0agwb77143r/HubDaBia_Suite.zip?rlkey=0gxz2ew1hwe6d1jf126l8nijj&dl=1"
                temp_fd, temp_zip = tempfile.mkstemp(suffix=".zip", prefix="hub_install_")
                os.close(temp_fd)

                req = urllib.request.Request(
                    cloud_zip_url,
                    headers={"User-Agent": f"Mozilla/5.0 HubDaBia-Installer/{INSTALLER_VERSION}"}
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    total_size = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    block_size = 1024 * 64
                    with open(temp_zip, "wb") as f_out:
                        while True:
                            chunk = resp.read(block_size)
                            if not chunk:
                                break
                            f_out.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                pct = int(35 + (downloaded / total_size) * 30)
                                mb_down = downloaded / (1024 * 1024)
                                mb_tot = total_size / (1024 * 1024)
                                self.progress_changed.emit(
                                    pct,
                                    f"Baixando arquivos: {mb_down:.1f} MB de {mb_tot:.1f} MB ({pct}%)"
                                )
                self.progress_changed.emit(65, "Extraindo arquivos baixados...")
                import zipfile
                with zipfile.ZipFile(temp_zip, "r") as zf:
                    zf.extractall(target_dir)
                try:
                    os.remove(temp_zip)
                except Exception:
                    pass
                installed_ok = os.path.exists(os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))

            if not installed_ok:
                self.finished.emit(False, f"Falha ao gravar arquivos em {target_dir}")
                return

            self.step_completed.emit(2, "Arquivos do programa instalados.")

            # Passo 3: Atalhos na Área de Trabalho e Menu Iniciar
            self.progress_changed.emit(70, "Criando atalhos na Área de Trabalho e Menu Iniciar...")
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            programs = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
            startup_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            desktop_lnk = os.path.join(desktop, "Hub da Bia.lnk")
            start_lnk = os.path.join(programs, "Hub da Bia.lnk")
            startup_lnk = os.path.join(startup_dir, "Hub da Bia.lnk")

            exe_name = "HubDaBia.exe"
            exe_path = os.path.join(target_dir, exe_name)
            if not os.path.exists(exe_path):
                exe_path = os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe")

            vbs_script = (
                'Set ws = CreateObject("WScript.Shell")\n'
                f'Set s1 = ws.CreateShortcut("{desktop_lnk}")\n'
                f's1.TargetPath = "{exe_path}"\n'
                f's1.WorkingDirectory = "{target_dir}"\n'
                's1.Description = "Hub da Bia - Suíte Pessoal de Produtividade"\n'
                f's1.IconLocation = "{icon_target},0"\n'
                's1.Save\n\n'
                f'Set s2 = ws.CreateShortcut("{start_lnk}")\n'
                f's2.TargetPath = "{exe_path}"\n'
                f's2.WorkingDirectory = "{target_dir}"\n'
                's2.Description = "Hub da Bia - Suíte Pessoal de Produtividade"\n'
                f's2.IconLocation = "{icon_target},0"\n'
                's2.Save\n\n'
                f'Set s3 = ws.CreateShortcut("{startup_lnk}")\n'
                f's3.TargetPath = "{exe_path}"\n'
                f's3.WorkingDirectory = "{target_dir}"\n'
                's3.Description = "Hub da Bia - Suíte Pessoal de Produtividade"\n'
                f's3.IconLocation = "{icon_target},0"\n'
                's3.Save\n'
            )
            vbs_temp = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "hub_shortcuts.vbs")
            with open(vbs_temp, "w", encoding="utf-8") as f:
                f.write(vbs_script)
            subprocess.run(["cscript", "//nologo", vbs_temp], capture_output=True)
            self.step_completed.emit(3, "Atalhos criados.")

            # Passo 4: Fixação opcional na Barra de Tarefas
            self.progress_changed.emit(85, "Fixando na Barra de Tarefas...")
            taskbar_dir = os.path.join(os.environ["APPDATA"], r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")
            if os.path.exists(taskbar_dir):
                taskbar_lnk = os.path.join(taskbar_dir, "Hub da Bia.lnk")
                try:
                    shutil.copy2(desktop_lnk, taskbar_lnk)
                except Exception:
                    pass
            self.step_completed.emit(4, "Fixado na Barra de Tarefas.")

            # Passo 5: Atualizar cache de ícones
            self.progress_changed.emit(95, "Finalizando...")
            try:
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            except Exception:
                pass
            self.step_completed.emit(5, "Cache de ícones atualizado.")

            self.progress_changed.emit(100, "Concluído!")
            self.finished.emit(True, os.path.join(target_dir, f"HubDaBia-v{INSTALLER_VERSION}.exe"))

        except Exception as e:
            self.finished.emit(False, str(e))


# ==================== UI SIMPLES E LIMPA ====================
class InstallerGUI(QDialog):
    def __init__(self):
        super().__init__()
        self.exe_target = None
        self.setWindowTitle("Instalador — Hub da Bia")
        self.resize(480, 380)
        self.setFixedSize(480, 380)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.init_ui()
        self.start_installation()

    def init_ui(self):
        # Container principal com bordas arredondadas
        container = QFrame(self)
        container.setObjectName("Container")
        container.setStyleSheet("""
            QFrame#Container {
                background-color: #0F1117;
                border: 1px solid #1E2330;
                border-radius: 16px;
            }
            QLabel {
                color: #E2E8F0;
            }
            QProgressBar {
                background-color: #161B26;
                border: 1px solid #1E293B;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: 600;
                height: 16px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #38BDF8);
                border-radius: 5px;
            }
            QPushButton#ActionBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #38BDF8);
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                padding: 14px 28px;
                min-height: 24px;
            }
            QPushButton#ActionBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
            }
            QPushButton#ActionBtn:disabled {
                background: #334155;
                color: #64748B;
            }
        """)

        # Sombra
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(container)

        # Layout interno do container
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        title = QLabel("Hub da Bia")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #F8FAFC; letter-spacing: -0.5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(f"Instalador v{INSTALLER_VERSION}")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #64748B;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Divisor
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #1E293B; max-height: 1px;")
        layout.addWidget(divider)

        # Status
        self.status_lbl = QLabel("Iniciando...")
        self.status_lbl.setFont(QFont("Segoe UI", 11))
        self.status_lbl.setStyleSheet("color: #38BDF8;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        layout.addSpacing(12)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        layout.addSpacing(20)

        # Botão
        self.action_btn = QPushButton("Instalando...")
        self.action_btn.setObjectName("ActionBtn")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setEnabled(False)
        self.action_btn.setFixedHeight(44)
        self.action_btn.clicked.connect(self.finish_and_launch)
        layout.addWidget(self.action_btn)

        layout.addSpacing(8)

        # Footer
        footer = QLabel("Hub da Bia — Craft Suite")
        footer.setFont(QFont("Segoe UI", 9))
        footer.setStyleSheet("color: #475569;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def start_installation(self):
        self.worker = InstallWorker()
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.step_completed.connect(self._on_step_completed)
        self.worker.finished.connect(self._on_finished)
        QTimer.singleShot(300, self.worker.start)

    def _on_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.status_lbl.setText(msg)

    def _on_step_completed(self, step_idx: int, msg: str):
        self.status_lbl.setText(msg)

    def _on_finished(self, success: bool, payload: str):
        if success:
            self.exe_target = payload
            self.status_lbl.setText("✨ Instalação concluída com sucesso!")
            self.status_lbl.setStyleSheet("color: #10B981; font-weight: 600;")
            self.action_btn.setEnabled(True)
            self.action_btn.setText("Abrir Hub da Bia 🚀")
        else:
            self.status_lbl.setText(f"❌ Erro: {payload}")
            self.status_lbl.setStyleSheet("color: #EF4444; font-weight: 600;")
            QMessageBox.critical(self, "Erro", f"Falha na instalação:\n\n{payload}")

    def finish_and_launch(self):
        if not self.exe_target:
            QMessageBox.critical(self, "Erro", "Caminho do executável não definido.")
            return
        if not os.path.exists(self.exe_target):
            QMessageBox.critical(self, "Erro", f"Executável não encontrado:\n{self.exe_target}")
            return
        try:
            subprocess.Popen(
                [self.exe_target],
                cwd=os.path.dirname(self.exe_target),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Falha ao iniciar:\n{e}\n\nTentando método alternativo...")
            try:
                os.startfile(self.exe_target)
                self.accept()
            except Exception as e2:
                QMessageBox.critical(self, "Erro", f"Não foi possível abrir:\n{e2}")

    # Drag window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hub da Bia Installer")
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = InstallerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()