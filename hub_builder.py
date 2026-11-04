# -*- coding: utf-8 -*-
"""
Hub da Bia - Builder & Deploy (Ferramenta de Desenvolvedor)
3 Ações: Compilar (build + upload Dropbox) | Instalar | Desinstalar
"""

import sys
import os
import subprocess
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QProgressDialog,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QProcess, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QTextCursor

# ==================== ESTILO DEV TOOL ====================
DEV_QSS = """
QMainWindow {
    background-color: #0D1117;
    border: 1px solid #1E2330;
}

QWidget {
    background-color: #0D1117;
    color: #E2E8F0;
    font-family: "Segoe UI", Arial, sans-serif;
}

#MainCard {
    background-color: #141721;
    border: 1px solid #1E2330;
    border-radius: 12px;
}

#TitleLabel {
    font-size: 24px;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.5px;
}

#SubtitleLabel {
    font-size: 13px;
    color: #64748B;
}

#VersionLabel {
    font-size: 11px;
    color: #475569;
}

#ActionBtn {
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    padding: 18px 32px;
    min-height: 28px;
    min-width: 220px;
}

#BuildBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #A855F7);
}
#BuildBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #9333EA);
}

#InstallBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
}
#InstallBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

#UninstallBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
}
#UninstallBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
}

#ActionBtn:disabled {
    background: #334155;
    color: #64748B;
}

#LogOutput {
    background-color: #0D1117;
    border: 1px solid #1E2330;
    border-radius: 8px;
    color: #E2E8F0;
    font-family: "Consolas", "Cascadia Code", monospace;
    font-size: 11px;
    padding: 12px;
}

#LogHeader {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 1px;
    padding: 8px 12px;
    background: #1E2330;
    border-bottom: 1px solid #334155;
}

#ClearLogBtn {
    background: transparent;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 12px;
}
#ClearLogBtn:hover {
    background: #1E2330;
    color: #F8FAFC;
}

#StatusLabel {
    font-size: 12px;
    color: #38BDF8;
    padding: 8px 12px;
}

#VersionBadge {
    background: #1E293B;
    color: #94A3B8;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid #334155;
}
"""

# ==================== THREADS ====================
class BuildThread(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
    
    def get_version(self):
        try:
            import json
            with open(Path(self.project_dir) / "version.json", "r", encoding="utf-8") as f:
                return json.load(f).get("version", "2.6.0")
        except:
            return "2.6.0"
    
    def run(self):
        try:
            VERSION = self.get_version()
            hub_exe = f"dist/HubDaBia-v{VERSION}/HubDaBia-v{VERSION}.exe"
            installer_exe = f"Instalador_Hub_da_Bia-v{VERSION}.exe"
            hub_exe_dropbox = f"HubDaBia-v{VERSION}.exe"
            installer_dropbox = f"Instalador_Hub_da_Bia-v{VERSION}.exe"
            
            steps = [
                ("🔨 [1/6] Build HubDaBia.exe...", "python scripts/build_exe.py"),
                ("📦 [2/6] Build Instalador...", "python scripts/build_installer_exe.py"),
                ("☁️ [3/6] Upload HubDaBia.exe...", f"python scripts/upload_hub_dropbox.py {hub_exe} {hub_exe_dropbox}"),
                ("☁️ [4/6] Upload Instalador...", f"python scripts/upload_hub_dropbox.py {installer_exe} {installer_dropbox}"),
                ("☁️ [5/6] Upload Suite ZIP...", "python scripts/upload_hub_dropbox.py HubDaBia_Suite.zip HubDaBia_Suite.zip"),
                ("☁️ [6/6] Upload version.json + apps.json...", "python scripts/upload_hub_dropbox.py version.json version.json && python scripts/upload_hub_dropbox.py config/apps.json apps.json"),
            ]
            
            for i, (msg, cmd) in enumerate(steps):
                self.log.emit(msg)
                self.progress.emit(int((i / len(steps)) * 100))
                
                proc = subprocess.run(
                    cmd, shell=True, cwd=self.project_dir,
                    capture_output=True, text=True, encoding='utf-8', errors='replace'
                )
                
                if proc.stdout:
                    for line in proc.stdout.strip().split('\n'):
                        if line.strip():
                            self.log.emit(f"   {line}")
                
                if proc.returncode != 0:
                    err = proc.stderr.strip() if proc.stderr else "Erro desconhecido"
                    self.log.emit(f"   ❌ ERRO: {err}")
                    self.finished.emit(False, f"Falhou em: {msg}")
                    return
                
                self.log.emit(f"   ✅ OK")
            
            self.progress.emit(100)
            self.finished.emit(True, "🎉 Build + Deploy concluído com sucesso!")
            
        except Exception as e:
            self.finished.emit(False, f"Erro inesperado: {e}")


class InstallThread(QThread):
    log = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, installer_path):
        super().__init__()
        self.installer_path = installer_path
    
    def run(self):
        try:
            self.log.emit(f"📦 Executando instalador: {self.installer_path}")
            
            proc = subprocess.run(
                [self.installer_path],
                capture_output=True, text=True, encoding='utf-8', errors='replace'
            )
            
            if proc.stdout:
                for line in proc.stdout.strip().split('\n'):
                    if line.strip():
                        self.log.emit(f"   {line}")
            
            if proc.returncode == 0:
                self.log.emit("✅ Instalação concluída!")
                self.finished.emit(True, "Hub da Bia instalado com sucesso!")
            else:
                err = proc.stderr.strip() if proc.stderr else "Erro na instalação"
                self.log.emit(f"❌ Erro: {err}")
                self.finished.emit(False, f"Instalação falhou: {err}")
                
        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")


