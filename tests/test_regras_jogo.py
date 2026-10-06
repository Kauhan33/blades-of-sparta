"""Testes das regras do jogo: estados, vidas, combate, itens, chefe e limites."""
import unittest

import auxiliar as A
from jogo import config as C
from jogo.entrada import Entrada
from jogo.jogo import Estado
from jogo.objetos import Particula, criar_lanca


class TestEstados(unittest.TestCase):
    def test_transicao_invalida_e_recusada(self):
        jogo = A.criar_jogo()
        jogo.estado = Estado.MENU
        self.assertFalse(jogo.mudar_estado(Estado.VITORIA))
        self.assertEqual(jogo.estado, Estado.MENU)

    def test_pausa_congela_a_partida(self):
        jogo = A.criar_jogo()
        A.simular(jogo, 0.5)
        jogo.atualizar(A.DT, Entrada(pausar=True))
        self.assertEqual(jogo.estado, Estado.PAUSADO)
        tempo, x = jogo.tempo, jogo.heroi.x
        A.simular(jogo, 1.0, direita=True)
        self.assertEqual((jogo.tempo, jogo.heroi.x), (tempo, x))
        jogo.atualizar(A.DT, Entrada(pausar=True))
        self.assertEqual(jogo.estado, Estado.JOGANDO)

    def test_menu_enter_inicia_e_esc_fecha(self):
        jogo = A.criar_jogo()
        jogo.estado = Estado.MENU
        jogo.atualizar(A.DT, Entrada(confirmar=True))
        self.assertEqual(jogo.estado, Estado.JOGANDO)
        jogo.estado = Estado.MENU
        jogo.atualizar(A.DT, Entrada(voltar=True))
        self.assertFalse(jogo.rodando)

    def test_menu_navega_entre_as_opcoes(self):
        jogo = A.criar_jogo()
        jogo.mudar_estado(Estado.PAUSADO)
        jogo.mudar_estado(Estado.MENU)
        jogo.atualizar(A.DT, Entrada(baixo_apertou=True))
        jogo.atualizar(A.DT, Entrada(confirmar=True))      # CONTROLES
        self.assertEqual(jogo.menu_tela, "controles")
        self.assertEqual(jogo.estado, Estado.MENU)
        jogo.atualizar(A.DT, Entrada(confirmar=True))      # volta ao menu
        self.assertEqual(jogo.menu_tela, "principal")
        jogo.atualizar(A.DT, Entrada(cima=True))
        jogo.atualizar(A.DT, Entrada(cima=True))           # dá a volta até SAIR
        jogo.atualizar(A.DT, Entrada(confirmar=True))
        self.assertFalse(jogo.rodando)


