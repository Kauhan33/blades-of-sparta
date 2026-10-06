# Plano de adoção — Claude Code Game Studios

> **Gerado em**: 2026-10-05
> **Fase do projeto**: Produção (jogo completo e funcional; 51 testes passando)
> **Engine**: Python 3.12 + Pygame 2.6.1 — fora das engines suportadas pelo template (Godot/Unity/Unreal); `engine.name` fica vazio de propósito
> **Versão do template**: framework 1.1.2
> **Modo**: rigor `minimal` · revisão `solo` · automação `collaborative` (padrões — `/start` nunca rodou)

Siga os passos em ordem e marque cada item ao concluir.
Rode `/adopt` de novo a qualquer momento para conferir o que falta.

No modo `minimal` não se espera GDD, ADR nem especificação de UX: o registro de
design é um único arquivo, `design/game-brief.md`. O código **não** precisa ser
reescrito em nenhum passo deste plano.

---

## Passo 1: Lacunas bloqueantes

Nenhuma. O conversor de configuração v1.0 → v1.1 respondeu "Nothing to do".

---

## Passo 2: Lacunas de prioridade alta

### 2.1 Criar o game brief (`design/game-brief.md`)

**Problema:** no modo `minimal` o brief é o único documento de design; sem ele,
`/create-stories`, `/dev-story` e `/story-done` não têm de onde tirar critérios de aceite.
**Correção:** `/reverse-document` (ou redação assistida) a partir de
`docs/MINI_PROJETO.md` e `README.md`, seguindo `.claude/docs/templates/game-brief.md`
(pitch, core loop, objetivo e fail state, MVP, fora de escopo, ordem de construção).
Documentar só o que já existe — não inventar recursos.
**Tempo:** 30 min
- [x] `design/game-brief.md` criado e revisado (2026-10-05)

### 2.2 Registrar a stack Python/Pygame

**Problema:** o template só conhece Godot, Unity e Unreal; sem registro, skills e agentes
roteiam código para especialistas que não se aplicam.
**Correção:** `CLAUDE.md` já descreve a stack corretamente (verificado em 2026-10-05).
`.claude/docs/technical-preferences.md` foi preenchido com linguagem, renderização,
física, plataforma, convenções de nome, metas de desempenho, `unittest` e o
roteamento de especialistas (lead-programmer / gameplay-programmer / ui-programmer /
ai-programmer). **Não** rodar `/setup-engine`.
**Tempo:** feito
- [x] `CLAUDE.md` — seção Technology Stack com Python/Pygame
- [x] `technical-preferences.md` — campos preenchidos (2026-10-05)

---

## Passo 3: Infraestrutura

Não faz parte do caminho `minimal`: a ordem de construção do brief é o plano
(sem `tr-registry`, manifesto de controle, `sprint-status.yaml` nem `/gate-check`).
Próximo passo depois do brief: `/create-stories` para as melhorias aprovadas.

---

## Passo 4: Lacunas médias

### 4.1 Convenções de nome
Registradas em `technical-preferences.md` (PascalCase em português para classes,
snake_case em português para variáveis/arquivos, MAIÚSCULAS em `jogo/config.py`).
- [x] Feito

### 4.2 Metas de desempenho
Registradas: 60 FPS, `dt` limitado a 1/30 s, teto de 400 partículas.
- [x] Feito

### 4.3 Testes e CI
**Problema:** o padrão de testes do template só cita os comandos de CI de Godot/Unity/Unreal,
e espera `tests/unit/` e `tests/integration/`; o projeto usa `unittest` com os testes em `tests/`.
**Correção:** manter a estrutura atual (é o padrão do `unittest discover`).
Opcional: workflow do GitHub Actions rodando
`python -m unittest discover -s tests` com `SDL_VIDEODRIVER=dummy`.
**Tempo:** 15 min (opcional)
- [x] Framework registrado em `technical-preferences.md`
- [ ] (opcional) `.github/workflows/testes.yml`

---

## Passo 5: Melhorias opcionais

### 5.1 Pasta de evidências de QA
O padrão pede capturas retidas em `production/qa/evidence/`; hoje elas estão em
`docs/img/` (geradas por `tools/capturar_telas.py`). Basta apontar a evidência das
próximas histórias de UI/visual para `docs/img/` ou gerar cópias em `production/qa/evidence/`.
**Tempo:** 5 min
- [ ] Decidir onde ficam as evidências

### 5.2 Checkpoint de sessão
Criar `production/session-state/active.md` (ignorado pelo git) para retomar o trabalho
depois de compactação ou `/clear`.
**Tempo:** 5 min
- [ ] `active.md` criado

### 5.3 Bloco `modes` no `project.yaml`
O `/start` nunca rodou, então `modes.rigor` e `modes.automation` estão nos padrões
(`minimal` / `collaborative`), que servem bem a um projeto acadêmico solo.
Fixar só se quiser mudar o comportamento.
- [ ] (opcional) fixar `modes.rigor` / `modes.automation`

### 5.4 Aviso falso de "projeto novo"
O hook de início de sessão diz "No engine configured, no game concept, no source code"
porque procura código em `src/`. É um falso positivo: o código está em `jogo/`. Ignorar.

---

## Histórias existentes

Não há histórias em `production/epics/`. Quando forem criadas, as novas verificações
de formato passam automaticamente nos campos ausentes.

---

## Rodar de novo

Rode `/adopt` depois do Passo 2.1 para confirmar que não restam lacunas altas.
