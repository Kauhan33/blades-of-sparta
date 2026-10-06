"""Gera capturas de tela do jogo sem abrir janela (usado na documentação).

Uso:  python tools/capturar_telas.py
Salva PNGs em docs/img/.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from jogo.config import ALTURA, LARGURA  # noqa: E402
from jogo.entrada import Entrada  # noqa: E402
from jogo.jogo import Estado, Jogo  # noqa: E402
from jogo.recursos import caminho  # noqa: E402

DT = 1 / 60


def salvar(jogo, nome):
    jogo.desenhar()
    destino = caminho("docs", "img", nome)
    pygame.image.save(jogo.tela, destino)
    print("salvo", destino)


def avancar(jogo, segundos, **teclas):
    for _ in range(int(segundos / DT)):
        jogo.atualizar(DT, Entrada(**teclas))


def main():
    pygame.init()
    os.makedirs(caminho("docs", "img"), exist_ok=True)
    tela = pygame.Surface((LARGURA, ALTURA))
    jogo = Jogo(tela)
    avancar(jogo, 0.7)
    salvar(jogo, "menu.png")

    # Fase 1: anda até o primeiro esqueleto e ataca
    jogo.atualizar(DT, Entrada(confirmar=True))
    avancar(jogo, 1.0, direita=True)
    jogo.atualizar(DT, Entrada(direita=True, atacar=True))
    avancar(jogo, 0.12, direita=True)
    salvar(jogo, "fase1.png")

    # Fase 2
    jogo.carregar_fase(1)
    avancar(jogo, 2.8)
    jogo.atualizar(DT, Entrada(atacar=True))
    avancar(jogo, 0.1)
    salvar(jogo, "fase2.png")

    # Fase 3: chefe acordado
    jogo.carregar_fase(2)
    jogo.heroi.x = 36 * 48
    jogo.heroi.furia_t = 3.0
    avancar(jogo, 1.2)
    jogo.atualizar(DT, Entrada(atacar=True))
    avancar(jogo, 0.12)
    salvar(jogo, "fase3_chefe.png")

    jogo.mudar_estado(Estado.PAUSADO)
    salvar(jogo, "pausa.png")
    jogo.mudar_estado(Estado.JOGANDO)
    jogo.vidas = 1
    jogo.matar_heroi()
    avancar(jogo, 2.0)
    salvar(jogo, "game_over.png")

    jogo.novo_jogo()
    jogo.estado = Estado.JOGANDO
    jogo.carregar_fase(2)
    jogo.chefe.vivo = False
    jogo.heroi.x = jogo.portal.x + 20
    avancar(jogo, 0.2)
    salvar(jogo, "vitoria.png")
    pygame.quit()


if __name__ == "__main__":
    main()
