# -*- coding: utf-8 -*-
"""
Gerenciador Dinâmico de Temas e Cores do Hub da Bia
Detecta automaticamente se o Windows está no modo Claro ou Escuro e aplica o tema correspondente.
"""

import sys
if sys.platform == "win32":
    import winreg

def is_windows_light_theme() -> bool:
    """Verifica se o Windows está configurado com tema claro."""
    if sys.platform != "win32":
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        apps_use_light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return bool(apps_use_light_theme)
    except Exception:
        return False

# --- TEMA ESCURO (Dark Mode Craft) ---
DARK_THEME_QSS = """
* {
    font-family: "Segoe UI", Arial, sans-serif;
    outline: none;
    color: #E2E8F0;
}

QMainWindow, #CentralWidget {
    background-color: #0F1117;
    border: 1px solid #1E2330;
}

#TitleBar {
    background-color: #0F1117;
    border-bottom: 1px solid #1E2330;
    min-height: 44px;
    max-height: 44px;
    padding: 0 16px;
}

#TitleLabel {
    font-size: 14px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: 0.5px;
}

#TitleVersionBadge {
    background-color: #1E293B;
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid #334155;
}

#WindowBtn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #94A3B8;
    font-size: 13px;
    font-weight: bold;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
}

#WindowBtn:hover {
    background-color: #1E2330;
    color: #F8FAFC;
}

#Sidebar {
    background-color: #141721;
    border-right: 1px solid #1E2330;
    min-width: 210px;
    max-width: 210px;
}

#SidebarTitle {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 1px;
    padding: 4px 10px;
}

#CategoryBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    font-weight: 600;
    color: #94A3B8;
    text-align: left;
}

#CategoryBtn:hover {
    background-color: #1E2330;
    color: #F8FAFC;
}

#CategoryBtn[active="true"] {
    background-color: #2563EB;
    color: #FFFFFF;
}

#AddAppBtn {
    background: transparent;
    border: 1px dashed #334155;
    border-radius: 8px;
    color: #94A3B8;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
}

#AddAppBtn:hover {
    border-color: #38BDF8;
    color: #38BDF8;
    background-color: rgba(56, 189, 248, 0.05);
}

#ContentArea {
    background-color: #0F1117;
}

#CatalogScrollArea, #CardsContainer {
    background-color: transparent;
    border: none;
}

#HeaderTitle {
    font-size: 22px;
    font-weight: 800;
    color: #F8FAFC;
}

#HeaderSubtitle {
    font-size: 12px;
    color: #64748B;
}

#SearchInput {
    background-color: #171B26;
    border: 1px solid #283247;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
    color: #F8FAFC;
    min-width: 200px;
}

#SearchInput:focus {
    border-color: #38BDF8;
    background-color: #1B2130;
}

/* Cards Ultra Compactos (Slim) - Dark Mode */
AppCard, QFrame#AppCard {
    background-color: #171B26;
    border: 1px solid #283247;
    border-radius: 10px;
}

AppCard:hover, QFrame#AppCard:hover {
    background-color: #1B2130;
    border-color: #38BDF8;
}

#AppCardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #F8FAFC;
}

#AppCardVersionBadge {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
    font-weight: 700;
}

#AppCardVersionBadgeUpdate {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
    font-weight: 700;
}

#AppCardSubtitle {
    font-size: 11px;
    font-weight: 500;
    color: #94A3B8;
}

#LaunchBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#LaunchBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
}

#InstallCardBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#InstallCardBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

#TerminateCardBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #DC2626);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#TerminateCardBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #EF4444);
}

/* Botão Atualizar Desativado (Acinzentado / Discreto quando atualizado) */
#UpdateIdleBtn {
    background-color: #1E293B;
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 6px;
    border: 1px solid #334155;
    min-height: 16px;
}

#UpdateIdleBtn:hover {
    background-color: #334155;
    color: #94A3B8;
}

/* Botão Atualizar Ativo (Verde Vibrante quando há nova versão disponível) */
#UpdateActiveBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 4px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#UpdateActiveBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

/* Botão Desinstalar (Tema Escuro) */
#UninstallCardBtn {
    background-color: transparent;
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 6px;
    border: 1px solid #334155;
    min-height: 16px;
}

#UninstallCardBtn:hover {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid #EF4444;
}

#LaunchSplitMenuBtn {
    background: #1D4ED8;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 800;
    padding: 6px 8px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    border: none;
    border-left: 1px solid rgba(255, 255, 255, 0.2);
    min-height: 16px;
}

#LaunchSplitMenuBtn:hover {
    background-color: #1E40AF;
}

/* ToolTips do Windows no Tema Escuro (Perfeitamente Legíveis) */
QToolTip {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 500;
}

QMenu {
    background-color: #151A23;
    border: 1px solid #2A3447;
    border-radius: 8px;
    padding: 6px;
    color: #E2E8F0;
}

QMenu::item {
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    color: #E2E8F0;
}

QMenu::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

#SecondaryCardBtn {
    background-color: #1E293B;
    color: #CBD5E1;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #334155;
    min-height: 16px;
}

#SecondaryCardBtn:hover {
    background-color: #334155;
    color: #F8FAFC;
    border-color: #38BDF8;
}
"""

