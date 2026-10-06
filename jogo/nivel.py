"""Fases do jogo descritas como mapas ASCII e a grade de tiles carregada deles.

Cada caractere ocupa um tile de TILE x TILE pixels. A coordenada de mundo
de um tile é (coluna * TILE, linha * TILE) — origem no canto superior
esquerdo, com y crescendo para baixo, como na tela do pygame.

Legenda
    ' '  vazio                  '#'  chão / rocha (sólido)
    '='  bloco de pedra (sólido)'-'  plataforma de uma via (atravessa por baixo)
    '^'  espinhos (dano)        '~'  lava (morte)
    'X'  ânfora quebrável       'o'  orbe vermelho (pontos)
    'g'  orbe verde (cura)      'P'  início do herói
    'K'  altar (checkpoint)     'F'  portal de saída
    'S'  esqueleto legionário   'A'  esqueleto arqueiro
    'H'  harpia                 'C'  Ciclope (chefe)
    'M'  plataforma móvel
"""
from .config import TILE

SOLIDOS = frozenset("#=X")
TILES_FIXOS = frozenset("#=X-^~")
ENTIDADES = frozenset("PKFogSAHCM")
LEGENDA = frozenset(" ") | TILES_FIXOS | ENTIDADES

FASE_1 = [
    "                                                                                                                ",
    "                                                                                                                ",
    "                                                                                                                ",
    "                                                                                                                ",
    "                                                                  ooo                              H            ",
    "         oooo              oooo              oooo                 ===                       oooo                ",
    "         ----              ====              ----              ooo                          ----                ",
    "                                   oo                          ===                                              ",
    "  P  ooo      S         X    A S  ####        ^^    K   S                 K       S   XX  g      S   ooo   F    ",
    "##################  ##################   ####################          #########################################",
    "##################  ##################   ####################          #########################################",
]

FASE_2 = [
    "############################################################################################################################",
    "                                                                                                                            ",
    "                                                                                                                            ",
    "                                         H                                                             H                    ",
    "                                                                                                              H             ",
    "                  ooo       ooo               oooo                   g                  ooo                     ooo         ",
    "                            ===              ------       o         ----                                        ===         ",
    "                M                                         =                           M                                     ",
    "  P  ooo   S                       A    X      ^^    K            S      S AXX      K              oooX   S            F    ",
    "################~~~~~~~~################################~~~~~#########################~~~~~~~~##############################",
    "################~~~~~~~~################################~~~~~#########################~~~~~~~~##############################",
]

FASE_3 = [
    "                                                                            ",
    "                                                                            ",
    "                                                                            ",
    "                                                                            ",
    "                                                                            ",
    "              ooo                  g                     go                 ",
    "              ---                 ----                  ----                ",
    "                                                                            ",
    "  P  ooo o   S    A       K                   C                        F    ",
    "############################################################################",
    "############################################################################",
]

FASES = [
    {"nome": "Portões de Esparta", "tema": "esparta", "mapa": FASE_1},
    {"nome": "Cavernas do Hades", "tema": "hades", "mapa": FASE_2},
    {"nome": "Arena do Ciclope", "tema": "arena", "mapa": FASE_3},
]


def validar_mapa(mapa):
    """Confere se o mapa é jogável; levanta ValueError explicando o problema."""
    if not mapa:
        raise ValueError("mapa vazio")
    largura = len(mapa[0])
    for numero, linha in enumerate(mapa):
        if len(linha) != largura:
            raise ValueError(f"linha {numero} tem {len(linha)} colunas, esperado {largura}")
        desconhecidos = set(linha) - LEGENDA
        if desconhecidos:
            raise ValueError(f"caractere(s) desconhecido(s) {sorted(desconhecidos)} na linha {numero}")
    texto = "".join(mapa)
    if texto.count("P") != 1:
        raise ValueError(f"o mapa precisa de exatamente 1 'P' (encontrado {texto.count('P')})")
    if "F" not in texto:
        raise ValueError("o mapa precisa de um portal de saída 'F'")


class Nivel:
    """Grade de tiles fixos de uma fase e a lista de entidades a criar."""

    def __init__(self, dados):
        mapa = dados["mapa"]
        validar_mapa(mapa)
        self.nome = dados["nome"]
        self.tema = dados.get("tema", "esparta")
        self.altura = len(mapa)
        self.largura = len(mapa[0])
        self.largura_px = self.largura * TILE
        self.altura_px = self.altura * TILE
        self.grade = []
        self.spawns = []  # (caractere, coluna, linha)
        for linha, texto in enumerate(mapa):
            fileira = []
            for coluna, ch in enumerate(texto):
                if ch in TILES_FIXOS:
                    fileira.append(ch)
                else:
                    fileira.append(" ")
                    if ch in ENTIDADES:
                        self.spawns.append((ch, coluna, linha))
            self.grade.append(fileira)
        self.inicio = next((c, l) for ch, c, l in self.spawns if ch == "P")

    def tile(self, coluna, linha):
        """Tile na posição; as laterais do mapa funcionam como paredes."""
        if coluna < 0 or coluna >= self.largura:
            return "#"
        if linha < 0 or linha >= self.altura:
            return " "
        return self.grade[linha][coluna]

    def solido(self, coluna, linha):
        return self.tile(coluna, linha) in SOLIDOS

    def uma_via(self, coluna, linha):
        return self.tile(coluna, linha) == "-"

    def apoio(self, coluna, linha):
        """Verdadeiro se o tile sustenta algo em cima (sólido ou uma via)."""
        return self.solido(coluna, linha) or self.uma_via(coluna, linha)

    def remover(self, coluna, linha):
        if 0 <= coluna < self.largura and 0 <= linha < self.altura:
            self.grade[linha][coluna] = " "

    def tiles_no_retangulo(self, x, y, largura, altura):
        """Gera (coluna, linha, tile) de todos os tiles que tocam o retângulo."""
        c0 = int(x // TILE)
        c1 = int((x + largura - 0.001) // TILE)
        l0 = int(y // TILE)
        l1 = int((y + altura - 0.001) // TILE)
        for linha in range(l0, l1 + 1):
            for coluna in range(c0, c1 + 1):
                yield coluna, linha, self.tile(coluna, linha)
