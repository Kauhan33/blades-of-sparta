"""Testes dos mapas das fases, do carregamento de recursos e um teste de fumaça."""
import os
import re
import sys
import unittest

import auxiliar as A
from jogo.config import ORBES_POR_VIDA, TILE
from jogo.entrada import Entrada
from jogo.jogo import Estado
from jogo.nivel import FASES, validar_mapa
from jogo.recursos import Audio, carregar_imagem

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))


class TestMapas(unittest.TestCase):
    def test_todas_as_fases_sao_validas(self):
        for fase in FASES:
            with self.subTest(fase=fase["nome"]):
                validar_mapa(fase["mapa"])
                nivel = A.nivel(fase["mapa"], fase["nome"], fase["tema"])
                self.assertGreater(nivel.largura_px, 960)

    def test_orbes_dos_mapas_bastam_para_uma_vida_extra(self):
        # Sem contar as ânforas: a regra da vida extra precisa ser alcançável.
        total = sum("".join(fase["mapa"]).count("o") for fase in FASES)
        self.assertGreaterEqual(total, ORBES_POR_VIDA)

    def test_todo_campo_de_espinhos_pode_ser_pulado(self):
        # O pulo passa no máximo ~195 px acima da altura de dano: 3 tiles de espinho.
        for fase in FASES:
            with self.subTest(fase=fase["nome"]):
                maior = max((len(t) for linha in fase["mapa"] for t in re.findall(r"\^+", linha)), default=0)
                self.assertLessEqual(maior, 3)

    def test_checkpoints_no_maximo_a_60_colunas(self):
        # Morrer não pode custar mais que ~60 tiles de caminho refeito.
        for fase in FASES:
            with self.subTest(fase=fase["nome"]):
                colunas = sorted(c for linha in fase["mapa"] for c, t in enumerate(linha) if t in "PKF")
                self.assertLessEqual(max(b - a for a, b in zip(colunas, colunas[1:])), 60)

    def test_arena_do_chefe_sem_fosso(self):
        # Um vão no chão vira esconderijo: o Ciclope não atravessa andando.
        chao = FASES[-1]["mapa"][-2]
        self.assertNotIn(" ", chao)

    def test_ultima_fase_tem_o_chefe(self):
        self.assertIn("C", "".join(FASES[-1]["mapa"]))

    def test_mapa_sem_inicio_e_recusado(self):
        with self.assertRaises(ValueError):
            validar_mapa(["   F ", "#####"])

    def test_mapa_com_linhas_de_tamanhos_diferentes_e_recusado(self):
        with self.assertRaises(ValueError):
            validar_mapa([" P F ", "####"])

    def test_caractere_desconhecido_e_recusado(self):
        with self.assertRaises(ValueError):
            validar_mapa([" P F ", "##?##"])

    def test_laterais_sao_paredes_e_abaixo_e_vazio(self):
        nivel = A.nivel(A.MAPA_PLANO)
        self.assertTrue(nivel.solido(-1, 2))
        self.assertTrue(nivel.solido(nivel.largura, 2))
        self.assertFalse(nivel.solido(3, nivel.altura + 1))

    def test_coordenadas_de_mundo_do_inicio(self):
        jogo = A.criar_jogo()
        coluna, linha = jogo.nivel.inicio
        self.assertEqual((coluna, linha), (2, 4))
        self.assertAlmostEqual(jogo.heroi.base, (linha + 1) * TILE)


class TestRecursos(unittest.TestCase):
    def test_imagem_inexistente_vira_substituto_do_tamanho_pedido(self):
        imagem = carregar_imagem("nao_existe.png", (40, 20))
        self.assertEqual(imagem.get_size(), (40, 20))

    def test_audio_desligado_ou_som_desconhecido_nao_quebra(self):
        Audio(ativo=False).tocar("qualquer")
        audio = Audio()
        audio.tocar("pulo")
        audio.tocar("som_que_nao_existe")


class TestFumaca(unittest.TestCase):
    """Joga cada fase por alguns segundos com entradas variadas, desenhando a tela."""

    def test_todas_as_fases_rodam_sem_erro(self):
        jogo = A.criar_jogo(*[f["mapa"] for f in FASES])
        for indice in range(len(FASES)):
            jogo.carregar_fase(indice)
            jogo.estado = Estado.JOGANDO
            jogo.vidas = 99  # continua jogando mesmo morrendo, para cobrir a fase toda
            for quadro in range(900):
                entrada = Entrada(direita=quadro % 240 < 200, esquerda=quadro % 240 >= 220,
                                  pular=quadro % 45 == 0, pular_segurado=quadro % 45 < 20,
                                  atacar=quadro % 20 == 0, furia=quadro % 300 == 0)
                jogo.atualizar(A.DT, entrada)
                if quadro % 30 == 0:
                    jogo.desenhar()
                if jogo.estado != Estado.JOGANDO:
                    break
            self.assertIn(jogo.estado, set(Estado))
            self.assertGreaterEqual(jogo.vidas, 0)

    def test_bot_consegue_terminar_cada_fase(self):
        import bot_percurso
        for indice, fase in enumerate(FASES):
            with self.subTest(fase=fase["nome"]):
                resultado, _, _ = bot_percurso.percorrer(indice)
                self.assertIn(resultado, (Estado.FASE_CONCLUIDA, Estado.VITORIA))

    def test_todas_as_telas_desenham(self):
        jogo = A.criar_jogo()
        for estado in Estado:
            jogo.estado = estado
            jogo.desenhar()


if __name__ == "__main__":
    unittest.main()
