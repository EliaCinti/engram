# Decisions

A memory says *what is*. A decision says *what we chose, why, and what we gave up*.
Six months later, the second one is the treasure.

## Storing a decision

```
store_decision(
  decision     = "We use SQLite, not Postgres",
  rationale    = "local-first, zero-config, one file to back up",
  alternatives = "Postgres rejected: operational overkill at this scale;
                  DuckDB rejected: no concurrent writers",
  context      = "storage layer for v1, single-user product",
  project      = "myapp")
```

All four narrative fields matter. **`alternatives` is the one people skip and then
regret** — "why didn't we use X?" is the question that returns every quarter.

## Decisions are graph nodes

In the typed [[graph]], decisions are first-class nodes (labelled `D7`, drawn as
diamonds). Edges form when:

- a memory cites one: "as per decision #7", `[[D7]]`;
- a decision's rationale cites memories: "see memory #12" — evidence links.

## Asking why

```
why("why sqlite and not postgres?")
```

returns the matching decision(s) with rationale, rejected alternatives, context,
date — **and the memories that cite them** as supporting evidence, walked from the
graph. Full story in [[time-travel]].

## Decisions vs memories: a rule of thumb

Chose between alternatives? → decision. Discovered a fact, fixed a bug, learned a
pattern? → memory. When a decision gets *revisited*, store the new decision and cite
the old one ("supersedes decision #7") — the graph keeps the chain.
