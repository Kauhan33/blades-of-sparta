"""Configuração comum dos testes: pygame sem janela e fábricas de cenários."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from jogo.config import ALTURA, LARGURA, TILE  # noqa: E402
from jogo.entrada import Entrada  # noqa: E402
from jogo.jogo import Estado, Jogo  # noqa: E402
from jogo.nivel import Nivel  # noqa: E402

pygame.init()

DT = 1 / 60

# Chão na linha 5 (topo em y = 5 * TILE = 240).
MAPA_PLANO = [
    "                    ",
    "                    ",
    "                    ",
    "                    ",
    "  P              F  ",
    "####################",
]
CHAO_PLANO = 5 * TILE


def nivel(mapa, nome="Teste", tema="esparta"):
    return Nivel({"nome": nome, "tema": tema, "mapa": mapa})


def criar_jogo(*mapas):
    """Jogo já no estado JOGANDO com as fases dadas."""
    fases = [{"nome": f"Teste {i + 1}", "tema": "esparta", "mapa": m} for i, m in enumerate(mapas or [MAPA_PLANO])]
    jogo = Jogo(pygame.Surface((LARGURA, ALTURA)), fases=fases)
    jogo.novo_jogo()
    jogo.mudar_estado(Estado.JOGANDO)
    return jogo


def simular(alvo, segundos, nivel_ou_none=None, **teclas):
    """Avança um Jogo (ou um Herói, se nivel_ou_none for dado) por alguns segundos."""
    for _ in range(int(round(segundos / DT))):
        if nivel_ou_none is None:
            alvo.atualizar(DT, Entrada(**teclas))
        else:
            alvo.atualizar(DT, Entrada(**teclas), nivel_ou_none)
