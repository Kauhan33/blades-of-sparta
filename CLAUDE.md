# Claude Code Game Studios -- Game Studio Agent Architecture

Indie game development managed through 49 coordinated Claude Code subagents.
Each agent owns a specific domain, enforcing separation of concerns and quality.

## Technology Stack

- **Engine**: Pygame 2.6.1 (SDL 2.28) — custom engine, no Godot/Unity/Unreal
- **Language**: Python 3.12
- **Version Control**: Git with trunk-based development (GitHub: Kauhan33/blades-of-sparta, public)
- **Build System**: none — run with `python main.py`; deps in `requirements.txt`
- **Asset Pipeline**: procedural drawing + synthesized sounds; optional files in
  `assets/` are loaded with a safe fallback when missing
- **Tests**: `python -m unittest discover -s tests` (headless via
  `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy`)

> **Note**: The Godot/Unity/Unreal specialist agents do NOT apply to this
> project. Use the engine-agnostic agents (game-designer, level-designer,
> gameplay-programmer, qa-tester, etc.).

## Academic Context

Mini-projeto da UC Computação Gráfica e Realidade Virtual. Requirements come from
the class PDF in `docs/referencias/` (gitignored — professor's material).

**Privacy rule:** the public GitHub repo must never contain the student's full
name, RA or the professor's name. Those live only in `entrega/` (gitignored):
`entrega/dados_capa.json` feeds the PDF cover, and `python tools/gerar_pdf.py`
writes the delivery PDF to `entrega/`. Never commit PDFs or `entrega/`.
User-facing text, docs and in-game text are in **Portuguese (pt-BR)**.

## Project Structure

@.claude/docs/directory-structure.md

**Override for this project (Python/Pygame):** the code root is `jogo/`
(Python package) with entry point `main.py`; tests live in `tests/`.
Read any `src/…` path in the template docs as `jogo/…`.


## Technical Preferences

`project.yaml` at the repo root is the primary config store — engine, specialists,
naming, platform, performance, modes. Skills resolve it via `resolve_config`
(see `.claude/docs/config-resolution.md`).

`.claude/docs/technical-preferences.md` is the **legacy fallback**, read on demand
when a key is absent from `project.yaml`. It is no longer imported here: before
`/setup-engine` runs it is almost entirely `[TO BE CONFIGURED]` placeholders, and
after it runs `project.yaml` holds the real values.

## Coordination Rules

@.claude/docs/coordination-rules.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow.

## Coding Standards

@.claude/docs/coding-standards.md

## Context Management

Read `.claude/docs/context-management.md` on demand — it is a reference, not
session context. Two of its conventions are load-bearing and cited by name
elsewhere in the repo, so they are restated here rather than lost:

- **`production/session-state/active.md` is the session checkpoint.** The file is
  the memory, not the conversation. Read it first after any compaction, crash, or
  `/clear`.
- **Helpers in `.claude/scripts/` emit observations, never verdicts.** A script
  that scores or judges will eventually contradict a mode or override it cannot
  see. (Cited by `artifact-check.sh` and `adr-dep-graph.sh`.)
