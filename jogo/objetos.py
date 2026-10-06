"""Objetos do mundo que não são personagens."""
import math
import random

import pygame

from . import config as C


class Projetil:
    """Objeto que voa em linha reta e some ao bater em parede ou expirar."""

    def __init__(self, x, y, vx, largura, altura, dano=1, duracao=C.VIDA_PROJETIL, tipo="lanca"):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.w = largura
        self.h = altura
        self.dano = dano
        self.duracao = duracao
        self.tipo = tipo
        self.t = 0.0
        self.vivo = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def atualizar(self, dt, nivel):
        self.x += self.vx * dt
        self.t += dt
        frente = self.x + self.w if self.vx > 0 else self.x
        coluna = int(frente // C.TILE)
        linha = int((self.y + self.h / 2) // C.TILE)
        # Remove projéteis que expiram, batem ou saem do mapa: a lista não cresce para sempre.
        if self.t >= self.duracao or nivel.solido(coluna, linha) or not (0 <= self.x <= nivel.largura_px):
            self.vivo = False


def criar_lanca(x, y, direcao):
    return Projetil(x, y, 360 * direcao, 30, 6, dano=1, tipo="lanca")


def criar_onda_choque(x, y_chao, direcao):
    return Projetil(x, y_chao - 26, 380 * direcao, 28, 26, dano=1, duracao=1.6, tipo="onda")


class Orbe:
    """Orbe coletável: vermelho dá pontos, verde recupera vida."""

    def __init__(self, x, y, tipo="vermelho"):
        self.x = float(x)
        self.y = float(y)
        self.tipo = tipo
        self.t = random.uniform(0, math.tau)
        self.vivo = True
        self.raio = 9 if tipo == "vermelho" else 11

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.raio), int(self.y - self.raio), self.raio * 2, self.raio * 2)

    def atualizar(self, dt):
        self.t += dt

    @property
    def flutuacao(self):
        return math.sin(self.t * 4) * 4


class Altar:
    """Checkpoint: ao ser tocado, passa a ser o ponto de renascimento."""

    def __init__(self, coluna, linha):
        self.x = coluna * C.TILE + 8
        self.y = linha * C.TILE + 14
        self.w = C.TILE - 16
        self.h = C.TILE - 14
        self.ativo = False
        self.t = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y - 40, self.w, self.h + 40)

    @property
    def ponto_renascer(self):
        return self.x + self.w / 2, self.y + self.h


class Portal:
    """Saída da fase. Fica trancado enquanto o chefe estiver vivo."""

    def __init__(self, coluna, linha):
        self.x = coluna * C.TILE - 12
        self.y = (linha + 1) * C.TILE - 110
        self.w = C.TILE + 24
        self.h = 110
        self.travado = False
        self.t = 0.0

    @property
    def rect(self):
        return pygame.Rect(self.x + 18, self.y + 20, self.w - 36, self.h - 20)


class PlataformaMovel:
    """Plataforma que vai e volta na horizontal carregando quem está em cima."""

    LARGURA = 2 * C.TILE
    ALTURA = 16
    PERCURSO = 4 * C.TILE
    VELOCIDADE = 85

    def __init__(self, coluna, linha):
        self.x = float(coluna * C.TILE)
        self.y = float(linha * C.TILE)
        self.w = self.LARGURA
        self.h = self.ALTURA
        self.x_min = self.x
        self.x_max = self.x + self.PERCURSO
        self.direcao = 1
        self.dx = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def atualizar(self, dt):
        anterior = self.x
        self.x += self.VELOCIDADE * self.direcao * dt
        if self.x >= self.x_max:
            self.x, self.direcao = self.x_max, -1
        elif self.x <= self.x_min:
            self.x, self.direcao = self.x_min, 1
        self.dx = self.x - anterior


class Particula:
    """Faísca, sangue de osso, brasa... Some quando o tempo de vida acaba."""

    def __init__(self, x, y, vx, vy, cor, vida, tamanho=3, gravidade=900):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.cor = cor
        self.vida = vida
        self.vida_max = vida
        self.tamanho = tamanho
        self.gravidade = gravidade

    @property
    def viva(self):
        return self.vida > 0

    def atualizar(self, dt):
        self.vida -= dt
        self.vy += self.gravidade * dt
        self.x += self.vx * dt
        self.y += self.vy * dt


class TextoFlutuante:
    """Texto que sobe e desaparece (ex.: "+100")."""

    def __init__(self, x, y, texto, cor=C.AMARELO, vida=0.9):
        self.x = x
        self.y = y
        self.texto = texto
        self.cor = cor
        self.vida = vida

    @property
    def viva(self):
        return self.vida > 0

    def atualizar(self, dt):
        self.vida -= dt
        self.y -= 40 * dt


def explosao(x, y, cores, quantidade=14, forca=260, vida=0.6, tamanho=3, gravidade=900):
    """Cria partículas espalhadas em todas as direções a partir de um ponto."""
    particulas = []
    for _ in range(quantidade):
        angulo = random.uniform(0, math.tau)
        velocidade = random.uniform(forca * 0.3, forca)
        particulas.append(Particula(x, y, math.cos(angulo) * velocidade, math.sin(angulo) * velocidade - forca * 0.3,
                                    random.choice(cores), random.uniform(vida * 0.5, vida),
                                    random.randint(max(1, tamanho - 1), tamanho + 1), gravidade))
    return particulas
