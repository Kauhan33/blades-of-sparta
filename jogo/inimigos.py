"""Inimigos e suas inteligências simples.

Cada inimigo recebe `mundo` em atualizar(): um objeto com os métodos
adicionar_projetil(p), tocar(som) e tremer(intensidade, duracao).
"""
import math
import random

from . import config as C
from .fisica import Corpo, mover
from .objetos import criar_lanca, criar_onda_choque


class Inimigo(Corpo):
    """Base comum: vida, dano de contato, pontos e reação a golpes."""

    LARGURA = 34
    ALTURA = 50
    VIDA = 1
    DANO = 1
    PONTOS = 100
    PISAVEL = True
    TEM_GRAVIDADE = True

    def __init__(self, coluna, linha):
        x = coluna * C.TILE + (C.TILE - self.LARGURA) / 2
        y = (linha + 1) * C.TILE - self.ALTURA
        super().__init__(x, y, self.LARGURA, self.ALTURA)
        self.vida = self.VIDA
        self.vivo = True
        self.direcao = -1
        self.piscar = 0.0
        self.empurrao = 0.0
        self.anim_t = random.uniform(0, 10)
        self.ativo = True

    def receber_golpe(self, dano, lado):
        """Aplica dano; lado (-1/1) é para onde o inimigo é empurrado. Retorna True se morreu."""
        if not self.vivo:
            return False
        self.vida -= dano
        self.piscar = 0.15
        if lado:
            self.vx = 240 * lado
            self.empurrao = 0.18
        if self.vida <= 0:
            self.vivo = False
        return not self.vivo

    def tem_chao_a_frente(self, nivel, direcao):
        frente = self.x + self.w + 2 if direcao > 0 else self.x - 2
        return nivel.apoio(int(frente // C.TILE), int((self.base + 2) // C.TILE))

    def _fisica(self, dt, nivel):
        self.vy = min(self.vy + C.GRAVIDADE * dt, C.VEL_MAX_QUEDA)
        mover(self, dt, nivel)
        if self.y > nivel.altura_px + 200:  # caiu no abismo
            self.vivo = False

    def atualizar(self, dt, nivel, heroi, mundo):
        self.anim_t += dt
        self.piscar = max(0.0, self.piscar - dt)
        self.empurrao = max(0.0, self.empurrao - dt)


class Esqueleto(Inimigo):
    """Legionário morto-vivo: patrulha e vira ao achar parede ou beirada."""

    VIDA = 2
    PONTOS = 100

    def __init__(self, coluna, linha):
        super().__init__(coluna, linha)
        self.velocidade = random.uniform(60, 100)

    def atualizar(self, dt, nivel, heroi, mundo):
        super().atualizar(dt, nivel, heroi, mundo)
        if self.empurrao <= 0:
            self.vx = self.direcao * self.velocidade
        self._fisica(dt, nivel)
        if self.empurrao > 0:
            return
        if self.bateu_parede:
            self.direcao *= -1
        elif self.no_chao and not self.tem_chao_a_frente(nivel, self.direcao):
            self.direcao *= -1


class Arqueiro(Inimigo):
    """Esqueleto que fica parado e arremessa lanças quando vê o herói."""

    VIDA = 2
    PONTOS = 150

    def __init__(self, coluna, linha):
        super().__init__(coluna, linha)
        self.recarga = random.uniform(1.0, 2.0)
        self.arremesso = 0.0

    def atualizar(self, dt, nivel, heroi, mundo):
        super().atualizar(dt, nivel, heroi, mundo)
        if self.empurrao <= 0:
            self.vx = 0.0
        self._fisica(dt, nivel)
        distancia_x = heroi.centro_x - self.centro_x
        self.direcao = 1 if distancia_x > 0 else -1
        self.recarga -= dt
        self.arremesso = max(0.0, self.arremesso - dt)
        if self.recarga <= 0 and abs(distancia_x) < 520 and abs(heroi.centro_y - self.centro_y) < 140:
            self.recarga = random.uniform(1.6, 2.4)
            self.arremesso = 0.25
            x = self.centro_x + self.direcao * 18 - (0 if self.direcao > 0 else 30)
            mundo.adicionar_projetil(criar_lanca(x, self.y + 16, self.direcao))
            mundo.tocar("lanca")


class Harpia(Inimigo):
    """Voa em onda (seno) e mergulha em direção ao herói."""

    LARGURA = 40
    ALTURA = 34
    VIDA = 1
    PONTOS = 150
    TEM_GRAVIDADE = False

    def __init__(self, coluna, linha):
        super().__init__(coluna, linha)
        self.base_x = self.x
        self.base_y = self.y
        self.tp = random.uniform(0, math.tau)
        self.estado = "patrulha"
        self.timer = 0.0
        self.recarga = 1.5

    def _posicao_patrulha(self):
        return (self.base_x + math.sin(self.tp * 0.9) * 120,
                self.base_y + math.sin(self.tp * 3.0) * 14)

    def atualizar(self, dt, nivel, heroi, mundo):
        super().atualizar(dt, nivel, heroi, mundo)
        self.recarga -= dt
        if self.estado == "patrulha":
            self.tp += dt
            antes = self.x
            self.x, self.y = self._posicao_patrulha()
            self.direcao = 1 if self.x >= antes else -1
            perto = abs(heroi.centro_x - self.centro_x) < 230 and 0 < heroi.centro_y - self.centro_y < 300
            if perto and self.recarga <= 0 and not heroi.morto:
                angulo = math.atan2(heroi.centro_y - self.centro_y, heroi.centro_x - self.centro_x)
                self.vx = math.cos(angulo) * 340
                self.vy = math.sin(angulo) * 340
                self.direcao = 1 if self.vx > 0 else -1
                self.estado = "mergulho"
                self.timer = 0.9
        elif self.estado == "mergulho":
            self.timer -= dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            centro_coluna = int(self.centro_x // C.TILE)
            centro_linha = int(self.centro_y // C.TILE)
            if self.timer <= 0 or nivel.solido(centro_coluna, centro_linha) or self.empurrao > 0:
                self.estado = "retorno"
        else:  # retorno ao trajeto de patrulha
            alvo_x, alvo_y = self._posicao_patrulha()
            dx, dy = alvo_x - self.x, alvo_y - self.y
            distancia = math.hypot(dx, dy)
            if distancia < 6:
                self.estado = "patrulha"
                self.recarga = 2.5
            else:
                passo = min(distancia, 200 * dt)
                self.x += dx / distancia * passo
                self.y += dy / distancia * passo
                self.direcao = 1 if dx > 0 else -1

    def receber_golpe(self, dano, lado):
        morreu = super().receber_golpe(dano, lado)
        self.vx = 0.0
        self.estado = "retorno"
        return morreu


class Ciclope(Inimigo):
    """Chefe final: anda, prepara uma investida e salta criando ondas de choque."""

    LARGURA = 84
    ALTURA = 120
    VIDA = C.CICLOPE_VIDA
    DANO = 2
    PONTOS = 2000
    PISAVEL = False

    def __init__(self, coluna, linha):
        super().__init__(coluna, linha)
        self.inicio = (self.x, self.y)
        self.reiniciar()

    def reiniciar(self):
        """Volta ao estado inicial (usado quando o herói morre na luta)."""
        self.x, self.y = self.inicio
        self.vx = self.vy = 0.0
        self.vida = self.VIDA
        self.vivo = True
        self.estado = "dormindo"
        self.timer = 0.0
        self.proximo_ataque = "investida"

    @property
    def furioso(self):
        return self.vida <= self.VIDA // 2

    @property
    def acordado(self):
        return self.estado != "dormindo"

    def _tempo_andando(self):
        return C.CICLOPE_TEMPO_ANDANDO_FURIOSO if self.furioso else C.CICLOPE_TEMPO_ANDANDO

    def _atordoar(self, duracao, mundo):
        self.estado = "atordoado"
        self.timer = duracao
        self.vx = 0.0
        mundo.tocar("impacto")
        mundo.tremer(8, 0.4)

    def acertou_heroi(self):
        """A investida termina ao acertar: um ataque, um acerto."""
        if self.estado == "investida":
            self.estado = "andando"
            self.timer = self._tempo_andando()
            self.vx = 0.0

    def receber_golpe(self, dano, lado):
        if self.estado == "dormindo":
            self.estado = "andando"
            self.timer = 1.0
        return super().receber_golpe(dano, 0)  # pesado demais para ser empurrado

    def atualizar(self, dt, nivel, heroi, mundo):
        super().atualizar(dt, nivel, heroi, mundo)
        distancia_x = heroi.centro_x - self.centro_x
        rapidez = C.CICLOPE_RAPIDEZ_FURIOSO if self.furioso else 1.0
        self.timer -= dt

        if self.estado == "dormindo":
            self.vx = 0.0
            if abs(distancia_x) < 520:
                self.estado = "andando"
                self.timer = 1.6
                mundo.tocar("rugido")
                mundo.tremer(6, 0.5)
        elif self.estado == "andando":
            self.direcao = 1 if distancia_x > 0 else -1
            self.vx = self.direcao * C.CICLOPE_ANDAR * rapidez
            if self.timer <= 0:
                self.estado = "preparando"
                self.timer = max(C.CICLOPE_PREPARO_MIN, C.CICLOPE_PREPARO / rapidez)
                self.vx = 0.0
                # aviso sonoro diferente para cada ataque
                mundo.tocar("rugido" if self.proximo_ataque == "investida" else "preparo_salto")
        elif self.estado == "preparando":
            self.vx = 0.0
            if self.timer <= 0:
                if self.proximo_ataque == "investida":
                    self.estado = "investida"
                    self.timer = C.CICLOPE_INVESTIDA_TEMPO
                    self.proximo_ataque = "salto"
                else:
                    self.estado = "salto"
                    self.vy = -C.CICLOPE_PULO
                    self.vx = max(-180, min(180, distancia_x * 1.2))
                    self.no_chao = False
                    self.proximo_ataque = "investida"
        elif self.estado == "investida":
            self.vx = self.direcao * C.CICLOPE_INVESTIDA_VEL * rapidez
            if self.bateu_parede:
                self._atordoar(C.CICLOPE_ATORDOADO_PAREDE, mundo)
            elif self.timer <= 0:  # errou: fica um instante sem reação
                self._atordoar(C.CICLOPE_ATORDOADO_ERROU, mundo)
        elif self.estado == "salto":
            if self.no_chao and self.vy >= 0:
                self.estado = "atordoado"
                self.timer = C.CICLOPE_ATORDOADO_POUSO
                self.vx = 0.0
                for lado in (-1, 1):
                    x = self.centro_x + lado * (self.w / 2) - (28 if lado < 0 else 0)
                    mundo.adicionar_projetil(criar_onda_choque(x, self.base, lado))
                mundo.tocar("impacto")
                mundo.tremer(12, 0.5)
        elif self.estado == "atordoado":
            self.vx = 0.0
            if self.timer <= 0:
                self.estado = "andando"
                self.timer = self._tempo_andando()

        # Não anda nem investe para fora da beirada.
        if self.no_chao and self.vx and not self.tem_chao_a_frente(nivel, 1 if self.vx > 0 else -1):
            self.vx = 0.0
            if self.estado == "investida":
                self._atordoar(C.CICLOPE_ATORDOADO_PAREDE, mundo)
        self.vy = min(self.vy + C.GRAVIDADE * dt, C.VEL_MAX_QUEDA)
        mover(self, dt, nivel)


TIPOS = {"S": Esqueleto, "A": Arqueiro, "H": Harpia, "C": Ciclope}


def criar_inimigo(caractere, coluna, linha):
    return TIPOS[caractere](coluna, linha)
