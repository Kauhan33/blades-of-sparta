"""Bot de QA: tenta atravessar cada fase (sem inimigos) para provar que é possível terminá-la.

Uso:  python tools/bot_percurso.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from jogo.config import ALTURA, LARGURA, TILE  # noqa: E402
from jogo.entrada import Entrada  # noqa: E402
from jogo.jogo import Estado, Jogo  # noqa: E402
from jogo.nivel import FASES  # noqa: E402

DT = 1 / 60


def decidir(jogo):
    """Escolhe a entrada do quadro olhando o terreno à frente do herói."""
    h = jogo.heroi
    nivel = jogo.nivel
    if h.no_chao and h.plataforma is None:
        jogo.bot_saindo = False
    if not h.no_chao:
        for p in ([] if getattr(jogo, "bot_saindo", False) else jogo.plataformas):  # no ar sobre uma plataforma móvel: mira o centro dela
            centro = p.x + p.w / 2
            if p.y >= h.base - 10 and abs(h.centro_x - centro) < 2.5 * TILE:
                return Entrada(direita=h.centro_x < centro - 8, esquerda=h.centro_x > centro + 8,
                               pular_segurado=True)
        return Entrada(direita=True, pular_segurado=True)

    if h.plataforma is not None:  # em cima de plataforma móvel: espera chegar perto do chão
        p = h.plataforma
        coluna_destino = int((p.x + p.w + TILE * 1.5) // TILE)
        linha_pe = int((h.base + 2) // TILE)
        alvo_proximo = any(nivel.apoio(coluna_destino, l) for l in range(linha_pe, linha_pe + 3))
        if p.x >= p.x_max - 6 or alvo_proximo and p.direcao > 0:
            jogo.bot_saindo = True
            return Entrada(direita=True, pular=True, pular_segurado=True)
        return Entrada()

    frente = int((h.x + h.w + 8) // TILE)
    linha_pe = int((h.base + 2) // TILE)
    buraco = not nivel.apoio(frente, linha_pe)
    perigo = nivel.tile(frente, linha_pe - 1) == "^"
    parede = nivel.solido(frente, linha_pe - 1)

    if buraco:
        # há plataforma móvel por perto? espera ela encostar
        for p in jogo.plataformas:
            if abs(p.y - h.base) < 3 * TILE and h.x - 2 * TILE < p.x < h.x + 7 * TILE:
                if p.x <= h.x + h.w + 20 and p.direcao < 0 or p.x <= h.x + h.w - 10:
                    return Entrada(direita=True, pular=True, pular_segurado=True)
                return Entrada()
    if buraco or perigo or parede:
        return Entrada(direita=True, pular=True, pular_segurado=True)
    return Entrada(direita=True)


def percorrer(indice, limite_s=120):
    jogo = Jogo(pygame.Surface((LARGURA, ALTURA)))
    jogo.novo_jogo()
    jogo.carregar_fase(indice)
    jogo.estado = Estado.JOGANDO
    jogo.inimigos = []
    jogo.chefe = None
    jogo.vidas = 1
    for quadro in range(int(limite_s / DT)):
        jogo.atualizar(DT, decidir(jogo))
        if jogo.estado != Estado.JOGANDO:
            return jogo.estado, quadro * DT, jogo
        if jogo.heroi.morto:
            return "morreu", quadro * DT, jogo
    return "tempo", limite_s, jogo


def main():
    pygame.init()
    ok = True
    for indice, fase in enumerate(FASES):
        resultado, tempo, jogo = percorrer(indice)
        h = jogo.heroi
        concluiu = resultado in (Estado.FASE_CONCLUIDA, Estado.VITORIA)
        ok &= concluiu
        print(f"{fase['nome']:22s} -> {resultado if isinstance(resultado, str) else resultado.name:15s} "
              f"em {tempo:5.1f}s  (coluna {int(h.centro_x // TILE)}, linha {int(h.base // TILE)})")
    pygame.quit()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
