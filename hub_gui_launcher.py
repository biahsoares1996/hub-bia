# -*- coding: utf-8 -*-
"""
Hub da Bia - Launcher GUI com Sidebar + Terminal Embarcado
Estilo IDE: opções na esquerda, terminal na direita
"""

import sys
import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSplitter, QTextEdit,
    QLineEdit, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QProcess, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon, QPixmap

# ==================== ESTILOS (Dark Craft Theme) ====================
DARK_QSS = """
QMainWindow, QWidget {
    background-color: #0F1117;
    color: #E2E8F0;
    font-family: "Segoe UI", Arial, sans-serif;
}

#Sidebar {
    background-color: #141721;
    border-right: 1px solid #1E2330;
    min-width: 220px;
    max-width: 220px;
}

#SidebarTitle {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 1px;
    padding: 12px 16px 8px 16px;
}

#NavBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #94A3B8;
    text-align: left;
    margin: 2px 8px;
}

#NavBtn:hover {
    background-color: #1E2330;
    color: #F8FAFC;
}

#NavBtn[active="true"] {
    background-color: #2563EB;
    color: #FFFFFF;
}

#TerminalArea {
    background-color: #0D1117;
    border: 1px solid #1E2330;
    border-radius: 8px;
}

#TerminalOutput {
    background-color: #0D1117;
    border: none;
    color: #E2E8F0;
    font-family: "Consolas", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    padding: 12px;
    selection-background-color: #2563EB;
}

#TerminalInput {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 6px;
    color: #E2E8F0;
    font-family: "Consolas", "Cascadia Code", "Fira Code", monospace;
    font-size: 12px;
    padding: 8px 12px;
}

#TerminalInput:focus {
    border-color: #2563EB;
}

#RunBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    border: none;
    border-radius: 6px;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 8px 16px;
}

#RunBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
}

#ClearBtn {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #94A3B8;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 16px;
}

#ClearBtn:hover {
    background-color: #334155;
    color: #F8FAFC;
}

QScrollBar:vertical {
    background: #0D1117;
    width: 8px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""

# ==================== COMANDOS PREDEFINIDOS ====================
COMMANDS = [
    {
        "category": "BUILD",
        "icon": "🔨",
        "items": [
            {"name": "Build HubDaBia.exe", "cmd": "python scripts/build_exe.py", "desc": "Compila o executável principal"},
            {"name": "Build Instalador", "cmd": "python scripts/build_installer_exe.py", "desc": "Compila Instalador_Hub_da_Bia.exe"},
            {"name": "Build Tudo", "cmd": "python scripts/build_exe.py && python scripts/build_installer_exe.py", "desc": "Compila ambos em sequência"},
        ]
    },
    {
        "category": "DEPLOY",
        "icon": "☁️",
        "items": [
            {"name": "Upload HubDaBia.exe", "cmd": "python scripts/upload_hub_dropbox.py dist/HubDaBia/HubDaBia.exe HubDaBia.exe", "desc": "Sobe executável pro Dropbox"},
            {"name": "Upload Instalador", "cmd": "python scripts/upload_hub_dropbox.py Instalador_Hub_da_Bia.exe Instalador_Hub_da_Bia.exe", "desc": "Sobe instalador pro Dropbox"},
            {"name": "Upload Suite ZIP", "cmd": "python scripts/upload_hub_dropbox.py HubDaBia_Suite.zip HubDaBia_Suite.zip", "desc": "Sobe pacote ZIP pro Dropbox"},
            {"name": "Upload version.json", "cmd": "python scripts/upload_hub_dropbox.py version.json version.json", "desc": "Atualiza versão no Dropbox"},
            {"name": "Upload apps.json", "cmd": "python scripts/upload_hub_dropbox.py config/apps.json apps.json", "desc": "Sincroniza catálogo de apps"},
            {"name": "Deploy Completo", "cmd": "python scripts/upload_hub_dropbox.py dist/HubDaBia/HubDaBia.exe HubDaBia.exe && python scripts/upload_hub_dropbox.py Instalador_Hub_da_Bia.exe Instalador_Hub_da_Bia.exe && python scripts/upload_hub_dropbox.py HubDaBia_Suite.zip HubDaBia_Suite.zip && python scripts/upload_hub_dropbox.py version.json version.json && python scripts/upload_hub_dropbox.py config/apps.json apps.json", "desc": "Sobe tudo de uma vez"},
        ]
    },
    {
        "category": "TOKEN",
        "icon": "🔐",
        "items": [
            {"name": "Gerar Novo Token Dropbox", "cmd": "python gerar_token_dropbox.py", "desc": "OAuth2 flow para novo refresh token"},
            {"name": "Ver Token Atual", "cmd": "type %LOCALAPPDATA%\\HubDaBiaDeploy\\dropbox_hub_token.json", "desc": "Mostra token salvo"},
        ]
    },
    {
        "category": "TESTE",
        "icon": "🧪",
        "items": [
            {"name": "Testar HubDaBia.exe", "cmd": "dist/HubDaBia/HubDaBia.exe", "desc": "Executa build local"},
            {"name": "Testar Instalador", "cmd": "Instalador_Hub_da_Bia.exe", "desc": "Executa instalador local"},
            {"name": "Rodar Hub (dev mode)", "cmd": "python -m hubbia", "desc": "Executa direto do source"},
        ]
    },
    {
        "category": "UTILITÁRIOS",
        "icon": "🛠️",
        "items": [
            {"name": "Limpar Builds (temp)", "cmd": "rmdir /s /q C:\\temp_hub_build 2>nul && rmdir /s /q C:\\temp_hub_installer_build 2>nul && echo Pastas temporarias limpas", "desc": "Remove pastas de build temporárias"},
            {"name": "Abrir Pasta Dist", "cmd": "explorer dist", "desc": "Abre pasta de builds no Explorer"},
            {"name": "Abrir Pasta Config", "cmd": "explorer %LOCALAPPDATA%\\HubDaBiaDeploy", "desc": "Abre pasta de tokens/config"},
            {"name": "Ver Versão Atual", "cmd": "type version.json", "desc": "Mostra version.json"},
        ]
    },
]


# ==================== WIDGET TERMINAL ====================
class EmbeddedTerminal(QWidget):
    """Terminal embarcado com QProcess"""
    
    def __init__(self, work_dir: str = None):
        super().__init__()
        self.work_dir = work_dir or str(Path(__file__).parent)
        self.process = None
        self.init_ui()
        self.start_shell()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Header com botões
        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 0)
        
        title = QLabel("💻 Terminal")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #94A3B8;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.clear_btn = QPushButton("🗑 Limpar")
        self.clear_btn.setObjectName("ClearBtn")
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.clicked.connect(self.clear_output)
        header.addWidget(self.clear_btn)
        
        layout.addLayout(header)
        
        # Área de saída
        self.output = QTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.output, 1)
        
        # Linha de input
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(8, 0, 8, 8)
        input_layout.setSpacing(8)
        
        self.prompt_label = QLabel(f"{self.work_dir}>")
        self.prompt_label.setStyleSheet("color: #2563EB; font-family: monospace; font-size: 12px; font-weight: 600; min-width: 120px;")
        input_layout.addWidget(self.prompt_label)
        
        self.input = QLineEdit()
        self.input.setObjectName("TerminalInput")
        self.input.setPlaceholderText("Digite um comando e pressione Enter...")
        self.input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.input, 1)
        
        self.run_btn = QPushButton("▶ Executar")
        self.run_btn.setObjectName("RunBtn")
        self.run_btn.setFixedHeight(32)
        self.run_btn.setFixedWidth(100)
        self.run_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(self.run_btn)
        
        layout.addLayout(input_layout)
    
    def start_shell(self):
        """Inicia shell interativo (cmd no Windows)"""
        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.work_dir)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_output)
        self.process.readyReadStandardError.connect(self.on_output)
        self.process.finished.connect(self.on_finished)
        
        # Inicia cmd.exe
        self.process.start("cmd.exe", ["/K", "chcp", "65001"])
        
        self.append_output(f"[Terminal iniciado em {self.work_dir}]\n", "#2563EB")
    
    def execute_command(self):
        cmd = self.input.text().strip()
        if not cmd:
            return
        
        self.append_output(f"{self.work_dir}> {cmd}\n", "#2563EB")
        self.input.clear()
        
        if self.process and self.process.state() == QProcess.Running:
            self.process.write((cmd + "\n").encode("utf-8"))
    
    def append_output(self, text: str, color: str = "#E2E8F0"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<span style="color: {color};">{text}</span>')
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()
    
    def on_output(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        if data:
            self.append_output(data)
    
    def on_finished(self, exit_code, exit_status):
        self.append_output(f"\n[Processo finalizado com código {exit_code}]\n", "#EF4444")
        # Reinicia shell
        QTimer.singleShot(500, self.start_shell)
    
    def clear_output(self):
        self.output.clear()
        self.append_output("[Terminal limpo]\n", "#2563EB")


# ==================== SIDEBAR ====================
class Sidebar(QWidget):
    def __init__(self, on_command_selected):
        super().__init__()
        self.setObjectName("Sidebar")
        self.on_command_selected = on_command_selected
        self.active_btn = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Título
        title = QLabel("HUB DA BIA")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)
        
        subtitle = QLabel("Launcher & Deploy")
        subtitle.setStyleSheet("font-size: 11px; color: #64748B; padding: 0 16px 16px 16px;")
        layout.addWidget(subtitle)
        
        # Scroll para categorias
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(8)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        # Cria botões por categoria
        for cat in COMMANDS:
            self.add_category(cat)
        
        self.content_layout.addStretch()
        scroll.setWidget(self.content)
        layout.addWidget(scroll, 1)
        
        # Rodapé
        footer = QFrame()
        footer.setStyleSheet("border-top: 1px solid #1E2330; padding: 12px 16px;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setSpacing(8)
        
        version_label = QLabel("v2.6.0")
        version_label.setStyleSheet("font-size: 10px; color: #64748B;")
        version_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(version_label)
        
        layout.addWidget(footer)
    
    def add_category(self, cat: dict):
        # Título da categoria
        cat_label = QLabel(f"{cat['icon']}  {cat['category']}")
        cat_label.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B; letter-spacing: 1px; padding: 8px 16px 4px 16px;")
        self.content_layout.addWidget(cat_label)
        
        # Botões dos itens
        for item in cat["items"]:
            btn = QPushButton(f"  {item['name']}")
            btn.setObjectName("NavBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(item["desc"])
            btn.setProperty("cmd", item["cmd"])
            btn.clicked.connect(lambda checked, b=btn, c=item["cmd"]: self.on_click(b, c))
            self.content_layout.addWidget(btn)
    
    def on_click(self, btn, cmd):
        if self.active_btn:
            self.active_btn.setProperty("active", "false")
            self.active_btn.style().unpolish(self.active_btn)
            self.active_btn.style().polish(self.active_btn)
        
        btn.setProperty("active", "true")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        self.active_btn = btn
        
        self.on_command_selected(cmd)


# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hub da Bia - Launcher & Terminal")
        self.resize(1300, 800)
        self.setMinimumSize(1000, 600)
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet(DARK_QSS)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #1E2330; }")
        
        # Sidebar esquerda
        self.sidebar = Sidebar(self.on_command_selected)
        splitter.addWidget(self.sidebar)
        
        # Terminal direita
        self.terminal = EmbeddedTerminal(str(Path(__file__).parent))
        terminal_container = QFrame()
        terminal_container.setObjectName("TerminalArea")
        terminal_layout = QVBoxLayout(terminal_container)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        terminal_layout.addWidget(self.terminal)
        splitter.addWidget(terminal_container)
        
        # Proporções: 220px sidebar, resto terminal
        splitter.setSizes([220, 1080])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        self.setCentralWidget(splitter)
    
    def on_command_selected(self, cmd: str):
        """Executa comando selecionado no terminal"""
        self.terminal.input.setText(cmd)
        self.terminal.execute_command()
        # Foca no terminal
        self.terminal.input.setFocus()


# ==================== ENTRY POINT ====================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hub da Bia Launcher")
    
    # Fonte padrão
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()