"""
wadachi CLI.

    wadachi                # avvia il server MCP (stdio) — comportamento storico,
                           # le config MCP esistenti continuano a funzionare
    wadachi init           # setup guidato: brain dir, DB migrato, config MCP
    wadachi --version

`init` è idempotente: rieseguirlo non danneggia nulla (le migrazioni fanno
backup automatico del DB e i file esistenti non vengono toccati).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from wadachi import __version__


def _default_brain_dir() -> Path:
    legacy = Path.home() / ".engram"
    if legacy.is_dir():
        return legacy
    return Path.home() / ".wadachi"


def _wadachi_bin() -> str:
    """Il binario `wadachi` da mettere nelle config MCP."""
    return shutil.which("wadachi") or sys.argv[0]


def _ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def _skip(msg: str) -> None:
    print(f"  – {msg}")


def cmd_init(args: argparse.Namespace) -> int:
    brain = Path(args.brain_dir or os.environ.get("BRAIN_DIR") or _default_brain_dir()).expanduser()

    print(f"wadachi {__version__} — setup\n")
    print(f"Brain dir: {brain}")

    # 1 · directory
    brain.mkdir(parents=True, exist_ok=True)
    (brain / "global").mkdir(exist_ok=True)
    (brain / "projects").mkdir(exist_ok=True)
    _ok("directory create (global/, projects/)")

    # 2 · DB migrato all'ultima versione (backup automatico se esisteva già)
    from wadachi.migrations import run_migrations
    applied = run_migrations(brain / "brain.db")
    if applied:
        _ok(f"database pronto (migrazioni applicate: {applied})")
    else:
        _ok("database già all'ultima versione dello schema")

    # 3 · registrazione in Claude Code (se il CLI `claude` è disponibile)
    if args.no_claude:
        _skip("Claude Code: saltato (--no-claude)")
    elif shutil.which("claude"):
        bin_path = _wadachi_bin()
        subprocess.run(["claude", "mcp", "remove", "wadachi", "--scope", "user"],
                       capture_output=True)
        r = subprocess.run(
            ["claude", "mcp", "add", "wadachi", "--scope", "user",
             "-e", f"BRAIN_DIR={brain}", "--", bin_path],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            _ok(f"Claude Code: server MCP 'wadachi' registrato ({bin_path})")
        else:
            print(f"  ✗ Claude Code: registrazione fallita: {(r.stderr or r.stdout).strip()[:200]}")
    else:
        _skip("Claude Code: CLI `claude` non trovato — registra a mano con:\n"
              f"      claude mcp add wadachi -e BRAIN_DIR={brain} -- {_wadachi_bin()}")

    # 4 · config Antigravity (solo se l'IDE è presente)
    ag_dir = Path(args.antigravity_dir or (Path.home() / ".gemini" / "antigravity-ide"))
    if args.no_antigravity:
        _skip("Antigravity: saltato (--no-antigravity)")
    elif ag_dir.is_dir():
        cfg_path = ag_dir / "mcp_config.json"
        try:
            cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
        except json.JSONDecodeError:
            print(f"  ✗ Antigravity: {cfg_path} non è JSON valido, non lo tocco")
            cfg = None
        if cfg is not None:
            cfg.setdefault("mcpServers", {})["wadachi"] = {
                "command": _wadachi_bin(),
                "args": [],
                "env": {"BRAIN_DIR": str(brain)},
            }
            cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
            _ok(f"Antigravity: server 'wadachi' scritto in {cfg_path}")
    else:
        _skip("Antigravity: non installato")

    print("\nFatto. Riavvia Claude Code e inizia con `get_context`. 轍")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="wadachi",
        description="wadachi 轍 — persistent memory for AI agents (MCP). "
                    "Senza argomenti avvia il server MCP su stdio.",
    )
    parser.add_argument("--version", action="version", version=f"wadachi {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="setup guidato: brain dir, DB, config MCP")
    p_init.add_argument("--brain-dir", help="dove vive il brain (default: $BRAIN_DIR, "
                                            "poi ~/.wadachi, o ~/.engram se già esiste)")
    p_init.add_argument("--no-claude", action="store_true",
                        help="non registrare il server in Claude Code")
    p_init.add_argument("--no-antigravity", action="store_true",
                        help="non scrivere la config Antigravity")
    p_init.add_argument("--antigravity-dir", help=argparse.SUPPRESS)  # per i test

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args)

    # nessun sottocomando → server MCP (import lazy: init non deve toccare
    # il BRAIN_DIR di default solo per colpa dell'import del server)
    from wadachi.server import mcp
    mcp.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
