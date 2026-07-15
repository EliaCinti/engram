# FAQ — the honest answers

## Privacy & trust

**Does wadachi send my data anywhere?**
No. No telemetry, no analytics, no cloud calls, no "anonymous usage statistics".
Embeddings are computed locally. The only network access in the product's life is
pip downloading the package. This is design rule #1, not a toggle.

**How do you improve it without telemetry, then?**
People tell us. There's a "Share your setup" issue template — voluntary feedback is
the only channel, which is exactly the trade we want.

**Can I audit what it stores?**
`cat` your brain. It's markdown in a folder ([[brain]]). `log.md` lists every
operation ever performed.

**What if I want out?**
`pipx uninstall wadachi` and your brain remains as plain files — readable forever,
openable in Obsidian, importable anywhere as an OKF bundle. Exit is as easy as
entry.

## Costs & performance

**What does it cost to run?** $0. Local embeddings, no API calls. The optional
entity graph uses your local `claude` CLI (your existing plan, not metered API).

**How big can a brain get?** The design target is a personal brain: hundreds to a
few thousand memories. Search is instant at that scale; the graph builds in
well under a second at ~100 nodes.

**Does it work offline?** Entirely, after the one-time model download.

## Behaviour

**Will it ever change my memories on its own?**
No. Bookkeeping (index, log, access counters) happens on your own writes; everything
cognitive — merging, retiring, insights — is proposed and waits for you
([[get-context]], [[sleep]]).

**What happens on upgrades?** Migrations with automatic backups; you can snapshot
first with `wadachi export`. Full chain in [[safety]].

**Semantic search in my language?** The default model is English-optimized but
handles Italian and other European languages reasonably. Keyword mode is
language-neutral. A multilingual model option is on the roadmap.

**Can several agents share one brain?** Several *clients* on one machine, yes —
they're all the same server. Several machines: one writer at a time ([[connect]]).

## Comparisons

**vs Mem0 / Zep?** They're good, production-scale, managed services with
multi-tenant APIs. Wadachi is single-brain, local, files-you-own, with a cognitive
model (beliefs, provenance, time-travel, sleep) they don't aim for. If you need a
hosted memory API for your SaaS, use them. If you want *your* brain on *your* disk
that reasons about what it believes — that's wadachi.

**vs Obsidian + plugins?** Obsidian is a wonderful editor for humans. Wadachi is a
memory *server* for agents that happens to speak Obsidian's format
([[obsidian-okf]]). They compose: same folder, two doors.

**vs just using CLAUDE.md?** CLAUDE.md is instructions — a few hundred lines the
model always reads. Wadachi is knowledge — thousands of memories retrieved by
relevance. You need both; wadachi's `get_context` is how the right slice of the
second reaches the model without drowning it.

## Project

**Who's behind this?** One engineering student and his AI pair programmer. The
whole history is in the repo's CHANGELOG — including the day it was renamed from
Engram after discovering four name collisions ([[faq|ask why() about it]] 😉).

**When is v1.0?** When the tool API and schema have been stable for a month.
The clock is running.

**How do I contribute?** PRs welcome (CONTRIBUTING.md has the four rules and the
dev setup). Not a coder? Feedback is the most valuable contribution there is.
