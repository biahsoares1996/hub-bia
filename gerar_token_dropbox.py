import http.server
import threading
import webbrowser
import urllib.parse
import requests
import json
import os
import sys
from pathlib import Path

APP_KEY = 'hd655p5levcaajv'
APP_SECRET = 'hnnl02r9evwklvt'
REDIRECT_URI = 'http://localhost:53682/callback'

code_container = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if '/callback' in self.path:
            parsed = urllib.parse.urlparse(self.path)
            code = urllib.parse.parse_qs(parsed.query).get('code', [None])[0]
            code_container['code'] = code
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Autorizado! Pode fechar esta aba.</h1><script>window.close();</script>')
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *args):
        pass

def main():
    print('=' * 60)
    print('  GERADOR DE REFRESH TOKEN DROPBOX')
    print('=' * 60)
    print()

    # Inicia servidor
    server = http.server.HTTPServer(('localhost', 53682), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    print('Servidor rodando em http://localhost:53682/callback')
    print('Abrindo browser para autorizacao...')
    print()

    # Abre browser
    auth_url = f'https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&response_type=code&token_access_type=offline&redirect_uri={urllib.parse.quote(REDIRECT_URI)}'
    webbrowser.open(auth_url)

    # Aguarda callback (timeout 120s)
    print('Aguardando autorizacao no browser (max 120s)...')
    thread.join(timeout=120)
    server.server_close()

    code = code_container.get('code')
    if not code:
        print('Timeout ou cancelado')
        sys.exit(1)

    print(f'Code recebido: {code[:20]}...')
    print('Trocando code por tokens...')

    # Troca code por tokens
    resp = requests.post('https://api.dropboxapi.com/oauth2/token', data={
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': APP_KEY,
        'client_secret': APP_SECRET,
        'redirect_uri': REDIRECT_URI
    })
    if resp.status_code != 200:
        print('Erro:', resp.status_code, resp.text)
        sys.exit(1)

    tokens = resp.json()
    refresh_token = tokens.get('refresh_token')
    access_token = tokens.get('access_token')
    print(f'Refresh token: {refresh_token[:50]}...')
    print(f'Access token: {access_token[:50]}...')

    # Salva no arquivo
    token_file = Path(os.environ['LOCALAPPDATA']) / 'HubDaBiaDeploy' / 'dropbox_hub_token.json'
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'w', encoding='utf-8') as f:
        json.dump({
            'refresh_token': refresh_token,
            'app_key': APP_KEY,
            'app_secret': APP_SECRET
        }, f, indent=2)
    print(f'Token salvo em: {token_file}')
    print()
    print('PRONTO! Agora teste o upload:')
    print('  python scripts/upload_hub_dropbox.py dist/HubDaBia/HubDaBia.exe HubDaBia.exe')

if __name__ == '__main__':
    main()