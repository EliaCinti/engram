#!/usr/bin/env bash
#
# setup-device.sh — configura wadachi (ex engram) su QUESTA macchina.
#
# Crea un venv LOCALE alla macchina (i venv non sono portabili tra Mac),
# installa wadachi + motore semantico, e registra il server MCP in Claude Code
# puntando al brain condiviso sull'SSD.
#
# Uso:  /Volumes/ExtremeSSD/engram/scripts/setup-device.sh
# Poi:  riavvia Claude Code.

set -euo pipefail

# ── Configurazione condivisa (IDENTICA su ogni Mac) ──────────────────────────
SSD="/Volumes/ExtremeSSD"
ENGRAM_REPO="$SSD/wadachi"
BRAIN_DIR="$SSD/wadachi-brain"

# ── Ambiente per-macchina (NON sull'SSD: il venv è locale e ricreabile) ──────
VENV="$HOME/.local/share/engram/venv"
PYVER="3.13"

log()  { printf '\033[1;36m[wadachi]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[wadachi]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[wadachi] ERRORE:\033[0m %s\n' "$*" >&2; exit 1; }

# 1 ─ SSD montato e repo presente?
[ -d "$ENGRAM_REPO" ] || die "SSD non montato o repo assente: $ENGRAM_REPO"

# 2 ─ Brain condiviso presente? (avviso, non blocco: potresti doverlo ancora migrare)
if [ ! -f "$BRAIN_DIR/brain.db" ]; then
  warn "Nessun brain in $BRAIN_DIR."
  warn "Migra prima i dati del Mac che li possiede:"
  warn "    rsync -av ~/.engram/ $BRAIN_DIR/"
  warn "Proseguo comunque: verrà creato un brain vuoto al primo avvio del server."
fi

# 3 ─ Venv locale: preferisci uv (veloce, riproducibile), fallback su venv stdlib
mkdir -p "$(dirname "$VENV")"
if command -v uv >/dev/null 2>&1; then
  log "Creo/aggiorno il venv con uv → $VENV"
  uv venv "$VENV" --python "$PYVER"
  log "Installo wadachi[semantic] (editable) dal repo sull'SSD…"
  uv pip install --python "$VENV/bin/python" -e "${ENGRAM_REPO}[semantic]"
else
  log "uv non trovato; uso python3 -m venv → $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --upgrade pip >/dev/null
  log "Installo wadachi[semantic] (editable) dal repo sull'SSD…"
  "$VENV/bin/python" -m pip install -e "${ENGRAM_REPO}[semantic]"
fi

# 4 ─ Registra il server MCP a livello utente (vale per tutte le sessioni)
if command -v claude >/dev/null 2>&1; then
  log "Registro il server MCP 'wadachi' in Claude Code (scope user)…"
  claude mcp remove wadachi --scope user >/dev/null 2>&1 || true
  claude mcp remove engram --scope user >/dev/null 2>&1 || true
  claude mcp add wadachi --scope user \
    --env "BRAIN_DIR=$BRAIN_DIR" \
    -- "$VENV/bin/python" "$ENGRAM_REPO/wadachi/server.py"
else
  warn "CLI 'claude' non trovata: registra il server a mano (vedi docs/multi-device-setup.md §4)."
fi

# 5 ─ Verifica import + percorso brain effettivo
log "Verifica…"
BRAIN_DIR="$BRAIN_DIR" "$VENV/bin/python" - <<'PY'
from wadachi.store import MemoryStore
s = MemoryStore()
print("  brain_dir:", s.brain_dir)
print("  progetti :", [p["name"] for p in s.list_projects()])
print("  memorie  :", len(s.list_memories()))
PY

log "Fatto. Riavvia Claude Code per caricare il server MCP 'wadachi'."
