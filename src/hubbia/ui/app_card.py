# -*- coding: utf-8 -*-
"""
Widget de Card de Aplicativo do Hub da Bia
Inspirado nos cards de ferramentas do Craft Suite / ArtCraft.
"""

import os
from pathlib import Path
from hubbia.core.paths import get_asset_path
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsDropShadowEffect, QMenu
)
from PySide6.QtGui import QPixmap, QColor, QCursor, QAction
from PySide6.QtCore import Qt, Signal

class AppCard(QFrame):
    """Card interativo que representa um aplicativo da suíte."""
    launch_requested = Signal(dict)
    install_requested = Signal(dict)
    open_folder_requested = Signal(dict)
    update_requested = Signal(dict)
    terminate_requested = Signal(dict)
    uninstall_requested = Signal(dict)

    def __init__(self, app_info: dict, is_running: bool = False, is_installed: bool = True, has_update: bool = False, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self.is_running = is_running
        self.is_installed = is_installed
        self.has_update = has_update or self.app_info.get("has_update", False)
        self.setObjectName("AppCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumWidth(260)
        self.setFixedHeight(94)
        
        self.init_ui()
        self.update_states(is_running=is_running, is_installed=is_installed, has_update=self.has_update)

    def init_ui(self):
        # Sombra sutil de profundidade
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # 1. Ícone Compacto (34x34)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(36, 36)
        self.icon_label.setStyleSheet("""
            background-color: #1A202C;
            border-radius: 8px;
            border: 1px solid #2D3748;
            padding: 2px;
        """)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.load_icon()
        layout.addWidget(self.icon_label)

        # 2. Informações de Texto (Nome e Subtítulo)
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        text_col.setAlignment(Qt.AlignVCenter)

        # Linha do Título com Badge de Versão
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        title_row.setAlignment(Qt.AlignVCenter)

        self.title_lbl = QLabel(self.app_info.get("name", "App"))
        self.title_lbl.setObjectName("AppCardTitle")
        self.title_lbl.setTextFormat(Qt.PlainText)
        title_row.addWidget(self.title_lbl)

        self.version_badge = QLabel(self.app_info.get("version", ""))
        self.version_badge.setObjectName("AppCardVersionBadge")
        title_row.addWidget(self.version_badge)
        title_row.addStretch()

        text_col.addLayout(title_row)

        self.sub_lbl = QLabel(self.app_info.get("subtitle", ""))
        self.sub_lbl.setObjectName("AppCardSubtitle")
        self.sub_lbl.setTextFormat(Qt.PlainText)
        text_col.addWidget(self.sub_lbl)

        layout.addLayout(text_col, 1)

        # 3. Cluster de Ações (Layout Vertical em 2 Linhas: Topo = Abrir/Encerrar; Base = Atualizado/Atualizar + Desinstalar)
        actions_col = QVBoxLayout()
        actions_col.setContentsMargins(0, 0, 0, 0)
        actions_col.setSpacing(5)
        actions_col.setAlignment(Qt.AlignVCenter)

        # Linha 1: Ação Principal (Largura 172px)
        self.top_container = QWidget()
        self.top_container.setFixedWidth(172)
        top_layout = QHBoxLayout(self.top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # Botão Principal (Abrir / ⏹ Encerrar / ⬇ Instalar)
        self.action_btn = QPushButton("Abrir")
        self.action_btn.setObjectName("LaunchBtn")
        self.action_btn.setFixedHeight(28)
        self.action_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.action_btn.clicked.connect(self._on_action_click)

        # Split dropdown se houver múltiplas ações (mais de 1)
        self.extra_actions = self.app_info.get("actions", [])
        self.split_btn = None
        if len(self.extra_actions) > 1:
            self.action_btn.setFixedWidth(148)
            self.action_btn.setStyleSheet("border-top-right-radius: 0px; border-bottom-right-radius: 0px;")
            top_layout.addWidget(self.action_btn)

            self.split_btn = QPushButton("⌄")
            self.split_btn.setObjectName("LaunchSplitMenuBtn")
            self.split_btn.setFixedWidth(24)
            self.split_btn.setFixedHeight(28)
            self.split_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.split_btn.setToolTip("Mais opções")
            self.split_btn.clicked.connect(self._show_extra_actions_menu)
            top_layout.addWidget(self.split_btn)
        else:
            self.action_btn.setFixedWidth(172)
            top_layout.addWidget(self.action_btn)

        actions_col.addWidget(self.top_container)

        # Linha 2: Ações Secundárias (Atualizado/Atualizar + Desinstalar)
        self.bot_container = QWidget()
        self.bot_container.setFixedWidth(172)
        bot_layout = QHBoxLayout(self.bot_container)
        bot_layout.setContentsMargins(0, 0, 0, 0)
        bot_layout.setSpacing(6)

        # Botão Atualizado / Atualizar (83px de largura)
        self.update_btn = QPushButton("Atualizado")
        self.update_btn.setObjectName("UpdateIdleBtn")
        self.update_btn.setFixedSize(83, 24)
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.clicked.connect(lambda: self.update_requested.emit(self.app_info))
        bot_layout.addWidget(self.update_btn)

        # Botão Desinstalar (83px de largura)
        self.uninstall_btn = QPushButton("Desinstalar")
        self.uninstall_btn.setObjectName("UninstallCardBtn")
        self.uninstall_btn.setFixedSize(83, 24)
        self.uninstall_btn.setToolTip(f"Desinstalar {self.app_info.get('name', 'o aplicativo')} deste computador.")
        self.uninstall_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.uninstall_btn.clicked.connect(lambda: self.uninstall_requested.emit(self.app_info))
        bot_layout.addWidget(self.uninstall_btn)

        actions_col.addWidget(self.bot_container)
        layout.addLayout(actions_col)

    def load_icon(self):
        icon_path = self.app_info.get("icon", "")
        full_path = get_asset_path(icon_path)

        if full_path.exists():
            pix = QPixmap(str(full_path))
            if not pix.isNull():
                self.icon_label.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        
        # Fallback de letra inicial
        initial = self.app_info.get("name", "A")[:1].upper()
        self.icon_label.setText(initial)
        self.icon_label.setStyleSheet("""
            background-color: #2563EB;
            color: white;
            font-size: 16px;
            font-weight: 800;
            border-radius: 8px;
        """)

    def update_running_state(self, is_running: bool):
        self.update_states(is_running=is_running, is_installed=self.is_installed)

    def update_states(self, is_running: bool = None, is_installed: bool = None, has_update: bool = None):
        if is_running is not None:
            self.is_running = is_running
        if is_installed is not None:
            self.is_installed = is_installed
        if has_update is not None:
            self.has_update = has_update

        if not self.is_installed:
            # Não instalado: Exibe apenas botão grande ⬇ Instalar centralizado
            self.action_btn.setText("⬇ Instalar")
            self.action_btn.setObjectName("InstallCardBtn")
            self.action_btn.setFixedHeight(32)
            self.action_btn.setFixedWidth(172)
            self.action_btn.setStyleSheet("")
            self.action_btn.setToolTip(f"Baixar e instalar {self.app_info.get('name', 'o aplicativo')} a partir da nuvem.")
            if self.split_btn:
                self.split_btn.setVisible(False)
            self.bot_container.setVisible(False)
        else:
            # Instalado: Linha 1 = Abrir / Encerrar; Linha 2 = Atualizado/Atualizar + Desinstalar
            self.bot_container.setVisible(True)
            self.action_btn.setFixedHeight(28)

            if self.split_btn:
                self.action_btn.setFixedWidth(148)
                self.action_btn.setStyleSheet("border-top-right-radius: 0px; border-bottom-right-radius: 0px;")
                self.split_btn.setVisible(True)
            else:
                self.action_btn.setFixedWidth(172)
                self.action_btn.setStyleSheet("")

            if self.is_running:
                self.action_btn.setText("⏹ Encerrar")
                self.action_btn.setObjectName("TerminateCardBtn")
                self.action_btn.setToolTip("Encerrar o aplicativo e seus processos.")
            else:
                self.action_btn.setText("Abrir")
                self.action_btn.setObjectName("LaunchBtn")
                self.action_btn.setToolTip("Iniciar o aplicativo.")

            if self.has_update:
                self.update_btn.setText("Atualizar")
                self.update_btn.setObjectName("UpdateActiveBtn")
                self.update_btn.setToolTip(f"Nova versão {self.app_info.get('version', '')} disponível! Clique para atualizar pelo Hub.")
            else:
                self.update_btn.setText("Atualizado")
                self.update_btn.setObjectName("UpdateIdleBtn")
                self.update_btn.setToolTip(f"{self.app_info.get('name', 'O aplicativo')} está na versão mais recente.")

        # Atualizar Badge de Versão do Card
        target_ver = self.app_info.get("version", "")
        try:
            from hubbia.core.launcher import AppManager
            installed_versions = AppManager().get_installed_versions()
            installed_ver = installed_versions.get(self.app_info.get("id"), "")
        except Exception:
            installed_ver = ""

        if self.is_installed and self.has_update and installed_ver and installed_ver != target_ver:
            self.version_badge.setText(f"{installed_ver} ➜ {target_ver}")
            self.version_badge.setObjectName("AppCardVersionBadgeUpdate")
            self.version_badge.setToolTip(f"Versão instalada: {installed_ver}\nNova versão disponível: {target_ver}")
        elif self.is_installed and installed_ver:
            self.version_badge.setText(installed_ver)
            self.version_badge.setObjectName("AppCardVersionBadge")
            self.version_badge.setToolTip(f"Versão instalada: {installed_ver}")
        else:
            self.version_badge.setText(target_ver)
            self.version_badge.setObjectName("AppCardVersionBadge")
            self.version_badge.setToolTip(f"Versão disponível: {target_ver}")

        self.version_badge.style().unpolish(self.version_badge)
        self.version_badge.style().polish(self.version_badge)
        self.action_btn.style().unpolish(self.action_btn)
        self.action_btn.style().polish(self.action_btn)
        self.update_btn.style().unpolish(self.update_btn)
        self.update_btn.style().polish(self.update_btn)
        self.uninstall_btn.style().unpolish(self.uninstall_btn)
        self.uninstall_btn.style().polish(self.uninstall_btn)

    def _on_action_click(self):
        if self.is_running:
            self.terminate_requested.emit(self.app_info)
        elif self.is_installed:
            self.launch_requested.emit(self.app_info)
        else:
            self.install_requested.emit(self.app_info)

    def _show_extra_actions_menu(self):
        if not self.extra_actions or not self.split_btn:
            return
        menu = QMenu(self)
        for act in self.extra_actions:
            title = act.get("title", "Executar")
            target_path = act.get("target", "")
            action_item = menu.addAction(title)
            action_item.triggered.connect(lambda chk=False, t=target_path: self._run_custom_target(t))
        
        # Posicionar menu logo abaixo do botão
        pos = self.split_btn.mapToGlobal(self.split_btn.rect().bottomLeft())
        menu.exec(pos)

    def _run_custom_target(self, target_path: str):
        if not target_path:
            return
        # Copiar app_info substituindo o executável temporariamente
        custom_info = dict(self.app_info)
        custom_info["executable"] = target_path
        self.launch_requested.emit(custom_info)

    def mouseDoubleClickEvent(self, event):
        # Duplo clique no card também abre o app
        self.launch_requested.emit(self.app_info)
        super().mouseDoubleClickEvent(event)
