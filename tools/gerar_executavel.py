"""Gera o executável do jogo com PyInstaller.

Uso:  python tools/gerar_executavel.py
Resultado: dist/BladesOfSparta.exe (arquivo único, sem console).
Requer: pip install pyinstaller pillow
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402
import PyInstaller.__main__  # noqa: E402
from PIL import Image  # noqa: E402

from jogo.desenho import desenhar_espartano  # noqa: E402

NOME = "BladesOfSparta"


def gerar_icone():
    """Desenha o espartano e salva como .ico (vários tamanhos)."""
    pygame.init()
    superficie = pygame.Surface((256, 256), pygame.SRCALPHA)
    pygame.draw.circle(superficie, (120, 20, 16), (128, 128), 124)
    pygame.draw.circle(superficie, (212, 168, 60), (128, 128), 124, 8)
    desenhar_espartano(superficie, 118, 34, 1, escala=3.0, em_furia=True)
    png = os.path.join(RAIZ, "build", "icone.png")
    ico = os.path.join(RAIZ, "build", "icone.ico")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    pygame.image.save(superficie, png)
    Image.open(png).save(ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    pygame.quit()
    return ico


def main():
    icone = gerar_icone()
    PyInstaller.__main__.run([
        os.path.join(RAIZ, "main.py"),
        "--name", NOME,
        "--onefile",
        "--windowed",
        "--icon", icone,
        # fonte Cinzel embutida no .exe (recursos.caminho() a encontra em sys._MEIPASS)
        "--add-data", f"{os.path.join(RAIZ, 'assets', 'fontes')}{os.pathsep}{os.path.join('assets', 'fontes')}",
        "--distpath", os.path.join(RAIZ, "dist"),
        "--workpath", os.path.join(RAIZ, "build"),
        "--specpath", os.path.join(RAIZ, "build"),
        "--noconfirm",
        "--clean",
    ])
    print("\nExecutável:", os.path.join(RAIZ, "dist", f"{NOME}.exe"))


if __name__ == "__main__":
    main()
