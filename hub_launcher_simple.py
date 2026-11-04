# -*- coding: utf-8 -*-
"""
Hub da Bia - Launcher Simples (Usuário Final)
Apenas: Abrir Hub, Atualizar, Configurações
"""

import sys
import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QProcess, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor

# ==================== ESTILO SIMPLES ====================
SIMPLE_QSS = """
QMainWindow {
    background-color: #0F1117;
    border: 1px solid #1E2330;
}

QWidget {
    background-color: #0F1117;
    color: #E2E8F0;
    font-family: "Segoe UI", Arial, sans-serif;
}

#MainCard {
    background-color: #141721;
    border: 1px solid #1E2330;
    border-radius: 16px;
}

#TitleLabel {
    font-size: 28px;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.5px;
}

#SubtitleLabel {
    font-size: 14px;
    color: #64748B;
    margin-bottom: 8px;
}

#ActionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    border: none;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
    padding: 16px 32px;
    min-height: 24px;
    min-width: 280px;
}

#ActionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
}

#ActionBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E40AF, stop:1 #1D4ED8);
}

#SecondaryBtn {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
    padding: 12px 24px;
    min-width: 180px;
}

#SecondaryBtn:hover {
    background-color: #334155;
    color: #F8FAFC;
    border-color: #38BDF8;
}

#UpdateBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    border: none;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 700;
    padding: 16px 32px;
    min-width: 280px;
}

#UpdateBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

#VersionLabel {
    font-size: 12px;
    color: #64748B;
    padding-top: 8px;
}

#StatusLabel {
    font-size: 13px;
    color: #38BDF8;
    padding: 8px;
}
"""

# ==================== THREAD DE ATUALIZAÇÃO ====================
class UpdateCheckerThread(QThread):
    progress = Signal(str)
    finished = Signal(bool, str, dict)  # success, message, update_info
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            import urllib.request
            import json
            
            self.progress.emit("Conectando ao servidor de atualizações...")
            
            url = "https://www.dropbox.com/scl/fi/iksyr3qpxfuhrdd6trfp9/version.json?rlkey=brbhu3ruuqmo0cwhdehzbc8na&dl=1"
            req = urllib.request.Request(url, headers={"User-Agent": f"HubDaBia-Updater/{self.current_version}"})
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            remote_ver = data.get("version", self.current_version)
            
            self.progress.emit(f"Versão local: {self.current_version} | Remota: {remote_ver}")
            
            from packaging.version import parse as parse_version
            if parse_version(remote_ver) > parse_version(self.current_version):
                self.finished.emit(True, f"Nova versão {remote_ver} disponível!", data)
            else:
                self.finished.emit(False, "Você já está na versão mais recente.", {})
                
        except Exception as e:
            self.finished.emit(False, f"Erro ao verificar: {e}", {})


class UpdateDownloaderThread(QThread):
    progress = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, update_info):
        super().__init__()
        self.update_info = update_info
    
    def run(self):
        try:
            import urllib.request
            import tempfile
            import zipfile
            import subprocess
            import os
            
            zip_url = self.update_info.get("zip_url", 
                "https://www.dropbox.com/scl/fi/p9oubha0cr0agwb77143r/HubDaBia_Suite.zip?rlkey=0gxz2ew1hwe6d1jf126l8nijj&dl=1")
            
            self.progress.emit(5, "Baixando atualização...")
            
            req = urllib.request.Request(zip_url, headers={"User-Agent": "HubDaBia-Updater"})
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                block = 1024 * 64
                
                fd, tmp_path = tempfile.mkstemp(suffix=".zip", prefix="hub_update_")
                os.close(fd)
                
                with open(tmp_path, "wb") as f:
                    while True:
                        chunk = resp.read(block)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(5 + (downloaded / total) * 85)
                            mb_d = downloaded / (1024*1024)
                            mb_t = total / (1024*1024)
                            self.progress.emit(pct, f"Baixando: {mb_d:.1f} MB / {mb_t:.1f} MB ({pct}%)")
            
            self.progress.emit(90, "Aplicando atualização...")
            
            # Extrai e aplica
            install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\HubDaBia")
            os.makedirs(install_dir, exist_ok=True)
            
            # Mata processo antigo
            subprocess.run(["taskkill", "/F", "/IM", "HubDaBia.exe", "/T"], capture_output=True)
            import time
            time.sleep(1)
            
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(install_dir)
            
            os.remove(tmp_path)
            
            self.progress.emit(100, "Atualização concluída!")
            self.finished.emit(True, f"Hub da Bia atualizado para {self.update_info.get('version', 'nova versão')}!")
            
        except Exception as e:
            self.finished.emit(False, f"Erro na atualização: {e}")


