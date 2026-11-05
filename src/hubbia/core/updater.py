# -*- coding: utf-8 -*-
"""
Mecanismo de Atualização Automática do Hub da Bia
Suporta verificação via Google Drive local e URLs remotas (HTTP / Dropbox / GitHub).
"""

import os
import sys
import json
import urllib.request
from pathlib import Path
from packaging.version import parse as parse_version
from PySide6.QtCore import QThread, Signal

# Importar versão do pacote
try:
    from hubbia import __version__ as CURRENT_VERSION
except ImportError:
    CURRENT_VERSION = "2.6.0"

DEFAULT_VERSION_URL = "https://raw.githubusercontent.com/biahsoares1996/hub-bia/main/version.json"
DEFAULT_APPS_URL = "https://raw.githubusercontent.com/biahsoares1996/hub-bia/main/config/apps.json"
FALLBACK_VERSION_URL = "https://github.com/biahsoares1996/hub-bia/releases/latest/download/version.json"
FALLBACK_APPS_URL = "https://github.com/biahsoares1996/hub-bia/releases/latest/download/apps.json"


def get_installed_version_info() -> dict:
    """Lê version.json do pacote instalado (_internal ou ao lado do exe)."""
    candidates = []
    try:
        from hubbia.core.paths import get_base_dir
        base = get_base_dir()
        if base:
            candidates.extend([base / "version.json", base / "_internal" / "version.json"])
    except Exception:
        pass

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([exe_dir / "version.json", exe_dir / "_internal" / "version.json"])
    else:
        dev_root = Path(__file__).resolve().parent.parent.parent.parent
        candidates.append(dev_root / "version.json")

    for p in candidates:
        if p and p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "version" in data:
                        return data
            except Exception:
                pass

    return {"version": CURRENT_VERSION}


def get_current_app_version() -> str:
    """Retorna a versão atualmente instalada em execução."""
    return get_installed_version_info().get("version", CURRENT_VERSION)


def compare_versions(v1_str: str, v2_str: str) -> int:
    """Retorna 1 se v2 > v1, -1 se v1 > v2, 0 se iguais."""
    try:
        p1 = parse_version(v1_str)
        p2 = parse_version(v2_str)
        if p2 > p1:
            return 1
        elif p2 < p1:
            return -1
        return 0
    except Exception:
        # Fallback simples por tupla de inteiros
        def to_tuple(v):
            return tuple(int(x) for x in v.strip("v").split(".") if x.isdigit())
        t1, t2 = to_tuple(v1_str), to_tuple(v2_str)
        return (t2 > t1) - (t2 < t1)


class UpdateCheckerThread(QThread):
    update_available = Signal(dict)  # info da nova versao
    no_update = Signal()
    check_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            # 1. Localização da fonte de atualização (opcional: Google Drive do dev)
            master_gdrive_path = Path(r"F:\Meu Drive\.AntigravityGoogle\HubDaBia\version.json")
            target_data = None

            if master_gdrive_path.exists():
                try:
                    with open(master_gdrive_path, "r", encoding="utf-8") as f:
                        target_data = json.load(f)
                except Exception as e:
                    print(f"[Updater] Erro ao ler version.json do Drive: {e}")

            if not target_data:
                # 2. Busca remota no GitHub (ou URL definida no version.json instalado)
                local_info = get_installed_version_info()
                url = local_info.get("update_url", DEFAULT_VERSION_URL)
                if url.startswith("http://") or url.startswith("https://"):
                    try:
                        req = urllib.request.Request(url, headers={"User-Agent": f"HubDaBia-Updater/{CURRENT_VERSION}"})
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            target_data = json.loads(resp.read().decode("utf-8"))
                    except Exception as e_fetch:
                        print(f"[Updater] Erro ao buscar da URL principal ({url}): {e_fetch}. Tentando fallback...")
                        try:
                            req_fb = urllib.request.Request(FALLBACK_VERSION_URL, headers={"User-Agent": f"HubDaBia-Updater/{CURRENT_VERSION}"})
                            with urllib.request.urlopen(req_fb, timeout=15) as resp_fb:
                                target_data = json.loads(resp_fb.read().decode("utf-8"))
                        except Exception as e_fb:
                            print(f"[Updater] Erro no fallback: {e_fb}")

            # Sincronização remota de catálogo de apps e versões em segundo plano
            try:
                from hubbia.core.paths import get_config_dir
                local_info = get_installed_version_info()
                apps_url = local_info.get("apps_url", DEFAULT_APPS_URL)
                try:
                    req_apps = urllib.request.Request(apps_url, headers={"User-Agent": f"HubDaBia-Updater/{CURRENT_VERSION}"})
                    with urllib.request.urlopen(req_apps, timeout=10) as resp_apps:
                        remote_apps = json.loads(resp_apps.read().decode("utf-8"))
                except Exception:
                    req_apps_fb = urllib.request.Request(FALLBACK_APPS_URL, headers={"User-Agent": f"HubDaBia-Updater/{CURRENT_VERSION}"})
                    with urllib.request.urlopen(req_apps_fb, timeout=10) as resp_apps:
                        remote_apps = json.loads(resp_apps.read().decode("utf-8"))

                if remote_apps and "apps" in remote_apps:
                    local_hub_dir = get_config_dir()
                    local_hub_dir.mkdir(parents=True, exist_ok=True)
                    with open(local_hub_dir / "apps.json", "w", encoding="utf-8") as f_a:
                        json.dump(remote_apps, f_a, indent=2, ensure_ascii=False)
            except Exception as e_a:
                print(f"[Updater] Aviso ao sincronizar apps.json remoto: {e_a}")

            if not target_data:
                self.no_update.emit()
                return

            remote_ver = target_data.get("version", CURRENT_VERSION)
            current_ver = get_installed_version_info().get("version", CURRENT_VERSION)

            if compare_versions(current_ver, remote_ver) > 0:
                self.update_available.emit(target_data)
            else:
                self.no_update.emit()

        except Exception as e:
            self.check_error.emit(str(e))