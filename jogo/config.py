"""Constantes globais do jogo: tela, física, regras e cores."""

TITULO = "Blades of Sparta"

# Tela
LARGURA = 960
ALTURA = 540
FPS = 60
# Limite do delta-time: se o jogo travar, a física não "teleporta" objetos
# através das paredes (evita o problema de FPS instável).
DT_MAX = 1 / 30

# Mapa
TILE = 48

# Física do herói (pixels/segundo)
GRAVIDADE = 2200
VEL_MAX_QUEDA = 1100
VEL_ANDAR = 300
ACEL_CHAO = 2600
ACEL_AR = 1500
FORCA_PULO = 800
TEMPO_COYOTE = 0.10        # tempo extra para pular logo após sair da borda
TEMPO_BUFFER_PULO = 0.12   # aperto de pulo "guardado" antes de tocar o chão
PULOS_NO_AR = 1            # pulo duplo: pulos extras até tocar o chão de novo
FORCA_PULO_DUPLO = 680     # impulso do pulo no ar (um pouco menor que o do chão)
FORCA_QUIQUE = 560         # impulso ao pisar em um inimigo
TOLERANCIA_PISAO = 12      # px: no quadro anterior a base podia estar até isto abaixo do topo do inimigo

# Regras do herói
VIDA_MAX = 5
VIDAS_INICIAIS = 3
TEMPO_INVENCIVEL = 1.2
TEMPO_FERIDO = 0.30
ORBES_POR_VIDA = 50
TEMPO_FASE = 300

# Combate
ATAQUE_DURACAO = 0.28
ATAQUE_ATIVO_INICIO = 0.04
ATAQUE_ATIVO_FIM = 0.22
ATAQUE_RECARGA = 0.08
ATAQUE_ALCANCE = 84
COMBO_JANELA = 0.60        # s desde o golpe anterior para o próximo continuar o combo
BUFFER_ATAQUE = 0.15       # aperto de ataque "guardado" enquanto o golpe atual termina
FURIA_MAX = 100
FURIA_POR_GOLPE = 12
FURIA_DURACAO = 6.0
HITSTOP = 0.05             # pausa do mundo a cada acerto (sensação de impacto)
HITSTOP_FINAL = 0.09       # pausa maior no 3º golpe do combo

# Esquiva (dash)
ESQUIVA_VEL = 640
ESQUIVA_DURACAO = 0.18     # invencível durante a esquiva
ESQUIVA_RECARGA = 0.6      # e só uma esquiva no ar até pousar

# Chefe: Polifemo, o Ciclope
CICLOPE_VIDA = 20
CICLOPE_ANDAR = 75                 # px/s
CICLOPE_TEMPO_ANDANDO = 2.0        # s entre ataques
CICLOPE_TEMPO_ANDANDO_FURIOSO = 1.4
CICLOPE_RAPIDEZ_FURIOSO = 1.35     # multiplica velocidades com metade da vida
CICLOPE_PREPARO = 0.65             # aviso antes de cada ataque
CICLOPE_PREPARO_MIN = 0.55         # o aviso nunca fica mais curto que isto
CICLOPE_INVESTIDA_VEL = 430
CICLOPE_INVESTIDA_TEMPO = 1.3
CICLOPE_PULO = 780
CICLOPE_ATORDOADO_PAREDE = 1.4     # bateu na parede ou na beirada
CICLOPE_ATORDOADO_POUSO = 0.9      # depois do salto
CICLOPE_ATORDOADO_ERROU = 0.6      # a investida acabou sem acertar nada
CICLOPE_ESCORREGAR = 300           # px/s: o herói escorrega da cabeça dele
CICLOPE_ESCORREGAR_TEMPO = 0.25

# Pontuação
PONTOS_ORBE = 10
PONTOS_CAIXA = 50
PONTOS_FASE = 1000
PONTOS_POR_SEGUNDO = 10

# Limites de segurança
MAX_PARTICULAS = 400
VIDA_PROJETIL = 4.0

# Cores
PRETO = (12, 10, 14)
BRANCO = (245, 240, 230)
CINZA = (120, 116, 112)
VERMELHO = (200, 30, 30)
VERMELHO_ESCURO = (120, 14, 14)
LARANJA = (255, 140, 30)
AMARELO = (255, 210, 70)
DOURADO = (212, 168, 60)
VERDE = (60, 200, 90)
AZUL = (70, 130, 220)
PELE_ESPARTANO = (214, 208, 198)

# Paleta da interface ("épico sombrio")
CARVAO = (14, 10, 12)
SANGUE = (150, 18, 22)
BRASA = (255, 128, 40)
OURO_CLARO = (255, 232, 160)
OURO = (214, 164, 64)
OURO_ESCURO = (112, 74, 24)
OSSO = (236, 224, 200)
OSSO_APAGADO = (176, 150, 124)
METAL_OURO = (OURO_CLARO, OURO, OURO_ESCURO)          # gradiente dos títulos
METAL_SANGUE = ((255, 200, 170), (220, 70, 50), (120, 20, 16))
BARRA_VIDA = ((255, 96, 70), (206, 30, 26), (110, 10, 14))
BARRA_FURIA = ((255, 220, 120), (255, 130, 30), (170, 50, 10))
COURO = (110, 62, 34)
