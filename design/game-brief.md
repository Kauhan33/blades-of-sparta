# Game Brief: Blades of Sparta

> **Status**: Implemented · fonte: docs/MINI_PROJETO.md (2026-10-05)

**One-sentence pitch:** Um plataforma 2D estilo Mario em que um guerreiro espartano com lâminas acorrentadas atravessa a mitologia grega, abrindo caminho entre esqueletos e harpias até derrotar o Ciclope Polifemo.

## Core loop
- Atravessar a fase pulando fossos, espinhos e lava, usando plataformas de uma via e móveis.
- Derrotar inimigos com o combo de lâminas (3 golpes) ou o pisão, e encher o medidor de Fúria Espartana.
- Coletar orbes e quebrar ânforas para ganhar pontos e vidas extras; acender altares para renascer mais perto.
- Chegar ao portal: bônus de fase e uma fase nova, mais difícil.

## Player goal & fail state — what "working" looks like
- **Vitória:** tocar o portal da fase 3, que só destranca com o Ciclope derrotado. Fase concluída = tocar o portal (+1000 pontos + 10 por segundo restante).
- **Derrota:** vida (5 segmentos) zerada, queda no fosso, lava ou tempo esgotado (300 s) custam 1 de 3 vidas; com 0 vidas, Game Over (R/Enter recomeça). Renasce no último altar com vida cheia.

## MVP — what must exist to be the game
- Física de plataforma por delta-time: gravidade, pulo variável, pulo duplo, esquiva, coyote time e buffer, plataformas de uma via e móveis.
- Combate: combo de lâminas (com buffer de ataque e hitstop), pisão, invencibilidade após dano, Fúria Espartana.
- Inimigos com IA: esqueleto (patrulha), arqueiro (lanças), harpia (voo senoidal + mergulho).
- Chefe Ciclope com máquina de estados (investida, salto com ondas de choque, atordoamento, fase de raiva).
- 3 fases em mapas ASCII: Portões de Esparta, Cavernas do Hades, Arena do Ciclope.
- Regras: vida, vidas, orbes (50 = vida extra), checkpoints, tempo limite, pontuação.
- Estados: menu, jogando, pausa, fase concluída, Game Over, vitória — com transições validadas.

## Out of scope — not building this
- Sem save, recorde persistente ou seleção de fase.
- Sem gamepad, mouse ou toque — só teclado.
- Sem multiplayer.
- Sem arquivos de arte/som obrigatórios: tudo procedural/sintetizado (assets/ é opcional, com fallback).
- Sem personagens, nomes ou marcas da franquia God of War — só inspiração de estilo.
- Sem fases além das 3 atuais.

## Build order
1. Física e colisão eixo a eixo com a grade de tiles (o núcleo do plataforma).
2. Herói: movimento, pulo e combate.
3. Inimigos comuns e regras de dano/vidas/orbes.
4. Fases 1 e 2, checkpoints e portal.
5. Chefe Ciclope e fase 3.
6. HUD, telas de estado, arte procedural e sons sintetizados.
7. Testes automatizados, bot de percurso e executável.

---
**Who it's for / what they feel:** colegas e professora da UC jogando em 10–15 minutos; sensação de poder espartano com desafio justo de plataforma.

**Art & audio direction:** "épico sombrio" — formas procedurais com contorno escuro, céus escuros com horizonte em brasa, ouro e vermelho só no que importa (herói, perigos, HUD), fonte Cinzel; sons sintetizados curtos.

**Reference game:** Super Mario Bros. (correr, pular, pisar e checkpoints em fases lineares) + o combate de God of War reduzido a um combo de 3 golpes e um medidor de fúria.
