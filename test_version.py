import sys
sys.path.insert(0, 'src')
from hub_builder import BuilderWindow
from pathlib import Path

b = BuilderWindow.__new__(BuilderWindow)
b.project_dir = Path('F:/z.Drives/Programas/HubBia')
print('Version:', b.get_version())