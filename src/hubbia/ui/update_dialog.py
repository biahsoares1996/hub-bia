# -*- coding: utf-8 -*-
"""
Janela Moderna e Profissional de Atualização Automática do Hub da Bia
Exibe progresso, detalhes da versão, changelog e aplica a atualização silenciosamente.
"""

import os
import sys
import tempfile
import urllib.request
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QCursor

class SelfUpdateWorker(QThread):
    progress_changed = Signal(int, str)
    update_finished = Signal(bool, str)

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            zip_url = self.update_info.get(
                "zip_url",
                "https://github.com/biahsoares1996/hub-bia/releases/latest/download/HubDaBia_Suite.zip"
            )
            version = self.update_info.get("version", "mais recente")

            self.progress_changed.emit(5, f"Conectando ao servidor seguro (v{version})...")

            req = urllib.request.Request(
                zip_url,
                headers={"User-Agent": f"Mozilla/5.0 HubDaBia-AutoUpdater/{version}"}
            )

            temp_fd, temp_zip = tempfile.mkstemp(suffix=".zip", prefix="hub_update_")
            os.close(temp_fd)

            with urllib.request.urlopen(req, timeout=60) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                block_size = 1024 * 64

                with open(temp_zip, "wb") as f_out:
                    while True:
                        if self._is_cancelled:
                            self.update_finished.emit(False, "Atualização cancelada.")
                            try:
                                os.remove(temp_zip)
                            except Exception:
                                pass
                            return

                        chunk = resp.read(block_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int(5 + (downloaded / total_size) * 80)
                            mb_down = downloaded / (1024 * 1024)
                            mb_tot = total_size / (1024 * 1024)
                            self.progress_changed.emit(
                                percent,
                                f"Baixando nova versão: {mb_down:.1f} MB de {mb_tot:.1f} MB ({percent}%)"
                            )
                        else:
                            mb_down = downloaded / (1024 * 1024)
                            self.progress_changed.emit(50, f"Baixando nova versão: {mb_down:.1f} MB...")

            self.progress_changed.emit(90, "Extraindo pacote de atualização...")

            # 2. Extrair em pasta temporária
            temp_extract = tempfile.mkdtemp(prefix="hub_extract_")
            import zipfile
            with zipfile.ZipFile(temp_zip, "r") as zf:
                zf.extractall(temp_extract)

            self.progress_changed.emit(95, "Preparando reinicialização do Hub...")

            # 3. Gerar script VBS/BAT auxiliar que aguarda o Hub fechar, substitui e reabre
            current_pid = os.getpid()
            install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\HubDaBia")
            exe_target = os.path.join(install_dir, "HubDaBia.exe")

            # Fallback se executado fora de %LOCALAPPDATA%
            if getattr(sys, "frozen", False):
                frozen_dir = os.path.dirname(sys.executable)
                if os.path.exists(os.path.join(frozen_dir, "HubDaBia.exe")):
                    install_dir = frozen_dir
                    exe_target = os.path.join(frozen_dir, "HubDaBia.exe")
                elif os.path.exists(sys.executable):
                    install_dir = frozen_dir
                    exe_target = sys.executable

            helper_bat = os.path.join(tempfile.gettempdir(), "hub_apply_update.bat")
            bat_content = f'''@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul

rem 1. Aguardar o encerramento do processo anterior
:WAIT_LOOP
tasklist /FI "PID eq {current_pid}" 2>NUL | find /I "{current_pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

rem 2. Aplicar arquivos novos
robocopy "{temp_extract}" "{install_dir}" /E /NP /R:3 /W:1 >nul

rem 3. Limpar temporarios
del /f /q "{temp_zip}" >nul 2>&1
rd /s /q "{temp_extract}" >nul 2>&1

rem 4. Reabrir o Hub atualizado
if exist "{install_dir}\\HubDaBia.exe" (
    start "" "{install_dir}\\HubDaBia.exe"
) else if exist "{install_dir}\\HubDaBia-v{version}.exe" (
    start "" "{install_dir}\\HubDaBia-v{version}.exe"
) else (
    for /f "delims=" %%f in ('dir /b /o-d "{install_dir}\\HubDaBia*.exe"') do (
        start "" "{install_dir}\\%%f"
        goto FINISH
    )
)
:FINISH
exit
'''
            with open(helper_bat, "w", encoding="utf-8") as f:
                f.write(bat_content)

            self.progress_changed.emit(100, "Pronto! Reiniciando...")
            self.update_finished.emit(True, helper_bat)

        except Exception as e:
            self.update_finished.emit(False, f"Erro ao aplicar atualização: {e}")


class UpdateDialog(QDialog):
    """Tela moderna de atualização automática do Hub da Bia."""

    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.worker = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(500, 320)

        self.init_ui()

    def init_ui(self):
        container = QFrame(self)
        container.setObjectName("UpdateContainer")
        container.setStyleSheet("""
            QFrame#UpdateContainer {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(container)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(container)

        box = QVBoxLayout(container)
        box.setContentsMargins(24, 24, 24, 24)
        box.setSpacing(14)

        # 1. Cabeçalho com Ícone e Título
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_lbl = QLabel("✨")
        icon_lbl.setStyleSheet("""
            font-size: 24px;
            background-color: #1E293B;
            border-radius: 8px;
            padding: 6px;
        """)
        header.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        title_lbl = QLabel("Atualização do Hub da Bia")
        title_lbl.setStyleSheet("color: #F8FAFC; font-size: 16px; font-weight: 700;")
        title_vbox.addWidget(title_lbl)

        ver = self.update_info.get("version", "Nova Versão")
        self.sub_lbl = QLabel(f"Versão {ver} pronta para ser aplicada automaticamente.")
        self.sub_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 500;")
        title_vbox.addWidget(self.sub_lbl)

        header.addLayout(title_vbox)
        header.addStretch()
        box.addLayout(header)

        # 2. Resumo das Novidades (Changelog)
        self.changes_frame = QFrame()
        self.changes_frame.setStyleSheet("""
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px;
        """)
        cf_layout = QVBoxLayout(self.changes_frame)
        cf_layout.setContentsMargins(8, 8, 8, 8)
        cf_layout.setSpacing(4)

        ch_title = QLabel("O que há de novo:")
        ch_title.setStyleSheet("color: #E2E8F0; font-size: 11px; font-weight: 700; text-transform: uppercase;")
        cf_layout.addWidget(ch_title)

        changelog = self.update_info.get("changelog", ["Melhorias de desempenho e estabilidade"])
        for item in changelog[:3]: # primeiras 3 linhas
            line = QLabel(f"• {item}")
            line.setStyleSheet("color: #94A3B8; font-size: 12px;")
            line.setWordWrap(True)
            cf_layout.addWidget(line)

        box.addWidget(self.changes_frame)

        # 3. Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #38BDF8);
                border-radius: 4px;
            }
        """)
        self.progress_bar.setVisible(False)
        box.addWidget(self.progress_bar)

        # 4. Status de Progresso
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        self.status_lbl.setVisible(False)
        box.addWidget(self.status_lbl)

        box.addStretch()

        # 5. Botões de Ação
        self.btn_row = QHBoxLayout()
        self.btn_row.setSpacing(10)
        self.btn_row.addStretch()

        self.cancel_btn = QPushButton("Mais tarde")
        self.cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1E293B;
                color: #F8FAFC;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        self.btn_row.addWidget(self.cancel_btn)

        self.action_btn = QPushButton("Atualizar Agora")
        self.action_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 7px 20px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
            }
        """)
        self.action_btn.clicked.connect(self._start_update)
        self.btn_row.addWidget(self.action_btn)

        box.addLayout(self.btn_row)

    def _start_update(self):
        self.action_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelar")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self._cancel_update)

        self.changes_frame.setVisible(False)
        self.progress_bar.setVisible(True)
        self.status_lbl.setVisible(True)
        self.sub_lbl.setText("Baixando e aplicando a atualização silenciosamente...")

        self.worker = SelfUpdateWorker(self.update_info, self)
        self.worker.progress_changed.connect(self._on_progress)
        self.worker.update_finished.connect(self._on_finished)
        self.worker.start()

    def _cancel_update(self):
        if self.worker:
            self.worker.cancel()
        self.reject()

    def _on_progress(self, val: int, text: str):
        self.progress_bar.setValue(val)
        self.status_lbl.setText(text)

    def _on_finished(self, success: bool, message_or_script: str):
        if success:
            self.status_lbl.setText("✨ Atualização pronta! Reiniciando em 2 segundos...")
            import subprocess
            # Disparar helper_bat em segundo plano desanexado
            subprocess.Popen(
                ["cmd.exe", "/c", message_or_script],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            # Fechar aplicação imediatamente para liberar os arquivos
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, lambda: sys.exit(0))
        else:
            self.status_lbl.setText(f"❌ {message_or_script}")
            self.status_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
            self.action_btn.setEnabled(True)
            self.action_btn.setText("Tentar Novamente")
            self.cancel_btn.setText("Fechar")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.reject)
