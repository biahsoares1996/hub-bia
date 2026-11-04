# -*- coding: utf-8 -*-
"""
Compila o Instalador Oficial Standalone (Instalador_Hub_da_Bia.exe)
Gera um único arquivo .exe com interface gráfica PySide6 e payload embutido.
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def build_installer():
    print("=" * 60)
    print("  COMPILADOR DO INSTALADOR EXE (HUB DA BIA)")
    print("=" * 60)

    base_dir = Path(__file__).resolve().parent.parent
    src_dir = base_dir / "src" / "hubbia"
    local_build = Path(r"C:\temp_hub_installer_build")

    # Lê versão do version.json
    with open(base_dir / "version.json", "r", encoding="utf-8") as f:
        VERSION = json.load(f).get("version", "0.0.0")

    out_dst = base_dir / f"Instalador_Hub_da_Bia-v{VERSION}.exe"

    print(f"\n[1/4] Preparando pasta de compilacao em {local_build}...")
    if local_build.exists():
        # Remove read-only attributes on Windows before deleting
        import stat
        def handle_remove_readonly(func, path, exc):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(local_build, onerror=handle_remove_readonly)
    local_build.mkdir(parents=True, exist_ok=True)

    # 2. Copiar arquivos necessários
    print("[2/4] Copiando script do instalador, icone e pacote compactado do Hub...")
    shutil.copy(base_dir / "scripts" / "installer_gui.py", local_build / "installer_gui.py")
    shutil.copytree(src_dir / "assets", local_build / "assets")

    # Copiar HubDaBia_Suite.zip como payload embutido
    zip_src = base_dir / "HubDaBia_Suite.zip"
    if not zip_src.exists():
        # Gerar zip a partir de dist/HubDaBia se não existir
        import zipfile
        dist_dir = base_dir / "dist" / f"HubDaBia-v{VERSION}"
        if not dist_dir.exists():
            print(f"[ERRO] Pasta dist nao encontrada: {dist_dir}")
            print("Rode primeiro: python scripts/build_exe.py")
            return False
        with zipfile.ZipFile(zip_src, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(dist_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, dist_dir)
                    zf.write(full_p, rel_p)

    shutil.copy2(zip_src, local_build / "HubDaBia_Suite.zip")

    # 3. Compilar em .exe único via PyInstaller
    print("\n[3/4] Compilando Instalador_Hub_da_Bia.exe com PyInstaller (--onefile)...")
    icon_path = local_build / "assets" / "hub_icon.ico"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name=Instalador_Hub_da_Bia-v{VERSION}",
        "--onefile",
        "--windowed",
        "--noconfirm",
        f"--icon={str(icon_path)}",
        "--add-data=assets;assets",
        "--add-data=HubDaBia_Suite.zip;.",
        str(local_build / "installer_gui.py")
    ]

    print("Executando:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(local_build))

    if res.returncode == 0:
        print("\n[4/4] Copiando executavel final do instalador...")
        built_exe = local_build / "dist" / f"Instalador_Hub_da_Bia-v{VERSION}.exe"
        import time
        if out_dst.exists():
            try:
                out_dst.unlink()
            except Exception:
                pass

        time.sleep(2.0)
        for attempt in range(12):
            try:
                if out_dst.exists():
                    try:
                        out_dst.unlink()
                    except Exception:
                        pass
                shutil.copy2(built_exe, out_dst)
                print(f"\n[OK] SUCESSO! Instalador executavel gerado com sucesso em:\n{out_dst}")
                return True
            except Exception as e:
                print(f"Tentativa {attempt+1}: aguardando liberacao ({e})...")
                time.sleep(1.5)
        return False
    else:
        print("\n[ERRO] Falha durante a compilacao do instalador.")
        return False

if __name__ == "__main__":
    success = build_installer()
    sys.exit(0 if success else 1)