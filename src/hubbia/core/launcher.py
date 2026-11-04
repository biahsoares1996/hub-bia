# -*- coding: utf-8 -*-
"""
Gerenciador de Processos e Lançamento de Aplicativos do Hub da Bia
Detecta processos ativos de forma ultra-rápida via Win32 ctypes
e executa processos de forma desanexada e não-bloqueante.
"""

import os
import sys
import json
import ctypes
from ctypes import wintypes
import subprocess
from pathlib import Path
from hubbia.core.paths import get_config_path

TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('cntUsage', wintypes.DWORD),
        ('th32ProcessID', wintypes.DWORD),
        ('th32DefaultHeapID', ctypes.c_void_p),
        ('th32ModuleID', wintypes.DWORD),
        ('cntThreads', wintypes.DWORD),
        ('th32ParentProcessID', wintypes.DWORD),
        ('pcPriClassBase', wintypes.LONG),
        ('dwFlags', wintypes.DWORD),
        ('szExeFile', ctypes.c_char * 260)
    ]

def get_running_process_names() -> set[str]:
    """Retorna conjunto de nomes de executáveis rodando no Windows em minúsculas."""
    running = set()
    try:
        kernel32 = ctypes.windll.kernel32
        hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnapshot == -1:
            return running

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

        if kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
            while True:
                exe = entry.szExeFile.decode('ansi', errors='ignore').strip().lower()
                if exe:
                    running.add(exe)
                if not kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
                    break
        kernel32.CloseHandle(hSnapshot)
    except Exception as e:
        print(f"[Launcher] Erro ao listar processos: {e}")
    return running

def get_process_name_by_pid(pid: int) -> str | None:
    """Retorna o nome do executável em minúsculas para um determinado PID."""
    try:
        kernel32 = ctypes.windll.kernel32
        hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnapshot == -1:
            return None
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        if kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
            while True:
                if entry.th32ProcessID == pid:
                    exe = entry.szExeFile.decode('ansi', errors='ignore').strip().lower()
                    kernel32.CloseHandle(hSnapshot)
                    return exe
                if not kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
                    break
        kernel32.CloseHandle(hSnapshot)
    except Exception:
        pass
    return None

