"""O herói: um guerreiro espartano com lâminas acorrentadas."""
import pygame

from . import config as C
from .fisica import Corpo, aproximar, mover


class Heroi(Corpo):
    """Personagem controlado pelo jogador."""

    LARGURA = 30
    ALTURA = 62

    def __init__(self, x, y):
        super().__init__(x, y, self.LARGURA, self.ALTURA)
        self.direcao = 1
        self.vida = C.VIDA_MAX
        self.morto = False
        self.invencivel = 0.0
        self.ferido = 0.0
        self.deslize = 0.0        # sem controle por um instante (escorregando do Ciclope)
        self.coyote = 0.0
        self.buffer_pulo = 0.0
        self.pulo_cortado = True
        self.pulos_extras = C.PULOS_NO_AR
        # esquiva
        self.esquiva_t = 0.0
        self.esquiva_recarga = 0.0
        self.esquivou_no_ar = False
        # combate
        self.ataque_t = 0.0
        self.recarga = 0.0
        self.combo = -1
        self.desde_ataque = 99.0
        self.buffer_ataque = 0.0
        self.atingidos = set()
        self.furia = 0.0
        self.furia_t = 0.0
        # animação e eventos sonoros do quadro
        self.anim_t = 0.0
        self.pouso_t = 0.0        # achatamento ao aterrissar (só visual)
        self.eventos = []

    # ------------------------------------------------------------ estado
    @property
    def atacando(self):
        return self.ataque_t > 0

    @property
    def em_furia(self):
        return self.furia_t > 0

    @property
    def esquivando(self):
        return self.esquiva_t > 0

    @property
    def progresso_ataque(self):
        """0 → 1 ao longo do golpe atual."""
        return 1.0 - self.ataque_t / C.ATAQUE_DURACAO if self.atacando else 0.0

    # ------------------------------------------------------------ atualização
    def atualizar(self, dt, entrada, nivel, plataformas=()):
        self.anim_t += dt
        self.invencivel = max(0.0, self.invencivel - dt)
        self.ferido = max(0.0, self.ferido - dt)
        self.deslize = max(0.0, self.deslize - dt)
        self.recarga = max(0.0, self.recarga - dt)
        self.esquiva_recarga = max(0.0, self.esquiva_recarga - dt)
        self.furia_t = max(0.0, self.furia_t - dt)
        self.pouso_t = max(0.0, self.pouso_t - dt)
        self.desde_ataque += dt
        if self.morto:
            return

        tem_controle = self.ferido <= 0 and self.deslize <= 0
        if self.no_chao:  # tocar o chão recarrega o pulo duplo e a esquiva no ar
            self.pulos_extras = C.PULOS_NO_AR
            self.esquivou_no_ar = False

        # Esquerda e direita juntas se anulam (entrada simultânea tratada).
        eixo = int(entrada.direita) - int(entrada.esquerda)
        if not tem_controle:
            eixo = 0

        # Esquiva: avanço rápido e invencível; uma só no ar até pousar.
        if (entrada.esquivar and tem_controle and not self.esquivando and self.esquiva_recarga <= 0
                and (self.no_chao or not self.esquivou_no_ar)):
            if eixo:
                self.direcao = eixo
            self.esquiva_t = C.ESQUIVA_DURACAO
            self.esquiva_recarga = C.ESQUIVA_RECARGA
            self.esquivou_no_ar = not self.no_chao
            self.ataque_t = 0.0
            self.eventos.append("esquiva")
        if self.esquivando:
            self.esquiva_t = max(0.0, self.esquiva_t - dt)
            self.vx = self.direcao * (C.ESQUIVA_VEL if self.esquivando else C.VEL_ANDAR)
            self.vy = 0.0  # sem gravidade durante a esquiva
            self._mover(dt, nivel, plataformas, descer=False)
            return

        alvo = eixo * C.VEL_ANDAR
        if self.atacando and self.no_chao:
            alvo *= 0.35
        if tem_controle:
            acel = C.ACEL_CHAO if self.no_chao else C.ACEL_AR
            self.vx = aproximar(self.vx, alvo, acel * dt)
        if eixo and not self.atacando:
            self.direcao = eixo

        # Pulo do chão: permitido se esteve no chão há pouco (coyote time).
        # No ar há só C.PULOS_NO_AR pulos extras (pulo duplo), nunca infinitos.
        self.coyote = C.TEMPO_COYOTE if self.no_chao else max(0.0, self.coyote - dt)
        self.buffer_pulo = C.TEMPO_BUFFER_PULO if entrada.pular else max(0.0, self.buffer_pulo - dt)
        if self.buffer_pulo > 0 and self.coyote > 0 and tem_controle:
            self._pular(C.FORCA_PULO, "pulo")
            self.coyote = 0.0
        elif entrada.pular and not self.no_chao and self.pulos_extras > 0 and tem_controle:
            self._pular(C.FORCA_PULO_DUPLO, "pulo_duplo")
            self.pulos_extras -= 1
        # Soltar o botão cedo corta o pulo (altura variável).
        if not entrada.pular_segurado and self.vy < 0 and not self.pulo_cortado:
            self.vy *= 0.5
            self.pulo_cortado = True

        # Ataque com as lâminas (combo de 3 golpes). O aperto fica guardado por
        # um instante, então apertar um pouco antes do fim do golpe não se perde.
        self.buffer_ataque = C.BUFFER_ATAQUE if entrada.atacar else max(0.0, self.buffer_ataque - dt)
        if self.buffer_ataque > 0 and tem_controle and not self.atacando and self.recarga <= 0:
            self.combo = (self.combo + 1) % 3 if self.desde_ataque < C.COMBO_JANELA else 0
            self.ataque_t = C.ATAQUE_DURACAO
            self.desde_ataque = 0.0
            self.buffer_ataque = 0.0
            self.atingidos.clear()
            self.eventos.append("ataque")
        if self.atacando:
            self.ataque_t -= dt
            if self.ataque_t <= 0:
                self.ataque_t = 0.0
                self.recarga = C.ATAQUE_RECARGA

        # Fúria Espartana: dano dobrado por alguns segundos.
        if entrada.furia and self.furia >= C.FURIA_MAX and not self.em_furia:
            self.furia = 0.0
            self.furia_t = C.FURIA_DURACAO
            self.eventos.append("furia")

        # Gravidade e movimento com colisão.
        self.vy = min(self.vy + C.GRAVIDADE * dt, C.VEL_MAX_QUEDA)
        self._mover(dt, nivel, plataformas, descer=entrada.baixo)

    def _pular(self, forca, evento):
        self.vy = -forca
        self.buffer_pulo = 0.0
        self.no_chao = False
        self.pulo_cortado = False
        self.eventos.append(evento)

    def _mover(self, dt, nivel, plataformas, descer):
        """Move com colisão e avisa quando aterrissa (para poeira e achatamento)."""
        estava_no_ar = not self.no_chao
        velocidade_queda = self.vy
        self.base_anterior = self.base
        mover(self, dt, nivel, plataformas, descer=descer)
        if estava_no_ar and self.no_chao and velocidade_queda > 300:
            self.pouso_t = 0.14
            self.eventos.append("pouso")

    # ------------------------------------------------------------ combate
    def hitbox_ataque(self):
        """Retângulo atingido pelas lâminas neste quadro, ou None."""
        if not self.atacando:
            return None
        decorrido = C.ATAQUE_DURACAO - self.ataque_t
        if not (C.ATAQUE_ATIVO_INICIO <= decorrido <= C.ATAQUE_ATIVO_FIM):
            return None
        alcance = C.ATAQUE_ALCANCE
        topo = int(self.y) - 14
        altura = self.h + 20
        if self.combo == 2:  # giro: acerta os dois lados
            return pygame.Rect(int(self.centro_x - alcance), topo, alcance * 2, altura)
        if self.direcao > 0:
            return pygame.Rect(int(self.centro_x), topo, alcance, altura)
        return pygame.Rect(int(self.centro_x - alcance), topo, alcance, altura)

    def dano_golpe(self):
        dano = 2 if self.combo == 2 else 1
        return dano * 2 if self.em_furia else dano

    def ganhar_furia(self, quantidade):
        if not self.em_furia:
            self.furia = min(C.FURIA_MAX, self.furia + quantidade)

    def receber_dano(self, quantidade, origem_x):
        """Aplica dano com empurrão e invencibilidade. Retorna True se o dano valeu."""
        if self.invencivel > 0 or self.morto or self.esquivando:
            return False
        self.vida = max(0, self.vida - quantidade)
        self.invencivel = C.TEMPO_INVENCIVEL
        self.ferido = C.TEMPO_FERIDO
        lado = 1 if self.centro_x >= origem_x else -1
        self.vx = 360 * lado
        self.vy = -420
        self.pulo_cortado = True
        self.ataque_t = 0.0
        self.eventos.append("dano")
        if self.vida == 0:
            self.morto = True
        return True

    def quicar(self, topo):
        """Impulso para cima ao pisar em um inimigo cujo topo está em `topo`.

        Encosta o herói no topo antes do impulso, para que no quadro seguinte
        ele já esteja fora do inimigo (senão o contato contaria como dano).
        """
        self.y = topo - self.h
        self.vy = -C.FORCA_QUIQUE
        self.pulos_extras = C.PULOS_NO_AR  # pisar recarrega o pulo duplo e a esquiva
        self.esquivou_no_ar = False
        self.pulo_cortado = False

    def curar(self, quantidade):
        self.vida = min(C.VIDA_MAX, self.vida + quantidade)

    def ressuscitar(self, x, y):
        """Volta ao jogo no checkpoint com vida cheia."""
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.vida = C.VIDA_MAX
        self.morto = False
        self.invencivel = 1.5
        self.ferido = 0.0
        self.ataque_t = 0.0
        self.esquiva_t = 0.0
        self.deslize = 0.0
        self.furia_t = 0.0
        self.plataforma = None
