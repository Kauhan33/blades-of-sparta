"""Câmera que acompanha o herói suavemente sem mostrar fora do mapa."""
import random

from .config import ALTURA, LARGURA


class Camera:
    def __init__(self, largura_mundo, altura_mundo):
        self.largura_mundo = largura_mundo
        self.altura_mundo = altura_mundo
        self.x = 0.0
        self.y = 0.0
        self.tremor = 0.0
        self.tremor_t = 0.0

    def _limitar(self, x, y):
        x = max(0.0, min(x, self.largura_mundo - LARGURA))
        y = max(0.0, min(y, max(0, self.altura_mundo - ALTURA)))
        return x, y

    def seguir(self, alvo_x, alvo_y, dt, instantaneo=False):
        """Aproxima a câmera do alvo (interpolação linear limitada aos cantos do mapa)."""
        destino_x, destino_y = self._limitar(alvo_x - LARGURA * 0.42, alvo_y - ALTURA * 0.55)
        if instantaneo:
            self.x, self.y = destino_x, destino_y
        else:
            fator = min(1.0, 7.0 * dt)
            self.x += (destino_x - self.x) * fator
            self.y += (destino_y - self.y) * fator
        self.tremor_t = max(0.0, self.tremor_t - dt)

    def tremer(self, intensidade, duracao):
        if intensidade >= self.tremor or self.tremor_t <= 0:
            self.tremor = intensidade
            self.tremor_t = duracao

    @property
    def deslocamento(self):
        """(x, y) inteiros a subtrair das coordenadas de mundo para obter as de tela."""
        dx = dy = 0.0
        if self.tremor_t > 0:
            dx = random.uniform(-self.tremor, self.tremor)
            dy = random.uniform(-self.tremor, self.tremor)
        x, y = self._limitar(self.x + dx, self.y + dy)
        return int(x), int(y)
