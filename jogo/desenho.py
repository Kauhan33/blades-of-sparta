"""Arte procedural: tudo é desenhado com primitivas do pygame (sem arquivos de imagem).

Convenção dos personagens: as funções recebem o centro horizontal (cx) e o
topo (topo) em coordenadas de TELA, a direção (1 = direita, -1 = esquerda)
e trabalham com deslocamentos locais em que +x é "para frente". A função
interna P() espelha o desenho quando o personagem olha para a esquerda.
"""
import math
import random

import pygame

from . import config as C
from .recursos import fonte

# --------------------------------------------------------------------------- utilidades


def misturar(cor_a, cor_b, t):
    """Interpolação linear entre duas cores."""
    return tuple(int(a + (b - a) * t) for a, b in zip(cor_a, cor_b))


def gradiente_vertical(largura, altura, topo, base):
    superficie = pygame.Surface((largura, altura))
    for y in range(altura):
        pygame.draw.line(superficie, misturar(topo, base, y / max(1, altura - 1)), (0, y), (largura, y))
    return superficie


_brilhos = {}


def brilho(raio, cor, intensidade=110):
    """Círculo luminoso translúcido (cacheado)."""
    chave = (raio, cor, intensidade)
    if chave not in _brilhos:
        superficie = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        for i in range(raio, 0, -2):
            alfa = int(intensidade * (1 - i / raio) ** 1.6)
            pygame.draw.circle(superficie, (*cor, alfa), (raio, raio), i)
        _brilhos[chave] = superficie
    return _brilhos[chave]


def desenhar_brilho(tela, x, y, raio, cor, intensidade=110):
    tela.blit(brilho(raio, cor, intensidade), (int(x - raio), int(y - raio)))


