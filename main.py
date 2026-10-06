"""Blades of Sparta — ponto de entrada.

Loop principal: Entrada -> Regras -> Atualização -> Renderização -> repetir
"""
import sys

import pygame

from jogo.config import ALTURA, FPS, LARGURA, TITULO
from jogo.desenho import desenhar_espartano
from jogo.entrada import LeitorTeclado
from jogo.jogo import Jogo
from jogo.recursos import Audio


def criar_icone():
    icone = pygame.Surface((32, 32), pygame.SRCALPHA)
    desenhar_espartano(icone, 15, 2, 1, escala=0.45)
    return icone


def main():
    try:
        pygame.init()
        tela = pygame.display.set_mode((LARGURA, ALTURA))
    except pygame.error as erro:
        print(f"Não foi possível abrir a janela do jogo: {erro}")
        return 1
    pygame.display.set_caption(TITULO)
    pygame.display.set_icon(criar_icone())
    relogio = pygame.time.Clock()
    jogo = Jogo(tela, Audio())
    leitor = LeitorTeclado()

    while jogo.rodando:
        dt = relogio.tick(FPS) / 1000           # tempo do quadro em segundos
        entrada = leitor.ler(pygame.event.get())  # 1. entrada
        jogo.atualizar(dt, entrada)               # 2-3. regras e atualização
        jogo.fps = relogio.get_fps()
        jogo.desenhar()                           # 4. renderização
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
