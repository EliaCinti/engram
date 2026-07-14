# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com) · versioning: [SemVer](https://semver.org) (pre-1.0: minor = può rompere).

## [0.3.0] — 2026-07-14

### Added — Fase 1 roadmap: fondamenta
- **Migrazioni DB versionate** (`wadachi/migrations/`): tabella `schema_version`,
  runner all'avvio che applica gli script `000N_*.py` in ordine, ognuno nella sua
  transazione (BEGIN/COMMIT espliciti, rollback su errore). **Backup automatico**
  del `.db` in `backups/` prima di ogni migrazione su un DB non vuoto. I DB
  pre-esistenti vengono adottati dal baseline idempotente senza toccare i dati.
- **Suite pytest**: 51 test su migrazioni, store e tutti i 25 tool MCP — DB vuoto,
  DB corrotto, ID inesistenti, titoli duplicati/malformati, versioning, beliefs,
  insights, progetti. Hermetic (BRAIN_DIR temporanei), gira anche senza fastembed.
- **CI GitHub Actions**: test a ogni push/PR, matrice Python 3.11–3.14.

### Fixed
- `recall_associative` senza fastembed non crasha più il tool MCP: restituisce un
  errore chiaro + i risultati del fallback keyword (bug trovato dalla nuova suite).
- Il rollback delle migrazioni è garantito anche per le DDL (il modulo sqlite3 di
  Python committa implicitamente fuori transazione: ora BEGIN/COMMIT sono espliciti
  e `executescript` è vietato negli script di migrazione).

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
