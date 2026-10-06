# Technical Preferences

<!-- project.yaml at the repo root is the machine-readable source of truth for
     engine, specialists, naming, performance, platform, and testing.framework.
     This file is the human-readable LEGACY FALLBACK: agents and skills resolve
     each key from project.yaml first and fall back here only when the
     project.yaml key is absent. /setup-engine dual-writes both.
     Forbidden patterns and allowed libraries are NOT migrated — they live only
     in this file. Populated by /setup-engine; updated as decisions are made. -->

## Engine & Language

- **Engine**: Pygame 2.6.1 (SDL 2.28) — biblioteca, não engine suportada pelo template (`engine.name` fica vazio de propósito)
- **Language**: Python 3.12
- **Rendering**: 2D por software (`pygame.draw` + `Surface`), arte 100% procedural em `jogo/desenho.py`
- **Physics**: própria — colisão AABB eixo a eixo contra grade de tiles (`jogo/fisica.py`)

## Input & Platform

<!-- Written by /setup-engine. Read by /ux-design, /ux-review, /test-setup, /team-ui, and /dev-story -->
<!-- to scope interaction specs, test helpers, and implementation to the correct input methods. -->

- **Target Platforms**: PC Windows (executável PyInstaller em `dist/`); roda em qualquer SO com Python
- **Input Methods**: Teclado
- **Primary Input**: Teclado
- **Gamepad Support**: None
- **Touch Support**: None
- **Platform Notes**: janela 960×540; textos do jogo em pt-BR

## Naming Conventions

- **Classes**: PascalCase em português (`Heroi`, `PlataformaMovel`)
- **Variables**: snake_case em português (`buffer_pulo`, `no_chao`); privados com `_`
- **Signals/Events**: N/A (sem sinais; eventos sonoros do quadro em listas `eventos`)
- **Files**: snake_case `.py` em português, um módulo por sistema em `jogo/`
- **Scenes/Prefabs**: N/A — fases são mapas ASCII em `jogo/nivel.py`
- **Constants**: MAIÚSCULAS em `jogo/config.py` (importado como `C`)

## Performance Budgets

- **Target Framerate**: 60 FPS (`Clock.tick(60)`); `dt` limitado a 1/30 s
- **Frame Budget**: 16,6 ms
- **Draw Calls**: N/A (Pygame); teto de 400 partículas
- **Memory Ceiling**: não definido (jogo pequeno)

## Testing

- **Framework**: `unittest` (biblioteca padrão) — `python -m unittest discover -s tests`, sem janela via `SDL_VIDEODRIVER=dummy`
- **Minimum Coverage**: não definido
- **Required Tests**: Balance formulas, gameplay systems, networking (if applicable)

## Forbidden Patterns

<!-- Add patterns that should never appear in this project's codebase -->
- [None configured yet — add as architectural decisions are made]

## Allowed Libraries / Addons

<!-- Add approved third-party dependencies here -->
- `pygame>=2.5` (única dependência de execução)
- `pyinstaller` (só para gerar o executável — `tools/gerar_executavel.py`)

## Architecture Decisions Log

<!-- Quick reference linking to full ADRs in docs/architecture/ -->
- [No ADRs yet — use /architecture-decision to create one]

## Engine Specialists

<!-- Written by /setup-engine when engine is configured. -->
<!-- Read by /code-review, /architecture-decision, /architecture-review, and team skills -->
<!-- to know which specialist to spawn for engine-specific validation. -->

- **Primary**: lead-programmer (não há especialista de Pygame; os de Godot/Unity/Unreal NÃO se aplicam)
- **Language/Code Specialist**: gameplay-programmer
- **Shader Specialist**: N/A (sem shaders; arte procedural → technical-artist se preciso)
- **UI Specialist**: ui-programmer
- **Additional Specialists**: ai-programmer (inimigos e Ciclope), qa-tester
- **Routing Notes**: projeto Python/Pygame — nunca rotear para godot-*, unity-* ou ue-*

### File Extension Routing

<!-- Skills use this table to select the right specialist per file type. -->
<!-- If a row says [TO BE CONFIGURED], fall back to Primary for that file type. -->

| File Extension / Type | Specialist to Spawn |
|-----------------------|---------------------|
| Game code (primary language) | gameplay-programmer |
| Shader / material files | N/A |
| UI / screen files (`jogo/hud.py`) | ui-programmer |
| Level files (`jogo/nivel.py`) | level-designer + gameplay-programmer |
| Native extension / plugin files | N/A |
| General architecture review | Primary |
