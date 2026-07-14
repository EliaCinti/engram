"""
Access tracking per il decay score (Fase 4.16): le memorie mai richiamate
perdono leggermente priorità nel ranking. Ogni get_memory/expand_memory
incrementa access_count e aggiorna last_accessed.
"""

VERSION = 2
DESCRIPTION = "decay: access_count + last_accessed su memories"


def up(conn):
    conn.execute("ALTER TABLE memories ADD COLUMN access_count INTEGER NOT NULL DEFAULT 0")
    conn.execute("ALTER TABLE memories ADD COLUMN last_accessed TEXT")