class TestVidas(unittest.TestCase):
    def test_perder_vida_renasce_no_checkpoint_com_vida_cheia(self):
        jogo = A.criar_jogo()
        jogo.heroi.receber_dano(2, 0)
        jogo.heroi.x += 200
        jogo.perder_vida()
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS - 1)
        self.assertEqual(jogo.heroi.vida, C.VIDA_MAX)
        self.assertFalse(jogo.heroi.morto)
        self.assertAlmostEqual(jogo.heroi.centro_x, jogo.ponto_renascer[0])
        self.assertEqual(jogo.estado, Estado.JOGANDO)

    def test_sem_vidas_vai_para_game_over_e_para_de_jogar(self):
        jogo = A.criar_jogo()
        jogo.vidas = 1
        jogo.perder_vida()
        self.assertEqual(jogo.estado, Estado.GAME_OVER)
        self.assertEqual(jogo.vidas, 0)
        A.simular(jogo, 2.0, direita=True)  # nada acontece na partida
        self.assertEqual(jogo.vidas, 0)
        self.assertEqual(jogo.estado, Estado.GAME_OVER)

    def test_reiniciar_apos_game_over(self):
        jogo = A.criar_jogo()
        jogo.vidas = 1
        jogo.perder_vida()
        jogo.atualizar(A.DT, Entrada(reiniciar=True))
        self.assertEqual(jogo.estado, Estado.JOGANDO)
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS)
        self.assertEqual(jogo.pontos, 0)

    def test_cair_no_abismo_custa_uma_vida(self):
        mapa = [
            "            ",
            "            ",
            "  P       F ",
            "#####   ####",
            "#####   ####",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.heroi.x = 6 * C.TILE  # em cima do buraco
        A.simular(jogo, 3.0)
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS - 1)

    def test_tempo_esgotado_mata_o_heroi(self):
        jogo = A.criar_jogo()
        jogo.tempo = 0.05
        A.simular(jogo, 2.0)
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS - 1)
        self.assertGreater(jogo.tempo, C.TEMPO_FASE - 2)  # cronômetro reiniciado

    def test_morrer_por_outro_motivo_nao_reinicia_o_tempo(self):
        mapa = [
            "            ",
            "            ",
            "  P       F ",
            "#####   ####",
            "#####   ####",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.tempo = 120.0
        jogo.heroi.x = 6 * C.TILE  # em cima do buraco
        A.simular(jogo, 3.0)
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS - 1)
        self.assertLess(jogo.tempo, 120.0)
        self.assertGreater(jogo.tempo, 115.0)

    def test_espinhos_causam_dano(self):
        mapa = [
            "          ",
            "          ",
            "  P ^^  F ",
            "##########",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.heroi.invencivel = 0
        A.simular(jogo, 1.0, direita=True)
        self.assertLess(jogo.heroi.vida, C.VIDA_MAX)

    def test_lava_mata(self):
        mapa = [
            "          ",
            "          ",
            "  P     F ",
            "####~~####",
            "####~~####",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.heroi.x = 4 * C.TILE + 8
        A.simular(jogo, 0.6)
        self.assertTrue(jogo.heroi.morto)


class TestCombate(unittest.TestCase):
    MAPA = [
        "            ",
        "            ",
        "  PS      F ",
        "############",
    ]

    def test_dois_golpes_derrotam_o_esqueleto_e_dao_pontos(self):
        jogo = A.criar_jogo(self.MAPA)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        jogo.heroi.direcao = 1
        for _ in range(2):
            jogo.atualizar(A.DT, Entrada(atacar=True))
            A.simular(jogo, 0.4)
        self.assertFalse(esqueleto.vivo)
        self.assertNotIn(esqueleto, jogo.inimigos)  # removido da lista
        self.assertEqual(jogo.pontos, esqueleto.PONTOS)
        self.assertGreater(jogo.heroi.furia, 0)

    def test_um_golpe_acerta_cada_inimigo_so_uma_vez(self):
        jogo = A.criar_jogo(self.MAPA)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        jogo.atualizar(A.DT, Entrada(atacar=True))
        A.simular(jogo, C.ATAQUE_DURACAO)
        self.assertEqual(esqueleto.vida, esqueleto.VIDA - 1)

    def test_pisar_no_esqueleto_causa_dano_e_quica(self):
        jogo = A.criar_jogo(self.MAPA)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        A.simular(jogo, 0.3)
        heroi = jogo.heroi
        heroi.x = esqueleto.x
        heroi.y = esqueleto.y - heroi.h - 4
        heroi.vy = 300
        A.simular(jogo, 0.05)
        self.assertEqual(esqueleto.vida, esqueleto.VIDA - 1)
        self.assertLess(heroi.vy, 0)

    MAPA_ALTO = [
        "            ",
        "            ",
        "            ",
        "            ",
        "            ",
        "            ",
        "  PS      F ",
        "############",
    ]

    def _cair_sobre(self, jogo, inimigo, altura, segurar):
        """Solta o herói `altura` px acima do inimigo; devolve True se o pisão aconteceu."""
        heroi = jogo.heroi
        heroi.invencivel = 0
        heroi.x = inimigo.centro_x - heroi.w / 2
        heroi.y = inimigo.y - heroi.h - altura
        heroi.vx = heroi.vy = 0
        vida_inimigo = inimigo.vida
        for _ in range(120):
            jogo.atualizar(A.DT, Entrada(pular_segurado=segurar))
            if inimigo.vida < vida_inimigo or heroi.vy < 0:
                return True
        return False

    def test_pisao_nunca_machuca_o_heroi(self):
        # Regressão: o herói ainda estava dentro do inimigo no quadro seguinte
        # ao quique e levava dano em mais da metade dos pisões.
        for segurar in (False, True):
            for altura in range(1, 201, 7):
                with self.subTest(altura=altura, segurando_pulo=segurar):
                    jogo = A.criar_jogo(self.MAPA_ALTO)
                    esqueleto = jogo.inimigos[0]
                    esqueleto.velocidade = 0
                    A.simular(jogo, 0.3)
                    self.assertTrue(self._cair_sobre(jogo, esqueleto, altura, segurar))
                    A.simular(jogo, 0.1, pular_segurado=segurar)
                    self.assertEqual(jogo.heroi.vida, C.VIDA_MAX)

    def test_pisar_no_ciclope_nao_machuca_o_heroi(self):
        mapa = [" " * 16] * 8 + ["  P      C   F  ", "#" * 16]
        jogo = A.criar_jogo(mapa)
        A.simular(jogo, 0.3)
        chefe = jogo.chefe
        self.assertTrue(self._cair_sobre(jogo, chefe, 40, False))
        A.simular(jogo, 0.1)
        self.assertEqual(jogo.heroi.vida, C.VIDA_MAX)

    def test_cair_encostando_na_lateral_do_inimigo_causa_dano(self):
        jogo = A.criar_jogo(self.MAPA_ALTO)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        A.simular(jogo, 0.3)
        heroi = jogo.heroi
        heroi.invencivel = 0
        heroi.x = esqueleto.x - heroi.w + 6       # encostado do lado esquerdo
        heroi.y = esqueleto.y + 30 - heroi.h      # base já abaixo do topo dele
        heroi.vy = 200
        A.simular(jogo, 0.05)
        self.assertLess(heroi.vida, C.VIDA_MAX)
        self.assertEqual(esqueleto.vida, esqueleto.VIDA)

    def test_encostar_no_inimigo_causa_dano(self):
        jogo = A.criar_jogo(self.MAPA)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        jogo.heroi.invencivel = 0
        A.simular(jogo, 0.5, direita=True)
        self.assertLess(jogo.heroi.vida, C.VIDA_MAX)

    def test_ataque_quebra_anfora_e_solta_orbes(self):
        mapa = [
            "          ",
            "          ",
            "  PX    F ",
            "##########",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.heroi.direcao = 1
        jogo.atualizar(A.DT, Entrada(atacar=True))
        A.simular(jogo, 0.3)
        self.assertEqual(jogo.nivel.tile(3, 2), " ")
        self.assertGreaterEqual(len(jogo.orbes_mapa), 2)


class TestItens(unittest.TestCase):
    def test_orbes_suficientes_dao_uma_vida_extra(self):
        jogo = A.criar_jogo()
        for _ in range(C.ORBES_POR_VIDA):
            jogo.coletar_orbe_vermelho()
        self.assertEqual(jogo.vidas, C.VIDAS_INICIAIS + 1)
        self.assertEqual(jogo.pontos, C.ORBES_POR_VIDA * C.PONTOS_ORBE)

    def test_coletar_orbe_no_mapa(self):
        mapa = [
            "          ",
            "          ",
            "  Pooo  F ",
            "##########",
        ]
        jogo = A.criar_jogo(mapa)
        A.simular(jogo, 1.0, direita=True)
        self.assertEqual(jogo.orbes, 3)
        self.assertEqual(len(jogo.orbes_mapa), 0)

    def test_orbe_verde_cura_sem_passar_do_maximo(self):
        mapa = [
            "          ",
            "          ",
            "  Pg    F ",
            "##########",
        ]
        jogo = A.criar_jogo(mapa)
        jogo.heroi.vida = C.VIDA_MAX - 1
        A.simular(jogo, 0.6, direita=True)
        self.assertEqual(jogo.heroi.vida, C.VIDA_MAX)

    def test_checkpoint_muda_o_ponto_de_renascer(self):
        mapa = [
            "          ",
            "          ",
            "  P  K  F ",
            "##########",
        ]
        jogo = A.criar_jogo(mapa)
        inicio = jogo.ponto_renascer
        A.simular(jogo, 1.0, direita=True)
        self.assertNotEqual(jogo.ponto_renascer, inicio)
        self.assertTrue(jogo.altares[0].ativo)


class TestFaseEVitoria(unittest.TestCase):
    MAPA_CURTO = [
        "      ",
        "      ",
        "  PF  ",
        "######",
    ]

    def test_portal_conclui_fase_e_proxima_carrega(self):
        jogo = A.criar_jogo(self.MAPA_CURTO, A.MAPA_PLANO)
        A.simular(jogo, 0.6, direita=True)
        self.assertEqual(jogo.estado, Estado.FASE_CONCLUIDA)
        self.assertGreater(jogo.pontos, 0)
        jogo.atualizar(A.DT, Entrada(confirmar=True))
        self.assertEqual(jogo.estado, Estado.JOGANDO)
        self.assertEqual(jogo.indice_fase, 1)

    def test_portal_da_ultima_fase_da_vitoria(self):
        jogo = A.criar_jogo(self.MAPA_CURTO)
        A.simular(jogo, 0.6, direita=True)
        self.assertEqual(jogo.estado, Estado.VITORIA)

    def test_chefe_vivo_tranca_o_portal(self):
        mapa = [
            "                    ",
            "                    ",
            "                    ",
            "  PF            C   ",
            "####################",
        ]
        jogo = A.criar_jogo(mapa)
        A.simular(jogo, 0.6, direita=True)
        self.assertTrue(jogo.portal.travado)
        self.assertEqual(jogo.estado, Estado.JOGANDO)
        jogo.chefe.vivo = False
        jogo.heroi.x = jogo.portal.rect.centerx - jogo.heroi.w / 2
        A.simular(jogo, 0.1)
        self.assertEqual(jogo.estado, Estado.VITORIA)

    def test_chefe_reinicia_quando_o_heroi_morre(self):
        mapa = [
            "                    ",
            "                    ",
            "                    ",
            "  P        C     F  ",
            "####################",
        ]
        jogo = A.criar_jogo(mapa)
        A.simular(jogo, 0.5)
        jogo.chefe.vida = 3
        jogo.perder_vida()
        self.assertEqual(jogo.chefe.vida, jogo.chefe.VIDA)
        self.assertEqual(jogo.chefe.estado, "dormindo")


class TestChefe(unittest.TestCase):
    MAPA = [" " * 40] * 8 + [("  P" + " " * 16 + "C").ljust(38) + "F ", "#" * 40]

    def _jogo(self):
        jogo = A.criar_jogo(self.MAPA)
        A.simular(jogo, 0.2)
        return jogo, jogo.chefe, jogo.heroi

    def test_investida_que_erra_deixa_o_ciclope_atordoado(self):
        jogo, chefe, heroi = self._jogo()
        heroi.x = 2 * C.TILE
        chefe.estado, chefe.direcao, chefe.timer = "investida", 1, 0.05  # corre para longe do herói
        A.simular(jogo, 0.1)
        self.assertEqual(chefe.estado, "atordoado")

    def test_investida_acerta_o_heroi_uma_vez_so(self):
        jogo, chefe, heroi = self._jogo()
        heroi.x = chefe.x - 60
        heroi.invencivel = 0
        chefe.estado, chefe.direcao, chefe.timer = "investida", -1, C.CICLOPE_INVESTIDA_TEMPO
        A.simular(jogo, 0.3)
        self.assertEqual(heroi.vida, C.VIDA_MAX - chefe.DANO)
        self.assertNotEqual(chefe.estado, "investida")
        A.simular(jogo, 1.4)
        self.assertGreaterEqual(heroi.vida, C.VIDA_MAX - chefe.DANO)

    def test_pisar_no_ciclope_tira_o_heroi_de_cima(self):
        jogo, chefe, heroi = self._jogo()
        heroi.x = chefe.centro_x - heroi.w / 2
        heroi.y = chefe.y - heroi.h - 20
        heroi.vy = 200
        heroi.invencivel = 0
        A.simular(jogo, 0.6)
        self.assertGreater(abs(heroi.centro_x - chefe.centro_x), chefe.w / 2)
        self.assertEqual(heroi.vida, C.VIDA_MAX)

    def test_golpe_causa_pausa_curta(self):
        jogo = A.criar_jogo(TestCombate.MAPA)
        esqueleto = jogo.inimigos[0]
        esqueleto.velocidade = 0
        jogo.heroi.direcao = 1
        jogo.atualizar(A.DT, Entrada(atacar=True))
        A.simular(jogo, 0.08)
        self.assertGreater(jogo.congelar_t, 0)


class TestLimites(unittest.TestCase):
    def test_particulas_tem_teto_e_sao_removidas(self):
        jogo = A.criar_jogo()
        jogo._adicionar_particulas([Particula(0, 0, 0, 0, (255, 0, 0), 0.5) for _ in range(1000)])
        self.assertLessEqual(len(jogo.particulas), C.MAX_PARTICULAS)
        A.simular(jogo, 1.0)
        self.assertEqual(len(jogo.particulas), 0)

    def test_projeteis_somem_ao_bater_ou_expirar(self):
        jogo = A.criar_jogo()
        jogo.heroi.x = 0
        jogo.adicionar_projetil(criar_lanca(10 * C.TILE, 4 * C.TILE, 1))  # vai até a parede direita
        A.simular(jogo, C.VIDA_PROJETIL + 0.5)
        self.assertEqual(len(jogo.projeteis), 0)


if __name__ == "__main__":
    unittest.main()
