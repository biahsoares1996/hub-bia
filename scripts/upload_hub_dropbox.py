# -*- coding: utf-8 -*-
"""
Utilitário de Upload e Compartilhamento para o HubDaBiaUpdates no Dropbox
Usa Access Token de longa duração (sem OAuth2, sem prompts)
Com limpeza automática de versões antigas antes do upload
"""

import os
import sys
import json
import requests
from pathlib import Path

# ===== CONFIGURAÇÃO =====
# Token de longa duração (gerado em: https://www.dropbox.com/developers/apps)
LONG_LIVED_TOKEN = "sl.u.AG1iWeTVn8L57jRXIc0ITuDMbxu_k5aB-brWg7l8lOVGiLzg0z8KYWB5KUNHYM-iXpGKjMmKGLCZLZjhi7AacoLW9V_jMKDV9cc2M9rnzKsVgOe5vgD-UcVg1IolzXoCtSCBqgOTpb_OYXbRE3_lUZp-3jSaBMvuIMxzWc_ehfp564mjkK1eFYPqMNNpktzNkNC6KQpgfi6SHBWWi4Rcqi-gVGlQFB1w8cSCIT4LZqEOPufdr2D1TS_9pUTdJz4j9XxxR1PdTnR-VHWK0VYcGCetBwupLrBFy_SHMUM0As2IzgK9Ppc5LVzff_qG6AQA59jgsQetzKnJl1nXqYdlBUeZBaLaP5uhKEN25n-odggsao6umstDUK2rTgl2LmzgFgwearJc_Mvns04i6JoKcbw4wIFZFW9qho_2AxUCF1BI6VJkJYvaKtotlBDNJdgP9toxMdHKd9pZcvkHKMyyq5GW9gQehrS4s4E_8BwGU2eHbRw2u1TNDkCu4fR2e15zjqHUDRDnp5A-fZTyr3WoTJHOfkcXWeruzI-tGf7m0DQMU20O1BsASdkLQB9eLPsmM7Bi0HGlZx2XeS5idMmoOLSvia2UKuiWAYWNRF66vEQ82O35bj7tT7bKL-lnCOfnm7LpNRblbAIku3iN_OH0TjAmt-aW-hqOIZlj4zA27L8wVUo7MzX2VBOD67a1uE6nnQm20Q5ERCUDTxrXl1wm6tzDAWXvZYHZlCp54DFAPQazTlGCq0H9FGX0sCVneInzV1AHXq84KF-ojg-1DloHt0eocJnHRmBGNB1V8WcvfRtre4h8KVWElnc2xCEuc4Dwv_SNJ2HvK8NkyjHFhFCJddqnw-2zC-RpHWNBVe9wrruhqNvR6EKAeuQlosGNsAKC51NQBngY5mh7zSoQrTXFQppPFX5WiKLO4QAVvOmd0GfXGrPYNpb11zfeWfADyqE_L8ObAkgCG3FwUdjyXRKMCkjLNgTSUses3lhCXvQxE71xqspPU1Wee49Q2Cp5iSNWMVHg8knwdQ6sdDJSBpDU_Up39pd4W4N7Wr7df7HkiD-MMtqB_jdwpB0QmZkslU7Xj2MB6OLMeXRxAwYVODx54kDTnKijWWpvDa_c4_CFCHcygtvmmQUtf_Lyy2D2Gp-tgC1WiH2Oh232Nt6fuaxVSANIAKOkMdzgTYtSRidw75YGV4IqjIaXYbwzVW7qqnZYu9Ky5hRV1fngvcURnUON1Gs5lf9OIgxkMR6lxDTMX1G9um56DzBhjUjw6Le4XdpcCigQjeCUiKRvZfX0CYTq6Rxli1crO8cYd49R9zE0bhJ5WCdgIlUysl78e8O8f7jRYHS86gTg4bunZ6Dnv2v_hxfa"

# Arquivos que devem ser mantidos (padrões de nome)
KEEP_PATTERNS = [
    "HubDaBia-v",           # HubDaBia-v2.6.0.exe, HubDaBia-v2.6.1.exe, etc.
    "Instalador_Hub_da_Bia-v",  # Instalador_Hub_da_Bia-v2.6.0.exe, etc.
    "HubDaBia_Suite.zip",
    "version.json",
    "apps.json",
]

import os
import sys
import json
import requests
from pathlib import Path


