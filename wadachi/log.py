"""
Logging di wadachi.

REGOLA FERREA: mai loggare su stdout — è il canale del protocollo MCP (stdio).
Tutto va su stderr (solo WARNING+) e su file rotante in <brain>/logs/wadachi.log
(livello da $WADACHI_LOG, default INFO) — così un utente può allegare un log
leggibile a una segnalazione senza rumore in console.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

_FMT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def get_logger(name: str = "wadachi") -> logging.Logger:
    return logging.getLogger(name)


def setup(brain_dir: Path | str | None = None) -> logging.Logger:
    """Configura il logger 'wadachi' (idempotente)."""
    log = logging.getLogger("wadachi")
    if log.handlers:                      # già configurato
        return log

    level = os.environ.get("WADACHI_LOG", "INFO").upper()
    log.setLevel(getattr(logging, level, logging.INFO))

    err = logging.StreamHandler(sys.stderr)   # MAI stdout: è il canale MCP
    err.setLevel(logging.WARNING)
    err.setFormatter(logging.Formatter(_FMT))
    log.addHandler(err)

    if brain_dir:
        try:
            logs_dir = Path(brain_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            fh = logging.handlers.RotatingFileHandler(
                logs_dir / "wadachi.log", maxBytes=1_000_000, backupCount=3,
                encoding="utf-8",
            )
            fh.setFormatter(logging.Formatter(_FMT))
            log.addHandler(fh)
        except OSError as e:              # brain su volume read-only: si degrada
            log.warning("impossibile aprire il file di log: %s", e)

    return log
