"""Carregamento seguro de recursos: imagens, fontes e sons.

Nenhum arquivo externo é obrigatório. Se uma imagem ou som não for
encontrado (ou estiver corrompido), o jogo usa um substituto e continua
rodando — tratamento do erro "arquivo não encontrado" pedido na aula.
"""
import math
import os
import random
import sys
from array import array

import pygame

if getattr(sys, "frozen", False):
    # Executável gerado pelo PyInstaller: procura assets/ ao lado do .exe.
    RAIZ = os.path.dirname(os.path.abspath(sys.executable))
else:
    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_avisos_emitidos = set()
_fontes = {}


def caminho(*partes):
    """Monta um caminho absoluto a partir da raiz do projeto.

    No executável, um arquivo ao lado do .exe tem prioridade; se não existir,
    usa a cópia embutida pelo PyInstaller (pasta temporária sys._MEIPASS).
    """
    arquivo = os.path.join(RAIZ, *partes)
    embutida = getattr(sys, "_MEIPASS", None)
    if embutida and not os.path.exists(arquivo):
        return os.path.join(embutida, *partes)
    return arquivo


def avisar(mensagem):
    """Mostra um aviso no console apenas uma vez por mensagem."""
    if mensagem not in _avisos_emitidos:
        _avisos_emitidos.add(mensagem)
        print(f"[aviso] {mensagem}")


def carregar_imagem(nome, tamanho=None, cor_substituta=(255, 0, 255)):
    """Carrega assets/imagens/<nome>; em caso de falha devolve um retângulo colorido."""
    arquivo = caminho("assets", "imagens", nome)
    try:
        imagem = pygame.image.load(arquivo)
        if pygame.display.get_surface() is not None:
            imagem = imagem.convert_alpha()
        if tamanho:
            imagem = pygame.transform.smoothscale(imagem, tamanho)
        return imagem
    except (FileNotFoundError, pygame.error) as erro:
        avisar(f"imagem '{nome}' indisponível ({erro}); usando substituto")
        substituta = pygame.Surface(tamanho or (32, 32), pygame.SRCALPHA)
        substituta.fill(cor_substituta)
        return substituta


FONTES_SISTEMA = "georgia,palatinolinotype,timesnewroman,serif"


def fonte(tamanho, negrito=False):
    """Fonte do texto corrido, com cache; cai para a padrão do pygame se a do sistema faltar."""
    chave = (tamanho, negrito)
    if chave not in _fontes:
        try:
            _fontes[chave] = pygame.font.SysFont(FONTES_SISTEMA, tamanho, bold=negrito)
        except Exception as erro:  # fonte do sistema ausente ou módulo de fontes quebrado
            avisar(f"fonte do sistema indisponível ({erro}); usando a padrão")
            _fontes[chave] = pygame.font.Font(None, tamanho)
    return _fontes[chave]


def fonte_titulo(tamanho, arquivo="Cinzel.ttf"):
    """Fonte de inscrição (Cinzel, em assets/fontes) para títulos e HUD.

    Se o arquivo faltar ou estiver corrompido, avisa uma vez e usa a fonte do sistema.
    """
    chave = ("titulo", arquivo, tamanho)
    if chave not in _fontes:
        try:
            f = pygame.font.Font(caminho("assets", "fontes", arquivo), tamanho)
            f.set_bold(True)  # traço mais grosso: o dourado com contorno ganha corpo
            _fontes[chave] = f
        except (FileNotFoundError, OSError, pygame.error) as erro:
            if ("falhou", arquivo) not in _fontes:
                avisar(f"fonte '{arquivo}' indisponível ({erro}); usando a do sistema")
                _fontes[("falhou", arquivo)] = True
            _fontes[chave] = fonte(tamanho, negrito=True)
    return _fontes[chave]


class SomNulo:
    """Substituto silencioso usado quando o áudio não está disponível."""

    def play(self, *args, **kwargs):
        return None

    def set_volume(self, volume):
        return None


# nome: (freq. inicial, freq. final, duração em s, forma de onda, volume)
RECEITAS_SONS = {
    "pulo": (300, 620, 0.12, "quadrada", 0.18),
    "ataque": (1200, 300, 0.10, "ruido", 0.16),
    "acerto": (220, 70, 0.12, "quadrada", 0.28),
    "orbe": (900, 1500, 0.08, "seno", 0.25),
    "dano": (420, 90, 0.25, "serra", 0.30),
    "morte": (320, 50, 0.80, "serra", 0.30),
    "vida": (500, 1100, 0.35, "quadrada", 0.20),
    "checkpoint": (400, 900, 0.30, "seno", 0.28),
    "caixa": (180, 60, 0.18, "ruido", 0.30),
    "portal": (300, 1300, 0.60, "seno", 0.28),
    "rugido": (110, 45, 0.70, "serra", 0.40),
    "impacto": (90, 30, 0.35, "ruido", 0.40),
    "lanca": (700, 400, 0.10, "ruido", 0.14),
    "furia": (120, 480, 0.45, "serra", 0.32),
    "pisao": (260, 120, 0.10, "quadrada", 0.25),
    "pulo_duplo": (500, 950, 0.12, "quadrada", 0.16),
    "esquiva": (900, 220, 0.14, "ruido", 0.18),
    "preparo_salto": (70, 150, 0.45, "serra", 0.32),
}


class Audio:
    """Efeitos sonoros: usa assets/sons/<nome>.wav se existir, senão sintetiza."""

    def __init__(self, ativo=True):
        self.ativo = False
        self.sons = {}
        if not ativo:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.ativo = True
        except pygame.error as erro:
            avisar(f"áudio indisponível ({erro}); o jogo seguirá sem som")
            return
        for nome, receita in RECEITAS_SONS.items():
            self.sons[nome] = self._carregar_ou_sintetizar(nome, receita)

    def _carregar_ou_sintetizar(self, nome, receita):
        arquivo = caminho("assets", "sons", f"{nome}.wav")
        if os.path.exists(arquivo):
            try:
                return pygame.mixer.Sound(arquivo)
            except pygame.error as erro:
                avisar(f"som '{nome}.wav' corrompido ({erro}); usando som sintetizado")
        try:
            return self._sintetizar(*receita)
        except (pygame.error, ValueError) as erro:
            avisar(f"não foi possível gerar o som '{nome}' ({erro})")
            return SomNulo()

    @staticmethod
    def _sintetizar(freq_ini, freq_fim, duracao, onda, volume):
        taxa, formato, canais = pygame.mixer.get_init()
        if formato != -16:
            raise ValueError(f"formato de áudio {formato} não suportado")
        total = int(taxa * duracao)
        amostras = array("h")
        fase = 0.0
        sorteio = random.Random(freq_ini)  # ruído determinístico
        for i in range(total):
            t = i / total
            fase += (freq_ini + (freq_fim - freq_ini) * t) / taxa
            if onda == "quadrada":
                valor = 1.0 if (fase % 1.0) < 0.5 else -1.0
            elif onda == "serra":
                valor = 2.0 * (fase % 1.0) - 1.0
            elif onda == "ruido":
                valor = sorteio.uniform(-1.0, 1.0)
            else:
                valor = math.sin(fase * math.tau)
            envelope = t / 0.02 if t < 0.02 else (1.0 - t) ** 2
            amostra = int(valor * envelope * volume * 32767)
            for _ in range(canais):
                amostras.append(amostra)
        return pygame.mixer.Sound(buffer=amostras.tobytes())

    def tocar(self, nome):
        """Toca um efeito; nomes desconhecidos são ignorados sem erro."""
        self.sons.get(nome, SomNulo()).play()
