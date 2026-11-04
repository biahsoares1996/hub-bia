# -*- coding: utf-8 -*-
"""
Janela Principal do Hub da Bia
Interface moderna inspirada no Craft Launcher (PhotoCraft / PdfCraft / ArtCraft)
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QFileDialog, QDialog,
    QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap, QCursor, QColor

from hubbia.core.launcher import AppManager, get_running_process_names
from hubbia.core.updater import UpdateCheckerThread, CURRENT_VERSION
from hubbia.core.app_installer import AppInstallerThread
from hubbia.core.paths import get_asset_path
from hubbia.ui.styles import DARK_THEME_QSS
from hubbia.ui.app_card import AppCard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_manager = AppManager()
        self.cards: list[AppCard] = []
        self.active_category = "Todos"
        self.search_query = ""

        # Drag da janela sem bordas
        self._drag_pos = QPoint()

        self.init_window()
        self.init_ui()
        self.init_tray()
        self.init_status_timer()
        self.init_periodic_update_checker()
        QTimer.singleShot(4000, self.check_updates_silent)

    def init_periodic_update_checker(self):
        """Verifica atualizações automaticamente a cada 60 segundos em background (sem pesar)."""
        self.periodic_update_timer = QTimer(self)
        self.periodic_update_timer.setInterval(60000) # 60 segundos
        self.periodic_update_timer.timeout.connect(self.check_updates_silent)
        self.periodic_update_timer.start()

    def init_window(self):
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(1060, 760)
        self.setMinimumSize(880, 580)
        self.setWindowTitle("Hub da Bia - Suíte Pessoal")

        # Ícone da Janela
        icon_path = get_asset_path("assets/hub_icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        from hubbia.ui.styles import get_theme_qss
        self.setStyleSheet(get_theme_qss())

    def init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # 1. Barra de Título Customizada
        self.title_bar = self._create_title_bar()
        main_vbox.addWidget(self.title_bar)

        # 2. Corpo (Conteúdo Direto - Sem Sidebar de Categorias)
        body_hbox = QHBoxLayout()
        body_hbox.setContentsMargins(0, 0, 0, 0)
        body_hbox.setSpacing(0)

        self.content_area = self._create_content_area()
        body_hbox.addWidget(self.content_area, 1)

        main_vbox.addLayout(body_hbox, 1)

        # Carregar Cards
        self.refresh_cards()

    # --- Barra de Título Customizada ---
    def _create_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TitleBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Logo / Título
        title_lbl = QLabel("HUB DA BIA")
        title_lbl.setObjectName("TitleLabel")
        layout.addWidget(title_lbl)

        version_badge = QLabel(f"CRAFT SUITE v{CURRENT_VERSION}")
        version_badge.setObjectName("TitleVersionBadge")
        layout.addWidget(version_badge)

        # Botão de Atualizações no Cabeçalho
        self.update_btn = QPushButton("🔄 Atualizações")
        self.update_btn.setObjectName("HeaderUpdateBtn")
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.setStyleSheet("""
            QPushButton#HeaderUpdateBtn {
                background: transparent;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
                color: #64748B;
            }
            QPushButton#HeaderUpdateBtn:hover {
                background: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.update_btn.clicked.connect(self.check_updates_manual)
        layout.addWidget(self.update_btn)

        layout.addStretch()

        # Botões da Janela
        min_btn = QPushButton("—")
        min_btn.setObjectName("WindowBtn")
        min_btn.clicked.connect(self.showMinimized)
        layout.addWidget(min_btn)

        self.max_btn = QPushButton("□")
        self.max_btn.setObjectName("WindowBtn")
        self.max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.max_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("WindowBtn")
        close_btn.setStyleSheet("""
            QPushButton#WindowBtn:hover {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return bar

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")
        else:
            self.showMaximized()
            self.max_btn.setText("❐")

    # --- Verificação de Atualizações ---
    def check_updates_manual(self):
        self.update_btn.setText("🔄 Verificando...")
        self.update_thread = UpdateCheckerThread(self)
        self.update_thread.update_available.connect(self._on_update_available)
        self.update_thread.no_update.connect(lambda: self._on_no_update(manual=True))
        self.update_thread.check_error.connect(lambda err: self._on_update_error(err))
        self.update_thread.start()

    def check_updates_silent(self):
        self.update_thread = UpdateCheckerThread(self)
        self.update_thread.update_available.connect(self._on_update_available)
        self.update_thread.start()

    def _on_update_available(self, info: dict):
        self.latest_update_info = info
        self.update_btn.setText("✨ Nova Versão!")
        self.update_btn.setStyleSheet("background-color: #065F46; color: #34D399; font-weight: bold;")
        self._execute_update(info)

    def _on_no_update(self, manual=False):
        self.update_btn.setText("🔄 Atualizações")
        if manual:
            QMessageBox.information(self, "Atualizações", f"Você já está utilizando a versão mais recente do Hub da Bia (v{CURRENT_VERSION}).")

    def _on_update_error(self, err: str):
        self.update_btn.setText("🔄 Atualizações")
        QMessageBox.warning(self, "Aviso", f"Não foi possível verificar atualizações no momento:\n{err}")

    def _execute_update(self, info: dict = None):
        """Abre a tela profissional de atualização automática do próprio Hub."""
        from hubbia.ui.update_dialog import UpdateDialog
        target_info = info or getattr(self, "latest_update_info", {})
        if not target_info:
            return

        dlg = UpdateDialog(target_info, self)
        dlg.exec()

    # --- Permite arrastar janela sem borda ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() <= 48:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull() and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    # --- Sidebar Lateral ---
    def _create_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setObjectName("Sidebar")
        layout = QVBoxLayout(sb)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(8)

        # Categorias
        cat_lbl = QLabel("CATEGORIAS")
        cat_lbl.setObjectName("SidebarTitle")
        layout.addWidget(cat_lbl)

        self.cat_buttons = {}
        for cat in self.app_manager.get_categories():
            btn = QPushButton(cat.replace("&", "&&"))
            btn.setObjectName("CategoryBtn")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            if cat == self.active_category:
                btn.setProperty("active", "true")
            btn.clicked.connect(lambda checked=False, c=cat: self._set_category(c))
            layout.addWidget(btn)
            self.cat_buttons[cat] = btn

        # Botão de Atualizações no Cabeçalho
        self.update_btn = QPushButton("🔄 Atualizações")
        self.update_btn.setObjectName("HeaderUpdateBtn")
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.setStyleSheet("""
            QPushButton#HeaderUpdateBtn {
                background: transparent;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
                color: #64748B;
            }
            QPushButton#HeaderUpdateBtn:hover {
                background: #E2E8F0;
                color: #0F172A;
            }
        """)
        self.update_btn.clicked.connect(self.check_updates_manual)
        layout.addWidget(self.update_btn)

        layout.addStretch()

        # Rodapé da Sidebar
        footer_widget = QWidget()
        footer_widget.setObjectName("SidebarFooter")
        f_layout = QVBoxLayout(footer_widget)
        f_layout.setContentsMargins(0, 10, 0, 0)
        f_layout.setSpacing(8)

        add_btn = QPushButton("＋ Novo Aplicativo")
        add_btn.setObjectName("AddAppBtn")
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.clicked.connect(self._on_add_app_clicked)
        f_layout.addWidget(add_btn)

        cfg_btn = QPushButton("⚙ Configurações (apps.json)")
        cfg_btn.setObjectName("SecondaryCardBtn")
        cfg_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cfg_btn.clicked.connect(self._open_config_file)
        f_layout.addWidget(cfg_btn)

        self.update_btn = QPushButton("🔄 Atualizações")
        self.update_btn.setObjectName("SecondaryCardBtn")
        self.update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_btn.clicked.connect(self.check_updates_manual)
        f_layout.addWidget(self.update_btn)

        layout.addWidget(footer_widget)
        return sb

    def _set_category(self, cat: str):
        self.active_category = cat
        for c_name, btn in self.cat_buttons.items():
            is_act = (c_name == cat)
            btn.setProperty("active", "true" if is_act else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.refresh_cards()

    # --- Área de Conteúdo ---
    def _create_content_area(self) -> QWidget:
        container = QWidget()
        container.setObjectName("MainContent")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Top Header (Saudação + Barra de Busca)
        header_row = QHBoxLayout()
        header_row.setSpacing(20)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        h_title = QLabel("Seu Espaço de Trabalho")
        h_title.setObjectName("HeaderTitle")
        
        self.h_subtitle = QLabel("Carregando status dos aplicativos...")
        self.h_subtitle.setObjectName("HeaderSubtitle")

        title_box.addWidget(h_title)
        title_box.addWidget(self.h_subtitle)
        header_row.addLayout(title_box, 1)

        # Campo de Busca
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchInput")
        self.search_bar.setPlaceholderText("🔍 Filtrar aplicativos...")
        self.search_bar.setFixedWidth(260)
        self.search_bar.textChanged.connect(self._on_search_changed)
        header_row.addWidget(self.search_bar)

        layout.addLayout(header_row)

        # Scroll Area com Grid de Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("CatalogScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_container.setObjectName("CardsContainer")
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setContentsMargins(0, 10, 10, 10)
        self.cards_grid.setSpacing(20)
        self.cards_grid.setAlignment(Qt.AlignTop)
        self.cards_grid.setColumnStretch(0, 1)
        self.cards_grid.setColumnStretch(1, 1)

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)

        return container

    def _on_search_changed(self, text: str):
        self.search_query = text.strip().lower()
        self.refresh_cards()

    def refresh_cards(self):
        # Limpar cards anteriores do layout
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self.cards.clear()

        running_set = get_running_process_names()
        apps = self.app_manager.get_apps()

        # Filtrar por categoria e busca
        filtered = []
        for app in apps:
            if self.active_category != "Todos" and app.get("category") != self.active_category:
                continue
            if self.search_query:
                q = self.search_query
                in_name = q in app.get("name", "").lower()
                in_desc = q in app.get("description", "").lower()
                in_tags = any(q in t.lower() for t in app.get("tags", []))
                if not (in_name or in_desc or in_tags):
                    continue
            filtered.append(app)

        # Montar grid (2 colunas)
        row = 0
        col = 0
        running_count = 0

        for app in filtered:
            is_running = self.app_manager.is_app_running(app, running_set)
            is_installed = self.app_manager.is_app_installed(app)
            has_update = self.app_manager.has_app_update(app)
            if is_running:
                running_count += 1

            card = AppCard(app, is_running=is_running, is_installed=is_installed, has_update=has_update)
            card.launch_requested.connect(self._launch_app)
            card.install_requested.connect(self._install_app)
            card.open_folder_requested.connect(self._open_folder)
            card.update_requested.connect(self._update_single_app)
            card.terminate_requested.connect(self._terminate_app)
            card.uninstall_requested.connect(self._uninstall_app)
            
            self.cards_grid.addWidget(card, row, col)
            self.cards.append(card)

            col += 1
            if col > 1:
                col = 0
                row += 1

        # Spacer no final para manter os cards no topo
        self.cards_grid.setRowStretch(row + 1, 1)

        # Atualizar estatísticas do subtítulo
        total_apps = len(apps)
        self.h_subtitle.setText(f"{total_apps} aplicativos cadastrados • {running_count} em execução")

    def _launch_app(self, app_info: dict):
        success, msg = self.app_manager.launch_app(app_info)
        if success:
            # Forçar atualização de status logo após abrir
            QTimer.singleShot(1500, self.update_running_statuses)
        else:
            QMessageBox.warning(self, "Aviso", msg)

    def _terminate_app(self, app_info: dict):
        # 1. Atualizar visualmente o card de imediato para feedback instantâneo
        target_id = app_info.get("id")
        for card in self.cards:
            if card.app_info.get("id") == target_id:
                card.update_states(is_running=False, is_installed=card.is_installed)
                break

        # 2. Executar encerramento completo e forçado
        self.app_manager.terminate_app(app_info)

        # 3. Disparar checagens rápidas para sincronizar status de processos e contadores
        self.update_running_statuses()
        QTimer.singleShot(150, self.update_running_statuses)
        QTimer.singleShot(500, self.update_running_statuses)
        QTimer.singleShot(1200, self.update_running_statuses)

    def _open_folder(self, app_info: dict):
        if not self.app_manager.open_folder(app_info):
            QMessageBox.information(self, "Aviso", f"Pasta de {app_info['name']} não encontrada.")

    def _uninstall_app(self, app_info: dict):
        """Desinstala o aplicativo após confirmação do usuário (com botões Sim e Não em português)."""
        app_name = app_info.get("name", "Aplicativo")
        msg_box = QMessageBox(
            QMessageBox.Question,
            f"Desinstalar {app_name}",
            f"Tem certeza que deseja desinstalar <b>{app_name}</b> deste computador?",
            parent=self
        )
        btn_sim = msg_box.addButton("Sim", QMessageBox.YesRole)
        btn_nao = msg_box.addButton("Não", QMessageBox.NoRole)
        msg_box.setDefaultButton(btn_nao)

        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #171B26;
                color: #F8FAFC;
            }
            QLabel {
                color: #F8FAFC;
                font-size: 13px;
            }
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: 600;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)

        msg_box.exec()
        if msg_box.clickedButton() == btn_sim:
            success, msg = self.app_manager.uninstall_app(app_info)
            self.refresh_cards()

    def _update_single_app(self, app_info: dict):
        app_name = app_info.get("name", "Aplicativo")
        download_url = app_info.get("download_url")
        if not download_url:
            QMessageBox.information(
                self,
                f"Atualização - {app_name}",
                f"{app_name} não possui instalador em nuvem cadastrado."
            )
            return

        has_update = self.app_manager.has_app_update(app_info)
        installed_versions = self.app_manager.get_installed_versions()
        installed_ver = installed_versions.get(app_info.get("id"), app_info.get("version", "v1.0.0"))

        if not has_update:
            # O aplicativo já está atualizado! Não inicia download surpresa.
            msg_box = QMessageBox(
                QMessageBox.Question,
                f"{app_name} - Atualizado",
                f"O aplicativo <b>{app_name}</b> já está na versão mais recente (<b>{installed_ver}</b>) e pronto para uso.<br><br>Deseja reinstalar o aplicativo?",
                parent=self
            )
            btn_sim = msg_box.addButton("Sim", QMessageBox.YesRole)
            btn_nao = msg_box.addButton("Não", QMessageBox.NoRole)
            msg_box.setDefaultButton(btn_nao)

            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #171B26;
                    color: #F8FAFC;
                }
                QLabel {
                    color: #F8FAFC;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 6px 20px;
                    font-weight: 600;
                    font-size: 12px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)

            msg_box.exec()
            if msg_box.clickedButton() != btn_sim:
                return

        # Inicia atualização/download transparente
        self._execute_app_download_and_install(app_info, is_update=True)

    def _install_app(self, app_info: dict):
        """Baixa e instala o aplicativo diretamente pelo Hub em segundo plano com barra de progresso."""
        app_name = app_info.get("name", "Aplicativo")
        download_url = app_info.get("download_url")

        if not download_url:
            QMessageBox.warning(
                self,
                f"Instalação - {app_name}",
                f"Não há instalador em nuvem cadastrado para {app_name}."
            )
            return

        # Inicia instalação direta sem diálogo redundante de confirmação (usuário já clicou no botão Instalar)
        self._execute_app_download_and_install(app_info, is_update=False)

    def _execute_app_download_and_install(self, app_info: dict, is_update: bool = False):
        """Executa download e instalação/atualização transparente diretamente pelo Hub."""
        app_name = app_info.get("name", "Aplicativo")
        target_ver = app_info.get("version", "")
        action_verb = "Atualizando" if is_update else "Instalando"
        ver_badge = f" ({target_ver})" if target_ver else ""

        # Se estiver rodando, encerra limpo antes para evitar arquivos travados
        if self.app_manager.is_app_running(app_info):
            self.app_manager.terminate_app(app_info)

        from PySide6.QtWidgets import QProgressDialog

        self.install_progress = QProgressDialog(
            f"Preparando {action_verb.lower()} de {app_name}{ver_badge}...",
            "Cancelar",
            0,
            100,
            self
        )
        self.install_progress.setWindowTitle(f"{action_verb} {app_name}{ver_badge}")
        self.install_progress.setWindowModality(Qt.WindowModal)
        self.install_progress.setMinimumDuration(0)
        self.install_progress.setValue(5)
        self.install_progress.setFixedSize(460, 140)
        self.install_progress.setStyleSheet("""
            QProgressDialog {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #F8FAFC;
                font-size: 13px;
                font-weight: 500;
            }
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
                border-radius: 5px;
            }
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.install_progress.show()

        self.installer_thread = AppInstallerThread(app_info, self)
        self.install_progress.canceled.connect(self.installer_thread.cancel)

        def _on_prog(val, text):
            if hasattr(self, "install_progress") and self.install_progress:
                self.install_progress.setValue(val)
                self.install_progress.setLabelText(text)

        def _on_finish(success, message):
            if hasattr(self, "install_progress") and self.install_progress:
                self.install_progress.close()
            if success:
                # Concluído: fecha diálogo e atualiza os cards diretamente sem popup redundante
                self.refresh_cards()
            else:
                QMessageBox.warning(self, f"{action_verb} - {app_name}", message)

        self.installer_thread.progress_changed.connect(_on_prog)
        self.installer_thread.install_finished.connect(_on_finish)
        self.installer_thread.start()

    def _open_config_file(self):
        cfg_file = self.app_manager.config_path
        if cfg_file.exists():
            os.startfile(str(cfg_file))

    def _on_add_app_clicked(self):
        # Abre diálogo amigável para cadastrar novo app
        dialog = AddAppDialog(self.app_manager.get_categories(), self)
        if dialog.exec() == QDialog.Accepted:
            new_app = dialog.get_data()
            if new_app["name"]:
                self.app_manager.data["apps"].append(new_app)
                self.app_manager.save_config()
                self.refresh_cards()
                QMessageBox.information(self, "Sucesso", f"Aplicativo '{new_app['name']}' adicionado ao Hub!")

    # --- Timer em segundo plano para monitorar apps rodando ---
    def init_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(2500) # a cada 2.5s
        self.status_timer.timeout.connect(self.update_running_statuses)
        self.status_timer.start()

    def update_running_statuses(self):
        running_set = get_running_process_names()
        running_count = 0
        for card in self.cards:
            is_r = self.app_manager.is_app_running(card.app_info, running_set)
            is_inst = self.app_manager.is_app_installed(card.app_info)
            if is_r != card.is_running or is_inst != card.is_installed:
                card.update_states(is_running=is_r, is_installed=is_inst)
            if is_r:
                running_count += 1
        total_apps = len(self.app_manager.get_apps())
        self.h_subtitle.setText(f"{total_apps} aplicativos cadastrados • {running_count} em execução")

    # --- Bandeja do Sistema (System Tray) ---
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = get_asset_path("assets/hub_icon.png")
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.windowIcon())

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Abrir Hub da Bia")
        show_action.triggered.connect(self.showNormal)
        tray_menu.addSeparator()

        for app in self.app_manager.get_apps():
            act = tray_menu.addAction(f"Abrir {app['name']}")
            act.triggered.connect(lambda checked=False, a=app: self._launch_app(a))

        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Sair do Hub")
        quit_action.triggered.connect(self._safe_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def _safe_quit(self):
        self.tray_icon.hide()
        sys.exit(0)


class AddAppDialog(QDialog):
    """Diálogo limpo para cadastrar um novo aplicativo no Hub."""
    def __init__(self, categories: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Novo Aplicativo no Hub")
        self.resize(460, 320)
        self.setStyleSheet(DARK_THEME_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Novo Aplicativo")
        title.setObjectName("HeaderTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("SearchInput")
        self.name_edit.setPlaceholderText("Ex: SketchUp, Canva, WhatsApp...")
        form.addRow("Nome:", self.name_edit)

        self.sub_edit = QLineEdit()
        self.sub_edit.setObjectName("SearchInput")
        self.sub_edit.setPlaceholderText("Ex: Modelagem 3D, Design...")
        form.addRow("Subtítulo:", self.sub_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setObjectName("SearchInput")
        self.desc_edit.setPlaceholderText("Breve descrição do app...")
        form.addRow("Descrição:", self.desc_edit)

        # Seleção de executável
        exe_row = QHBoxLayout()
        self.exe_edit = QLineEdit()
        self.exe_edit.setObjectName("SearchInput")
        self.exe_edit.setPlaceholderText("Caminho do .exe ou script")
        exe_btn = QPushButton("Procurar...")
        exe_btn.setObjectName("SecondaryCardBtn")
        exe_btn.clicked.connect(self._browse_exe)
        exe_row.addWidget(self.exe_edit)
        exe_row.addWidget(exe_btn)
        form.addRow("Executável:", exe_row)

        layout.addLayout(form)

        # Botões Salvar / Cancelar
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Executável", "", "Executáveis (*.exe *.bat *.py)")
        if path:
            self.exe_edit.setText(path)

    def get_data(self) -> dict:
        name = self.name_edit.text().strip()
        exe = self.exe_edit.text().strip()
        exe_name = os.path.basename(exe) if exe else ""
        return {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "subtitle": self.sub_edit.text().strip(),
            "category": "Utilitários",
            "version": "v1.0.0",
            "description": self.desc_edit.text().strip(),
            "icon": "assets/aurea.png",
            "executable": exe,
            "fallback_script": "",
            "process_names": [exe_name] if exe_name else [],
            "folder": os.path.dirname(exe) if exe else "",
            "tags": [name],
            "pinned": False
        }