class AppManager:
    """Gerencia a lista de aplicativos cadastrados no Hub da Bia."""

    def __init__(self, config_path: str = None):
        if not config_path:
            self.config_path = get_config_path()
        else:
            self.config_path = Path(config_path)
        self.data = self.load_config()

    def load_config(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[AppManager] Erro ao ler {self.config_path}: {e}")
        return {"hub_name": "Hub da Bia", "categories": ["Todos"], "apps": []}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AppManager] Erro ao salvar {self.config_path}: {e}")

    def get_apps(self) -> list[dict]:
        return self.data.get("apps", [])

    def get_categories(self) -> list[str]:
        return self.data.get("categories", ["Todos"])

    def detect_local_app_version(self, app_info: dict) -> str | None:
        """Detecta a versão real instalada no disco a partir de arquivos version.json ou metadados oficiais."""
        app_id = app_info.get("id", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        user_profile = os.environ.get("USERPROFILE", "")

        candidates = []
        if app_id == "omnidvr":
            candidates.extend([
                r"D:\DVR\version.json",
                os.path.join(localappdata, "Programs", "OmniDVR", "version.json")
            ])
        elif app_id == "software_vault":
            candidates.extend([
                os.path.join(localappdata, "Programs", "SoftwareVault", "versao_vault.json"),
                r"F:\Meu Drive\.AntigravityGoogle\SoftwareVault\versao_vault.json"
            ])
        elif app_id == "gatoceiro":
            candidates.extend([
                os.path.join(user_profile, "Documents", "Gatoceiro", "version.json"),
                os.path.join(user_profile, "Documents", "Gatoceiro", "versao.json"),
                r"D:\Documentos\Gatoceiro\version.json",
                r"F:\Meu Drive\.AntigravityGoogle\Gatoceiro\version.json"
            ])
        elif app_id == "aurea_browser":
            candidates.extend([
                os.path.join(localappdata, "Programs", "AureaBrowser", "version.json"),
                r"F:\Meu Drive\.AntigravityGoogle\NavegadorBia\version.json"
            ])
        elif app_id == "biabim":
            candidates.extend([
                os.path.join(localappdata, "Programs", "OpenSketch 2026", "version.json"),
                r"F:\Meu Drive\.AntigravityGoogle\SketchUp OpenSource\version.json"
            ])

        for c in candidates:
            if os.path.exists(c):
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        v = d.get("version")
                        if v:
                            return f"v{v}" if not str(v).startswith("v") else str(v)
                except Exception:
                    pass
        return None

    def get_installed_versions(self) -> dict:
        """Carrega o histórico de versões dos aplicativos instalados nesta máquina."""
        from hubbia.core.paths import get_installed_versions_path
        p = get_installed_versions_path()
        data = {}
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        # Detecção dinâmica nos arquivos locais dos apps para preencher o que faltar
        updated = False
        for app in self.get_apps():
            app_id = app.get("id")
            if app_id and app_id not in data and self.is_app_installed(app):
                # Tenta ler versão local instalada nos arquivos
                ver = self.detect_local_app_version(app)
                if ver:
                    data[app_id] = ver
                    updated = True
                else:
                    # Se está instalado no computador e não há divergência, adota a versão do catálogo
                    data[app_id] = app.get("version", "v1.0.0")
                    updated = True

        if updated:
            try:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass

        return data

    def set_installed_version(self, app_id: str, version: str):
        """Salva a versão instalada de um aplicativo no histórico local."""
        from hubbia.core.paths import get_installed_versions_path
        p = get_installed_versions_path()
        data = self.get_installed_versions()
        data[app_id] = version
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AppManager] Erro ao salvar installed_versions: {e}")

    def has_app_update(self, app_info: dict) -> bool:
        """Verifica se há uma versão mais nova cadastrada em apps.json do que a instalada na máquina."""
        if not self.is_app_installed(app_info):
            return False
        app_id = app_info.get("id", "")
        target_ver = app_info.get("version", "v1.0.0")
        installed_versions = self.get_installed_versions()
        installed_ver = installed_versions.get(app_id)
        
        # Se não há versão registrada mesmo após detecção, não acusa falso positivo
        if not installed_ver:
            return False
        
        from hubbia.core.updater import compare_versions
        return compare_versions(installed_ver, target_ver) > 0

    def get_installed_executable_path(self, app_info: dict) -> str | None:
        """Retorna o caminho absoluto do executável ou script realmente existente no computador."""
        import glob
        app_id = app_info.get("id", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        progfiles = os.environ.get("ProgramFiles", "")
        progfiles86 = os.environ.get("ProgramFiles(x86)", "")
        user_profile = os.environ.get("USERPROFILE", "")

        candidates = []

        # 1. Caminhos oficiais de instalação nos computadores dos usuários
        if app_id == "aurea_browser":
            candidates.extend([
                os.path.join(localappdata, "Programs", "AureaBrowser", "Aurea.exe"),
                os.path.join(progfiles, "AureaBrowser", "Aurea.exe"),
                r"f:\Meu Drive\.AntigravityGoogle\NavegadorBia\aurea_browser\main.py"
            ])
        elif app_id == "gatoceiro":

            # 1. Pastas Documentos / Documents e OneDrive do usuário
            for doc_name in ["Documents", "Documentos"]:
                candidates.append(os.path.join(user_profile, doc_name, "Gatoceiro", "Gatoceiro.exe"))
                candidates.append(os.path.join(user_profile, "OneDrive", doc_name, "Gatoceiro", "Gatoceiro.exe"))

            # 2. Pasta Personal do Registro (caso o usuário tenha redirecionado 'Documentos')
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                    for v_name in ["Personal", "{F42EE2D3-909F-4907-8871-4C22FC0BF756}"]:
                        try:
                            val, _ = winreg.QueryValueEx(k, v_name)
                            expanded = os.path.expandvars(val)
                            candidates.append(os.path.join(expanded, "Gatoceiro", "Gatoceiro.exe"))
                        except Exception:
                            pass
            except Exception:
                pass

            # 3. Chave de Desinstalação do Windows Registry (Inno Setup)
            try:
                import winreg
                for hive in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                    for sub in [r"Software\Microsoft\Windows\CurrentVersion\Uninstall", r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
                        try:
                            with winreg.OpenKey(hive, sub) as uninst_key:
                                num_sub = winreg.QueryInfoKey(uninst_key)[0]
                                for i in range(num_sub):
                                    sk_name = winreg.EnumKey(uninst_key, i)
                                    try:
                                        with winreg.OpenKey(uninst_key, sk_name) as app_k:
                                            dn = ""
                                            try:
                                                dn, _ = winreg.QueryValueEx(app_k, "DisplayName")
                                            except Exception:
                                                pass
                                            if "gato" in dn.lower() or "gato" in sk_name.lower():
                                                try:
                                                    loc, _ = winreg.QueryValueEx(app_k, "InstallLocation")
                                                    if loc:
                                                        candidates.append(os.path.join(loc, "Gatoceiro.exe"))
                                                except Exception:
                                                    pass
                                                try:
                                                    un_str, _ = winreg.QueryValueEx(app_k, "UninstallString")
                                                    if un_str:
                                                        clean_un = un_str.replace('"', '').strip()
                                                        candidates.append(os.path.join(os.path.dirname(clean_un), "Gatoceiro.exe"))
                                                except Exception:
                                                    pass
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            except Exception:
                pass

            # 4. Atalhos no Desktop e Menu Iniciar
            for base_dir in [
                os.path.join(user_profile, "Desktop"),
                r"C:\Users\Public\Desktop",
                os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"),
                os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs")
            ]:
                if os.path.exists(base_dir):
                    for lnk in glob.glob(os.path.join(base_dir, "**", "*Gatoceiro*.lnk"), recursive=True):
                        try:
                            with open(lnk, "rb") as f:
                                raw = f.read()
                            import re
                            m = re.findall(rb'[a-zA-Z]:\\[^\x00\r\n\t\<\>\|\?\*]+\.exe', raw)
                            for bpath in m:
                                try:
                                    exe_str = bpath.decode('latin1', 'ignore')
                                    if 'gatoceiro.exe' in exe_str.lower():
                                        candidates.append(exe_str)
                                except Exception:
                                    pass
                        except Exception:
                            pass

            # 5. Demais caminhos locais conhecidos
            candidates.extend([
                os.path.join(localappdata, "Programs", "Gatoceiro", "Gatoceiro.exe"),
                os.path.join(localappdata, "Gatoceiro", "Gatoceiro.exe"),
                os.path.join(progfiles, "Gatoceiro", "Gatoceiro.exe"),
                os.path.join(progfiles86, "Gatoceiro", "Gatoceiro.exe"),
                r"D:\Documentos\Gatoceiro\Gatoceiro.exe",
                r"D:\Documentos\Gatoceiro\iniciar_gatoceiro.bat",
                r"f:\Meu Drive\.AntigravityGoogle\Gatoceiro\iniciar_gatoceiro.bat",
                r"f:\Meu Drive\.AntigravityGoogle\Gatoceiro\dist\Gatoceiro.exe"
            ])
        elif app_id == "omnidvr":
            candidates.extend([
                os.path.join(localappdata, "Programs", "OmniDVR", "OmniDVR.exe"),
                os.path.join(progfiles, "OmniDVR", "OmniDVR.exe"),
                os.path.join(progfiles86, "OmniDVR", "OmniDVR.exe"),
                r"D:\DVR\dist\OmniDVR\OmniDVR.exe",
                r"D:\DVR\OmniDVR.exe",
                r"D:\DVR\iniciar_dvr.bat",
                r"D:\DVR\Iniciar_OmniDVR_App.bat"
            ])
        elif app_id == "software_vault":
            candidates.extend([
                os.path.join(localappdata, "Programs", "SoftwareVault", "SketchUp_Vault.exe"),
                os.path.join(localappdata, "Programs", "SoftwareVault", "SoftwareVault.exe"),
                os.path.join(localappdata, "SoftwareVault", "SketchUp_Vault.exe"),
                os.path.join(appdata, "SoftwareVault", "SketchUp_Vault.exe"),
                os.path.join(progfiles, "SoftwareVault", "SketchUp_Vault.exe"),
                os.path.join(progfiles86, "SoftwareVault", "SketchUp_Vault.exe"),
                os.path.join(user_profile, "Downloads", "SketchUp_Vault.exe"),
                os.path.join(user_profile, "Downloads", "SketchUp Vault.exe"),
                os.path.join(user_profile, "Desktop", "SketchUp_Vault.exe"),
                os.path.join(user_profile, "Desktop", "SketchUp Vault.exe"),
                r"F:\Meu Drive\.AntigravityGoogle\SoftwareVault\iniciar_software_vault.bat",
                r"F:\Meu Drive\.AntigravityGoogle\SoftwareVault\sketchup_vault_app.py",
                r"F:\Meu Drive\.AntigravityGoogle\SoftwareVault\dist\SketchUp_Vault.exe",
                r"F:\Meu Drive\.AntigravityGoogle\SoftwareVault\SketchUp_Vault.exe"
            ])

            # Varredura de atalhos .lnk no Desktop e Menu Iniciar
            for base_dir in [
                os.path.join(user_profile, "Desktop"),
                r"C:\Users\Public\Desktop",
                os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"),
                os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs")
            ]:
                if os.path.exists(base_dir):
                    for lnk in glob.glob(os.path.join(base_dir, "**", "*Vault*.lnk"), recursive=True):
                        try:
                            with open(lnk, "rb") as f:
                                raw = f.read()
                            import re
                            m = re.findall(rb'[a-zA-Z]:\\[^\x00\r\n\t\<\>\|\?\*]+\.exe', raw)
                            for bpath in m:
                                try:
                                    exe_str = bpath.decode('latin1', 'ignore')
                                    if 'vault' in exe_str.lower() or 'sketchup' in exe_str.lower():
                                        candidates.append(exe_str)
                                except Exception:
                                    pass
                        except Exception:
                            pass
        elif app_id == "biabim":
            candidates.extend([
                os.path.join(localappdata, "Programs", "OpenSketch 2026", "OpenSketch 2026.exe"),
                os.path.join(localappdata, "Programs", "BiaBIM", "BiaBIM.exe"),
                os.path.join(progfiles, "OpenSketch 2026", "OpenSketch 2026.exe"),
                r"F:\Meu Drive\.AntigravityGoogle\SketchUp OpenSource\launch.vbs"
            ])
        elif app_id == "milux":
            candidates.extend([
                r"F:\Meu Drive\.AntigravityGoogle\milux_studio-BAT.exe",
                r"F:\Meu Drive\.AntigravityGoogle\Instalador_Milux.exe"
            ])
            skp_plugins = glob.glob(os.path.join(appdata, "SketchUp", "SketchUp *", "SketchUp", "Plugins", "milux_plugin.rb"))
            candidates.extend(skp_plugins)

        # 2. Verificar caminhos explícitos de app_info (expandindo variáveis de ambiente)
        for field in ["executable", "fallback_script"]:
            val = app_info.get(field)
            if val:
                exp = os.path.expandvars(val)
                candidates.append(exp)

        # Retornar o primeiro candidato existente no disco
        for cand in candidates:
            if cand and os.path.exists(cand):
                return cand

        return None

    def is_app_installed(self, app_info: dict) -> bool:
        """Verifica se o aplicativo está instalado no computador atual."""
        return self.get_installed_executable_path(app_info) is not None

    def is_app_running(self, app_info: dict, running_set: set[str] = None) -> bool:
        # REGRA FUNDAMENTAL: Se o aplicativo nem sequer está instalado neste PC,
        # ele NUNCA pode ser considerado em execução!
        if not self.is_app_installed(app_info):
            return False

        app_id = app_info.get("id")

        if app_id == "omnidvr":
            # OmniDVR só está rodando se:
            # 1. O executável OmniDVR.exe estiver na lista de processos
            # 2. OU se houver janela ativa visível com título contendo 'OmniDVR'
            # 3. OU se o endpoint de câmeras da API do OmniDVR responder com sucesso
            # NUNCA checar processo genérico como node.exe!
            if running_set is None:
                running_set = get_running_process_names()
            if "omnidvr.exe" in running_set or "omnidvr" in running_set:
                return True

            # Checar janela ativa com título OmniDVR
            try:
                import ctypes
                from ctypes import wintypes
                found_dvr = []
                def _enum_win_dvr(hwnd, _):
                    if ctypes.windll.user32.IsWindowVisible(hwnd):
                        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                            if "omnidvr" in buff.value.lower():
                                found_dvr.append(True)
                                return False
                    return True
                CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                ctypes.windll.user32.EnumWindows(CB(_enum_win_dvr), 0)
                if found_dvr:
                    return True
            except Exception:
                pass

            # Checar se o servidor REST oficial do OmniDVR responde no endpoint /api/cameras/health
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    "http://127.0.0.1:3000/api/cameras/health",
                    headers={"User-Agent": "HubDaBia"}
                )
                with urllib.request.urlopen(req, timeout=0.15) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("success") is True and "health" in data:
                            return True
            except Exception:
                pass

            return False

        if app_id == "software_vault":
            # SketchUp Vault só está rodando se o executável SketchUp_Vault.exe estiver rodando
            # ou se a janela dedicada estiver aberta (nunca checar python genérico)
            if running_set is None:
                running_set = get_running_process_names()
            if "sketchup_vault.exe" in running_set or "sketchup_vault" in running_set:
                return True
            # Checar janela
            try:
                import ctypes
                from ctypes import wintypes
                found_vault = []
                def _enum_win_vault(hwnd, _):
                    if ctypes.windll.user32.IsWindowVisible(hwnd):
                        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                            if "SketchUp Vault" in buff.value or "SketchUp Installer" in buff.value:
                                found_vault.append(True)
                                return False
                    return True
                CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                ctypes.windll.user32.EnumWindows(CB(_enum_win_vault), 0)
                if found_vault:
                    return True
            except Exception:
                pass
            return False

        if app_info.get("id") == "gatoceiro":
            # Verificar se há janela ativa do Gatoceiro (caso esteja rodando via pythonw.exe)
            try:
                import ctypes
                from ctypes import wintypes
                found_gato = []
                def _enum_win_gato(hwnd, _):
                    if ctypes.windll.user32.IsWindowVisible(hwnd):
                        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                            if "Gatoceiro" in buff.value:
                                found_gato.append(True)
                                return False
                    return True
                CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                ctypes.windll.user32.EnumWindows(CB(_enum_win_gato), 0)
                if found_gato:
                    return True
            except Exception:
                pass

        if running_set is None:
            running_set = get_running_process_names()
        targets = [p.lower() for p in app_info.get("process_names", [])]
        for t in targets:
            if t in running_set:
                return True
        return False

    def launch_app(self, app_info: dict) -> tuple[bool, str]:
        """Inicia o aplicativo de forma assíncrona e desvinculada do Hub."""
        app_id = app_info.get("id")
        app_name = app_info.get("name", "Aplicativo")

        # 1. Tratamento específico do OmniDVR quando servidor já está rodando
        if app_id == "omnidvr" and self.is_app_running(app_info):
            try:
                os.startfile("http://localhost:3000")
                return True, "Painel do OmniDVR aberto no navegador!"
            except Exception as e:
                print(f"[Launcher] Falha ao abrir URL: {e}")

        # 2. Localizar o executável ou script realmente instalado na máquina do usuário
        target = self.get_installed_executable_path(app_info)
        if not target or not os.path.exists(target):
            return False, f"Executável ou script de {app_name} não encontrado no disco."

        working_dir = app_info.get("folder")
        if not working_dir or not os.path.exists(working_dir):
            working_dir = os.path.dirname(target)

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        # 3. Execução de arquivos em lote (.bat / .cmd), VBS (.vbs) ou atalhos (.lnk)
        if target.lower().endswith(('.bat', '.cmd', '.vbs', '.lnk')):
            try:
                os.startfile(target)
                return True, f"{app_name} iniciado com sucesso!"
            except Exception as e:
                return False, f"Erro ao executar {target}: {e}"

        # 4. Execução de scripts Python (.py)
        if target.lower().endswith('.py'):
            try:
                python_exe = sys.executable
                pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                cmd_exe = pythonw if os.path.exists(pythonw) else python_exe
                subprocess.Popen(
                    [cmd_exe, target],
                    cwd=working_dir,
                    creationflags=creation_flags,
                    close_fds=True,
                    shell=False
                )
                return True, f"{app_name} iniciado via script Python!"
            except Exception as e:
                return False, f"Erro ao executar script Python {target}: {e}"

        # 5. Caso especial: MiLux plugin .rb (abre o SketchUp correspondente)
        if app_id == "milux" and target.lower().endswith('.rb'):
            try:
                skp_dir = Path(target).parents[2]
                skp_exe = skp_dir / "SketchUp.exe"
                if skp_exe.exists():
                    os.startfile(str(skp_exe))
                    return True, "SketchUp iniciado com Plugin MiLux!"
            except Exception:
                pass

        # 6. Execução padrão de arquivo executável (.exe)
        try:
            subprocess.Popen(
                [target],
                cwd=working_dir,
                creationflags=creation_flags,
                close_fds=True,
                shell=False
            )
            return True, f"{app_name} iniciado com sucesso!"
        except Exception as e:
            try:
                os.startfile(target)
                return True, f"{app_name} iniciado com sucesso!"
            except Exception as e2:
                return False, f"Falha ao iniciar {app_name}: {e2}"

    def open_folder(self, app_info: dict):
        """Abre a pasta local do aplicativo no Explorador de Arquivos."""
        folder = app_info.get("folder")
        if folder and os.path.exists(folder):
            os.startfile(folder)
            return True
        return False

    def terminate_app(self, app_info: dict) -> tuple[bool, str]:
        """Encerra os processos e janelas associados ao aplicativo de forma completa, rápida e garantida."""
        app_id = app_info.get("id", "")
        app_name = app_info.get("name", "Aplicativo")
        terminated_any = False

        # 1. Encerramento gracioso via envio de mensagens às janelas (WM_CLOSE / SC_CLOSE)
        target_titles = []
        if app_id == "aurea_browser":
            target_titles.extend(["aurea", "áurea"])
        elif app_id == "software_vault":
            target_titles.extend(["sketchup vault", "sketchup installer", "softwarevault"])
        elif app_id == "gatoceiro":
            target_titles.extend(["gatoceiro", "contas"])
        elif app_id == "omnidvr":
            target_titles.extend(["omnidvr"])
        elif app_id == "biabim":
            target_titles.extend(["biabim", "opensketch"])
        elif app_id == "milux":
            target_titles.extend(["milux"])
        target_titles.append(app_name.lower())

        window_pids = set()
        try:
            user32 = ctypes.windll.user32
            WM_CLOSE = 0x0010
            WM_SYSCOMMAND = 0x0112
            SC_CLOSE = 0xF060

            def _enum_close_win(hwnd, _):
                try:
                    if user32.IsWindowVisible(hwnd):
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buff, length + 1)
                            t_low = buff.value.lower()
                            if any(tt in t_low for tt in target_titles if tt):
                                pid = wintypes.DWORD()
                                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                                if pid.value:
                                    window_pids.add(pid.value)
                                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                                user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_CLOSE, 0)
                except Exception:
                    pass
                return True

            CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(CB(_enum_close_win), 0)
        except Exception as e:
            print(f"[Launcher] Erro ao enumerar janelas para fechamento: {e}")

        # 2. Encerramentos especializados por aplicativo
        if app_id == "omnidvr":
            # Matar processos escutando na porta 3000
            try:
                out = subprocess.check_output("netstat -ano -p tcp | findstr :3000", shell=True, text=True)
                for line in out.strip().split("\n"):
                    parts = line.split()
                    if len(parts) >= 5 and parts[1].endswith(":3000") and parts[3] == "LISTENING":
                        pid = parts[4]
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                        terminated_any = True
            except Exception:
                pass

            # Encerrar processos Node do OmniDVR
            try:
                ps_kill = 'Get-CimInstance Win32_Process -Filter "Name = \'node.exe\'" | Where-Object { $_.CommandLine -like "*DVR*" -or $_.CommandLine -like "*OmniDVR*" } | Stop-Process -Force'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_kill], capture_output=True)
                terminated_any = True
            except Exception:
                pass

        elif app_id == "gatoceiro":
            try:
                ps_kill = 'Get-CimInstance Win32_Process -Filter "Name like \'python%\'" | Where-Object { $_.CommandLine -like "*Contas.py*" -or $_.CommandLine -like "*Gatoceiro*" } | Stop-Process -Force'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_kill], capture_output=True)
                terminated_any = True
            except Exception:
                pass

        elif app_id == "software_vault":
            try:
                ps_kill = 'Get-CimInstance Win32_Process -Filter "Name like \'python%\'" | Where-Object { $_.CommandLine -like "*sketchup_vault*" -or $_.CommandLine -like "*SoftwareVault*" } | Stop-Process -Force'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_kill], capture_output=True)
                terminated_any = True
            except Exception:
                pass

        elif app_id == "aurea_browser":
            try:
                ps_kill = 'Get-CimInstance Win32_Process -Filter "Name like \'python%\'" | Where-Object { $_.CommandLine -like "*aurea*" -or $_.CommandLine -like "*NavegadorBia*" } | Stop-Process -Force'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_kill], capture_output=True)
                terminated_any = True
            except Exception:
                pass

        # 3. Coleta de todos os processos pelo Toolhelp32Snapshot
        target_process_names = set()
        for p in app_info.get("process_names", []):
            p_clean = p.strip().lower()
            if not p_clean.endswith(".exe"):
                p_clean += ".exe"
            target_process_names.add(p_clean)

        exe_path = self.get_installed_executable_path(app_info)
        if exe_path and exe_path.lower().endswith(".exe"):
            target_process_names.add(os.path.basename(exe_path).lower())

        target_pids = set(window_pids)
        try:
            kernel32 = ctypes.windll.kernel32
            hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if hSnapshot != -1:
                entry = PROCESSENTRY32()
                entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
                if kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
                    while True:
                        exe_name = entry.szExeFile.decode('ansi', errors='ignore').strip().lower()
                        if exe_name in target_process_names:
                            target_pids.add(entry.th32ProcessID)
                            # Se o processo pai for um processo wrapper python/cmd, finaliza também
                            if entry.th32ParentProcessID and entry.th32ParentProcessID > 4:
                                p_name = get_process_name_by_pid(entry.th32ParentProcessID)
                                if p_name in ("python.exe", "pythonw.exe", "cmd.exe"):
                                    target_pids.add(entry.th32ParentProcessID)
                        if not kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
                            break
                kernel32.CloseHandle(hSnapshot)
        except Exception as e:
            print(f"[Launcher] Erro no snapshot para finalização: {e}")

        # 4. Finalização direta via Win32 TerminateProcess e taskkill /PID
        kernel32 = ctypes.windll.kernel32
        for pid in target_pids:
            if pid <= 4:
                continue
            # TerminateProcess nativo via handle Win32
            try:
                h_proc = kernel32.OpenProcess(0x0001, False, pid)  # PROCESS_TERMINATE
                if h_proc:
                    kernel32.TerminateProcess(h_proc, 1)
                    kernel32.CloseHandle(h_proc)
                    terminated_any = True
            except Exception:
                pass

            # taskkill direto por PID (sem /T para não abortar com erro de acesso negado em nó pai)
            try:
                r = subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True, text=True)
                if r.returncode == 0:
                    terminated_any = True
            except Exception:
                pass

        # 5. Encerramento forçado por Nome de Imagem (taskkill e PowerShell Stop-Process)
        for proc_exe in target_process_names:
            proc_no_ext = proc_exe[:-4] if proc_exe.endswith(".exe") else proc_exe
            # 5a. taskkill sem /T (individual, direto)
            try:
                r1 = subprocess.run(f'taskkill /F /IM "{proc_exe}"', shell=True, capture_output=True, text=True)
                if r1.returncode == 0:
                    terminated_any = True
            except Exception:
                pass

            # 5b. taskkill com /T (em árvore, caso haja subprocessos)
            try:
                r2 = subprocess.run(f'taskkill /F /T /IM "{proc_exe}"', shell=True, capture_output=True, text=True)
                if r2.returncode == 0:
                    terminated_any = True
            except Exception:
                pass

            # 5c. PowerShell Stop-Process
            try:
                ps_cmd = f'Stop-Process -Name "{proc_no_ext}" -Force -ErrorAction SilentlyContinue'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
                terminated_any = True
            except Exception:
                pass

        return True, f"{app_name} encerrado com sucesso!"

    def uninstall_app(self, app_info: dict) -> tuple[bool, str]:
        """Desinstala o aplicativo, removendo seus arquivos instalados, processos e atalhos."""
        import shutil
        app_id = app_info.get("id")
        app_name = app_info.get("name", "Aplicativo")

        # 1. Encerra processos do aplicativo caso esteja aberto
        self.terminate_app(app_info)

        # 2. Localiza o executável instalado
        target = self.get_installed_executable_path(app_info)
        localappdata = os.environ.get("LOCALAPPDATA", "")
        programs_dir = os.path.join(localappdata, "Programs")
        deleted_anything = False

        if target and os.path.exists(target):
            target_p = Path(target).resolve()
            programs_p = Path(programs_dir).resolve()
            target_dir = target_p.parent

            # Se houver desinstalador oficial (ex: Inno Setup unins000.exe do Gatoceiro ou outro app)
            unins_exe = target_dir / "unins000.exe"
            if unins_exe.exists():
                try:
                    subprocess.run(
                        [str(unins_exe), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                        capture_output=True,
                        timeout=15
                    )
                    deleted_anything = True
                except Exception as e:
                    print(f"[Launcher] Erro ao executar desinstalador oficial {unins_exe}: {e}")

            # Remoção segura da pasta de instalação do app
            try:
                # 1. Se estiver em %LOCALAPPDATA%\Programs
                if target_p.is_relative_to(programs_p):
                    rel_parts = target_p.relative_to(programs_p).parts
                    if rel_parts:
                        app_install_dir = programs_p / rel_parts[0]
                        if app_install_dir.exists() and app_install_dir != programs_p:
                            shutil.rmtree(app_install_dir, ignore_errors=True)
                            deleted_anything = True
                # 2. Se for uma pasta dedicada do aplicativo (ex: Documents\Gatoceiro)
                elif target_dir.name.lower() in ("gatoceiro", "omnidvr", "softwarevault", "aureabrowser"):
                    shutil.rmtree(target_dir, ignore_errors=True)
                    deleted_anything = True
            except Exception as e:
                print(f"[Launcher] Erro ao remover diretório de instalação: {e}")

        # Caso especial Gatoceiro: limpar dados locais em %LOCALAPPDATA%\Gatoceiro
        if app_id == "gatoceiro":
            gato_local = os.path.join(localappdata, "Gatoceiro")
            if os.path.exists(gato_local):
                try:
                    shutil.rmtree(gato_local, ignore_errors=True)
                    deleted_anything = True
                except Exception:
                    pass

        # Fallback de pastas conhecidas em %LOCALAPPDATA%\Programs
        known_subfolders = {
            "software_vault": "SoftwareVault",
            "aurea_browser": "AureaBrowser",
            "gatoceiro": "Gatoceiro",
            "omnidvr": "OmniDVR",
            "biabim": "OpenSketch 2026"
        }
        sub = known_subfolders.get(app_id)
        if sub:
            known_dir = os.path.join(programs_dir, sub)
            if os.path.exists(known_dir):
                try:
                    shutil.rmtree(known_dir, ignore_errors=True)
                    deleted_anything = True
                except Exception as e:
                    print(f"[Launcher] Erro ao remover {known_dir}: {e}")

        # Caso especial MiLux: se plugin no SketchUp
        if app_id == "milux":
            appdata = os.environ.get("APPDATA", "")
            import glob
            skp_plugins = glob.glob(os.path.join(appdata, "SketchUp", "SketchUp *", "SketchUp", "Plugins", "milux_plugin.rb"))
            for p in skp_plugins:
                try:
                    os.remove(p)
                    deleted_anything = True
                except Exception:
                    pass

        # 3. Remover atalhos residuais
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        start_menu = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
        cleanup_names = [
            f"{app_name}.lnk",
            f"{app_name.replace(' ', '')}.lnk",
            "SketchUp Vault.lnk",
            "SketchUp_Vault.lnk",
            "Software Vault.lnk",
            "OmniDVR.lnk",
            "Gatoceiro.lnk",
            "Aurea Browser.lnk",
            "BiaBIM.lnk"
        ]
        for name in cleanup_names:
            for base in [desktop, start_menu]:
                lnk_p = os.path.join(base, name)
                if os.path.exists(lnk_p):
                    try:
                        os.remove(lnk_p)
                    except Exception:
                        pass

        # 4. Remover do registro local de versões instaladas
        try:
            from hubbia.core.paths import get_installed_versions_path
            p = get_installed_versions_path()
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    v_data = json.load(f)
                if app_id in v_data:
                    v_data.pop(app_id, None)
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(v_data, f, indent=2)
        except Exception as e:
            print(f"[Launcher] Erro ao atualizar installed_versions.json: {e}")

        return True, f"{app_name} desinstalado com sucesso."
