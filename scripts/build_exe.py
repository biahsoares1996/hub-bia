# -*- coding: utf-8 -*-
"""
Compilador PyInstaller para o Hub da Bia
Gera o executável standalone HubDaBia.exe em pasta local rápida para evitar locks de rede/Drive.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def build():
    print("=" * 60)
    print("  COMPILADOR DO HUB DA BIA (CRAFT SUITE)")
    print("=" * 60)

    base_dir = Path(__file__).resolve().parent.parent
    src_dir = base_dir / "src"
    local_build = Path(r"C:\temp_hub_build")
    dist_final = base_dir / "dist"

    # Lê versão do version.json
    with open(base_dir / "version.json", "r", encoding="utf-8") as f:
        VERSION = json.load(f).get("version", "0.0.0")

    exe_name = f"HubDaBia-v{VERSION}.exe"

    print(f"\n[1/4] Preparando pasta de compilacao em {local_build}...")
    if local_build.exists():
        # Remove read-only attributes on Windows before deleting
        import stat
        def handle_remove_readonly(func, path, exc):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(local_build, onerror=handle_remove_readonly)
    local_build.mkdir(parents=True, exist_ok=True)

    # 2. Copiar TODA a estrutura src/ (preserva hubbia como pacote)
    print("[2/4] Copiando arquivos do Hub para o drive local C:...")
    shutil.copytree(src_dir, local_build / "src")
    # version.json na raiz do build para o PyInstaller encontrar
    shutil.copy(base_dir / "version.json", local_build / "version.json")

    # 3. Compilar com PyInstaller
    print("\n[3/4] Compilando executavel com PyInstaller...")
    icon_path = (local_build / "src" / "hubbia" / "assets" / "hub_icon.ico")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name=HubDaBia-v{VERSION}",
        "--windowed",
        "--noconfirm",
        f"--icon={str(icon_path)}",
        "--add-data=src/hubbia/assets;src/hubbia/assets",
        "--add-data=version.json;.",
        # Hidden imports para garantir que o pacote hubbia seja incluído
        "--hidden-import=hubbia",
        "--hidden-import=hubbia.core",
        "--hidden-import=hubbia.core.paths",
        "--hidden-import=hubbia.core.launcher",
        "--hidden-import=hubbia.core.updater",
        "--hidden-import=hubbia.core.app_installer",
        "--hidden-import=hubbia.ui",
        "--hidden-import=hubbia.ui.main_window",
        "--hidden-import=hubbia.ui.app_card",
        "--hidden-import=hubbia.ui.styles",
        "--hidden-import=hubbia.ui.update_dialog",
        str(local_build / "src" / "hubbia" / "__main__.py")
    ]

    print("Executando:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(local_build))

    if res.returncode == 0:
        print("\n[4/4] Copiando pasta compilada final para dist/...")
        dist_final.mkdir(parents=True, exist_ok=True)
        out_src = local_build / "dist" / f"HubDaBia-v{VERSION}"
        out_dst = base_dir / "dist" / f"HubDaBia-v{VERSION}"

        if out_dst.exists():
            try:
                shutil.rmtree(out_dst)
            except Exception:
                pass
        shutil.copytree(local_build / "dist" / f"HubDaBia-v{VERSION}", out_dst)
        
        # Renomeia o executável final com a versão
        final_exe = out_dst / f"HubDaBia-v{VERSION}.exe"
        if (out_dst / f"HubDaBia-v{VERSION}.exe").exists():
            pass  # já tem o nome correto
        
        print(f"\n[OK] SUCESSO! Executavel gerado com sucesso em:\n{out_dst / f'HubDaBia-v{VERSION}.exe'}")
        return True
    else:
        print("\n[ERRO] Falha durante a compilacao do PyInstaller.")
        return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)