# -*- coding: utf-8 -*-
"""
Gerenciador de Download e Instalação Silenciosa/Automática de Aplicativos do Hub da Bia
Baixa arquivos (.exe ou .zip) do Dropbox diretamente em segundo plano e instala/executa sem abrir navegador.
"""

import os
import sys
import time
import zipfile
import tempfile
import urllib.request
import subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal

try:
    from hubbia import __version__ as HUBBIA_VERSION
except ImportError:
    HUBBIA_VERSION = "2.6.0"


class AppInstallerThread(QThread):
    progress_changed = Signal(int, str)  # porcentagem (0-100), mensagem de status
    install_finished = Signal(bool, str)  # sucesso, mensagem final

    def __init__(self, app_info: dict, parent=None):
        super().__init__(parent)
        self.app_info = app_info
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        app_name = self.app_info.get("name", "Aplicativo")
        app_id = self.app_info.get("id", "")
        target_ver = self.app_info.get("version", "")
        download_url = self.app_info.get("download_url", "")

        # Resolução das versões atual e de destino para exibição clara ao usuário
        try:
            from hubbia.core.launcher import AppManager
            installed_ver = AppManager().get_installed_versions().get(app_id, "")
        except Exception:
            installed_ver = ""

        if installed_ver and target_ver and installed_ver != target_ver:
            ver_desc = f"{target_ver} (versão atual: {installed_ver})"
        elif target_ver:
            ver_desc = f"{target_ver}"
        else:
            ver_desc = ""

        ver_suffix = f" {ver_desc}" if ver_desc else ""

        if not download_url:
            self.install_finished.emit(False, f"URL de download não configurada para {app_name}.")
            return

        try:
            self.progress_changed.emit(5, f"Conectando à nuvem para baixar {app_name}{ver_suffix}...")

            # 1. Preparar requisição de download
            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) HubDaBia-Installer/{HUBBIA_VERSION}"}
            )

            # Criar arquivo temporário para salvar o download
            is_zip = ".zip" in download_url.lower()
            suffix = ".zip" if is_zip else ".exe"
            temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=f"hub_{app_id}_")
            os.close(temp_fd)

            with urllib.request.urlopen(req, timeout=60) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                block_size = 1024 * 64  # 64 KB

                with open(temp_path, "wb") as f_out:
                    while True:
                        if self._is_cancelled:
                            self.install_finished.emit(False, "Instalação cancelada pelo usuário.")
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                            return

                        chunk = resp.read(block_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int(5 + (downloaded / total_size) * 75)
                            mb_down = downloaded / (1024 * 1024)
                            mb_tot = total_size / (1024 * 1024)
                            self.progress_changed.emit(
                                percent,
                                f"Baixando {app_name}{ver_suffix}: {mb_down:.1f} MB de {mb_tot:.1f} MB ({percent}%)"
                            )
                        else:
                            mb_down = downloaded / (1024 * 1024)
                            self.progress_changed.emit(50, f"Baixando {app_name}{ver_suffix}: {mb_down:.1f} MB...")

            self.progress_changed.emit(85, f"Download concluído! Instalando {app_name}{' ' + target_ver if target_ver else ''}...")

            # 2. Instalação / Extração de acordo com o tipo
            localappdata = os.environ.get("LOCALAPPDATA", "")
            programs_dir = os.path.join(localappdata, "Programs")

            if is_zip:
                # Se for arquivo ZIP (ex: Aurea Browser, Software Vault, BiaBIM)
                folder_mapping = {
                    "aurea_browser": "AureaBrowser",
                    "software_vault": "SoftwareVault",
                    "biabim": "OpenSketch 2026",
                }
                dest_subfolder = folder_mapping.get(app_id, app_name.replace(" ", ""))
                dest_dir = os.path.join(programs_dir, dest_subfolder)
                os.makedirs(dest_dir, exist_ok=True)

                self.progress_changed.emit(90, f"Extraindo arquivos para {dest_dir} ({target_ver})...")
                with zipfile.ZipFile(temp_path, "r") as zf:
                    zf.extractall(dest_dir)

                # Criar atalho no Menu Iniciar / Área de Trabalho se aplicável
                self._create_shortcuts(app_info=self.app_info, target_dir=dest_dir)

            else:
                # Se for arquivo .EXE (Instalador ou Executável Direto)
                if app_id == "software_vault":
                    # É o SketchUp_Vault.exe standalone! Copiar para %LOCALAPPDATA%\Programs\SoftwareVault
                    dest_dir = os.path.join(programs_dir, "SoftwareVault")
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_exe = os.path.join(dest_dir, "SketchUp_Vault.exe")
                    import shutil
                    shutil.copy2(temp_path, dest_exe)
                    self._create_shortcuts(app_info=self.app_info, target_dir=dest_dir, main_exe=dest_exe)
                elif app_id == "gatoceiro":
                    # Instalador Inno Setup: executa instalação 100% silenciosa e aguarda o término
                    self.progress_changed.emit(90, f"Instalando {app_name}{' ' + target_ver if target_ver else ''} silenciosamente...")
                    try:
                        res = subprocess.run(
                            [temp_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"],
                            capture_output=True,
                            timeout=60
                        )
                        if res.returncode != 0:
                            subprocess.Popen([temp_path])
                    except Exception:
                        subprocess.Popen([temp_path])
                    self._create_shortcuts(app_info=self.app_info, target_dir="")
                else:
                    # É um instalador executável (.exe interativo / silencioso, ex: OmniDVR, Milux)
                    self.progress_changed.emit(92, f"Iniciando instalador oficial de {app_name}{' ' + target_ver if target_ver else ''}...")
                    subprocess.Popen([temp_path])

            # 3. Registrar versão instalada com sucesso
            try:
                from hubbia.core.launcher import AppManager
                AppManager().set_installed_version(app_id, self.app_info.get("version", "v1.0.0"))
            except Exception:
                pass

            self.progress_changed.emit(100, f"{app_name}{' ' + target_ver if target_ver else ''} instalado com sucesso!")
            self.install_finished.emit(True, f"O aplicativo {app_name}{' ' + target_ver if target_ver else ''} foi instalado com sucesso!")

        except Exception as e:
            self.install_finished.emit(False, f"Erro durante o download/instalação de {app_name}: {e}")

    def _create_shortcuts(self, app_info: dict, target_dir: str, main_exe: str = None):
        """Remove atalhos antigos do app específico da Área de Trabalho.
        NÃO remove o atalho do próprio Hub da Bia."""
        try:
            desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            app_name = app_info.get("name", "App")
            # Nunca remover o atalho do Hub da Bia
            protected = {"Hub da Bia.lnk", "Hub da Bia"}
            cleanup_candidates = [
                f"{app_name}.lnk",
                "SketchUp Vault.lnk",
                "SketchUp_Vault.lnk",
                "Software Vault.lnk",
                "OmniDVR.lnk",
                "Gatoceiro.lnk",
                "Aurea Browser.lnk",
                "BiaBIM.lnk"
            ]
            for c in cleanup_candidates:
                if c in protected:
                    continue
                p = os.path.join(desktop, c)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                        print(f"[Installer] Atalho da Área de Trabalho removido: {p}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Installer] Erro ao verificar/limpar atalhos: {e}")