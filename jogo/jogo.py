"""Classe principal: estados do jogo, regras e o ciclo atualizar/desenhar.

Loop principal (ver main.py):  Entrada -> Regras -> Atualização -> Renderização -> repetir
"""
import random
from enum import Enum, auto

import pygame

from . import config as C
from . import desenho, hud
from .camera import Camera
from .heroi import Heroi
from .inimigos import Ciclope, criar_inimigo
from .nivel import FASES, Nivel
from .objetos import Altar, Orbe, PlataformaMovel, Portal, TextoFlutuante, explosao
from .recursos import Audio, avisar


class Estado(Enum):
    MENU = auto()
    JOGANDO = auto()
    PAUSADO = auto()
    FASE_CONCLUIDA = auto()
    GAME_OVER = auto()
    VITORIA = auto()


# Transições permitidas. Qualquer outra é recusada: assim o jogo nunca fica
# num estado impossível (ex.: "jogando" e "game over" ao mesmo tempo).
TRANSICOES = {
    Estado.MENU: {Estado.JOGANDO},
    Estado.JOGANDO: {Estado.PAUSADO, Estado.FASE_CONCLUIDA, Estado.GAME_OVER, Estado.VITORIA},
    Estado.PAUSADO: {Estado.JOGANDO, Estado.MENU},
    Estado.FASE_CONCLUIDA: {Estado.JOGANDO},
    Estado.GAME_OVER: {Estado.JOGANDO, Estado.MENU},
    Estado.VITORIA: {Estado.JOGANDO, Estado.MENU},
}

CORES_OSSO = [(236, 230, 210), (190, 182, 160), (150, 140, 120)]
CORES_FOGO = [(255, 200, 80), (255, 120, 30), (220, 50, 20)]
CORES_SANGUE_HEROI = [(200, 30, 30), (140, 20, 20), (240, 220, 200)]
CORES_POEIRA = [(170, 150, 120), (130, 112, 90), (210, 196, 170)]


