# -*- coding: utf-8 -*-
"""
Gera o ícone oficial em alta resolução do Hub da Bia (.ico e .png)
Estética Craft Suite / Hub central.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_hub_icon():
    base_dir = Path(__file__).resolve().parent.parent
    assets_dir = base_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Fundo arredondado (Squircle) moderno com gradiente sutil
    # Desenhar cantos suaves
    r = 110
    draw.rounded_rectangle(
        [16, 16, size - 16, size - 16],
        radius=r,
        fill=(15, 23, 42, 255), # Deep Navy #0F172A
        outline=(56, 189, 248, 220), # Cyan glow #38BDF8
        width=8
    )

    # 2. Desenho do Símbolo Central (Hub Craft: 4 blocos conectados / grade moderna de apps)
    # Caixa superior esquerda (Ciano / Azul Áurea)
    draw.rounded_rectangle([110, 110, 230, 230], radius=28, fill=(37, 99, 235, 255))
    # Caixa superior direita (Âmbar / Gatoceiro)
    draw.rounded_rectangle([282, 110, 402, 230], radius=28, fill=(245, 158, 11, 255))
    # Caixa inferior esquerda (Esmeralda / OmniDVR)
    draw.rounded_rectangle([110, 282, 230, 402], radius=28, fill=(16, 185, 129, 255))
    # Caixa inferior direita (Roxo / Craft Studio)
    draw.rounded_rectangle([282, 282, 402, 402], radius=28, fill=(168, 85, 247, 255))

    # Conector central do Hub (ponto luminoso / núcleo brilhante)
    center = size // 2
    draw.ellipse([center - 32, center - 32, center + 32, center + 32], fill=(15, 23, 42, 255), outline=(255, 255, 255, 240), width=6)
    draw.ellipse([center - 16, center - 16, center + 16, center + 16], fill=(56, 189, 248, 255))

    # Salvar PNG alta definição
    png_path = assets_dir / "hub_icon.png"
    img.save(str(png_path), "PNG")
    print(f"Ícone PNG gerado: {png_path}")

    # Salvar ICO multi-resoluções para o Windows (256, 128, 64, 48, 32, 16)
    ico_path = assets_dir / "hub_icon.ico"
    img.save(
        str(ico_path),
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    print(f"Ícone ICO gerado: {ico_path}")

if __name__ == "__main__":
    create_hub_icon()