def texto_sombreado(tela, texto, tamanho, cor, centro=None, topo_esquerdo=None, negrito=True, sombra=(0, 0, 0)):
    """Escreve um texto com sombra; devolve o retângulo ocupado."""
    f = fonte(tamanho, negrito)
    imagem = f.render(texto, True, cor)
    imagem_sombra = f.render(texto, True, sombra)
    retangulo = imagem.get_rect()
    if centro is not None:
        retangulo.center = centro
    elif topo_esquerdo is not None:
        retangulo.topleft = topo_esquerdo
    deslocamento = max(2, tamanho // 16)
    tela.blit(imagem_sombra, (retangulo.x + deslocamento, retangulo.y + deslocamento))
    tela.blit(imagem, retangulo)
    return retangulo


# --------------------------------------------------------------------------- temas e cenário

# Estilo "épico sombrio": céus escuros com horizonte em brasa, silhuetas quase
# pretas e cores quentes só onde o olho deve ir (herói, perigos, orbes).
TEMAS = {
    "esparta": {
        "ceu": ((10, 8, 22), (148, 46, 30)), "longe": (46, 24, 40), "perto": (26, 14, 22),
        "detalhe": "templos", "terra": (58, 40, 34), "topo": (78, 88, 46), "topo_escuro": (46, 52, 30),
        "pedra": (112, 100, 92), "sol": (255, 96, 50), "sol_pos": (0.70, 0.56), "sol_raio": 58,
    },
    "hades": {
        "ceu": ((12, 4, 8), (90, 20, 12)), "longe": (56, 18, 20), "perto": (32, 11, 13),
        "detalhe": "estalactites", "terra": (50, 38, 42), "topo": (92, 32, 26), "topo_escuro": (60, 20, 18),
        "pedra": (84, 72, 74), "sol": None,
    },
    "arena": {
        "ceu": ((12, 6, 16), (120, 30, 22)), "longe": (60, 26, 30), "perto": (40, 18, 22),
        "detalhe": "coliseu", "terra": (112, 86, 64), "topo": (140, 112, 78), "topo_escuro": (96, 74, 52),
        "pedra": (130, 114, 96), "sol": (255, 80, 40), "sol_pos": (0.72, 0.42), "sol_raio": 40,
    },
}


def _silhueta_montanhas(largura, altura, base, amplitude, cor, semente):
    """Camada de montanhas que se repete sem emenda (senoides com períodos inteiros)."""
    sorteio = random.Random(semente)
    ondas = [(k, sorteio.uniform(0.3, 1.0), sorteio.uniform(0, math.tau)) for k in (1, 2, 3, 5, 8)]
    soma_pesos = sum(peso for _, peso, _ in ondas)
    superficie = pygame.Surface((largura, altura), pygame.SRCALPHA)
    pontos = [(0, altura)]
    for x in range(0, largura + 1, 8):
        valor = sum(peso * math.sin(math.tau * k * x / largura + fase) for k, peso, fase in ondas) / soma_pesos
        pontos.append((x, base - valor * amplitude))
    pontos.append((largura, altura))
    pygame.draw.polygon(superficie, cor, pontos)
    return superficie


class Cenario:
    """Céu em gradiente + camadas com paralaxe (as distantes andam mais devagar)."""

    LARGURA_CAMADA = 1200

    def __init__(self, tema):
        self.tema = tema
        self.cores = TEMAS[tema]
        self.ceu = gradiente_vertical(C.LARGURA, C.ALTURA, *self.cores["ceu"])
        if self.cores["sol"]:
            fx, fy = self.cores["sol_pos"]
            raio = self.cores["sol_raio"]
            x, y = int(C.LARGURA * fx), int(C.ALTURA * fy)
            desenhar_brilho(self.ceu, x, y, raio * 4, self.cores["sol"], 150)
            pygame.draw.circle(self.ceu, misturar(self.cores["sol"], (255, 255, 255), 0.25), (x, y), raio)
            pygame.draw.circle(self.ceu, misturar(self.cores["sol"], (255, 255, 255), 0.45), (x - 6, y - 6),
                               int(raio * 0.8))
        self.camadas = [
            (0.12, _silhueta_montanhas(self.LARGURA_CAMADA, C.ALTURA, C.ALTURA * 0.55, 90, self.cores["longe"], 7)),
            (0.35, self._camada_detalhe()),
        ]

    def _camada_detalhe(self):
        largura = self.LARGURA_CAMADA
        cor = self.cores["perto"]
        superficie = _silhueta_montanhas(largura, C.ALTURA, C.ALTURA * 0.72, 40, cor, 21)
        detalhe = self.cores["detalhe"]
        if detalhe == "templos":
            return self._camada_acropoles()
        elif detalhe == "estalactites":
            sorteio = random.Random(5)
            for _ in range(26):
                x = sorteio.randint(0, largura)
                comprimento = sorteio.randint(40, 150)
                meia = sorteio.randint(10, 26)
                pygame.draw.polygon(superficie, cor, [(x - meia, 0), (x + meia, 0), (x, comprimento)])
        elif detalhe == "coliseu":
            topo = int(C.ALTURA * 0.42)
            pygame.draw.rect(superficie, cor, (0, topo, largura, C.ALTURA - topo))
            for andar, (y, altura_arco) in enumerate(((topo + 24, 60), (topo + 104, 70))):
                for x in range(20, largura, 60):
                    pygame.draw.ellipse(superficie, (0, 0, 0, 0), (x, y, 34, altura_arco))
                    pygame.draw.rect(superficie, (0, 0, 0, 0), (x, y + altura_arco // 2, 34, altura_arco // 2))
            pygame.draw.rect(superficie, misturar(cor, (0, 0, 0), 0.2), (0, topo, largura, 10))
        return superficie

    def _camada_acropoles(self):
        """Platôs de topo reto com templos apoiados exatamente no topo (nada flutua)."""
        largura = self.LARGURA_CAMADA
        cor = self.cores["perto"]
        luz = misturar(cor, self.cores["sol"], 0.35)
        superficie = pygame.Surface((largura, C.ALTURA), pygame.SRCALPHA)
        chao = int(C.ALTURA * 0.74)
        pygame.draw.rect(superficie, cor, (0, chao, largura, C.ALTURA - chao))
        sorteio = random.Random(11)
        for x0, x1, topo, templo in ((90, 520, int(C.ALTURA * 0.63), "inteiro"),
                                     (760, 1110, int(C.ALTURA * 0.67), "ruina")):
            # encosta rochosa com degraus irregulares, topo plano
            pontos = [(x0, chao)]
            for i in range(1, 5):
                pontos.append((x0 + i * 12 + sorteio.randint(-3, 3), chao - (chao - topo) * i // 5))
            pontos += [(x0 + 60, topo), (x1 - 60, topo)]
            for i in range(4, 0, -1):
                pontos.append((x1 - i * 12 + sorteio.randint(-3, 3), chao - (chao - topo) * i // 5))
            pontos.append((x1, chao))
            pygame.draw.polygon(superficie, cor, pontos)
            pygame.draw.line(superficie, luz, (x0 + 60, topo), (x1 - 60, topo), 2)  # borda iluminada
            centro = (x0 + x1) // 2
            if templo == "inteiro":
                self._templo(superficie, centro, topo, 250, 6, 80, cor, luz, inteiro=True)
            else:
                self._templo(superficie, centro, topo, 200, 5, 70, cor, luz, inteiro=False)
        # ciprestes no vale entre os platôs
        for x in (600, 640, 676, 1170):
            altura = sorteio.randint(46, 70)
            pygame.draw.ellipse(superficie, cor, (x - 9, chao - altura, 18, altura + 6))
        return superficie

    @staticmethod
    def _templo(superficie, centro, base, largura, colunas, altura, cor, luz, inteiro):
        """Templo dórico: 3 degraus, colunas igualmente espaçadas, arquitrave e frontão."""
        esquerda = centro - largura // 2
        for degrau in range(3):  # estilóbato
            recuo = degrau * 8
            pygame.draw.rect(superficie, cor, (esquerda + recuo, base - (degrau + 1) * 6, largura - 2 * recuo, 6))
        piso = base - 18
        largura_util = largura - 40
        alturas = [altura] * colunas if inteiro else [altura, int(altura * 0.55), altura, int(altura * 0.3), altura]
        for i in range(colunas):
            x = esquerda + 20 + i * largura_util // (colunas - 1) - 7
            a = alturas[i % len(alturas)]
            pygame.draw.rect(superficie, cor, (x, piso - a, 14, a))
            pygame.draw.rect(superficie, cor, (x - 3, piso - a - 4, 20, 5))  # capitel
            pygame.draw.line(superficie, luz, (x + 10, piso - a), (x + 10, piso), 1)
        topo = piso - altura - 4
        if inteiro:
            pygame.draw.rect(superficie, cor, (esquerda + 8, topo - 14, largura - 16, 14))
            pygame.draw.polygon(superficie, cor, [(esquerda + 2, topo - 14), (centro, topo - 50),
                                                  (esquerda + largura - 2, topo - 14)])
            pygame.draw.line(superficie, luz, (esquerda + 2, topo - 14), (centro, topo - 50), 2)
        else:  # arquitrave quebrada só sobre as colunas inteiras da esquerda
            pygame.draw.rect(superficie, cor, (esquerda + 8, topo - 12, largura // 2, 12))

    def desenhar(self, tela, camera_x, t):
        tela.blit(self.ceu, (0, 0))
        for fator, camada in self.camadas:
            deslocamento = -int(camera_x * fator) % self.LARGURA_CAMADA
            tela.blit(camada, (deslocamento - self.LARGURA_CAMADA, 0))
            tela.blit(camada, (deslocamento, 0))
        if self.tema == "hades":  # brasas subindo
            for i in range(36):
                x = (i * 97 + t * 18 * (1 + i % 3) - camera_x * 0.5) % C.LARGURA
                y = C.ALTURA - (i * 53 + t * 38 * (1 + i % 2)) % C.ALTURA
                pygame.draw.circle(tela, (255, 120 + (i * 7) % 90, 30), (int(x), int(y)), 1 + i % 2)


# --------------------------------------------------------------------------- tiles


class DesenhistaTiles:
    """Pré-renderiza cada tipo de tile do tema e desenha só o que aparece na tela."""

    def __init__(self, tema):
        self.tema = tema
        self.cores = TEMAS[tema]
        T = C.TILE
        self.cache = {
            ("#", True): self._terra(topo=True),
            ("#", False): self._terra(topo=False),
            ("=", False): self._bloco(),
            ("-", False): self._laje(),
            ("^", False): self._espinhos(),
            ("X", False): self._anfora(),
        }
        self.lava_corpo = pygame.Surface((T, T))
        self.lava_corpo.fill((200, 50, 10))

    def _terra(self, topo):
        T = C.TILE
        cores = self.cores
        superficie = pygame.Surface((T, T))
        superficie.fill(cores["terra"])
        sorteio = random.Random(3 if topo else 4)
        escura = misturar(cores["terra"], (0, 0, 0), 0.25)
        clara = misturar(cores["terra"], (255, 255, 255), 0.12)
        for _ in range(14):
            x, y = sorteio.randint(2, T - 6), sorteio.randint(10 if topo else 2, T - 4)
            pygame.draw.rect(superficie, sorteio.choice((escura, clara)), (x, y, sorteio.randint(3, 7), 3))
        if topo:
            pygame.draw.rect(superficie, cores["topo"], (0, 0, T, 11))
            pygame.draw.rect(superficie, cores["topo_escuro"], (0, 11, T, 3))
            if self.tema == "esparta":
                for x in range(0, T, 6):
                    pygame.draw.line(superficie, cores["topo_escuro"], (x + 2, 9), (x + 3, 4), 2)
            elif self.tema == "hades":
                pygame.draw.lines(superficie, (255, 96, 24), False, [(4, 18), (14, 24), (22, 20), (34, 30)], 2)
            else:
                pygame.draw.line(superficie, (255, 230, 180), (0, 1), (T, 1), 2)
        return superficie

    def _bloco(self):
        T = C.TILE
        pedra = self.cores["pedra"]
        superficie = pygame.Surface((T, T))
        superficie.fill(pedra)
        escura = misturar(pedra, (0, 0, 0), 0.35)
        clara = misturar(pedra, (255, 255, 255), 0.3)
        pygame.draw.line(superficie, clara, (0, 0), (T, 0), 3)
        pygame.draw.line(superficie, clara, (0, 0), (0, T), 3)
        pygame.draw.rect(superficie, escura, (0, 0, T, T), 2)
        pygame.draw.line(superficie, escura, (0, T // 2), (T, T // 2), 2)
        pygame.draw.line(superficie, escura, (T // 2, 0), (T // 2, T // 2), 2)
        pygame.draw.line(superficie, escura, (T // 4, T // 2), (T // 4, T), 2)
        # meandro grego
        pygame.draw.lines(superficie, misturar(pedra, C.DOURADO, 0.5), False,
                          [(8, 36), (8, 30), (16, 30), (16, 40), (24, 40), (24, 32)], 2)
        return superficie

    def _laje(self):
        T = C.TILE
        superficie = pygame.Surface((T, T), pygame.SRCALPHA)
        marmore = misturar(self.cores["pedra"], (255, 255, 255), 0.45)
        pygame.draw.rect(superficie, marmore, (0, 0, T, 12))
        pygame.draw.rect(superficie, misturar(marmore, (0, 0, 0), 0.35), (0, 10, T, 4))
        pygame.draw.line(superficie, (255, 255, 255), (0, 1), (T, 1), 2)
        pygame.draw.polygon(superficie, misturar(marmore, (0, 0, 0), 0.25), [(T // 2 - 6, 14), (T // 2 + 6, 14),
                                                                             (T // 2, 22)])
        return superficie

    def _espinhos(self):
        T = C.TILE
        superficie = pygame.Surface((T, T), pygame.SRCALPHA)
        for i in range(4):
            x = i * 12
            pygame.draw.polygon(superficie, (150, 120, 70), [(x, T), (x + 12, T), (x + 6, T - 26)])
            pygame.draw.line(superficie, (230, 210, 150), (x + 6, T - 26), (x + 3, T), 1)
        pygame.draw.rect(superficie, (90, 70, 50), (0, T - 4, T, 4))
        return superficie

    def _anfora(self):
        T = C.TILE
        superficie = pygame.Surface((T, T), pygame.SRCALPHA)
        barro = (196, 98, 46)
        preto = (34, 22, 18)
        pygame.draw.ellipse(superficie, barro, (8, 12, 32, 32))
        pygame.draw.rect(superficie, barro, (17, 4, 14, 12))
        pygame.draw.rect(superficie, barro, (13, 2, 22, 5))
        pygame.draw.rect(superficie, barro, (16, 40, 16, 7))
        pygame.draw.arc(superficie, barro, (6, 6, 14, 18), math.pi * 0.5, math.pi * 1.4, 3)
        pygame.draw.arc(superficie, barro, (28, 6, 14, 18), -math.pi * 0.4, math.pi * 0.5, 3)
        pygame.draw.rect(superficie, preto, (9, 24, 30, 6))
        for x in range(12, 38, 6):
            pygame.draw.rect(superficie, barro, (x, 26, 3, 2))
        pygame.draw.ellipse(superficie, (236, 150, 96), (14, 16, 6, 10))
        return superficie

    def desenhar(self, tela, nivel, cam_x, cam_y, t):
        T = C.TILE
        c0 = max(0, cam_x // T)
        c1 = min(nivel.largura - 1, (cam_x + C.LARGURA) // T + 1)
        l0 = max(0, cam_y // T)
        l1 = min(nivel.altura - 1, (cam_y + C.ALTURA) // T + 1)
        for linha in range(l0, l1 + 1):
            for coluna in range(c0, c1 + 1):
                tile = nivel.grade[linha][coluna]
                if tile == " ":
                    continue
                x, y = coluna * T - cam_x, linha * T - cam_y
                if tile == "~":
                    self._desenhar_lava(tela, x, y, nivel.tile(coluna, linha - 1) != "~", t, coluna)
                elif tile == "#":
                    tela.blit(self.cache[("#", nivel.tile(coluna, linha - 1) != "#")], (x, y))
                    if linha == nivel.altura - 1:  # preenche a faixa abaixo do mapa
                        tela.blit(self.cache[("#", False)], (x, y + T))
                else:
                    tela.blit(self.cache[(tile, False)], (x, y))

    def _desenhar_lava(self, tela, x, y, superficie_lava, t, coluna):
        T = C.TILE
        if not superficie_lava:
            tela.blit(self.lava_corpo, (x, y))
            tela.blit(self.lava_corpo, (x, y + T))
            return
        pygame.draw.rect(tela, (200, 50, 10), (x, y + 12, T, T - 12))
        pontos = [(x, y + T)]
        for i in range(0, T + 1, 6):
            onda = math.sin(t * 3 + (coluna * T + i) * 0.08) * 3
            pontos.append((x + i, y + 12 + onda))
        pontos.append((x + T, y + T))
        pygame.draw.polygon(tela, (255, 110, 20), pontos)
        pygame.draw.lines(tela, (255, 220, 90), False, pontos[1:-1], 2)
        if (coluna + int(t * 2)) % 5 == 0:
            pygame.draw.circle(tela, (255, 200, 80), (x + 24, y + 18 - int((t * 30) % 10)), 2)


# --------------------------------------------------------------------------- herói


def _lamina(tela, P, s, base, ponta, brilhando):
    """Lâmina curva incandescente entre dois pontos locais."""
    bx, by = base
    px, py = ponta
    dx, dy = px - bx, py - by
    comprimento = math.hypot(dx, dy) or 1
    nx, ny = -dy / comprimento, dx / comprimento
    pontos = [P(bx + nx * 3, by + ny * 3), P(bx + dx * 0.6 + nx * 5, by + dy * 0.6 + ny * 5),
              P(px, py), P(bx - nx * 2, by - ny * 2)]
    if brilhando:
        x, y = P(px, py)
        desenhar_brilho(tela, x, y, int(16 * s), (255, 120, 30), 120)
    pygame.draw.polygon(tela, (232, 92, 22), pontos)
    pygame.draw.polygon(tela, (255, 206, 96), pontos, max(1, int(s)))


def _corrente(tela, P, s, inicio, fim):
    ix, iy = inicio
    fx, fy = fim
    distancia = math.hypot(fx - ix, fy - iy)
    elos = max(2, int(distancia / 6))
    for i in range(elos + 1):
        t = i / elos
        x, y = P(ix + (fx - ix) * t, iy + (fy - iy) * t)
        pygame.draw.circle(tela, (70, 70, 76), (int(x), int(y)), max(1, int(2 * s)))
        pygame.draw.circle(tela, (150, 150, 158), (int(x), int(y)), max(1, int(1 * s)))


def _angulo_golpe(combo, progresso):
    suave = 1 - (1 - progresso) ** 2
    if combo == 0:
        return -1.9 + 2.8 * suave
    if combo == 1:
        return 1.0 - 2.7 * suave
    return -math.pi / 2 + math.tau * progresso


def desenhar_espartano(tela, cx, topo, direcao, anim_t=0.0, correndo=False, no_ar=False, vy=0.0,
                       progresso_ataque=0.0, atacando=False, combo=0, em_furia=False, escala=1.0):
    """Guerreiro espartano: careca, pele cinzenta, tatuagem vermelha e lâminas acorrentadas."""
    s = escala
    d = direcao

    def P(dx, dy):
        return (cx + dx * d * s, topo + dy * s)

    def L(largura):
        return max(1, int(largura * s))

    pele = C.PELE_ESPARTANO
    pele_sombra = misturar(pele, (0, 0, 0), 0.25)
    tatuagem = (178, 18, 18)
    bronze = (186, 140, 60)

    if em_furia:
        x, y = P(0, 30)
        pulso = 46 + int(math.sin(anim_t * 12) * 6)
        desenhar_brilho(tela, x, y, int(pulso * s), (255, 40, 20), 120)

    # ângulos de pernas e braços
    if no_ar:
        perna_a, perna_b = (0.55, -0.35) if vy < 0 else (0.25, -0.15)
        balanco = -0.9
    elif correndo:
        perna_a = math.sin(anim_t * 14) * 0.7
        perna_b = -perna_a
        balanco = math.sin(anim_t * 14) * 0.6
    else:
        perna_a, perna_b = 0.12, -0.12
        balanco = math.sin(anim_t * 3) * 0.08

    def perna(angulo, cor_pele):
        quadril = (0, 40)
        joelho = (quadril[0] + math.sin(angulo) * 11, quadril[1] + math.cos(angulo) * 11)
        pe = (joelho[0] + math.sin(angulo * 0.6) * 11, joelho[1] + math.cos(angulo * 0.6) * 11)
        pygame.draw.line(tela, cor_pele, P(*quadril), P(*joelho), L(7))
        pygame.draw.line(tela, bronze, P(*joelho), P(*pe), L(6))
        pygame.draw.line(tela, (60, 40, 26), P(pe[0] - 2, pe[1]), P(pe[0] + 5, pe[1]), L(4))

    ombro_frente = (5, 17)
    ombro_tras = (-6, 17)

    def braco_parado(ombro, angulo, cor_pele):
        cotovelo = (ombro[0] + math.sin(angulo) * 8, ombro[1] + math.cos(angulo) * 8)
        mao = (cotovelo[0] + math.sin(angulo + 0.4) * 8, cotovelo[1] + math.cos(angulo + 0.4) * 8)
        pygame.draw.line(tela, cor_pele, P(*ombro), P(*cotovelo), L(6))
        pygame.draw.line(tela, bronze, P(*cotovelo), P(*mao), L(6))
        return mao

    def lamina_na_mao(mao, angulo):
        direcao_lamina = (math.sin(angulo + 0.9), math.cos(angulo + 0.9))
        ponta = (mao[0] + direcao_lamina[0] * 20, mao[1] + direcao_lamina[1] * 20)
        _lamina(tela, P, s, mao, ponta, em_furia)

    # ---- braço e lâmina de trás
    if atacando and combo == 2:
        angulo_tras = _angulo_golpe(combo, progresso_ataque) + math.pi
        alcance = 18 + (C.ATAQUE_ALCANCE - 18) * math.sin(math.pi * progresso_ataque) ** 0.6
        mao = (ombro_tras[0] + math.cos(angulo_tras) * 13, ombro_tras[1] + math.sin(angulo_tras) * 13)
        pygame.draw.line(tela, pele_sombra, P(*ombro_tras), P(*mao), L(6))
        ponta = (ombro_tras[0] + math.cos(angulo_tras) * alcance, ombro_tras[1] + math.sin(angulo_tras) * alcance)
        base = (ponta[0] - math.cos(angulo_tras) * 18, ponta[1] - math.sin(angulo_tras) * 18)
        _corrente(tela, P, s, mao, base)
        _lamina(tela, P, s, base, ponta, True)
    else:
        mao = braco_parado(ombro_tras, -balanco, pele_sombra)
        lamina_na_mao(mao, -balanco)

    perna(perna_b, pele_sombra)
    perna(perna_a, pele)

    # saiote de couro e cinto
    pygame.draw.polygon(tela, (128, 30, 24), [P(-11, 33), P(11, 33), P(14, 46), P(-14, 46)])
    for faixa in (-8, -2, 4, 10):
        pygame.draw.line(tela, (82, 16, 14), P(faixa, 35), P(faixa * 1.25, 46), L(2))
    # tronco
    pygame.draw.polygon(tela, pele, [P(-10, 14), P(10, 14), P(11, 33), P(-11, 33)])
    pygame.draw.line(tela, pele_sombra, P(0, 18), P(0, 30), L(1))
    pygame.draw.polygon(tela, C.DOURADO, [P(-12, 31), P(12, 31), P(12, 35), P(-12, 35)])
    # tatuagem vermelha descendo pelo lado do corpo
    pygame.draw.lines(tela, tatuagem, False, [P(-5, 15), P(-8, 23), P(-4, 32)], L(4))
    # ombreira de bronze
    x, y = P(-8, 16)
    pygame.draw.circle(tela, bronze, (int(x), int(y)), L(6))
    pygame.draw.circle(tela, (120, 86, 34), (int(x), int(y)), L(6), L(1))

    # cabeça careca, barba e olho
    x, y = P(1, 7)
    pygame.draw.circle(tela, pele, (int(x), int(y)), L(8))
    pygame.draw.line(tela, tatuagem, P(-3, -1), P(-2, 12), L(3))
    pygame.draw.polygon(tela, (34, 28, 28), [P(-3, 9), P(8, 9), P(6, 17), P(0, 17)])
    olho = (255, 70, 40) if em_furia else (40, 30, 30)
    pygame.draw.line(tela, olho, P(4, 5), P(7, 5), L(2))
    pygame.draw.line(tela, (60, 40, 40), P(3, 3), P(8, 4), L(2))

    # ---- braço da frente e lâmina principal
    if atacando:
        angulo = _angulo_golpe(combo, progresso_ataque)
        alcance = 18 + (C.ATAQUE_ALCANCE - 18) * math.sin(math.pi * progresso_ataque) ** 0.6
        # rastro de fogo do golpe
        for k in range(1, 5):
            anterior = progresso_ataque - k * 0.06
            if anterior <= 0:
                break
            ang_k = _angulo_golpe(combo, anterior)
            alc_k = 18 + (C.ATAQUE_ALCANCE - 18) * math.sin(math.pi * anterior) ** 0.6
            x, y = P(ombro_frente[0] + math.cos(ang_k) * alc_k, ombro_frente[1] + math.sin(ang_k) * alc_k)
            pygame.draw.circle(tela, misturar((255, 200, 80), (160, 30, 10), k / 5), (int(x), int(y)), L(7 - k))
        mao = (ombro_frente[0] + math.cos(angulo) * 14, ombro_frente[1] + math.sin(angulo) * 14)
        pygame.draw.line(tela, pele, P(*ombro_frente), P(*mao), L(6))
        ponta = (ombro_frente[0] + math.cos(angulo) * alcance, ombro_frente[1] + math.sin(angulo) * alcance)
        base = (ponta[0] - math.cos(angulo) * 18, ponta[1] - math.sin(angulo) * 18)
        _corrente(tela, P, s, mao, base)
        _lamina(tela, P, s, base, ponta, True)
    else:
        mao = braco_parado(ombro_frente, balanco, pele)
        lamina_na_mao(mao, balanco)


CONTORNO = (10, 4, 6)
_camadas = {}


def _camada(largura, altura, chave):
    """Superfície transparente reaproveitada entre quadros (evita alocar toda vez)."""
    s = _camadas.get((largura, altura, chave))
    if s is None:
        s = _camadas[(largura, altura, chave)] = pygame.Surface((largura, altura), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    return s


def _desenhar_com_contorno(tela, retangulo, cam_x, cam_y, pintar, margem, escala=None, rastro=()):
    """Desenha um personagem numa camada própria e acrescenta um contorno escuro.

    O contorno separa o personagem do cenário escuro. `pintar(camada, ox, oy)` desenha
    usando (ox, oy) como deslocamento de câmera. `escala` (sx, sy) achata ou estica a
    partir dos pés; `rastro` é uma lista de (dx, alfa) com cópias translúcidas.
    """
    largura, altura = retangulo.w + 2 * margem, retangulo.h + 2 * margem
    ox, oy = retangulo.x - margem, retangulo.y - margem
    x, y = ox - cam_x, oy - cam_y
    if x > C.LARGURA or y > C.ALTURA or x + largura < 0 or y + altura < 0:
        return  # fora da tela
    camada = _camada(largura, altura, "pintura")
    pintar(camada, ox, oy)
    borda = pygame.mask.from_surface(camada).to_surface(setcolor=(*CONTORNO, 255), unsetcolor=(0, 0, 0, 0))
    final = _camada(largura, altura, "final")
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        final.blit(borda, (dx, dy))
    final.blit(camada, (0, 0))
    if escala:
        sx, sy = escala
        novo = (int(largura * sx), int(altura * sy))
        pes_x, pes_y = margem + retangulo.w / 2, margem + retangulo.h
        final = pygame.transform.smoothscale(final, novo)
        x += pes_x - pes_x * sx
        y += pes_y - pes_y * sy
    for dx, alfa in rastro:
        copia = final.copy()
        copia.set_alpha(alfa)
        tela.blit(copia, (int(x + dx), int(y)))
    tela.blit(final, (int(x), int(y)))


def desenhar_heroi(tela, heroi, cam_x, cam_y):
    if heroi.morto:
        return
    if heroi.invencivel > 0 and not heroi.esquivando and int(heroi.invencivel * 16) % 2 == 0:
        return  # pisca enquanto está invencível

    def pintar(camada, ox, oy):
        desenhar_espartano(camada, heroi.centro_x - ox, heroi.y - oy, heroi.direcao, heroi.anim_t,
                           correndo=abs(heroi.vx) > 30 and heroi.no_chao, no_ar=not heroi.no_chao, vy=heroi.vy,
                           progresso_ataque=heroi.progresso_ataque, atacando=heroi.atacando, combo=heroi.combo,
                           em_furia=heroi.em_furia)

    escala = None
    if heroi.pouso_t > 0:  # achata ao aterrissar
        k = heroi.pouso_t / 0.14 * 0.16
        escala = (1 + k, 1 - k)
    elif not heroi.no_chao and heroi.vy < -350:  # estica subindo
        escala = (0.94, 1.06)
    rastro = ((-heroi.direcao * 20, 110), (-heroi.direcao * 40, 50)) if heroi.esquivando else ()
    _desenhar_com_contorno(tela, heroi.rect, cam_x, cam_y, pintar, 110, escala, rastro)


# --------------------------------------------------------------------------- inimigos

OSSO = (226, 220, 198)
OSSO_SOMBRA = (160, 152, 130)


def desenhar_esqueleto(tela, ini, cam_x, cam_y, arqueiro=False):
    d = ini.direcao
    cx = ini.centro_x - cam_x
    topo = ini.y - cam_y
    branco = ini.piscar > 0
    osso = (255, 255, 255) if branco else OSSO
    sombra = (255, 255, 255) if branco else OSSO_SOMBRA

    def P(dx, dy):
        return (cx + dx * d, topo + dy)

    passo = math.sin(ini.anim_t * 10) * 0.5 if abs(ini.vx) > 5 else 0.0
    for angulo, cor in ((-passo, sombra), (passo, osso)):
        joelho = (math.sin(angulo) * 9, 32 + math.cos(angulo) * 9)
        pe = (joelho[0] + math.sin(angulo * 0.5) * 9, joelho[1] + math.cos(angulo * 0.5) * 9)
        pygame.draw.line(tela, cor, P(0, 32), P(*joelho), 3)
        pygame.draw.line(tela, cor, P(*joelho), P(*pe), 3)
    px, py = P(0, 31)
    pygame.draw.ellipse(tela, osso, (int(px) - 6, int(py) - 3, 12, 6))
    pygame.draw.line(tela, osso, P(0, 14), P(0, 31), 3)
    for y in (17, 21, 25):
        pygame.draw.line(tela, osso, P(-7, y), P(7, y), 2)

    if arqueiro:
        pygame.draw.polygon(tela, (52, 60, 44), [P(-9, 2), P(6, -2), P(9, 12), P(-10, 30)])  # capuz
        estendido = ini.arremesso > 0
        mao = (13, 18) if estendido else (8, 22)
        pygame.draw.line(tela, osso, P(3, 15), P(*mao), 2)
        arco_x, _ = P(mao[0] + 2, 0)
        retangulo = pygame.Rect(0, 0, 12, 30)
        retangulo.center = (int(arco_x), int(topo + mao[1]))
        if d > 0:
            pygame.draw.arc(tela, (120, 80, 40), retangulo, -math.pi / 2, math.pi / 2, 3)
        else:
            pygame.draw.arc(tela, (120, 80, 40), retangulo, math.pi / 2, math.pi * 1.5, 3)
        pygame.draw.line(tela, (220, 220, 220), (retangulo.centerx, retangulo.top), (retangulo.centerx, retangulo.bottom), 1)
    else:
        # espada (braço de trás) e escudo redondo (frente)
        pygame.draw.line(tela, sombra, P(-3, 16), P(-9, 24), 2)
        pygame.draw.line(tela, (190, 190, 200), P(-9, 24), P(-14, 6), 3)
        x, y = P(8, 22)
        pygame.draw.circle(tela, (176, 128, 52), (int(x), int(y)), 9)
        pygame.draw.circle(tela, (120, 80, 30), (int(x), int(y)), 9, 2)
        pygame.draw.circle(tela, (230, 190, 100), (int(x), int(y)), 3)

    x, y = P(1, 8)
    pygame.draw.circle(tela, osso, (int(x), int(y)), 7)
    jx, jy = P(2, 13)
    pygame.draw.rect(tela, osso, (int(jx) - 4, int(jy) - 2, 8, 4))
    for ox in (1, 5):
        ex, ey = P(ox, 7)
        pygame.draw.circle(tela, (20, 10, 10), (int(ex), int(ey)), 2)
        pygame.draw.circle(tela, (255, 60, 40), (int(ex), int(ey)), 1)
    if not arqueiro:  # elmo de legionário com crista
        pygame.draw.arc(tela, (176, 128, 52), (int(x) - 8, int(y) - 9, 16, 16), 0, math.pi, 4)
        pygame.draw.ellipse(tela, (190, 30, 30), (int(x) - 8, int(y) - 14, 16, 7))


def desenhar_harpia(tela, ini, cam_x, cam_y):
    d = ini.direcao
    cx = ini.centro_x - cam_x
    topo = ini.y - cam_y
    branco = ini.piscar > 0
    pena = (255, 255, 255) if branco else (98, 66, 120)
    pena_clara = (255, 255, 255) if branco else (150, 112, 168)
    pele = (255, 255, 255) if branco else (176, 196, 156)

    def P(dx, dy):
        return (cx + dx * d, topo + dy)

    bater = math.sin(ini.anim_t * (18 if ini.estado == "mergulho" else 12))
    pygame.draw.polygon(tela, pena, [P(-2, 12), P(-26, 6 - bater * 16), P(-20, 22 - bater * 6)])
    pygame.draw.ellipse(tela, pena, pygame.Rect(0, 0, 18, 22).move(int(cx - 9), int(topo + 8)))
    pygame.draw.line(tela, (230, 190, 60), P(-2, 28), P(-5, 34), 2)
    pygame.draw.line(tela, (230, 190, 60), P(3, 28), P(5, 34), 2)
    pygame.draw.polygon(tela, (40, 20, 40), [P(0, 2), P(-14, 4 + bater * 2), P(-4, 12)])  # cabelo
    x, y = P(3, 6)
    pygame.draw.circle(tela, pele, (int(x), int(y)), 6)
    ex, ey = P(6, 5)
    pygame.draw.circle(tela, (255, 40, 40), (int(ex), int(ey)), 2)
    pygame.draw.polygon(tela, pena_clara, [P(2, 12), P(24, 4 - bater * 18), P(16, 22 - bater * 6)])


def desenhar_ciclope(tela, ini, heroi, cam_x, cam_y, t):
    d = ini.direcao
    cx = ini.centro_x - cam_x
    topo = ini.y - cam_y
    branco = ini.piscar > 0
    pele = (125, 146, 106) if not ini.furioso else (166, 116, 92)
    if branco:
        pele = (255, 255, 255)
    sombra = misturar(pele, (0, 0, 0), 0.3)
    tremor = math.sin(t * 60) * 2 if ini.estado == "preparando" else 0
    cx += tremor
    agachado = ini.estado == "preparando" and ini.proximo_ataque == "salto"
    if agachado:  # vai saltar: abaixa o corpo (a investida ergue a clava)
        topo += 12

    def P(dx, dy):
        return (cx + dx * d, topo + dy)

    passo = math.sin(ini.anim_t * (14 if ini.estado == "investida" else 6)) * 6 if abs(ini.vx) > 5 else 0
    perna = 24 if agachado else 36  # agachado: pernas dobradas, pés continuam no chão
    pygame.draw.rect(tela, sombra, _ret(P(-26, 84 + passo * 0.3), 18, perna, d))
    pygame.draw.rect(tela, pele, _ret(P(8, 84 - passo * 0.3), 18, perna, d))
    pygame.draw.ellipse(tela, pele, pygame.Rect(0, 0, 84, 74).move(int(cx - 42), int(topo + 26)))
    pygame.draw.ellipse(tela, sombra, pygame.Rect(0, 0, 50, 34).move(int(cx - 25), int(topo + 56)), 3)
    pygame.draw.polygon(tela, (100, 62, 34), [P(-34, 76), P(34, 76), P(26, 98), P(-26, 98)])
    pygame.draw.line(tela, (60, 36, 20), P(-34, 78), P(34, 78), 4)

    # braço com a clava
    if ini.estado == "preparando":
        angulo = 1.3 if agachado else -2.4
    elif ini.estado in ("investida", "salto"):
        angulo = -0.3
    else:
        angulo = 0.6 + math.sin(ini.anim_t * 3) * 0.15
    ombro = (24, 40)
    mao = (ombro[0] + math.cos(angulo) * 26, ombro[1] + math.sin(angulo) * 26)
    pygame.draw.line(tela, pele, P(*ombro), P(*mao), 13)
    ponta = (mao[0] + math.cos(angulo - 0.5) * 46, mao[1] + math.sin(angulo - 0.5) * 46)
    pygame.draw.line(tela, (110, 70, 36), P(*mao), P(*ponta), 12)
    x, y = P(*ponta)
    pygame.draw.circle(tela, (90, 56, 28), (int(x), int(y)), 11)
    for k in range(5):
        a = k * math.tau / 5 + t
        pygame.draw.circle(tela, (210, 200, 180), (int(x + math.cos(a) * 11), int(y + math.sin(a) * 11)), 3)

    # cabeça e olho único que segue o herói
    hx, hy = P(6, 24)
    pygame.draw.circle(tela, pele, (int(hx), int(hy)), 24)
    pygame.draw.polygon(tela, (230, 220, 190), [P(0, 2), P(8, -14), P(12, 4)])
    ox, oy = P(12, 18)
    pygame.draw.circle(tela, (250, 246, 230), (int(ox), int(oy)), 10)
    alvo_x = heroi.centro_x - cam_x - ox
    alvo_y = heroi.centro_y - cam_y - oy
    distancia = math.hypot(alvo_x, alvo_y) or 1
    iris = (int(ox + alvo_x / distancia * 4), int(oy + alvo_y / distancia * 4))
    pygame.draw.circle(tela, (200, 30, 30), iris, 5)
    pygame.draw.circle(tela, (10, 10, 10), iris, 2)
    pygame.draw.line(tela, (40, 30, 26), P(0, 6), P(24, 11), 5)
    pygame.draw.line(tela, (40, 20, 20), P(4, 36), P(22, 34), 3)
    for dente in (8, 14, 20):
        pygame.draw.polygon(tela, (240, 240, 220), [P(dente, 35), P(dente + 3, 35), P(dente + 1.5, 40)])

    if ini.estado == "atordoado":
        for k in range(3):
            a = t * 5 + k * math.tau / 3
            sx, sy = hx + math.cos(a) * 26, hy - 30 + math.sin(a) * 6
            pygame.draw.circle(tela, C.AMARELO, (int(sx), int(sy)), 4)


def _ret(ponto, largura, altura, direcao):
    """Retângulo local ancorado no canto "de trás" (espelha quando direcao < 0)."""
    x, y = ponto
    return (int(x if direcao > 0 else x - largura), int(y), largura, altura)


def desenhar_inimigo(tela, ini, heroi, cam_x, cam_y, t):
    nome = type(ini).__name__

    def pintar(camada, ox, oy):
        if nome == "Esqueleto":
            desenhar_esqueleto(camada, ini, ox, oy)
        elif nome == "Arqueiro":
            desenhar_esqueleto(camada, ini, ox, oy, arqueiro=True)
        elif nome == "Harpia":
            desenhar_harpia(camada, ini, ox, oy)
        elif nome == "Ciclope":
            desenhar_ciclope(camada, ini, heroi, ox, oy, t)

    _desenhar_com_contorno(tela, ini.rect, cam_x, cam_y, pintar, 90 if nome == "Ciclope" else 60)


# --------------------------------------------------------------------------- objetos


def desenhar_orbe(tela, orbe, cam_x, cam_y):
    x = orbe.x - cam_x
    y = orbe.y - cam_y + orbe.flutuacao
    cor = (230, 36, 30) if orbe.tipo == "vermelho" else (60, 220, 90)
    desenhar_brilho(tela, x, y, orbe.raio * 3, cor, 90)
    pygame.draw.circle(tela, misturar(cor, (0, 0, 0), 0.3), (int(x), int(y)), orbe.raio)
    pygame.draw.circle(tela, cor, (int(x), int(y)), orbe.raio - 2)
    pygame.draw.circle(tela, (255, 255, 255), (int(x - orbe.raio * 0.35), int(y - orbe.raio * 0.35)), 2)


def desenhar_altar(tela, altar, cam_x, cam_y, t):
    x = altar.x - cam_x
    y = altar.y - cam_y
    pedra = (196, 186, 166)
    pygame.draw.rect(tela, misturar(pedra, (0, 0, 0), 0.3), (x - 4, y + altar.h - 8, altar.w + 8, 8))
    pygame.draw.rect(tela, pedra, (x + 4, y + 8, altar.w - 8, altar.h - 14))
    pygame.draw.rect(tela, pedra, (x - 2, y, altar.w + 4, 9))
    pygame.draw.line(tela, C.DOURADO, (x + 4, y + 14), (x + altar.w - 4, y + 14), 2)
    cx = x + altar.w / 2
    if altar.ativo:
        desenhar_brilho(tela, cx, y - 8, 40, (255, 140, 30), 110)
        for k, (cor, escala) in enumerate((((255, 90, 20), 1.0), ((255, 180, 40), 0.7), ((255, 240, 160), 0.4))):
            balanco = math.sin(t * 14 + k) * 3
            altura = (26 + math.sin(t * 20 + k * 2) * 4) * escala
            largura = 11 * escala
            pygame.draw.polygon(tela, cor, [(cx - largura, y), (cx + largura, y), (cx + balanco, y - altura)])
    else:
        pygame.draw.line(tela, (90, 90, 90), (cx - 6, y - 2), (cx + 6, y - 2), 3)


def desenhar_portal(tela, portal, cam_x, cam_y, t):
    x = portal.x - cam_x
    y = portal.y - cam_y
    marmore = (228, 222, 210)
    interior = pygame.Rect(x + 16, y + 18, portal.w - 32, portal.h - 18)
    if portal.travado:
        pygame.draw.rect(tela, (40, 10, 14), interior)
        pygame.draw.line(tela, (110, 110, 118), interior.topleft, interior.bottomright, 4)
        pygame.draw.line(tela, (110, 110, 118), interior.topright, interior.bottomleft, 4)
    else:
        desenhar_brilho(tela, interior.centerx, interior.centery, 70, (120, 170, 255), 110)
        pygame.draw.ellipse(tela, (40, 70, 160), interior)
        for k in range(6):
            a = t * 2.5 + k * math.tau / 6
            raio_x, raio_y = interior.w / 2 - 4, interior.h / 2 - 6
            pygame.draw.line(tela, (200, 220, 255), interior.center,
                             (interior.centerx + math.cos(a) * raio_x, interior.centery + math.sin(a) * raio_y), 2)
        pygame.draw.ellipse(tela, (255, 230, 150), interior, 3)
    for coluna_x in (x, x + portal.w - 16):
        pygame.draw.rect(tela, marmore, (coluna_x, y + 14, 16, portal.h - 14))
        for k in (4, 8, 12):
            pygame.draw.line(tela, (180, 172, 158), (coluna_x + k, y + 18), (coluna_x + k, y + portal.h - 6), 1)
    pygame.draw.rect(tela, marmore, (x - 6, y, portal.w + 12, 16))
    pygame.draw.line(tela, C.DOURADO, (x - 6, y + 8), (x + portal.w + 6, y + 8), 2)


def desenhar_plataforma(tela, plataforma, cam_x, cam_y):
    x = plataforma.x - cam_x
    y = plataforma.y - cam_y
    for corrente_x in (x + 10, x + plataforma.w - 10):
        for elo_y in range(int(y) - 6, -6, -12):
            pygame.draw.ellipse(tela, (90, 90, 96), (corrente_x - 3, elo_y - 5, 6, 10), 2)
    pygame.draw.rect(tela, (150, 136, 120), (x, y, plataforma.w, plataforma.h))
    pygame.draw.rect(tela, C.DOURADO, (x, y, plataforma.w, 4))
    pygame.draw.rect(tela, (80, 70, 60), (x, y, plataforma.w, plataforma.h), 2)


def desenhar_projetil(tela, projetil, cam_x, cam_y):
    x = projetil.x - cam_x
    y = projetil.y - cam_y
    if projetil.tipo == "lanca":
        frente = 1 if projetil.vx > 0 else -1
        ponta_x = x + projetil.w if frente > 0 else x
        cauda_x = x if frente > 0 else x + projetil.w
        meio_y = y + projetil.h / 2
        pygame.draw.line(tela, (120, 80, 44), (cauda_x, meio_y), (ponta_x - frente * 6, meio_y), 3)
        pygame.draw.polygon(tela, (200, 200, 210), [(ponta_x, meio_y), (ponta_x - frente * 9, meio_y - 4),
                                                    (ponta_x - frente * 9, meio_y + 4)])
    else:
        desenhar_brilho(tela, x + projetil.w / 2, y + projetil.h, 30, (255, 150, 40), 120)
        pygame.draw.ellipse(tela, (255, 190, 80), (x, y, projetil.w, projetil.h * 2), 4)


def desenhar_particulas(tela, particulas, cam_x, cam_y):
    for p in particulas:
        tamanho = max(1, int(p.tamanho * (p.vida / p.vida_max) + 0.5))
        pygame.draw.rect(tela, p.cor, (int(p.x - cam_x), int(p.y - cam_y), tamanho, tamanho))


def desenhar_textos(tela, textos, cam_x, cam_y):
    for texto in textos:
        texto_sombreado(tela, texto.texto, 18, texto.cor, centro=(texto.x - cam_x, texto.y - cam_y))


# --------------------------------------------------------------------------- moldura da tela

_vinheta = []


def desenhar_vinheta(tela):
    """Escurece as bordas da tela e leva o olhar para o centro."""
    if not _vinheta:
        superficie = pygame.Surface((C.LARGURA, C.ALTURA), pygame.SRCALPHA)
        for i in range(60):
            alfa = int(150 * (1 - i / 60) ** 2.2)
            pygame.draw.rect(superficie, (0, 0, 0, alfa), (i * 3, i * 2, C.LARGURA - i * 6, C.ALTURA - i * 4), 4)
        _vinheta.append(superficie)
    tela.blit(_vinheta[0], (0, 0))


class CenarioMenu:
    """Fundo do menu: lua de sangue, montanhas, ruínas e brasas subindo."""

    def __init__(self):
        L, A = C.LARGURA, C.ALTURA
        self.ceu = pygame.Surface((L, A))
        self.ceu.blit(gradiente_vertical(L, A // 2, (6, 4, 8), (26, 8, 12)), (0, 0))
        self.ceu.blit(gradiente_vertical(L, A - A // 2, (26, 8, 12), (92, 16, 14)), (0, A // 2))
        desenhar_brilho(self.ceu, 690, 190, 230, (200, 30, 20), 120)
        pygame.draw.circle(self.ceu, (150, 34, 26), (690, 190), 74)
        pygame.draw.circle(self.ceu, (176, 48, 34), (676, 178), 66)
        self.montes = [
            _silhueta_montanhas(1200, A, A * 0.62, 70, (34, 12, 16), 7),
            _silhueta_montanhas(1200, A, A * 0.78, 40, (16, 6, 9), 21),
        ]
        ruinas = self.montes[1]
        chao = int(A * 0.78)
        for x0, alturas in ((560, (140, 96, 150, 60)), (900, (120, 150, 80))):
            for i, altura in enumerate(alturas):
                x = x0 + i * 46
                pygame.draw.rect(ruinas, (16, 6, 9), (x, chao - altura, 20, altura + 30))
                pygame.draw.rect(ruinas, (16, 6, 9), (x - 6, chao - altura - 8, 32, 10))
        sorteio = random.Random(4)
        self.brasas = [(sorteio.uniform(0, L), sorteio.uniform(0, A), sorteio.uniform(20, 60),
                        sorteio.choice((1, 1, 2))) for _ in range(70)]
        self.nevoa = pygame.Surface((L, 140), pygame.SRCALPHA)
        for y in range(140):
            pygame.draw.line(self.nevoa, (40, 6, 8, int(170 * y / 139)), (0, y), (L, y))

    def desenhar(self, tela, t):
        tela.blit(self.ceu, (0, 0))
        for i, camada in enumerate(self.montes):
            deslocamento = -int(t * (6 + i * 10)) % 1200
            tela.blit(camada, (deslocamento - 1200, 0))
            tela.blit(camada, (deslocamento, 0))
        for x, y, velocidade, raio in self.brasas:
            yy = (y - t * velocidade) % C.ALTURA
            xx = x + math.sin(t + y) * 10
            pygame.draw.circle(tela, (255, 140 + int(y) % 80, 40), (int(xx), int(yy)), raio)
        tela.blit(self.nevoa, (0, C.ALTURA - 140))
