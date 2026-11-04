import os
from pathlib import Path

script = Path(r"F:\z.Drives\Programas\HubBia\scripts\upload_hub_dropbox.py")
content = script.read_text(encoding="utf-8")

old = 'TOKEN_FILE = Path(r"f:\\Meu Drive\\.AntigravityGoogle\\HubDaBia\\dropbox_hub_token.json")'
new = 'TOKEN_FILE = Path(os.environ["LOCALAPPDATA"]) / "HubDaBiaDeploy" / "dropbox_hub_token.json"'

# Garante import os
if not content.lstrip().startswith("import os"):
    content = "import os\n" + content

content = content.replace(old, new)
script.write_text(content, encoding="utf-8")
print("Script atualizado com sucesso!")
print("Novo TOKEN_FILE:", new)