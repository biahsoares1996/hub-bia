# -*- coding: utf-8 -*-
"""
Hub da Bia - Suíte Pessoal de Produtividade & Ferramentas
"""
import json
import sys
from pathlib import Path

__app_name__ = "Hub da Bia"
__author__ = "BiaStudio"


def _load_version() -> str:
    try:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).resolve().parent
            for p in [base / "version.json", base / "_internal" / "version.json"]:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f).get("version", "2.6.0")
        dev_v = Path(__file__).resolve().parent.parent.parent / "version.json"
        if dev_v.exists():
            with open(dev_v, "r", encoding="utf-8") as f:
                return json.load(f).get("version", "2.6.0")
    except Exception:
        pass
    return "2.6.0"


__version__ = _load_version()
