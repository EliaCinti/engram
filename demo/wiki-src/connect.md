# Connecting your client

Wadachi is a standard **MCP server over stdio**. The whole contract: run the command
`wadachi` (no arguments) with the environment variable `BRAIN_DIR` pointing at your
brain. Any MCP-compatible client works.

## Claude Code

`wadachi init` registers it for you. Manually:

```bash
claude mcp add wadachi -e BRAIN_DIR=$HOME/.wadachi -- wadachi
```

Check with `claude mcp list` — you should see `wadachi ✔ Connected`.

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "wadachi": {
      "command": "wadachi",
      "args": [],
      "env": { "BRAIN_DIR": "/Users/you/.wadachi" }
    }
  }
}
```

## Cursor

`.cursor/mcp_servers.json` — same JSON shape as Claude Desktop.

## Antigravity

`~/.gemini/antigravity-ide/mcp_config.json` — written by `wadachi init`; same shape.

## Any other MCP client

Point it at the `wadachi` executable with `BRAIN_DIR` in the environment. If your
client can't set env vars, wadachi falls back to `~/.wadachi` (or a legacy
`~/.engram` if present).

## One brain, many machines

`BRAIN_DIR` is the only pointer, so a brain on an external drive or synced folder can
serve several machines. The safe pattern is **one writer at a time** — SQLite handles
locking, but two agents writing simultaneously from different machines over network
filesystems is asking for trouble.

## Teaching your agent to use it

The server ships instructions to the model automatically (call `get_context` first,
store as you go, link memories). If you use a CLAUDE.md, a line like *"start every
session with wadachi's get_context"* makes the habit explicit. See [[get-context]].