# ==================== JANELA PRINCIPAL ====================
class SimpleLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_version = self.get_version()
        self.update_info = {}
        self.init_ui()
    
    def get_version(self):
        try:
            import json
            with open("version.json", "r", encoding="utf-8") as f:
                return json.load(f).get("version", "2.6.0")
        except:
            return "2.6.0"
    
    def init_ui(self):
        self.setWindowTitle("Hub da Bia")
        self.setFixedSize(480, 520)
        self.setStyleSheet(SIMPLE_QSS)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # Central widget com card
        central = QWidget()
        central.setObjectName("MainCard")
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("HUB DA BIA")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Suíte Pessoal de Produtividade")
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        version_lbl = QLabel(f"Versão {self.current_version}")
        version_lbl.setObjectName("VersionLabel")
        version_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_lbl)
        
        layout.addSpacing(16)
        
        # Botão principal: ABRIR HUB
        self.open_btn = QPushButton("🚀  ABRIR HUB DA BIA")
        self.open_btn.setObjectName("ActionBtn")
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self.open_hub)
        layout.addWidget(self.open_btn, alignment=Qt.AlignCenter)
        
        layout.addSpacing(12)
        
        # Botão secundário: ATUALIZAR
        self.update_btn = QPushButton("🔄  VERIFICAR ATUALIZAÇÕES")
        self.update_btn.setObjectName("UpdateBtn")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(self.check_updates)
        layout.addWidget(self.update_btn, alignment=Qt.AlignCenter)
        
        layout.addSpacing(16)
        
        # Botões secundários linha
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        config_btn = QPushButton("⚙  Configurações")
        config_btn.setObjectName("SecondaryBtn")
        config_btn.setCursor(Qt.PointingHandCursor)
        config_btn.clicked.connect(self.open_config)
        btn_row.addWidget(config_btn)
        
        folder_btn = QPushButton("📁  Pasta do Hub")
        folder_btn.setObjectName("SecondaryBtn")
        folder_btn.setCursor(Qt.PointingHandCursor)
        folder_btn.clicked.connect(self.open_folder)
        btn_row.addWidget(folder_btn)
        
        layout.addLayout(btn_row)
        
        layout.addSpacing(20)
        
        # Status bar
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("StatusLabel")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setVisible(False)
        layout.addWidget(self.status_lbl)
        
        layout.addStretch()
        
        # Window controls (minimal)
        controls = QHBoxLayout()
        controls.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 18px;
                color: #64748B;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #EF4444;
                color: white;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        controls.addWidget(close_btn)
        
        layout.addLayout(controls)
    
    # ==================== AÇÕES ====================
    def open_hub(self):
        """Abre o Hub da Bia"""
        exe_path = Path(r"%LOCALAPPDATA%\Programs\HubDaBia\HubDaBia.exe").expanduser()
        if not exe_path.exists():
            # Tenta na pasta dist local
            exe_path = Path("dist/HubDaBia/HubDaBia.exe")
        
        if exe_path.exists():
            try:
                subprocess.Popen(
                    [str(exe_path)],
                    cwd=str(exe_path.parent),
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    close_fds=True
                )
                self.close()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível abrir o Hub:\n{e}")
        else:
            QMessageBox.warning(self, "Não encontrado", 
                "HubDaBia.exe não encontrado.\nExecute o instalador ou compile primeiro.")
    
    def check_updates(self):
        """Verifica atualizações"""
        self.update_btn.setEnabled(False)
        self.update_btn.setText("🔄  Verificando...")
        self.show_status("Conectando ao servidor...", "#38BDF8")
        
        self.update_thread = UpdateCheckerThread(self.current_version)
        self.update_thread.progress.connect(lambda m: self.show_status(m, "#38BDF8"))
        self.update_thread.finished.connect(self.on_update_check_finished)
        self.update_thread.start()
    
    def on_update_check_finished(self, has_update, message, info):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("🔄  VERIFICAR ATUALIZAÇÕES")
        
        if has_update:
            self.update_info = info
            self.show_status(f"✨ {message}", "#10B981")
            self.update_btn.setText("✨  ATUALIZAR AGORA")
            self.update_btn.setObjectName("UpdateBtn")
            self.update_btn.setStyleSheet("")  # força refresh
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self.do_update)
        else:
            self.show_status(message, "#38BDF8")
            QTimer.singleShot(3000, lambda: self.status_lbl.setVisible(False))
    
    def do_update(self):
        """Executa download e instalação da atualização"""
        self.update_btn.setEnabled(False)
        self.update_btn.setText("🔄  Baixando...")
        
        self.download_thread = UpdateDownloaderThread(self.update_info)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_progress(self, pct, msg):
        self.update_btn.setText(f"🔄  {pct}%")
        self.show_status(msg, "#38BDF8")
    
    def on_download_finished(self, success, msg):
        self.update_btn.setEnabled(True)
        self.update_btn.setText("🔄  VERIFICAR ATUALIZAÇÕES")
        self.show_status(msg, "#10B981" if success else "#EF4444")
        
        if success:
            QTimer.singleShot(2000, self.close)
    
    def open_config(self):
        config_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "HubDaBiaDeploy"
        config_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(config_dir))
    
    def open_folder(self):
        hub_dir = Path(r"%LOCALAPPDATA%\Programs\HubDaBia").expanduser()
        if hub_dir.exists():
            os.startfile(str(hub_dir))
        else:
            os.startfile(str(Path("dist/HubDaBia").resolve()))
    
    def show_status(self, msg, color):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"color: {color}; font-size: 13px; padding: 8px;")
        self.status_lbl.setVisible(True)
    
    # Permite arrastar janela
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
    app.setApplicationName("Hub da Bia Launcher")
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = SimpleLauncher()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()