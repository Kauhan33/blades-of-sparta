"""Corpos com posição/velocidade e colisão contra a grade de tiles.

Movimento: nova posição = posição atual + velocidade * dt (dt em segundos),
então a velocidade do jogo não depende do FPS.

A colisão é resolvida um eixo por vez: primeiro move em X e empurra o corpo
para fora das paredes; depois move em Y. Se ao descer o corpo encosta no
topo de um tile sólido, ele é colocado exatamente sobre o tile e marcado
como "no chão" — é assim que o computador sabe que o personagem está em
cima do chão.
"""
import pygame

from .config import TILE

EPS = 0.001


class Corpo:
    """Retângulo com posição em ponto flutuante e velocidade."""

    def __init__(self, x, y, largura, altura):
        self.x = float(x)
        self.y = float(y)
        self.w = largura
        self.h = altura
        self.vx = 0.0
        self.vy = 0.0
        self.no_chao = False
        self.bateu_parede = False
        self.bateu_teto = False
        self.plataforma = None
        self.base_anterior = self.y + self.h  # base antes do último movimento

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    @property
    def centro_x(self):
        return self.x + self.w / 2

    @property
    def centro_y(self):
        return self.y + self.h / 2

    @property
    def base(self):
        return self.y + self.h


def mover(corpo, dt, nivel, plataformas=(), descer=False):
    """Move o corpo pelo mundo resolvendo colisões com tiles e plataformas móveis.

    descer=True deixa o corpo atravessar plataformas de uma via para baixo.
    """
    corpo.bateu_parede = False
    corpo.bateu_teto = False

    # Plataforma móvel carrega quem está em cima dela.
    dx = corpo.vx * dt
    if corpo.plataforma is not None:
        dx += corpo.plataforma.dx

    # ---- Eixo X ----
    corpo.x += dx
    linha0 = int(corpo.y // TILE)
    linha1 = int((corpo.y + corpo.h - EPS) // TILE)
    if dx > 0:
        coluna = int((corpo.x + corpo.w - EPS) // TILE)
        if any(nivel.solido(coluna, l) for l in range(linha0, linha1 + 1)):
            corpo.x = coluna * TILE - corpo.w
            corpo.vx = 0.0
            corpo.bateu_parede = True
    elif dx < 0:
        coluna = int(corpo.x // TILE)
        if any(nivel.solido(coluna, l) for l in range(linha0, linha1 + 1)):
            corpo.x = (coluna + 1) * TILE
            corpo.vx = 0.0
            corpo.bateu_parede = True

    # ---- Eixo Y ----
    base_anterior = corpo.y + corpo.h
    corpo.y += corpo.vy * dt
    corpo.no_chao = False
    corpo.plataforma = None
    coluna0 = int(corpo.x // TILE)
    coluna1 = int((corpo.x + corpo.w - EPS) // TILE)

    if corpo.vy >= 0:
        linha = int((corpo.y + corpo.h - EPS) // TILE)
        topo = linha * TILE
        colunas = range(coluna0, coluna1 + 1)
        pousou = any(nivel.solido(c, linha) for c in colunas)
        if not pousou and not descer and base_anterior <= topo + EPS:
            pousou = any(nivel.uma_via(c, linha) for c in colunas)
        if pousou:
            corpo.y = topo - corpo.h
            corpo.vy = 0.0
            corpo.no_chao = True
        elif not descer:
            for plataforma in plataformas:
                sobrepoe = corpo.x < plataforma.x + plataforma.w and corpo.x + corpo.w > plataforma.x
                if sobrepoe and base_anterior <= plataforma.y + EPS <= corpo.y + corpo.h:
                    corpo.y = plataforma.y - corpo.h
                    corpo.vy = 0.0
                    corpo.no_chao = True
                    corpo.plataforma = plataforma
                    break
    else:
        linha = int(corpo.y // TILE)
        if any(nivel.solido(c, linha) for c in range(coluna0, coluna1 + 1)):
            corpo.y = (linha + 1) * TILE
            corpo.vy = 0.0
            corpo.bateu_teto = True


def aproximar(valor, alvo, passo):
    """Move valor em direção ao alvo sem ultrapassá-lo."""
    if valor < alvo:
        return min(valor + passo, alvo)
    return max(valor - passo, alvo)
