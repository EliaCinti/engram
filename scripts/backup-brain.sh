#!/usr/bin/env bash
# backup-brain.sh — backup del brain wadachi (pensato per l'hook Stop di
# Claude Code: gira a fine sessione, silenzioso e veloce ~0.5MB).
# Rotazione: tiene gli ultimi 10 backup di sessione.

set -euo pipefail
BRAIN="${BRAIN_DIR:-/Volumes/ExtremeSSD/wadachi-brain}"
[ -d "$BRAIN" ] || exit 0                     # SSD non montato: esci in silenzio

DEST="$BRAIN/backups"
mkdir -p "$DEST"
TS=$(date +%Y%m%d-%H%M%S)
tar -czf "$DEST/session-$TS.tar.gz" -C "$BRAIN" \
  brain.db global projects index.md SCHEMA.md log.md 2>/dev/null || true

# rotazione: solo gli ultimi 10 backup di sessione
ls -t "$DEST"/session-*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
