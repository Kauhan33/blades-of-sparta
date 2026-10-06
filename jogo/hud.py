"""Interface no estilo "épico sombrio": HUD, menu, controles e telas de estado.

Elementos de base: texto metálico (gradiente dourado com contorno), placas com
cantos chanfrados, barras com gradiente e teclas desenhadas. Títulos e números
usam a fonte Cinzel (assets/fontes); se ela faltar, a do sistema assume.
"""
import math

import pygame

from . import config as C
from .desenho import desenhar_brilho, desenhar_espartano, misturar
from .recursos import fonte, fonte_titulo

OPCOES_MENU = ("JOGAR", "CONTROLES", "SAIR")
CONTROLES = (
    (("A", "D"), "andar  (ou as setas)"),
    (("ESPAÇO", "W"), "pular  ·  aperte de novo no ar: pulo duplo"),
    (("S",), "descer da plataforma"),
    (("J", "X"), "golpe das lâminas  (combo de 3)"),
    (("L", "SHIFT"), "esquiva  (invencível por um instante)"),
    (("K", "C"), "Fúria Espartana  (medidor cheio)"),
    (("P", "ESC"), "pausar"),
)
ROMANOS = ("I", "II", "III", "IV", "V")

# --------------------------------------------------------------------------- primitivas

_gradientes = {}
_textos = {}


def _gradiente(largura, altura, cores):
    """Gradiente vertical com várias paradas (cacheado)."""
    chave = (largura, altura, cores)
    if chave not in _gradientes:
        superficie = pygame.Surface((largura, altura), pygame.SRCALPHA)
        n = len(cores) - 1
        for y in range(altura):
            t = y / max(1, altura - 1) * n
            i = min(int(t), n - 1)
            pygame.draw.line(superficie, misturar(cores[i], cores[i + 1], t - i), (0, y), (largura, y))
        _gradientes[chave] = superficie
    return _gradientes[chave]


def _posicionar(retangulo, centro=None, esquerda=None, direita=None):
    if centro is not None:
        retangulo.center = centro
    elif direita is not None:
        retangulo.topright = direita
    else:
        retangulo.topleft = esquerda
    return retangulo


def texto_metal(tela, texto, tamanho, centro=None, esquerda=None, direita=None, cores=C.METAL_OURO,
                brilho=None):
    """Texto com gradiente metálico, contorno escuro e sombra (renderização cacheada)."""
    chave = (texto, tamanho, cores)
    imagem = _textos.get(chave)
    if imagem is None:
        if len(_textos) > 300:
            _textos.clear()
        f = fonte_titulo(tamanho)
        mascara = f.render(texto, True, (255, 255, 255))
        borda = f.render(texto, True, (20, 8, 6))
        e = max(1, tamanho // 22)
        w, h = mascara.get_size()
        imagem = pygame.Surface((w + 2 * e + 3, h + 2 * e + 4), pygame.SRCALPHA)
        imagem.blit(borda, (2 * e + 2, 2 * e + 3))  # sombra
        for dx in (-e, 0, e):
            for dy in (-e, 0, e):
                if dx or dy:
                    imagem.blit(borda, (e + dx, e + dy))
        metal = _gradiente(w, h, cores).copy()
        metal.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        imagem.blit(metal, (e, e))
        _textos[chave] = imagem
    retangulo = _posicionar(imagem.get_rect(), centro, esquerda, direita)
    if brilho:
        desenhar_brilho(tela, retangulo.centerx, retangulo.centery, max(retangulo.w, retangulo.h) // 2 + 30,
                        brilho, 70)
    tela.blit(imagem, retangulo)
    return retangulo


def texto(tela, conteudo, tamanho, cor, centro=None, esquerda=None, direita=None, titulo=False, negrito=False):
    """Texto simples com sombra curta; `titulo` usa a fonte de inscrição."""
    f = fonte_titulo(tamanho) if titulo else fonte(tamanho, negrito)
    imagem = f.render(conteudo, True, cor)
    retangulo = _posicionar(imagem.get_rect(), centro, esquerda, direita)
    tela.blit(f.render(conteudo, True, (0, 0, 0)), (retangulo.x + 1, retangulo.y + 2))
    tela.blit(imagem, retangulo)
    return retangulo


def _chanfrado(retangulo, c):
    x, y, w, h = retangulo
    return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c), (x + w - c, y + h),
            (x + c, y + h), (x, y + h - c), (x, y + c)]