class UninstallThread(QThread):
    log = Signal(str)
    finished = Signal(bool, str)
    
    def run(self):
        try:
            self.log.emit("🗑 Iniciando desinstalação do Hub da Bia...")
            
            # 1. Mata processos
            self.log.emit("   Encerrando processos...")
            subprocess.run(["taskkill", "/F", "/IM", "HubDaBia.exe", "/T"], capture_output=True)
            
            # 2. Remove pasta de instalação
            install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "HubDaBia"
            if install_dir.exists():
                self.log.emit(f"   Removendo {install_dir}")
                import shutil
                shutil.rmtree(install_dir, ignore_errors=True)
                self.log.emit("   ✅ Pasta removida")
            else:
                self.log.emit("   Pasta de instalação não encontrada")
            
            # 3. Remove atalhos
            self.log.emit("   Removendo atalhos...")
            for base in [
                Path(os.environ.get("USERPROFILE", "")) / "Desktop",
                Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs",
                Path(os.environ.get("APPDATA", "")) / r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar"
            ]:
                for lnk in base.glob("Hub da Bia.lnk"):
                    try:
                        lnk.unlink()
                        self.log.emit(f"   Removido: {lnk}")
                    except:
                        pass
            
            # 4. Remove config local
            config_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "HubDaBiaDeploy"
            if config_dir.exists():
                self.log.emit(f"   Removendo config: {config_dir}")
                import shutil
                shutil.rmtree(config_dir, ignore_errors=True)
            
            self.log.emit("✅ Desinstalação concluída!")
            self.finished.emit(True, "Hub da Bia removido completamente!")
            
        except Exception as e:
            self.finished.emit(False, f"Erro na desinstalação: {e}")


