# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com) · versioning: [SemVer](https://semver.org) (pre-1.0: minor = può rompere).

## [0.2.0] — 2026-07-14

### Changed — Rebrand: Engram → wadachi 轍 (Fase 0 roadmap)
- **Nuovo nome: wadachi** (轍 — i solchi che le ruote lasciano sulla strada). Scelto dopo un
  naming workshop con verifica sistematica di ~30 candidati (PyPI, domini, GitHub, collisioni
  nello spazio AI/memory). Nome PyPI riservato: [pypi.org/project/wadachi](https://pypi.org/project/wadachi/).
- **Package Python rinominato**: `engram` → `wadachi` (`from wadachi.store import …`).
- **Server MCP rinominato**: si registra come `wadachi` (era `engram`).
- **Entry point**: `wadachi` (+ alias legacy `engram`, così le config MCP esistenti che puntano
  a `venv/bin/engram` continuano a funzionare).
- **BRAIN_DIR default**: ora `~/.wadachi`; un brain legacy esistente in `~/.engram` viene
  rilevato e continua a funzionare senza modifiche.
- **Repo GitHub rinominato**: `EliaCinti/engram` → `EliaCinti/wadachi` (redirect automatici).
- **Sito**: engram.eliacinti.dev → **wadachi.eliacinti.dev** (301 dal vecchio dominio).

### Added
- **Brand identity "Sumi"** (`BRAND.md` + `assets/brand/`): palette inchiostro/vermiglio,
  tipografia Fraunces + Inter + JetBrains Mono, logomark a due pennellate con sigillo hanko,
  favicon, banner GitHub 1280×640.
- **Landing rebrandizzata** in stile Sumi (font self-hosted per CSP rigida, grafo hero
  ricolorato: hub vermiglio, nodi inchiostro, categorie in toni terra).
- Questo CHANGELOG.

## [0.1.0] — 2026-06-29

Stato pre-rebrand ("Engram 2.0"): 25 tool MCP — memoria persistente versionata (markdown +
SQLite), ricerca semantica locale (fastembed), auto-contesto, decision log, Constellation
(recall associativo con spreading activation + grafo entità via Graphify/claude-cli),
belief revision, reflection & insights, memoria procedurale, visualizzatore web del grafo.