class Jogo:
    def __init__(self, tela, audio=None, fases=None):
        self.tela = tela
        self.audio = audio if audio is not None else Audio(ativo=False)
        self.fases = fases if fases is not None else FASES
        self.estado = Estado.MENU
        self.rodando = True
        self.depurar = False
        self.fps = 0.0
        self.t = 0.0
        self.cenario_menu = desenho.CenarioMenu()
        self.menu_opcao = 0          # índice em hud.OPCOES_MENU
        self.menu_tela = "principal"  # ou "controles"
        self.novo_jogo()
        self.estado = Estado.MENU

    # ------------------------------------------------------------------ estados
    def mudar_estado(self, novo):
        if novo not in TRANSICOES[self.estado]:
            avisar(f"transição inválida ignorada: {self.estado.name} -> {novo.name}")
            return False
        self.estado = novo
        if novo == Estado.MENU:
            self.menu_opcao = 0
            self.menu_tela = "principal"
        return True

    def novo_jogo(self):
        self.vidas = C.VIDAS_INICIAIS
        self.pontos = 0
        self.orbes = 0
        self.indice_fase = 0
        self.carregar_fase(0)

    def carregar_fase(self, indice):
        self.indice_fase = indice
        self.nivel = Nivel(self.fases[indice])
        self.inimigos = []
        self.orbes_mapa = []
        self.altares = []
        self.plataformas = []
        self.projeteis = []
        self.particulas = []
        self.textos = []
        self.portal = None
        self.chefe = None
        T = C.TILE
        for ch, coluna, linha in self.nivel.spawns:
            if ch in "SAHC":
                inimigo = criar_inimigo(ch, coluna, linha)
                self.inimigos.append(inimigo)
                if isinstance(inimigo, Ciclope):
                    self.chefe = inimigo
            elif ch in "og":
                self.orbes_mapa.append(Orbe(coluna * T + T / 2, linha * T + T / 2,
                                            "vermelho" if ch == "o" else "verde"))
            elif ch == "K":
                self.altares.append(Altar(coluna, linha))
            elif ch == "F":
                self.portal = Portal(coluna, linha)
            elif ch == "M":
                self.plataformas.append(PlataformaMovel(coluna, linha))
        coluna, linha = self.nivel.inicio
        self.ponto_renascer = (coluna * T + T / 2, (linha + 1) * T)
        self.heroi = Heroi(0, 0)
        self._posicionar_heroi()
        self.camera = Camera(self.nivel.largura_px, self.nivel.altura_px)
        self.camera.seguir(self.heroi.centro_x, self.heroi.centro_y, 0, instantaneo=True)
        self.cenario = desenho.Cenario(self.nivel.tema)
        self.tiles = desenho.DesenhistaTiles(self.nivel.tema)
        self.tempo = C.TEMPO_FASE
        self.morte_t = 0.0
        self.morte_por_tempo = False
        self.congelar_t = 0.0  # hitstop: o mundo para por um instante a cada acerto
        self.banner_t = 2.5
        self.bonus_tempo = 0

    def _posicionar_heroi(self):
        x, base = self.ponto_renascer
        self.heroi.ressuscitar(x - self.heroi.w / 2, base - self.heroi.h)

    # ------------------------------------------------------------------ interface p/ inimigos
    def adicionar_projetil(self, projetil):
        self.projeteis.append(projetil)

    def tocar(self, som):
        self.audio.tocar(som)

    def tremer(self, intensidade, duracao):
        self.camera.tremer(intensidade, duracao)

    def _adicionar_particulas(self, novas):
        self.particulas.extend(novas)
        excesso = len(self.particulas) - C.MAX_PARTICULAS
        if excesso > 0:  # limite de segurança: descarta as mais antigas
            del self.particulas[:excesso]

    def _texto(self, x, y, texto, cor=C.AMARELO):
        self.textos.append(TextoFlutuante(x, y, texto, cor))

    # ------------------------------------------------------------------ atualização
    def atualizar(self, dt, entrada):
        dt = max(0.0, min(dt, C.DT_MAX))
        self.t += dt
        if entrada.fechar:
            self.rodando = False
            return
        if entrada.depurar:
            self.depurar = not self.depurar

        if self.estado == Estado.MENU:
            self._atualizar_menu(entrada)
        elif self.estado == Estado.JOGANDO:
            if entrada.pausar or entrada.voltar:
                self.mudar_estado(Estado.PAUSADO)
            else:
                self._atualizar_partida(dt, entrada)
        elif self.estado == Estado.PAUSADO:
            if entrada.pausar or entrada.voltar or entrada.confirmar:
                self.mudar_estado(Estado.JOGANDO)
            elif entrada.menu:
                self.mudar_estado(Estado.MENU)
        elif self.estado == Estado.FASE_CONCLUIDA:
            self._atualizar_efeitos(dt)
            if entrada.confirmar:
                self.carregar_fase(self.indice_fase + 1)
                self.mudar_estado(Estado.JOGANDO)
        elif self.estado in (Estado.GAME_OVER, Estado.VITORIA):
            self._atualizar_efeitos(dt)
            if entrada.reiniciar or entrada.confirmar:
                self.novo_jogo()
                self.mudar_estado(Estado.JOGANDO)
            elif entrada.menu or entrada.voltar:
                self.mudar_estado(Estado.MENU)

    def _atualizar_menu(self, entrada):
        """Menu principal: ↑/↓ escolhe, Enter confirma, Esc sai (ou volta dos controles)."""
        if self.menu_tela == "controles":
            if entrada.confirmar or entrada.voltar:
                self.menu_tela = "principal"
            return
        total = len(hud.OPCOES_MENU)
        if entrada.cima:
            self.menu_opcao = (self.menu_opcao - 1) % total
            self.tocar("orbe")
        elif entrada.baixo_apertou:
            self.menu_opcao = (self.menu_opcao + 1) % total
            self.tocar("orbe")
        elif entrada.confirmar:
            escolha = hud.OPCOES_MENU[self.menu_opcao]
            if escolha == "JOGAR":
                self.novo_jogo()
                self.mudar_estado(Estado.JOGANDO)
            elif escolha == "CONTROLES":
                self.menu_tela = "controles"
            else:
                self.rodando = False
        elif entrada.voltar:
            self.rodando = False

    def _atualizar_partida(self, dt, entrada):
        self.banner_t = max(0.0, self.banner_t - dt)
        heroi = self.heroi

        # Animação de morte: o mundo congela até o herói renascer.
        if self.morte_t > 0:
            self.morte_t -= dt
            self._atualizar_efeitos(dt)
            if self.morte_t <= 0:
                self.perder_vida()
            return

        # Hitstop: pausa curtíssima a cada golpe que acerta (sensação de impacto).
        if self.congelar_t > 0:
            self.congelar_t = max(0.0, self.congelar_t - dt)
            self._atualizar_efeitos(dt)
            return

        self.tempo -= dt
        if self.tempo <= 0:
            self.tempo = 0
            self.matar_heroi(por_tempo=True)
            return

        for plataforma in self.plataformas:
            plataforma.atualizar(dt)

        heroi.eventos.clear()
        heroi.atualizar(dt, entrada, self.nivel, self.plataformas)
        for evento in heroi.eventos:
            self.tocar(evento)
        if "dano" in heroi.eventos:
            self.tremer(5, 0.25)
        for evento in ("pulo", "pulo_duplo", "pouso", "esquiva"):
            if evento in heroi.eventos:
                self._poeira(evento)
        if "furia" in heroi.eventos:
            self.tremer(6, 0.4)
            self._adicionar_particulas(explosao(heroi.centro_x, heroi.centro_y, CORES_FOGO, 30, 320))

        if heroi.y > self.nivel.altura_px + 60:  # caiu no abismo
            self.matar_heroi()
            return
        self._verificar_perigos()
        self._resolver_ataque()
        self._atualizar_inimigos(dt)
        self._atualizar_projeteis(dt)
        self._coletar_itens(dt)
        self._verificar_altares(dt)

        if heroi.morto:
            self.matar_heroi()
            return
        if self._verificar_portal(dt):
            return
        self.camera.seguir(heroi.centro_x, heroi.centro_y, dt)
        self._atualizar_efeitos(dt)

    def _verificar_perigos(self):
        heroi = self.heroi
        T = C.TILE
        for coluna, linha, tile in self.nivel.tiles_no_retangulo(heroi.x, heroi.y, heroi.w, heroi.h):
            if tile == "~" and heroi.base > linha * T + 14:
                self.matar_heroi()
                return
            if tile == "^" and heroi.base > linha * T + T * 0.5:
                if heroi.receber_dano(1, coluna * T + T / 2):
                    heroi.vy = -520
                    self.tocar("dano")
                    self.tremer(5, 0.25)
                return

    def _resolver_ataque(self):
        heroi = self.heroi
        golpe = heroi.hitbox_ataque()
        if golpe is None:
            return
        for inimigo in self.inimigos:
            if not inimigo.vivo or id(inimigo) in heroi.atingidos or not golpe.colliderect(inimigo.rect):
                continue
            heroi.atingidos.add(id(inimigo))
            lado = 1 if inimigo.centro_x >= heroi.centro_x else -1
            inimigo.receber_golpe(heroi.dano_golpe(), lado)
            heroi.ganhar_furia(C.FURIA_POR_GOLPE)
            final = heroi.combo == 2
            self._adicionar_particulas(explosao(inimigo.centro_x, inimigo.centro_y, CORES_FOGO,
                                                18 if final else 10, 280 if final else 220, 0.35))
            self.tocar("acerto")
            self.tremer(7 if final else 3, 0.18 if final else 0.1)
            self.congelar_t = max(self.congelar_t, C.HITSTOP_FINAL if final else C.HITSTOP)
        for projetil in self.projeteis:
            if projetil.vivo and projetil.tipo == "lanca" and golpe.colliderect(projetil.rect):
                projetil.vivo = False  # lanças podem ser rebatidas
                self._adicionar_particulas(explosao(projetil.x, projetil.y, CORES_FOGO, 6, 160, 0.3))
        for coluna, linha, tile in list(self.nivel.tiles_no_retangulo(golpe.x, golpe.y, golpe.w, golpe.h)):
            if tile == "X":
                self.quebrar_anfora(coluna, linha)

    def quebrar_anfora(self, coluna, linha):
        T = C.TILE
        self.nivel.remover(coluna, linha)
        cx, cy = coluna * T + T / 2, linha * T + T / 2
        self._adicionar_particulas(explosao(cx, cy, [(196, 98, 46), (140, 64, 30), (34, 22, 18)], 16, 260))
        for i in range(3):
            tipo = "verde" if i == 1 and random.random() < 0.25 else "vermelho"
            self.orbes_mapa.append(Orbe(cx + (i - 1) * 16, cy - 10 - (i % 2) * 14, tipo))
        self.pontos += C.PONTOS_CAIXA
        self.tocar("caixa")

    def _atualizar_inimigos(self, dt):
        heroi = self.heroi
        for inimigo in self.inimigos:
            if not inimigo.vivo:
                continue
            inimigo.atualizar(dt, self.nivel, heroi, self)
            if not inimigo.vivo or heroi.morto or not heroi.rect.colliderect(inimigo.rect):
                continue
            # Pisão: no quadro anterior a base do herói estava acima do topo do
            # inimigo (vale para qualquer FPS, ao contrário de uma margem fixa).
            pisou = heroi.vy > 0 and heroi.base_anterior <= inimigo.y + C.TOLERANCIA_PISAO
            if pisou and inimigo.PISAVEL:
                inimigo.receber_golpe(1, 0)
                heroi.quicar(inimigo.y)
                self.tocar("pisao")
                self._adicionar_particulas(explosao(heroi.centro_x, heroi.base, CORES_OSSO, 8, 160, 0.3))
            elif pisou and isinstance(inimigo, Ciclope):
                # Na cabeça do Ciclope não dá para ficar: o herói quica e escorrega.
                heroi.quicar(inimigo.y)
                lado = 1 if heroi.centro_x >= inimigo.centro_x else -1
                heroi.vx = C.CICLOPE_ESCORREGAR * lado
                heroi.deslize = C.CICLOPE_ESCORREGAR_TEMPO
            elif heroi.receber_dano(inimigo.DANO, inimigo.centro_x):
                self.tocar("dano")
                self.tremer(5, 0.25)
                if isinstance(inimigo, Ciclope):
                    inimigo.acertou_heroi()

        # Remove os derrotados (a lista não cresce indefinidamente) e dá os pontos.
        vivos = []
        for inimigo in self.inimigos:
            if inimigo.vivo:
                vivos.append(inimigo)
            elif inimigo.y <= self.nivel.altura_px:  # morreu em combate (não caiu no abismo)
                self.pontos += inimigo.PONTOS
                self._texto(inimigo.centro_x, inimigo.y - 10, f"+{inimigo.PONTOS}")
                cores = CORES_FOGO if isinstance(inimigo, Ciclope) else CORES_OSSO
                self._adicionar_particulas(explosao(inimigo.centro_x, inimigo.centro_y, cores,
                                                    60 if isinstance(inimigo, Ciclope) else 18, 300))
                if isinstance(inimigo, Ciclope):
                    self.tremer(14, 1.0)
                    self.tocar("rugido")
        self.inimigos = vivos
        if self.portal is not None:
            self.portal.travado = self.chefe is not None and self.chefe.vivo

    def _poeira(self, evento):
        heroi = self.heroi
        if evento == "pulo_duplo":
            cores, quantidade, forca = CORES_FOGO, 10, 150
        elif evento == "esquiva":
            cores, quantidade, forca = CORES_FOGO, 8, 120
        else:
            cores, quantidade, forca = CORES_POEIRA, 7 if evento == "pulo" else 10, 110
        self._adicionar_particulas(explosao(heroi.centro_x, heroi.base - 2, cores, quantidade, forca, 0.35,
                                            tamanho=2, gravidade=300))

    def _atualizar_projeteis(self, dt):
        heroi = self.heroi
        for projetil in self.projeteis:
            projetil.atualizar(dt, self.nivel)
            if projetil.vivo and not heroi.morto and heroi.rect.colliderect(projetil.rect):
                if heroi.receber_dano(projetil.dano, projetil.x):
                    self.tocar("dano")
                    self.tremer(4, 0.2)
                if projetil.tipo == "lanca":
                    projetil.vivo = False
        self.projeteis = [p for p in self.projeteis if p.vivo]

    def _coletar_itens(self, dt):
        heroi = self.heroi
        corpo = heroi.rect
        for orbe in self.orbes_mapa:
            orbe.atualizar(dt)
            if orbe.vivo and corpo.colliderect(orbe.rect):
                orbe.vivo = False
                if orbe.tipo == "vermelho":
                    self.coletar_orbe_vermelho()
                else:
                    heroi.curar(2)
                    self._texto(orbe.x, orbe.y - 16, "+VIDA", C.VERDE)
                    self.tocar("vida")
                self._adicionar_particulas(explosao(orbe.x, orbe.y, [(255, 120, 100), (255, 220, 200)]
                                                    if orbe.tipo == "vermelho" else [(120, 255, 140)], 6, 120, 0.3,
                                                    2, 0))
        self.orbes_mapa = [o for o in self.orbes_mapa if o.vivo]

    def coletar_orbe_vermelho(self):
        self.orbes += 1
        self.pontos += C.PONTOS_ORBE
        self.tocar("orbe")
        if self.orbes % C.ORBES_POR_VIDA == 0:
            self.vidas += 1
            self._texto(self.heroi.centro_x, self.heroi.y - 20, "1UP!", C.VERDE)
            self.tocar("vida")

    def _verificar_altares(self, dt):
        for altar in self.altares:
            altar.t += dt
            if not altar.ativo and self.heroi.rect.colliderect(altar.rect):
                for outro in self.altares:
                    outro.ativo = False
                altar.ativo = True
                self.ponto_renascer = altar.ponto_renascer
                self._texto(altar.x + altar.w / 2, altar.y - 50, "CHECKPOINT", (255, 200, 120))
                self.tocar("checkpoint")

    def _verificar_portal(self, dt):
        portal = self.portal
        if portal is None:
            return False
        portal.t += dt
        if portal.travado or not self.heroi.rect.colliderect(portal.rect):
            return False
        self.bonus_tempo = int(self.tempo) * C.PONTOS_POR_SEGUNDO
        self.pontos += self.bonus_tempo + C.PONTOS_FASE
        self.tocar("portal")
        if self.indice_fase + 1 >= len(self.fases):
            self.mudar_estado(Estado.VITORIA)
        else:
            self.mudar_estado(Estado.FASE_CONCLUIDA)
        return True

    def _atualizar_efeitos(self, dt):
        for particula in self.particulas:
            particula.atualizar(dt)
        self.particulas = [p for p in self.particulas if p.viva]
        for texto in self.textos:
            texto.atualizar(dt)
        self.textos = [t for t in self.textos if t.viva]

    # ------------------------------------------------------------------ vida e morte
    def matar_heroi(self, por_tempo=False):
        if self.morte_t > 0:
            return
        self.morte_por_tempo = por_tempo
        heroi = self.heroi
        heroi.morto = True
        heroi.vida = 0
        self.morte_t = 1.4
        self.tocar("morte")
        self.tremer(8, 0.5)
        self._adicionar_particulas(explosao(heroi.centro_x, min(heroi.centro_y, self.nivel.altura_px - 10),
                                            CORES_SANGUE_HEROI, 40, 340, 1.0))

    def perder_vida(self):
        self.morte_t = 0.0
        self.vidas -= 1
        if self.vidas <= 0:
            self.vidas = 0
            self.mudar_estado(Estado.GAME_OVER)
            return
        self._posicionar_heroi()
        # O relógio só volta ao início se acabou; morrer de outro jeito não
        # devolve tempo (senão morrer renderia bônus de tempo no fim da fase).
        if self.morte_por_tempo:
            self.tempo = C.TEMPO_FASE
        self.projeteis.clear()
        if self.chefe is not None and self.chefe.vivo:
            self.chefe.reiniciar()
        self.camera.seguir(self.heroi.centro_x, self.heroi.centro_y, 0, instantaneo=True)

    # ------------------------------------------------------------------ renderização
    def desenhar(self):
        tela = self.tela
        if self.estado == Estado.MENU:
            hud.tela_menu(tela, self)
            return
        self._desenhar_mundo(tela)
        hud.desenhar_hud(tela, self)
        if self.estado == Estado.PAUSADO:
            hud.tela_pausa(tela, self)
        elif self.estado == Estado.FASE_CONCLUIDA:
            hud.tela_fase_concluida(tela, self)
        elif self.estado == Estado.GAME_OVER:
            hud.tela_game_over(tela, self)
        elif self.estado == Estado.VITORIA:
            hud.tela_vitoria(tela, self)

    def _desenhar_mundo(self, tela):
        cam_x, cam_y = self.camera.deslocamento
        self.cenario.desenhar(tela, cam_x, self.t)
        self.tiles.desenhar(tela, self.nivel, cam_x, cam_y, self.t)
        for altar in self.altares:
            desenho.desenhar_altar(tela, altar, cam_x, cam_y, self.t)
        if self.portal is not None:
            desenho.desenhar_portal(tela, self.portal, cam_x, cam_y, self.t)
        for plataforma in self.plataformas:
            desenho.desenhar_plataforma(tela, plataforma, cam_x, cam_y)
        for orbe in self.orbes_mapa:
            desenho.desenhar_orbe(tela, orbe, cam_x, cam_y)
        for inimigo in self.inimigos:
            desenho.desenhar_inimigo(tela, inimigo, self.heroi, cam_x, cam_y, self.t)
        for projetil in self.projeteis:
            desenho.desenhar_projetil(tela, projetil, cam_x, cam_y)
        desenho.desenhar_heroi(tela, self.heroi, cam_x, cam_y)
        desenho.desenhar_particulas(tela, self.particulas, cam_x, cam_y)
        desenho.desenhar_textos(tela, self.textos, cam_x, cam_y)
        desenho.desenhar_vinheta(tela)
        if self.depurar:
            self._desenhar_depuracao(tela, cam_x, cam_y)

    def _desenhar_depuracao(self, tela, cam_x, cam_y):
        pygame.draw.rect(tela, (0, 255, 0), self.heroi.rect.move(-cam_x, -cam_y), 1)
        golpe = self.heroi.hitbox_ataque()
        if golpe:
            pygame.draw.rect(tela, (255, 0, 0), golpe.move(-cam_x, -cam_y), 1)
        for inimigo in self.inimigos:
            pygame.draw.rect(tela, (255, 255, 0), inimigo.rect.move(-cam_x, -cam_y), 1)
        for projetil in self.projeteis:
            pygame.draw.rect(tela, (0, 200, 255), projetil.rect.move(-cam_x, -cam_y), 1)
