/* ── Engram landing — graphify-style hero ──────────────────────────
   A designed hub-and-spoke knowledge graph (SVG) that BUILDS as you
   scroll, a decoding headline, a flowing terminal recall ticker, and
   perpetual particle flow along the edges. Engram violet/cyan palette.
   Pure vanilla JS — no physics, no external libs.                     */

(function () {
  "use strict";

  var V = "#8b7cf6", C = "#34d3ee";
  var CAT = {
    architecture: "#7aa2ff", bugfix: "#ff6b6b", config: "#f4a259",
    pattern: "#c792ea", context: "#5ec8a0", reference: "#56c2d6",
    decision: "#f7c948", entity: "#8b7cf6",
  };
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var SVGNS = "http://www.w3.org/2000/svg";
  var T0 = performance.now();
  var now = function () { return (performance.now() - T0) / 1000; };

  // ── 1 · curated graph model (hub → ring1 → ring2) ───────────────
  var W = 600, H = 540, cx = W / 2, cy = H / 2 - 6;
  var nodes = [], edges = [];

  function addNode(o) { o.id = nodes.length; nodes.push(o); return o.id; }

  // central hub
  var hub = addNode({ x: cx, y: cy, r: 13, color: C, label: "get_context", kind: "hub" });

  // ring 1 — the cognitive faculties
  var ring1Defs = [
    { label: "recall", cat: "reference" },
    { label: "decisions", cat: "decision" },
    { label: "constellation", cat: "entity" },
    { label: "beliefs", cat: "pattern" },
    { label: "reflect", cat: "context" },
    { label: "procedural", cat: "config" },
  ];
  var ring1 = [];
  ring1Defs.forEach(function (d, i) {
    var a = (i / ring1Defs.length) * Math.PI * 2 - Math.PI / 2;
    var id = addNode({
      x: cx + Math.cos(a) * 132, y: cy + Math.sin(a) * 132,
      r: 7.5, color: V, label: d.label, kind: "r1", ang: a,
    });
    ring1.push(id); edges.push({ a: hub, b: id, main: true });
  });

  // ring 2 — memories hanging off each faculty
  var leafLabels = [
    "CRDT merge", "Yjs vs Automerge", "WS reconnect", "Redis pub/sub",
    "schema v3", "auth token TTL", "rate-limit 429", "snapshot GC",
    "vector index", "cold-start fix", "Node 18 EOL", "p95 latency",
  ];
  var li = 0;
  ring1.forEach(function (pid, k) {
    var p = nodes[pid];
    var count = 2;
    for (var j = 0; j < count; j++) {
      var spread = 0.46;
      var a = p.ang + (j - (count - 1) / 2) * spread;
      var cat = ring1Defs[k].cat;
      var id = addNode({
        x: cx + Math.cos(a) * 232, y: cy + Math.sin(a) * 232,
        r: 4.6, color: CAT[cat] || V, label: leafLabels[li % leafLabels.length],
        kind: "r2",
      });
      li++;
      edges.push({ a: pid, b: id });
    }
  });
  // a few cross-links so it reads as a graph, not a tree
  edges.push({ a: ring1[0], b: ring1[1], cross: true });
  edges.push({ a: ring1[2], b: ring1[3], cross: true });
  edges.push({ a: ring1[4], b: ring1[5], cross: true });
  edges.push({ a: ring1[1], b: ring1[4], cross: true });

  // reveal order: hub, ring1, ring2, then cross-links sit with ring1
  var nodeOrder = nodes.map(function (n) { return n.id; });
  nodeOrder.sort(function (a, b) {
    var rank = { hub: 0, r1: 1, r2: 2 };
    return rank[nodes[a].kind] - rank[nodes[b].kind];
  });

  // ── 2 · render SVG skeleton (hidden, revealed progressively) ─────
  var svg = document.getElementById("hero-svg");
  var gEdges = mk("g"), gParticles = mk("g"), gNodes = mk("g");
  svg.appendChild(gEdges); svg.appendChild(gParticles); svg.appendChild(gNodes);

  function mk(t) { return document.createElementNS(SVGNS, t); }

  edges.forEach(function (e) {
    var na = nodes[e.a], nb = nodes[e.b];
    var ln = mk("line");
    ln.setAttribute("x1", na.x); ln.setAttribute("y1", na.y);
    ln.setAttribute("x2", nb.x); ln.setAttribute("y2", nb.y);
    ln.setAttribute("stroke", e.cross ? "rgba(139,124,246,0.35)" : "rgba(52,211,238,0.4)");
    ln.setAttribute("stroke-width", e.main ? 1.4 : 0.9);
    var len = Math.hypot(nb.x - na.x, nb.y - na.y);
    ln.setAttribute("stroke-dasharray", len);
    ln.setAttribute("stroke-dashoffset", len);
    ln.style.transition = "stroke-dashoffset .55s cubic-bezier(.2,.7,.2,1)";
    e.el = ln; e.len = len; e.on = false;
    gEdges.appendChild(ln);
  });

  nodes.forEach(function (n) {
    var g = mk("g");
    g.setAttribute("transform", "translate(" + n.x + " " + n.y + ")");
    g.setAttribute("class", "gnode");
    g.style.opacity = 0;
    g.style.transform = "translate(" + n.x + "px," + n.y + "px) scale(.2)";
    g.style.transformBox = "fill-box";
    g.style.transition = "opacity .5s ease, transform .5s cubic-bezier(.2,1.5,.4,1)";

    // halo
    var halo = mk("circle");
    halo.setAttribute("r", n.r + 6); halo.setAttribute("fill", n.color);
    halo.setAttribute("opacity", "0.14"); halo.setAttribute("class", "halo");
    g.appendChild(halo);
    // core
    var core = mk("circle");
    core.setAttribute("r", n.r); core.setAttribute("fill", n.color);
    g.appendChild(core);
    // ring for hub/r1
    if (n.kind !== "r2") {
      var rg = mk("circle");
      rg.setAttribute("r", n.r + 3); rg.setAttribute("fill", "none");
      rg.setAttribute("stroke", n.color); rg.setAttribute("stroke-width", "1");
      rg.setAttribute("opacity", "0.5");
      g.appendChild(rg);
    }
    // label
    if (n.kind !== "r2") {
      var tx = mk("text");
      tx.textContent = n.label;
      tx.setAttribute("x", 0); tx.setAttribute("y", n.r + 15);
      tx.setAttribute("text-anchor", "middle");
      tx.setAttribute("class", "glabel " + (n.kind === "hub" ? "hub" : ""));
      g.appendChild(tx);
    }
    n.g = g; n.halo = halo; n.on = false;
    gNodes.appendChild(g);
  });

  // particles pool (one per edge)
  edges.forEach(function (e) {
    var p = mk("circle");
    p.setAttribute("r", e.main ? 2.2 : 1.6);
    p.setAttribute("fill", e.cross ? V : C);
    p.setAttribute("opacity", "0");
    e.particle = p; e.pPhase = Math.random();
    gParticles.appendChild(p);
  });

  // ── 3 · reveal driven by scroll progress (sticky build) ─────────
  function revealNode(n) {
    if (n.on) return; n.on = true;
    n.g.style.opacity = 1;
    n.g.style.transform = "translate(" + n.x + "px," + n.y + "px) scale(1)";
  }
  function revealEdge(e) {
    if (e.on) return; e.on = true;
    e.el.setAttribute("stroke-dashoffset", "0");
  }

  var counterEl = document.getElementById("node-count");
  var progressEl = document.getElementById("build-progress");
  var heroGrid = document.querySelector(".hero-grid");

  function applyProgress(p) {
    var e = p * p * (3 - 2 * p);            // smoothstep
    var bp = Math.min(1, e / 0.72);         // graph fully built by ~72% of the scroll
    var revealCount = Math.max(1, Math.round(bp * nodes.length));
    var shown = {};
    for (var i = 0; i < revealCount; i++) { var id = nodeOrder[i]; revealNode(nodes[id]); shown[id] = 1; }
    edges.forEach(function (ed) { if (shown[ed.a] && shown[ed.b]) revealEdge(ed); });
    if (counterEl) counterEl.textContent = revealCount;   // honest: the nodes actually drawn
    if (progressEl) progressEl.style.width = (bp * 100).toFixed(1) + "%";

    // gentle exit — lift & fade the hero as the pin ends, so it blends
    // into the next section instead of snapping to a black seam.
    if (heroGrid) {
      var exit = Math.max(0, (p - 0.82) / 0.18);
      heroGrid.style.transform = exit > 0 ? "translateY(" + (-exit * 44).toFixed(1) + "px)" : "";
      heroGrid.style.opacity = exit > 0 ? (1 - exit * 0.65).toFixed(3) : "";
    }
  }

  // effective progress = max(load-in auto build, scroll position)
  var track = document.getElementById("hero-track");
  var autoP = 0, autoStart = performance.now();
  function scrollP() {
    if (!track) return 0;
    var r = track.getBoundingClientRect();
    var span = r.height - window.innerHeight;
    if (span <= 0) return 0;
    return Math.min(1, Math.max(0, -r.top / span));
  }

  // ── 4 · perpetual life: particles + halo pulse (rAF) ────────────
  function tick() {
    var t = now();

    // auto build-in on first load so it's never empty (eases to ~0.4)
    if (!reduce && autoP < 0.4) {
      autoP = Math.min(0.4, (performance.now() - autoStart) / 1700 * 0.4);
    }
    var p = Math.max(reduce ? 1 : autoP, scrollP());
    applyProgress(p);

    if (!reduce) {
      // flow particles along visible edges
      edges.forEach(function (ed) {
        if (!ed.on) { ed.particle.setAttribute("opacity", "0"); return; }
        var f = (t * (ed.main ? 0.28 : 0.2) + ed.pPhase) % 1;
        var na = nodes[ed.a], nb = nodes[ed.b];
        ed.particle.setAttribute("cx", na.x + (nb.x - na.x) * f);
        ed.particle.setAttribute("cy", na.y + (nb.y - na.y) * f);
        var fade = Math.sin(f * Math.PI);        // dim at the ends
        ed.particle.setAttribute("opacity", (0.85 * fade).toFixed(2));
      });
      // halo breathing
      nodes.forEach(function (n) {
        if (!n.on) return;
        var pl = 0.1 + 0.09 * (0.5 + 0.5 * Math.sin(t * 1.7 + n.id));
        n.halo.setAttribute("opacity", pl.toFixed(3));
      });
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // ── 5 · decoding headline ───────────────────────────────────────
  function decode(el, delay) {
    if (!el) return;
    var GLYPH = "ΨΩΣ∇λπ∀∃ΔΦΘ01▓░▄▀█01";
    var full = el.getAttribute("data-text") || el.textContent;
    if (reduce) { el.textContent = full; return; }
    var dur = 1100;
    function run() {
      var start = performance.now();
      (function f(t) {
        var p = Math.min((t - start) / dur, 1);
        var out = "";
        for (var i = 0; i < full.length; i++) {
          var ch = full[i];
          if (ch === " " || ch === "\n") { out += ch; continue; }
          out += (i / full.length < p * 1.35) ? ch : GLYPH[(Math.random() * GLYPH.length) | 0];
        }
        el.textContent = out;
        if (p < 1) requestAnimationFrame(f); else el.textContent = full;
      })(start);
    }
    setTimeout(run, delay || 0);
  }
  decode(document.getElementById("hero-h1"), 250);

  // ── 6 · terminal recall ticker ──────────────────────────────────
  (function () {
    var qEl = document.getElementById("term-q");
    var rEl = document.getElementById("term-results");
    if (!qEl || !rEl) return;
    var QUERIES = [
      { q: 'recall("why Yjs over Automerge?")', r: [
        ["#34d3ee", "decision_03 → Yjs: smaller payload, faster merge"],
        ["#8b7cf6", "architecture_11 ↔ CRDT layer mentions Yjs"],
        ["#f7c948", "note_02 → Automerge revisit if memory grows"]] },
      { q: 'get_context("realtime sync")', r: [
        ["#34d3ee", "config_06 → Redis pub/sub fan-out"],
        ["#8b7cf6", "bugfix_08 → WS reconnect backoff"],
        ["#5ec8a0", "context_01 → p95 latency budget = 80ms"]] },
      { q: 'recall_associative("stale beliefs")', r: [
        ["#f7c948", "config_04 ⚠ CI still on Node 18 (EOL)"],
        ["#8b7cf6", "pattern_05 → supersede on schema bump"],
        ["#34d3ee", "reflect → 2 memories flagged for review"]] },
    ];
    var qi = 0;
    function type(q, done) {
      var i = 0; qEl.textContent = "";
      var iv = setInterval(function () {
        qEl.textContent += q[i++];
        if (i >= q.length) { clearInterval(iv); done(); }
      }, 34);
    }
    function results(rs, done) {
      rEl.innerHTML = "";
      rs.forEach(function (r, i) {
        var d = document.createElement("div");
        d.className = "tres";
        d.innerHTML = '<span class="dot" style="background:' + r[0] + '"></span>' +
                      '<span>' + r[1] + "</span>";
        rEl.appendChild(d);
        setTimeout(function () { d.classList.add("show"); }, 120 + i * 200);
      });
      setTimeout(done, rs.length * 220 + 2600);
    }
    function cycle() {
      var e = QUERIES[qi % QUERIES.length]; qi++;
      type(e.q, function () { results(e.r, function () {
        qEl.textContent = ""; rEl.innerHTML = ""; setTimeout(cycle, 600);
      }); });
    }
    setTimeout(cycle, 1300);
  })();

  // ── 7 · faint glyph rain texture ────────────────────────────────
  (function () {
    var c = document.getElementById("rain");
    if (!c || reduce) return;
    var ctx = c.getContext("2d");
    var CH = "ΨΩΣ∇λπ01ΔΦ100110∂∫";
    var Wd, Hd, drops;
    function rs() {
      Wd = c.width = c.offsetWidth; Hd = c.height = c.offsetHeight;
      drops = Array.from({ length: Math.floor(Wd / 22) }, function () { return (Math.random() * Hd / 16) | 0; });
    }
    function draw() {
      ctx.fillStyle = "rgba(7,8,12,0.16)"; ctx.fillRect(0, 0, Wd, Hd);
      ctx.fillStyle = "rgba(139,124,246,0.55)"; ctx.font = "12px 'JetBrains Mono',monospace";
      drops.forEach(function (y, i) {
        ctx.fillText(CH[(Math.random() * CH.length) | 0], i * 22, y * 16);
        if (y * 16 > Hd && Math.random() > 0.975) drops[i] = 0; else drops[i]++;
      });
    }
    rs(); setInterval(draw, 70); addEventListener("resize", rs);
  })();
})();