# ==================== MAIN WINDOW ====================
class BuilderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_dir = Path(__file__).parent
        self.current_version = self.get_version()
        self.init_ui()
    
    def get_version(self):
        try:
            import json
            with open(self.project_dir / "version.json", "r", encoding="utf-8") as f:
                return json.load(f).get("version", "2.6.0")
        except:
            return "2.6.0"
    
    def init_ui(self):
        self.setWindowTitle("Hub da Bia - Builder & Deploy")
        self.resize(900, 650)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(DEV_QSS)
        
        # Central widget
        central = QWidget()
        central.setObjectName("MainCard")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(16)
        
        title = QLabel("HUB DA BIA")
        title.setObjectName("TitleLabel")
        header.addWidget(title)
        
        version_badge = QLabel(f"v{self.current_version}")
        version_badge.setObjectName("VersionBadge")
        header.addWidget(version_badge)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        subtitle = QLabel("Builder & Deploy Tool")
        subtitle.setObjectName("SubtitleLabel")
        layout.addWidget(subtitle)
        
        layout.addSpacing(8)
        
        # 3 BOTÕES PRINCIPAIS
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        
        # 1. BUILD
        self.build_btn = QPushButton("🔨  COMPILAR + DEPLOY")
        self.build_btn.setObjectName("BuildBtn")
        self.build_btn.setCursor(Qt.PointingHandCursor)
        self.build_btn.setToolTip("Build HubDaBia.exe + Instalador + Upload completo pro Dropbox (Ctrl+B)")
        self.build_btn.setShortcut("Ctrl+B")
        self.build_btn.clicked.connect(self.start_build)
        btn_row.addWidget(self.build_btn, 1)
        
        # 2. INSTALL
        self.install_btn = QPushButton("📦  INSTALAR")
        self.install_btn.setObjectName("InstallBtn")
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.setToolTip("Executa o Instalador_Hub_da_Bia.exe gerado (Ctrl+I)")
        self.install_btn.setShortcut("Ctrl+I")
        self.install_btn.clicked.connect(self.start_install)
        btn_row.addWidget(self.install_btn, 1)
        
        # 3. UNINSTALL
        self.uninstall_btn = QPushButton("🗑  DESINSTALAR")
        self.uninstall_btn.setObjectName("UninstallBtn")
        self.uninstall_btn.setCursor(Qt.PointingHandCursor)
        self.uninstall_btn.setToolTip("Remove Hub da Bia completamente do sistema (Ctrl+U)")
        self.uninstall_btn.setShortcut("Ctrl+U")
        self.uninstall_btn.clicked.connect(self.start_uninstall)
        btn_row.addWidget(self.uninstall_btn, 1)
        
        layout.addLayout(btn_row)
        
        layout.addSpacing(16)
        
        # LOG AREA
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("📋  LOG DE EXECUÇÃO"))
        log_header.addStretch()
        
        self.clear_log_btn = QPushButton("🗑 Limpar")
        self.clear_log_btn.setObjectName("ClearLogBtn")
        self.clear_log_btn.setCursor(Qt.PointingHandCursor)
        self.clear_log_btn.setShortcut("Ctrl+L")
        self.clear_log_btn.setToolTip("Limpar log (Ctrl+L)")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_header.addWidget(self.clear_log_btn)
        
        layout.addLayout(log_header)
        
        self.log_output = QTextEdit()
        self.log_output.setObjectName("LogOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log_output, 1)
        
        # Status bar
        self.status_lbl = QLabel("Pronto")
        self.status_lbl.setObjectName("StatusLabel")
        layout.addWidget(self.status_lbl)
        
        # Inicializa log
        self.log(f"Hub da Bia Builder v{self.current_version}")
        self.log(f"Diretório: {self.project_dir}")
        self.log("Pronto.\n")
    
    def log(self, msg, color="#E2E8F0"):
        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<span style="color: {color};">{msg}</span><br>')
        self.log_output.setTextCursor(cursor)
        self.log_output.ensureCursorVisible()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
    
    def clear_log(self):
        self.log_output.clear()
        self.log("Log limpo.")
    
    def set_busy(self, busy, btn=None):
        for b in [self.build_btn, self.install_btn, self.uninstall_btn]:
            b.setEnabled(not busy)
        if btn:
            btn.setEnabled(not busy)
    
    def start_build(self):
        self.set_busy(True, self.build_btn)
        self.build_btn.setText("🔨  COMPILANDO...")
        self.status_lbl.setText("Iniciando build + deploy...")
        self.log("=" * 60)
        self.log("🔨 INICIANDO BUILD + DEPLOY COMPLETO", "#A855F7")
        self.log("=" * 60)
        
        self.build_thread = BuildThread(str(self.project_dir))
        self.build_thread.log.connect(lambda m: self.log(m, "#38BDF8" if m.startswith("   ✅") else "#EF4444" if "❌" in m else "#E2E8F0"))
        self.build_thread.progress.connect(lambda p: self.status_lbl.setText(f"Build + Deploy: {p}%"))
        self.build_thread.finished.connect(self.on_build_finished)
        self.build_thread.start()
    
    def on_build_finished(self, success, msg):
        self.set_busy(False)
        self.build_btn.setText("🔨  COMPILAR + DEPLOY")
        self.status_lbl.setText(msg)
        self.log("=" * 60)
        if success:
            self.log(f"✅ {msg}", "#10B981")
        else:
            self.log(f"❌ {msg}", "#EF4444")
        self.log("=" * 60)
        if not success:
            QMessageBox.critical(self, "Build Falhou", msg)
    
    def start_install(self):
        VERSION = self.get_version()
        installer = self.project_dir / f"Instalador_Hub_da_Bia-v{VERSION}.exe"
        if not installer.exists():
            QMessageBox.warning(self, "Não encontrado", f"Instalador_Hub_da_Bia-v{VERSION}.exe não existe.\nExecute o Build primeiro.")
            return
        
        self.set_busy(True, self.install_btn)
        self.install_btn.setText("📦  INSTALANDO...")
        self.status_lbl.setText("Executando instalador...")
        self.log("=" * 60)
        self.log(f"📦 INICIANDO INSTALAÇÃO v{VERSION}", "#10B981")
        self.log("=" * 60)
        
        self.install_thread = InstallThread(str(installer))
        self.install_thread.log.connect(lambda m: self.log(m, "#38BDF8" if m.startswith("   ✅") else "#EF4444" if "❌" in m else "#E2E8F0"))
        self.install_thread.finished.connect(self.on_install_finished)
        self.install_thread.start()
    
    def on_install_finished(self, success, msg):
        self.set_busy(False)
        self.install_btn.setText("📦  INSTALAR")
        self.status_lbl.setText(msg)
        self.log("=" * 60)
        if success:
            self.log(f"✅ {msg}", "#10B981")
        else:
            self.log(f"❌ {msg}", "#EF4444")
        self.log("=" * 60)
        if not success:
            QMessageBox.critical(self, "Instalação Falhou", msg)
    
    def start_uninstall(self):
        reply = QMessageBox.question(
            self, "Confirmar Desinstalação",
            "Isso removerá COMPLETAMENTE o Hub da Bia:\n"
            "- Pasta em %LOCALAPPDATA%\\Programs\\HubDaBia\n"
            "- Atalhos (Desktop, Menu Iniciar, Barra de Tarefas)\n"
            "- Configurações locais\n\nContinuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        
        self.set_busy(True, self.uninstall_btn)
        self.uninstall_btn.setText("🗑  DESINSTALANDO...")
        self.status_lbl.setText("Desinstalando...")
        self.log("=" * 60)
        self.log("🗑 INICIANDO DESINSTALAÇÃO COMPLETA", "#EF4444")
        self.log("=" * 60)
        
        self.uninstall_thread = UninstallThread()
        self.uninstall_thread.log.connect(lambda m: self.log(m, "#38BDF8" if m.startswith("   ✅") else "#EF4444" if "❌" in m else "#E2E8F0"))
        self.uninstall_thread.finished.connect(self.on_uninstall_finished)
        self.uninstall_thread.start()
    
    def on_uninstall_finished(self, success, msg):
        self.set_busy(False)
        self.uninstall_btn.setText("🗑  DESINSTALAR")
        self.status_lbl.setText(msg)
        self.log("=" * 60)
        if success:
            self.log(f"✅ {msg}", "#10B981")
        else:
            self.log(f"❌ {msg}", "#EF4444")
        self.log("=" * 60)
        if not success:
            QMessageBox.critical(self, "Desinstalação Falhou", msg)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hub da Bia Builder")
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = BuilderWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()