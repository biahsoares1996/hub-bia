# -*- coding: utf-8 -*-
"""
Gerenciador central de caminhos para Hub da Bia.
Usa platformdirs para portabilidade entre sistemas e usuários.
"""

import sys
import os
from pathlib import Path

try:
    from platformdirs import user_data_dir, user_config_dir, user_log_dir
except ImportError:
    # Fallback se platformdirs não estiver disponível
    def user_data_dir(appname: str, appauthor: str = None, roaming: bool = False) -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base / (appauthor or appname) / appname

    def user_config_dir(appname: str, appauthor: str = None, roaming: bool = False) -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / (appauthor or appname) / appname

    def user_log_dir(appname: str, appauthor: str = None) -> Path:
        return user_data_dir(appname, appauthor) / "logs"

APP_NAME = "HubDaBia"
APP_AUTHOR = "BiaStudio"


def get_base_dir() -> Path:
    """Retorna o diretório base da instalação (diretório que contém _internal ou raiz da aplicação)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Modo desenvolvimento: raiz do repositório
    return Path(__file__).resolve().parent.parent.parent.parent


def get_package_dir() -> Path:
    """Retorna o diretório do pacote hubbia (src/hubbia) onde estão assets, ui, core."""
    if getattr(sys, "frozen", False):
        # Executável compilado (PyInstaller) - assets em _internal
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.exists(meipass):
            return Path(meipass)
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "_internal").exists():
            return exe_dir / "_internal"
        return exe_dir
    # Modo desenvolvimento: src/hubbia
    return Path(__file__).resolve().parent.parent


def get_repo_root() -> Path:
    """Retorna a raiz do repositório (onde estão config/, scripts/, etc)."""
    if getattr(sys, "frozen", False):
        return get_package_dir()
    # Em desenvolvimento: src/hubbia/core -> parent.parent.parent.parent = raiz do repo
    return Path(__file__).resolve().parent.parent.parent.parent


def get_asset_path(rel_path: str) -> Path:
    """Retorna o caminho absoluto de um asset (em src/hubbia/assets ou _internal/assets)."""
    base = get_package_dir()
    p = base / rel_path
    if p.exists():
        return p
    # Fallback no diretório do executável
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        p2 = exe_dir / rel_path
        if p2.exists():
            return p2
    return p


def get_config_dir() -> Path:
    """Retorna o diretório de configuração do usuário (ex: %LOCALAPPDATA%\\HubDaBia no Windows)."""
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_config_path() -> Path:
    """
    Retorna o caminho do arquivo apps.json com prioridade:
    1. Configuração do usuário (runtime, sincronizada pela nuvem)
    2. Template do pacote instalado (_internal/config/apps.json)
    3. Template do repo (config/apps.json.example)
    """
    # 1. Configuração do usuário (runtime) - PRIORIDADE MÁXIMA
    user_cfg = get_config_dir() / "apps.json"
    if user_cfg.exists():
        return user_cfg

    # 2. Template do pacote instalado (_internal/config/apps.json)
    pkg_dir = get_package_dir()
    internal_cfg = pkg_dir / "config" / "apps.json"
    if internal_cfg.exists():
        return internal_cfg

    # 3. Template do repo (config/apps.json.example)
    repo_root = get_repo_root()
    repo_template = repo_root / "config" / "apps.json.example"
    if repo_template.exists():
        return repo_template

    # 4. Fallback: template ao lado do executável (dev)
    if getattr(sys, "frozen", False):
        exe_cfg = Path(sys.executable).resolve().parent / "config" / "apps.json"
        if exe_cfg.exists():
            return exe_cfg

    return internal_cfg


def get_template_config_path() -> Path:
    """Retorna o caminho do template de configuração (config/apps.json.example no repo)."""
    repo_root = get_repo_root()
    return repo_root / "config" / "apps.json.example"


def ensure_user_config_exists() -> Path:
    """
    Garante que existe um apps.json no diretório do usuário.
    Se não existe, copia do template.
    Retorna o caminho do arquivo do usuário.
    """
    user_cfg = get_config_dir() / "apps.json"
    if user_cfg.exists():
        return user_cfg

    # Criar diretório se não existe
    user_cfg.parent.mkdir(parents=True, exist_ok=True)

    # Copiar template se existe (prioridade: repo > package)
    template = get_template_config_path()
    if not template.exists():
        pkg_dir = get_package_dir()
        template = pkg_dir / "config" / "apps.json"

    if template.exists():
        import shutil
        shutil.copy2(template, user_cfg)
        return user_cfg

    # Fallback: criar config mínimo
    minimal = {
        "hub_name": "Hub da Bia",
        "version": "2.6.0",
        "theme": "dark_craft",
        "categories": ["Todos", "Navegação", "Finanças", "Segurança", "Arquitetura"],
        "apps": []
    }
    import json
    with open(user_cfg, "w", encoding="utf-8") as f:
        json.dump(minimal, f, indent=2, ensure_ascii=False)
    return user_cfg


def get_installed_versions_path() -> Path:
    """Retorna o caminho do arquivo JSON que registra a versão instalada de cada app no PC do usuário."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "installed_versions.json"


def get_log_path() -> Path:
    """Retorna o caminho do arquivo de log de debug."""
    log_dir = Path(user_log_dir(APP_NAME, APP_AUTHOR))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "hub_debug.log"