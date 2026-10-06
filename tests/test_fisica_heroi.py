"""Testes de movimento, gravidade, pulo, colisão e dano do herói."""
import unittest

import auxiliar as A
from jogo import config as C
from jogo.entrada import Entrada
from jogo.heroi import Heroi


def heroi_no_chao(nivel, coluna=4):
    heroi = Heroi(coluna * C.TILE, 0)
    A.simular(heroi, 1.0, nivel)
    return heroi


class TestGravidadeEChao(unittest.TestCase):
    def test_cai_e_para_exatamente_sobre_o_chao(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        self.assertTrue(heroi.no_chao)
        self.assertAlmostEqual(heroi.base, A.CHAO_PLANO)
        self.assertEqual(heroi.vy, 0)

    def test_nao_atravessa_o_chao_mesmo_com_dt_enorme(self):
        jogo = A.criar_jogo()
        jogo.heroi.y = 0
        for _ in range(30):
            jogo.atualizar(5.0, Entrada())  # dt é limitado a DT_MAX internamente
        self.assertLessEqual(jogo.heroi.base, A.CHAO_PLANO + 0.01)
        self.assertTrue(jogo.heroi.no_chao)

    def test_nao_sai_pela_borda_esquerda_do_mapa(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel, coluna=1)
        A.simular(heroi, 2.0, nivel, esquerda=True)
        self.assertGreaterEqual(heroi.x, 0)


class TestPulo(unittest.TestCase):
    def test_pula_quando_esta_no_chao(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        self.assertLess(heroi.vy, 0)
        self.assertFalse(heroi.no_chao)

    def test_pulo_duplo_no_ar(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        A.simular(heroi, 0.25, nivel, pular_segurado=True)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        self.assertLess(heroi.vy, -C.FORCA_PULO_DUPLO + C.GRAVIDADE * A.DT * 1.01)

    def test_nao_ha_terceiro_pulo_no_ar(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        A.simular(heroi, 0.2, nivel, pular_segurado=True)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)  # pulo duplo
        A.simular(heroi, 0.2, nivel, pular_segurado=True)
        vy_antes = heroi.vy
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        self.assertGreater(heroi.vy, vy_antes)  # só a gravidade agiu

    def test_pulo_duplo_recarrega_ao_pousar(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        for _ in range(2):
            heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
            A.simular(heroi, 0.2, nivel, pular_segurado=True)
            heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
            self.assertLess(heroi.vy, -C.FORCA_PULO_DUPLO + C.GRAVIDADE * A.DT * 1.01)
            A.simular(heroi, 1.5, nivel)
            self.assertTrue(heroi.no_chao)

    def test_soltar_o_botao_corta_o_pulo(self):
        nivel = A.nivel(A.MAPA_PLANO)
        alto = heroi_no_chao(nivel)
        baixo = heroi_no_chao(nivel)
        for heroi, segurando in ((alto, True), (baixo, False)):
            heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
            menor_y = heroi.y
            for _ in range(60):
                heroi.atualizar(A.DT, Entrada(pular_segurado=segurando), nivel)
                menor_y = min(menor_y, heroi.y)
            heroi.altura_maxima = A.CHAO_PLANO - heroi.h - menor_y
        self.assertGreater(alto.altura_maxima, baixo.altura_maxima)


class TestPlataformaUmaVia(unittest.TestCase):
    MAPA = [
        "          ",
        "          ",
        "          ",
        "   ----   ",
        "  P     F ",
        "##########",
    ]

    def test_atravessa_por_baixo_pousa_por_cima_e_desce(self):
        nivel = A.nivel(self.MAPA)
        heroi = heroi_no_chao(nivel, coluna=4)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        A.simular(heroi, 1.0, nivel, pular_segurado=True)
        self.assertTrue(heroi.no_chao)
        self.assertAlmostEqual(heroi.base, 3 * C.TILE)  # em cima da plataforma
        A.simular(heroi, 1.0, nivel, baixo=True)
        self.assertAlmostEqual(heroi.base, A.CHAO_PLANO)  # desceu de volta ao chão


    def test_pulo_duplo_alcanca_plataforma_de_tres_tiles(self):
        # Sem o pulo duplo o pico fica em ~139 px e a plataforma está a 144 px.
        mapa = [
            "          ",
            "          ",
            "          ",
            "   ----   ",
            "          ",
            "  P     F ",
            "##########",
        ]
        nivel = A.nivel(mapa)
        heroi = Heroi(4 * C.TILE, 6 * C.TILE - Heroi.ALTURA)  # no chão, embaixo da plataforma
        A.simular(heroi, 0.1, nivel)
        self.assertTrue(heroi.no_chao)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        A.simular(heroi, 0.3, nivel, pular_segurado=True)
        heroi.atualizar(A.DT, Entrada(pular=True, pular_segurado=True), nivel)
        A.simular(heroi, 1.5, nivel, pular_segurado=True)
        self.assertTrue(heroi.no_chao)
        self.assertAlmostEqual(heroi.base, 3 * C.TILE)


class TestEsquiva(unittest.TestCase):
    def test_esquiva_avanca_rapido_para_frente(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel, coluna=3)
        x0 = heroi.x
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        A.simular(heroi, C.ESQUIVA_DURACAO, nivel)
        self.assertGreater(heroi.x - x0, C.ESQUIVA_VEL * C.ESQUIVA_DURACAO * 0.8)

    def test_esquiva_ignora_dano(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertFalse(heroi.receber_dano(1, heroi.centro_x + 10))
        self.assertEqual(heroi.vida, C.VIDA_MAX)

    def test_esquiva_tem_recarga(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel, coluna=2)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        A.simular(heroi, C.ESQUIVA_DURACAO + 0.05, nivel)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertFalse(heroi.esquivando)
        A.simular(heroi, C.ESQUIVA_RECARGA, nivel)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertTrue(heroi.esquivando)

    def test_so_uma_esquiva_no_ar_ate_pousar(self):
        mapa = ["                    "] * 30 + ["  P              F  ", "####################"]
        nivel = A.nivel(mapa)
        heroi = Heroi(2 * C.TILE, 0)  # caindo de bem alto
        A.simular(heroi, 0.1, nivel)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertTrue(heroi.esquivando)
        A.simular(heroi, C.ESQUIVA_RECARGA + 0.01, nivel)
        self.assertFalse(heroi.no_chao)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertFalse(heroi.esquivando)
        A.simular(heroi, 2.0, nivel)
        heroi.atualizar(A.DT, Entrada(esquivar=True), nivel)
        self.assertTrue(heroi.esquivando)  # pousou: recarregou


class TestEntrada(unittest.TestCase):
    def test_esquerda_e_direita_juntas_se_anulam(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        A.simular(heroi, 0.5, nivel, esquerda=True, direita=True)
        self.assertEqual(heroi.vx, 0)


class TestDano(unittest.TestCase):
    def test_invencibilidade_impede_dano_seguido(self):
        heroi = Heroi(0, 0)
        self.assertTrue(heroi.receber_dano(1, 100))
        self.assertFalse(heroi.receber_dano(1, 100))
        self.assertEqual(heroi.vida, C.VIDA_MAX - 1)

    def test_dano_volta_a_valer_apos_a_invencibilidade(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.receber_dano(1, 0)
        A.simular(heroi, C.TEMPO_INVENCIVEL + 0.1, nivel)
        self.assertTrue(heroi.receber_dano(1, 0))
        self.assertEqual(heroi.vida, C.VIDA_MAX - 2)

    def test_dano_empurra_para_longe_da_origem(self):
        heroi = Heroi(100, 0)
        heroi.receber_dano(1, origem_x=0)
        self.assertGreater(heroi.vx, 0)

    def test_vida_zero_mata_e_nunca_fica_negativa(self):
        heroi = Heroi(0, 0)
        heroi.receber_dano(C.VIDA_MAX + 3, 0)
        self.assertEqual(heroi.vida, 0)
        self.assertTrue(heroi.morto)


class TestAtaque(unittest.TestCase):
    def test_hitbox_aparece_na_frente_durante_o_golpe(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.direcao = 1
        self.assertIsNone(heroi.hitbox_ataque())
        heroi.atualizar(A.DT, Entrada(atacar=True), nivel)
        A.simular(heroi, 0.06, nivel)
        golpe = heroi.hitbox_ataque()
        self.assertIsNotNone(golpe)
        self.assertGreaterEqual(golpe.left, int(heroi.centro_x))
        A.simular(heroi, 0.4, nivel)
        self.assertIsNone(heroi.hitbox_ataque())

    def test_furia_dobra_o_dano(self):
        heroi = Heroi(0, 0)
        heroi.combo = 0
        normal = heroi.dano_golpe()
        heroi.furia_t = 1.0
        self.assertEqual(heroi.dano_golpe(), normal * 2)

    def test_apertar_cedo_guarda_o_proximo_golpe(self):
        # Buffer de ataque: o aperto antes do fim do golpe não se perde.
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        heroi.atualizar(A.DT, Entrada(atacar=True), nivel)
        A.simular(heroi, C.ATAQUE_DURACAO - 0.05, nivel)
        heroi.atualizar(A.DT, Entrada(atacar=True), nivel)  # cedo demais
        A.simular(heroi, 0.15, nivel)
        self.assertTrue(heroi.atacando)
        self.assertEqual(heroi.combo, 1)

    def test_combo_completo_apertando_no_ritmo(self):
        nivel = A.nivel(A.MAPA_PLANO)
        heroi = heroi_no_chao(nivel)
        combos = []
        for _ in range(3):
            heroi.atualizar(A.DT, Entrada(atacar=True), nivel)
            combos.append(heroi.combo)
            A.simular(heroi, 0.5, nivel)
        self.assertEqual(combos, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
