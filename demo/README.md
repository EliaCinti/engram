# Engram — public demo site

A self-contained, static landing page + interactive knowledge-graph demo for
**Engram**, the persistent-memory MCP server. Meant to live at
`engram.eliacinti.dev`.

Dark, product-style landing à la graphifylabs.ai: a hub-and-spoke knowledge
graph that **builds as you scroll**, a decoding headline, a live recall
terminal, then problem/solution, a feature grid, "how it works", and a
quick-start CTA.

> The graph shows a **100% fictional** example brain. It never touches the real
> `~/.engram/brain.db`, and every number on the page is honest (the counter
> reports the nodes actually drawn — nothing inflated). See *Dataset* below.

---

## Files

| File | What it is |
|------|------------|
| `index.html` | The page (structure + sections). |
| `styles.css` | All styling (dark theme, no framework). |
| `app.js` | The whole hero engine: builds the SVG graph on scroll, decodes the headline, runs the recall terminal, animates particles. The small curated demo graph is defined inline here. |

No build step, **no external runtime dependencies**, no data files to load —
`app.js` is pure vanilla JS and carries its own curated graph.

---

## Local preview

From inside this directory:

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

---

## How the hero works

- **Scroll-build** — the hero is a tall track with a `sticky` stage. Scroll
  progress (0→1) reveals nodes/edges in order and ticks the "nodes indexed"
  counter. An initial auto-build plays on load so it's never empty.
- **Decoding headline** — the `<h1>` scrambles Greek/math/block glyphs into the
  title on load.
- **Recall terminal** — a looping ticker that types `recall(...)` queries and
  reveals the connected results.
- **Perpetual life** — particles flow along every visible edge, node halos
  breathe, and a faint glyph-rain canvas sits behind it all.
- Everything honours `prefers-reduced-motion` (static, fully readable fallback).

Palette is Engram's own violet `#8b7cf6` / cyan `#34d3ee` on near-black
`#07080c`, matching the README and `eliacinti.dev`.

---

## Deploy (Hetzner VPS + nginx, behind Cloudflare)

Same pattern as `briefing.eliacinti.dev → /usr/share/nginx/briefing`.

**One-line deploy** (rsync the static files to the VPS):

```bash
rsync -avz --delete ./ USER@VPS:/usr/share/nginx/engram/
```

### nginx server block — `engram.eliacinti.dev`

Drop this in `/etc/nginx/sites-available/engram.eliacinti.dev` (or your conf.d),
then `ln -s … sites-enabled/`, `nginx -t`, `systemctl reload nginx`.

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name engram.eliacinti.dev;

    root /usr/share/nginx/engram;
    index index.html;

    # static site — try the file, else fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # long cache for the immutable assets, short for HTML
    location ~* \.(js|css|json|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }
    location = /index.html {
        add_header Cache-Control "no-cache";
    }

    # Content-Security-Policy — fully self-hosted, no CDN needed.
    # 'unsafe-inline' for styles only (inline style attributes set from JS).
    add_header Content-Security-Policy "default-src 'self'; \
        script-src 'self'; \
        style-src 'self' 'unsafe-inline'; \
        img-src 'self' data:; \
        font-src 'self' data:; \
        connect-src 'self'; \
        base-uri 'self'; \
        frame-ancestors 'none'" always;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

TLS is terminated at Cloudflare (orange-cloud). If you also want origin TLS,
add a `listen 443 ssl;` block with your cert paths exactly like the other
subdomains; the `location`/headers stay identical.

> Fonts: the page uses only system + monospace fonts, so there are **no external
> font requests** and the CSP above needs no `fonts.googleapis.com` exception.

---

## Dataset (what's fictional)

The hero graph is a small curated brain for **"Tideflow"** — an imaginary
open-source CRDT real-time-sync engine (Yjs core, WebSocket server, Redis
fan-out, Postgres snapshots, React hooks). None of it is real; no person, repo,
or path belongs to Elia.

- A central **`get_context`** hub wired to Engram's six faculties
  (recall · decisions · constellation · beliefs · reflect · procedural).
- A ring of **memories** hanging off each faculty, plus a few cross-links so it
  reads as a graph, not a tree.
- The recall terminal cycles real-shaped Engram queries
  (`recall(...)`, `get_context(...)`, `recall_associative(...)`) returning
  connected memories/decisions — including one `stale` belief flagged for review.

To change the showcase, edit the model arrays at the top of `app.js`
(`ring1Defs`, `leafLabels`) and the `QUERIES` list in the terminal block.

---

Built by Elia Cinti — [eliacinti.dev](https://eliacinti.dev)