def clean_dropbox_old_versions(token: str, keep_latest: int = 2):
    """
    Remove versões antigas do Dropbox mantendo apenas as mais recentes.
    Mantém apenas os arquivos que correspondem aos padrões KEEP_PATTERNS
    e remove duplicatas antigas baseando-se na data de modificação.
    """
    print("[*] Limpando versões antigas no Dropbox...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Lista todos os arquivos na raiz do Dropbox (HubDaBiaUpdates)
    list_url = "https://api.dropboxapi.com/2/files/list_folder"
    list_data = {"path": "", "recursive": False}
    
    try:
        resp = requests.post(list_url, headers=headers, json=list_data)
        if resp.status_code != 200:
            print(f"[!] Erro ao listar arquivos: {resp.status_code} - {resp.text}")
            return
        
        entries = resp.json().get("entries", [])
        
        # Agrupa arquivos por padrão (prefixo antes da versão)
        file_groups = {}
        for entry in entries:
            if entry[".tag"] != "file":
                continue
            name = entry["name"]
            path = entry["path_display"]
            
            # Verifica se corresponde a algum padrão que devemos manter
            matched_pattern = None
            for pattern in KEEP_PATTERNS:
                if name.startswith(pattern):
                    matched_pattern = pattern
                    break
            
            if not matched_pattern:
                continue  # Não é um arquivo nosso, ignora
            
            # Extrai versão do nome (ex: "v2.6.0" de "HubDaBia-v2.6.0.exe")
            import re
            version_match = re.search(r'v(\d+\.\d+\.\d+)', name)
            version_str = version_match.group(1) if version_match else "0.0.0"
            
            # Converte versão para tupla para comparação
            try:
                version_tuple = tuple(map(int, version_str.split('.')))
            except:
                version_tuple = (0, 0, 0)
            
            if matched_pattern not in file_groups:
                file_groups[matched_pattern] = []
            file_groups[matched_pattern].append({
                "name": name,
                "path": path,
                "version": version_tuple,
                "version_str": version_str,
                "client_modified": entry.get("client_modified", "")
            })
        
        # Para cada grupo, mantém apenas as N versões mais recentes
        deleted_count = 0
        for pattern, files in file_groups.items():
            # Ordena por versão (mais recente primeiro)
            files.sort(key=lambda x: x["version"], reverse=True)
            
            # Mantém apenas as 'keep_latest' mais recentes
            to_delete = files[2:]  # keep_latest=2
            for f in to_delete:
                delete_url = "https://api.dropboxapi.com/2/files/delete_v2"
                try:
                    resp = requests.post(
                        delete_url,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json={"path": f["path"]}
                    )
                    if resp.status_code == 200:
                        print(f"   🗑 Removido: {f['name']} (v{f['version_str']})")
                        deleted_count += 1
                    else:
                        print(f"   [!] Erro ao remover {f['name']}: {resp.text}")
                except Exception as e:
                    print(f"   [!] Erro ao deletar {f['name']}: {e}")
        
        if deleted_count > 0:
            print(f"[+] Limpeza concluída: {deleted_count} arquivo(s) antigo(s) removido(s)")
        else:
            print("[*] Nenhum arquivo antigo para remover")
            
    except Exception as e:
        print(f"[!] Erro na limpeza: {e}")


def get_access_token():
    """Retorna o access token de longa duração"""
    return LONG_LIVED_TOKEN


def upload_file(local_path: str, dropbox_filename: str):
    local_p = Path(local_path)
    if not local_p.exists():
        raise FileNotFoundError(f"Arquivo local não encontrado: {local_path}")
    
    # Limpa versões antigas ANTES do upload
    token = get_access_token()
    clean_dropbox_old_versions(token, keep_latest=2)
    
    file_size = local_p.stat().st_size
    dropbox_path = f"/{dropbox_filename}" if not dropbox_filename.startswith("/") else dropbox_filename
    print(f"[*] Fazendo upload de '{local_p.name}' ({file_size / (1024*1024):.2f} MB) para HubDaBiaUpdates '{dropbox_path}'...")

    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {LONG_LIVED_TOKEN}",
        "Dropbox-API-Arg": json.dumps({
            "path": dropbox_path,
            "mode": "overwrite",
            "autorename": False,
            "mute": True
        }),
        "Content-Type": "application/octet-stream"
    }
    with open(local_path, "rb") as f:
        resp = requests.post(url, headers=headers, data=f)
    if resp.status_code != 200:
        raise RuntimeError(f"Erro no upload: {resp.status_code} - {resp.text}")
    print("[+] Upload concluído!")

    link = get_or_create_direct_link(dropbox_path, LONG_LIVED_TOKEN)
    return link


def get_or_create_direct_link(dropbox_path: str, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    create_url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    create_resp = requests.post(create_url, headers=headers, json={
        "path": dropbox_path,
        "settings": {"requested_visibility": "public"}
    })
    if create_resp.status_code == 200:
        url_raw = create_resp.json().get("url", "")
    else:
        list_url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
        list_resp = requests.post(list_url, headers=headers, json={"path": dropbox_path, "direct_only": True})
        if list_resp.status_code == 200 and list_resp.json().get("links"):
            url_raw = list_resp.json()["links"][0]["url"]
        else:
            raise RuntimeError(f"Erro ao obter link: {create_resp.text}")

    if "dl=0" in url_raw:
        return url_raw.replace("dl=0", "dl=1")
    elif "dl=1" not in url_raw:
        sep = "&" if "?" in url_raw else "?"
        return f"{url_raw}{sep}dl=1"
    return url_raw


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("LINK_HUB:", upload_file(sys.argv[1], sys.argv[2]))