# --- TEMA CLARO (Light Mode Nativo do Windows) ---
LIGHT_THEME_QSS = """
* {
    font-family: "Segoe UI", Arial, sans-serif;
    outline: none;
    color: #1E293B;
}

QMainWindow, #CentralWidget {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
}

#TitleBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    min-height: 44px;
    max-height: 44px;
    padding: 0 16px;
}

#TitleLabel {
    font-size: 14px;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: 0.5px;
}

#TitleVersionBadge {
    background-color: #F1F5F9;
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
}

#WindowBtn {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #64748B;
    font-size: 13px;
    font-weight: bold;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
}

#WindowBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

#Sidebar {
    background-color: #F1F5F9;
    border-right: 1px solid #E2E8F0;
    min-width: 210px;
    max-width: 210px;
}

#SidebarTitle {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 1px;
    padding: 4px 10px;
}

#CategoryBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    text-align: left;
}

#CategoryBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}

#CategoryBtn[active="true"] {
    background-color: #2563EB;
    color: #FFFFFF;
}

#AddAppBtn {
    background: transparent;
    border: 1px dashed #CBD5E1;
    border-radius: 8px;
    color: #64748B;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
}

#AddAppBtn:hover {
    border-color: #2563EB;
    color: #2563EB;
    background-color: rgba(37, 99, 235, 0.05);
}

#ContentArea {
    background-color: #F8FAFC;
}

#CatalogScrollArea, #CardsContainer {
    background-color: transparent;
    border: none;
}

#HeaderTitle {
    font-size: 22px;
    font-weight: 800;
    color: #0F172A;
}

#HeaderSubtitle {
    font-size: 12px;
    color: #64748B;
}

#SearchInput {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
    color: #0F172A;
    min-width: 200px;
}

#SearchInput:focus {
    border-color: #2563EB;
}

/* Cards Ultra Compactos no Tema Claro */
AppCard, QFrame#AppCard {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
}

AppCard:hover, QFrame#AppCard:hover {
    background-color: #F8FAFC;
    border-color: #2563EB;
}

#AppCardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
}

#AppCardVersionBadge {
    background-color: #F1F5F9;
    color: #64748B;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
    font-weight: 700;
}

#AppCardVersionBadgeUpdate {
    background-color: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 10px;
    font-weight: 700;
}

#AppCardSubtitle {
    font-size: 11px;
    font-weight: 500;
    color: #475569;
}

#LaunchBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#LaunchBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB);
}

#InstallCardBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#InstallCardBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

#TerminateCardBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DC2626, stop:1 #EF4444);
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 14px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#TerminateCardBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #B91C1C, stop:1 #DC2626);
}

/* Botão Atualizar Desativado (Acinzentado no Tema Claro) */
#UpdateIdleBtn {
    background-color: #F1F5F9;
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
    min-height: 16px;
}

#UpdateIdleBtn:hover {
    background-color: #E2E8F0;
    color: #64748B;
}

/* Botão Atualizar Ativo (Verde no Tema Claro) */
#UpdateActiveBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 4px;
    border-radius: 6px;
    border: none;
    min-height: 16px;
}

#UpdateActiveBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
}

/* Botão Desinstalar (Tema Claro) */
#UninstallCardBtn {
    background-color: transparent;
    color: #64748B;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 4px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
    min-height: 16px;
}

#UninstallCardBtn:hover {
    background-color: #FEE2E2;
    color: #DC2626;
    border: 1px solid #EF4444;
}

#LaunchSplitMenuBtn {
    background: #1D4ED8;
    color: #FFFFFF;
    font-size: 10px;
    font-weight: 800;
    padding: 6px 8px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    border: none;
    border-left: 1px solid rgba(255, 255, 255, 0.2);
    min-height: 16px;
}

/* ToolTips do Windows no Tema Claro (Perfeitamente Legíveis) */
QToolTip {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 500;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px;
    color: #0F172A;
}

QMenu::item {
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    color: #0F172A;
}

QMenu::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

#SecondaryCardBtn {
    background-color: #F1F5F9;
    color: #475569;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #CBD5E1;
    min-height: 16px;
}

#SecondaryCardBtn:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}
"""

def get_theme_qss() -> str:
    """Retorna o stylesheet baseado no tema atual do Windows do usuário."""
    if is_windows_light_theme():
        return LIGHT_THEME_QSS
    return DARK_THEME_QSS