def placa(tela, retangulo, alfa=200, c=10):
    """Painel escuro com cantos chanfrados, filete dourado e losangos nos cantos."""
    retangulo = pygame.Rect(retangulo)
    local = (0, 0, retangulo.w, retangulo.h)
    fundo = _gradiente(retangulo.w, retangulo.h, ((34, 22, 22), (12, 8, 10))).copy()
    mascara = pygame.Surface(retangulo.size, pygame.SRCALPHA)
    pygame.draw.polygon(mascara, (255, 255, 255, alfa), _chanfrado(local, c))
    fundo.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.polygon(fundo, C.OURO, _chanfrado((0, 0, retangulo.w - 1, retangulo.h - 1), c), 2)
    pygame.draw.polygon(fundo, (60, 36, 14), _chanfrado((3, 3, retangulo.w - 7, retangulo.h - 7), c - 2), 1)
    tela.blit(fundo, retangulo.topleft)
    m = c // 2 + 1
    for cx, cy in ((retangulo.x + m, retangulo.y + m), (retangulo.right - m, retangulo.y + m),
                   (retangulo.x + m, retangulo.bottom - m), (retangulo.right - m, retangulo.bottom - m)):
        pygame.draw.polygon(tela, C.OURO_CLARO, [(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)])


def barra(tela, retangulo, fracao, cores, segmentos=0, brilhar=False, t=0.0, rastro=None):
    """Barra chanfrada com gradiente; `rastro` mostra o dano recente num tom mais claro."""
    retangulo = pygame.Rect(retangulo)
    c = retangulo.h // 2
    pygame.draw.polygon(tela, (8, 4, 6), _chanfrado(retangulo.inflate(4, 4), c + 1))
    pygame.draw.polygon(tela, (40, 18, 18), _chanfrado(retangulo, c))
    mascara_cheia = _chanfrado((0, 0, retangulo.w, retangulo.h), c)
    for valor, paleta in ((rastro, ((255, 236, 200), (240, 200, 150), (200, 150, 110))), (fracao, cores)):
        if valor is None:
            continue
        largura = int(retangulo.w * max(0.0, min(1.0, valor)))
        if largura <= 2:
            continue
        preenchido = _gradiente(largura, retangulo.h, paleta).copy()
        mascara = pygame.Surface((largura, retangulo.h), pygame.SRCALPHA)
        pygame.draw.polygon(mascara, (255, 255, 255, 255), mascara_cheia)
        preenchido.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        tela.blit(preenchido, retangulo.topleft)
    largura = int(retangulo.w * max(0.0, min(1.0, fracao)))
    if largura > 2:
        pygame.draw.line(tela, misturar(cores[0], (255, 255, 255), 0.5),
                         (retangulo.x + c, retangulo.y + 2), (retangulo.x + max(c, largura - c), retangulo.y + 2))
        if brilhar:
            desenhar_brilho(tela, retangulo.x + largura, retangulo.centery, 22 + int(4 * math.sin(t * 8)),
                            C.BRASA, 120)
    for i in range(1, segmentos):
        x = retangulo.x + retangulo.w * i // segmentos
        pygame.draw.line(tela, (10, 4, 6), (x, retangulo.y + 1), (x, retangulo.bottom - 2), 2)
    pygame.draw.polygon(tela, C.OURO_ESCURO, _chanfrado(retangulo.inflate(4, 4), c + 1), 1)


