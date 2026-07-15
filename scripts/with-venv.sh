#!/usr/bin/env bash
#
# with-venv.sh — esegue un comando dentro il venv locale di wadachi (ex engram),
# con BRAIN_DIR già puntato al brain condiviso sull'SSD e un controllo
# che l'SSD sia montato (fallisce in modo esplicito se non lo è).
#
# Esempi:
#   scripts/with-venv.sh python -c "from wadachi.store import MemoryStore as M; print(M().brain_dir)"
#   scripts/with-venv.sh python wadachi/server.py        # avvio manuale del server

set -euo pipefail

SSD="/Volumes/ExtremeSSD"
export BRAIN_DIR="${BRAIN_DIR:-$SSD/wadachi-brain}"
VENV="$HOME/.local/share/engram/venv"

die() { printf '\033[1;31m[wadachi] ERRORE:\033[0m %s\n' "$*" >&2; exit 1; }

[ -d "$SSD" ]              || die "SSD non montato: $SSD"
[ -x "$VENV/bin/python" ]  || die "Venv assente: $VENV — esegui prima scripts/setup-device.sh"
[ "$#" -ge 1 ]             || die "Uso: with-venv.sh <comando> [args…]"

# Antepone il venv al PATH e delega al comando richiesto
export PATH="$VENV/bin:$PATH"
exec "$@"
