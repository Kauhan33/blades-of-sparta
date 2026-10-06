"""Leitura do teclado convertida em um objeto Entrada independente do pygame.

Separar a entrada da lógica permite testar o jogo simulando teclas.
"""
from dataclasses import dataclass

import pygame

TECLAS_PULO = (pygame.K_SPACE, pygame.K_w, pygame.K_UP, pygame.K_z)
TECLAS_ATAQUE = (pygame.K_j, pygame.K_x)
TECLAS_FURIA = (pygame.K_k, pygame.K_c)
TECLAS_ESQUIVA = (pygame.K_l, pygame.K_LSHIFT, pygame.K_RSHIFT)
TECLAS_CIMA = (pygame.K_w, pygame.K_UP)
TECLAS_BAIXO = (pygame.K_s, pygame.K_DOWN)


@dataclass
class Entrada:
    """Estado dos comandos em um quadro. Campos "apertou" valem só no quadro do toque."""

    esquerda: bool = False
    direita: bool = False
    baixo: bool = False
    pular_segurado: bool = False
    pular: bool = False
    atacar: bool = False
    furia: bool = False
    esquivar: bool = False
    cima: bool = False
    baixo_apertou: bool = False
    pausar: bool = False
    confirmar: bool = False
    reiniciar: bool = False
    menu: bool = False
    voltar: bool = False
    depurar: bool = False
    fechar: bool = False


class LeitorTeclado:
    """Converte eventos do pygame em Entrada."""

    def ler(self, eventos):
        entrada = Entrada()
        for evento in eventos:
            if evento.type == pygame.QUIT:
                entrada.fechar = True
            elif evento.type == pygame.KEYDOWN:
                tecla = evento.key
                entrada.pular |= tecla in TECLAS_PULO
                entrada.atacar |= tecla in TECLAS_ATAQUE
                entrada.furia |= tecla in TECLAS_FURIA
                entrada.esquivar |= tecla in TECLAS_ESQUIVA
                entrada.cima |= tecla in TECLAS_CIMA
                entrada.baixo_apertou |= tecla in TECLAS_BAIXO
                entrada.pausar |= tecla == pygame.K_p
                entrada.voltar |= tecla == pygame.K_ESCAPE
                entrada.confirmar |= tecla in (pygame.K_RETURN, pygame.K_KP_ENTER)
                entrada.reiniciar |= tecla == pygame.K_r
                entrada.menu |= tecla == pygame.K_m
                entrada.depurar |= tecla == pygame.K_F3

        teclas = pygame.key.get_pressed()
        entrada.esquerda = bool(teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        entrada.direita = bool(teclas[pygame.K_d] or teclas[pygame.K_RIGHT])
        entrada.baixo = bool(teclas[pygame.K_s] or teclas[pygame.K_DOWN])
        entrada.pular_segurado = any(teclas[t] for t in TECLAS_PULO)
        return entrada