def tecla(tela, x, y, rotulo):
    """Tecla dourada desenhada; devolve o x logo depois dela."""
    seta = rotulo in ("cima", "baixo")
    imagem = None if seta else fonte_titulo(13).render(rotulo, True, (30, 18, 10))
    largura = 26 if seta else max(26, imagem.get_width() + 14)
    pygame.draw.rect(tela, (60, 40, 20), (x, y + 3, largura, 24), border_radius=4)
    pygame.draw.rect(tela, C.OURO, (x, y, largura, 24), border_radius=4)
    pygame.draw.rect(tela, C.OURO_CLARO, (x + 2, y + 2, largura - 4, 6), border_radius=3)
    if seta:
        cx, cy, d = x + largura // 2, y + 12, (-1 if rotulo == "cima" else 1)
        pygame.draw.polygon(tela, (30, 18, 10), [(cx - 6, cy - 3 * d), (cx + 6, cy - 3 * d), (cx, cy + 4 * d)])
    else:
        tela.blit(imagem, (x + (largura - imagem.get_width()) // 2, y + 5))
    return x + largura


def dica(tela, itens, centro_x, y):
    """Linha de dicas: [(teclas, descrição), ...] centralizada."""
    def largura_tecla(rotulo):
        return 26 if rotulo in ("cima", "baixo") else max(26, fonte_titulo(13).size(rotulo)[0] + 14)

    largura = sum(sum(largura_tecla(t) + 4 for t in teclas) + fonte(15).size(descricao)[0] + 34
                  for teclas, descricao in itens) - 30
    x = centro_x - largura // 2
    for teclas, descricao in itens:
        for t in teclas:
            x = tecla(tela, x, y, t) + 4
        x = texto(tela, descricao, 15, C.OSSO, esquerda=(x + 4, y + 3)).right + 30


def _orbe(tela, x, y, r=7):
    desenhar_brilho(tela, x, y, r * 3, (255, 40, 30), 90)
    pygame.draw.circle(tela, (200, 24, 24), (x, y), r)
    pygame.draw.circle(tela, (255, 110, 90), (x - 2, y - 2), r // 2)
    pygame.draw.circle(tela, (255, 240, 230), (x - 3, y - 3), 2)


def _ampulheta(tela, x, y, cor):
    pygame.draw.line(tela, cor, (x - 6, y - 8), (x + 6, y - 8), 2)
    pygame.draw.line(tela, cor, (x - 6, y + 8), (x + 6, y + 8), 2)
    pygame.draw.polygon(tela, cor, [(x - 5, y - 7), (x + 5, y - 7), (x, y), (x + 5, y + 7), (x - 5, y + 7), (x, y)],
                        1)
    pygame.draw.polygon(tela, C.BRASA, [(x - 3, y + 6), (x + 3, y + 6), (x, y + 2)])


def _escurecer(tela, alfa=160, cor=(0, 0, 0)):
    veu = pygame.Surface((C.LARGURA, C.ALTURA), pygame.SRCALPHA)
    veu.fill((*cor, alfa))
    tela.blit(veu, (0, 0))


def _ornamento(tela, centro_x, y, meia=170):
    pygame.draw.line(tela, C.OURO, (centro_x - meia, y), (centro_x - 30, y), 1)
    pygame.draw.line(tela, C.OURO, (centro_x + 30, y), (centro_x + meia, y), 1)
    pygame.draw.polygon(tela, C.OURO_CLARO, [(centro_x, y - 7), (centro_x + 7, y), (centro_x, y + 7),
                                             (centro_x - 7, y)])


# --------------------------------------------------------------------------- HUD

_retrato = {}


def _medalhao(tela, cx, cy, jogo):
    heroi = jogo.heroi
    desenhar_brilho(tela, cx, cy, 52, (255, 60, 30) if heroi.em_furia else (120, 20, 10), 90)
    pygame.draw.circle(tela, (10, 6, 8), (cx, cy), 36)
    for raio, cor in ((36, C.OURO_ESCURO), (34, C.OURO), (31, C.OURO_ESCURO)):
        pygame.draw.circle(tela, cor, (cx, cy), raio, 2)
    if "mascara" not in _retrato:
        mascara = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), (30, 30), 29)
        _retrato["mascara"] = mascara
    rosto = pygame.Surface((60, 60), pygame.SRCALPHA)
    desenhar_espartano(rosto, 28, 6, 1, jogo.t, escala=2.3, em_furia=heroi.em_furia)
    rosto.blit(_retrato["mascara"], (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    tela.blit(rosto, (cx - 30, cy - 28))
    # vidas
    pygame.draw.circle(tela, (10, 6, 8), (cx + 26, cy + 26), 13)
    pygame.draw.circle(tela, C.OURO, (cx + 26, cy + 26), 13, 2)
    texto(tela, str(jogo.vidas), 16, C.OURO_CLARO, centro=(cx + 26, cy + 25), titulo=True)


def desenhar_hud(tela, jogo):
    heroi = jogo.heroi
    t = jogo.t
    _medalhao(tela, 50, 50, jogo)

    # vida (5 segmentos) e Fúria
    barra(tela, (96, 24, 230, 18), heroi.vida / C.VIDA_MAX, C.BARRA_VIDA, segmentos=C.VIDA_MAX)
    cheia = heroi.furia >= C.FURIA_MAX and not heroi.em_furia
    proporcao = heroi.furia_t / C.FURIA_DURACAO if heroi.em_furia else heroi.furia / C.FURIA_MAX
    barra(tela, (96, 50, 170, 10), proporcao, C.BARRA_FURIA, brilhar=cheia or heroi.em_furia, t=t)
    if cheia and int(t * 3) % 2 == 0:
        texto(tela, "K · FÚRIA!", 14, C.BRASA, esquerda=(276, 45), titulo=True)
    elif heroi.em_furia:
        texto(tela, "FÚRIA", 14, (255, 90, 50), esquerda=(276, 45), titulo=True)

    # orbes (rumo à próxima vida extra)
    _orbe(tela, 104, 76)
    numero = texto(tela, str(jogo.orbes % C.ORBES_POR_VIDA), 18, C.OSSO, esquerda=(118, 64), titulo=True)
    texto(tela, f"/ {C.ORBES_POR_VIDA}", 13, C.OSSO_APAGADO, esquerda=(numero.right + 5, 69), titulo=True)

    # pontos, tempo e fase
    texto_metal(tela, f"{jogo.pontos:06d}", 30, direita=(C.LARGURA - 20, 8))
    segundos = max(0, int(jogo.tempo))
    cor_tempo = (230, 50, 40) if jogo.tempo < 60 and int(t * 4) % 2 == 0 else C.OSSO
    relogio = texto(tela, f"{segundos // 60}:{segundos % 60:02d}", 20, cor_tempo, direita=(C.LARGURA - 20, 52),
                    titulo=True)
    _ampulheta(tela, relogio.x - 14, relogio.centery, cor_tempo)
    texto(tela, f"FASE {ROMANOS[jogo.indice_fase]}", 14, (190, 160, 120), direita=(relogio.x - 30, 55),
          titulo=True)

    # barra do chefe, com rastro do dano recente
    chefe = jogo.chefe
    if chefe is not None and chefe.vivo and chefe.acordado:
        fracao = chefe.vida / chefe.VIDA
        jogo.rastro_chefe = max(fracao, getattr(jogo, "rastro_chefe", fracao) - 0.006)
        largura = 520
        x = (C.LARGURA - largura) // 2
        y = C.ALTURA - 38
        placa(tela, (x - 18, y - 32, largura + 36, 56), 210, 12)
        texto_metal(tela, "POLIFEMO, O CICLOPE", 18, centro=(C.LARGURA // 2, y - 14), cores=C.METAL_SANGUE)
        barra(tela, (x, y, largura, 12), fracao, ((255, 90, 60), (190, 20, 24), (90, 6, 10)),
              rastro=jogo.rastro_chefe)

    # nome da fase ao começar
    if jogo.banner_t > 0 and jogo.estado.name == "JOGANDO":
        camada = pygame.Surface((C.LARGURA, 130), pygame.SRCALPHA)
        texto(camada, f"FASE {ROMANOS[jogo.indice_fase]}", 18, C.OSSO_APAGADO, centro=(C.LARGURA // 2, 16),
              titulo=True)
        texto_metal(camada, jogo.nivel.nome.upper(), 46, centro=(C.LARGURA // 2, 62), brilho=(160, 30, 10))
        _ornamento(camada, C.LARGURA // 2, 108, 220)
        camada.set_alpha(int(255 * min(1.0, jogo.banner_t / 0.6)))
        tela.blit(camada, (0, C.ALTURA // 3 - 70))

    if jogo.depurar:
        texto(tela, f"FPS {jogo.fps:.0f}  partículas {len(jogo.particulas)}  projéteis {len(jogo.projeteis)}",
              14, C.BRANCO, esquerda=(12, C.ALTURA - 22))


# --------------------------------------------------------------------------- menu


def tela_menu(tela, jogo):
    t = jogo.t
    jogo.cenario_menu.desenhar(tela, t)
    if jogo.menu_tela == "controles":
        _tela_controles(tela)
        return

    # guerreiro com as lâminas em brasa
    desenhar_brilho(tela, 165, 330, 150, (190, 30, 10), 110)
    camada = pygame.Surface((C.LARGURA, C.ALTURA), pygame.SRCALPHA)
    progresso = (t % 1.6) / 1.6
    desenhar_espartano(camada, 165, 222, 1, t, progresso_ataque=progresso, atacando=True,
                       combo=int(t / 1.6) % 3, em_furia=True, escala=2.6)
    borda = pygame.mask.from_surface(camada).to_surface(setcolor=(8, 2, 4, 255), unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
        tela.blit(borda, (dx, dy))
    tela.blit(camada, (0, 0))

    centro = 640
    texto_metal(tela, "BLADES", 74, centro=(centro, 88), brilho=(170, 30, 10))
    texto_metal(tela, "OF SPARTA", 44, centro=(centro, 150))
    _ornamento(tela, centro, 190)
    texto(tela, "Um guerreiro de Esparta contra os monstros do Olimpo", 15, (170, 140, 120),
          centro=(centro, 216))

    for i, nome in enumerate(OPCOES_MENU):
        y = 268 + i * 54
        if i == jogo.menu_opcao:
            placa(tela, (centro - 120, y - 21, 240, 42), 210, 10)
            texto_metal(tela, nome, 26, centro=(centro, y), brilho=(150, 30, 10))
            pulso = 3 * math.sin(t * 6)
            for lado in (-1, 1):
                x = centro + lado * (102 + pulso)
                pygame.draw.polygon(tela, C.BRASA, [(x, y), (x - lado * 14, y - 7), (x - lado * 14, y + 7)])
        else:
            texto(tela, nome, 22, C.OSSO_APAGADO, centro=(centro, y), titulo=True)

    dica(tela, [(("cima", "baixo"), "escolher"), (("ENTER",), "confirmar")], C.LARGURA // 2, C.ALTURA - 46)


def _tela_controles(tela):
    centro = C.LARGURA // 2
    _escurecer(tela, 90)
    texto_metal(tela, "CONTROLES", 44, centro=(centro, 62), brilho=(150, 30, 10))
    _ornamento(tela, centro, 98)
    placa(tela, (centro - 330, 120, 660, 330), 215, 14)
    for i, (teclas, descricao) in enumerate(CONTROLES):
        y = 140 + i * 43
        x = centro - 300
        for rotulo in teclas:
            x = tecla(tela, x, y, rotulo) + 6
        texto(tela, descricao, 17, C.OSSO, esquerda=(centro - 120, y + 2))
    dica(tela, [(("ENTER",), "voltar")], centro, C.ALTURA - 52)


# --------------------------------------------------------------------------- telas de estado


def tela_pausa(tela, jogo):
    _escurecer(tela, 170)
    centro = C.LARGURA // 2
    texto_metal(tela, "PAUSADO", 60, centro=(centro, C.ALTURA // 2 - 50), brilho=(140, 30, 10))
    _ornamento(tela, centro, C.ALTURA // 2)
    dica(tela, [(("P", "ENTER"), "continuar"), (("M",), "menu principal")], centro, C.ALTURA // 2 + 30)


def tela_fase_concluida(tela, jogo):
    _escurecer(tela, 170)
    centro = C.LARGURA // 2
    texto_metal(tela, "FASE CONCLUÍDA", 48, centro=(centro, 120), brilho=(160, 40, 10))
    texto(tela, jogo.nivel.nome.upper(), 18, C.OSSO_APAGADO, centro=(centro, 166), titulo=True)
    _ornamento(tela, centro, 192)
    placa(tela, (centro - 200, 220, 400, 150), 215, 12)
    linhas = (("Bônus de tempo", f"+{jogo.bonus_tempo}"), ("Bônus da fase", f"+{C.PONTOS_FASE}"))
    for i, (rotulo, valor) in enumerate(linhas):
        y = 244 + i * 34
        texto(tela, rotulo, 18, C.OSSO, esquerda=(centro - 170, y))
        texto(tela, valor, 18, C.OURO_CLARO, direita=(centro + 170, y), titulo=True)
    pygame.draw.line(tela, C.OURO_ESCURO, (centro - 170, 312), (centro + 170, 312), 1)
    texto(tela, "Pontos", 20, C.OSSO, esquerda=(centro - 170, 324), negrito=True)
    texto_metal(tela, f"{jogo.pontos:06d}", 24, direita=(centro + 172, 318))
    if int(jogo.t * 2) % 2 == 0:
        dica(tela, [(("ENTER",), "próxima fase")], centro, 420)


def tela_game_over(tela, jogo):
    _escurecer(tela, 200, (24, 0, 2))
    centro = C.LARGURA // 2
    texto_metal(tela, "GAME OVER", 76, centro=(centro, 160), cores=C.METAL_SANGUE, brilho=(160, 10, 10))
    texto(tela, "Sua alma desce ao Hades...", 20, (220, 190, 180), centro=(centro, 224))
    _ornamento(tela, centro, 256)
    texto(tela, f"Pontos  {jogo.pontos:06d}", 24, C.OURO_CLARO, centro=(centro, 296), titulo=True)
    texto(tela, f"Orbes  {jogo.orbes}", 18, C.OSSO_APAGADO, centro=(centro, 330), titulo=True)
    dica(tela, [(("R", "ENTER"), "tentar de novo"), (("M",), "menu")], centro, 400)


def tela_vitoria(tela, jogo):
    _escurecer(tela, 160)
    centro = C.LARGURA // 2
    desenhar_brilho(tela, centro, 140, 260, (255, 170, 60), 80)
    texto_metal(tela, "VITÓRIA!", 80, centro=(centro, 120), brilho=(200, 90, 20))
    texto(tela, "O Ciclope caiu. Esparta celebra seu campeão.", 20, C.OSSO, centro=(centro, 182))
    _ornamento(tela, centro, 212)
    texto_metal(tela, f"{jogo.pontos:06d}", 36, centro=(centro, 256))
    texto(tela, f"Orbes  {jogo.orbes}     Vidas  {jogo.vidas}", 18, C.OSSO_APAGADO, centro=(centro, 296),
          titulo=True)
    desenhar_espartano(tela, centro, 330, 1, jogo.t, escala=1.6, em_furia=True)
    dica(tela, [(("R", "ENTER"), "jogar de novo"), (("M",), "menu")], centro, C.ALTURA - 44)
