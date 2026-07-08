/* ── Engram landing — graphify-style hero ──────────────────────────
   A designed hub-and-spoke knowledge graph (SVG) that SELF-ASSEMBLES
   when it scrolls into view, reacts to the cursor (nodes repel with a
   springy jelly), then lives (particle flow + halo breathing). Plus a
   decoding headline, a terminal recall ticker, and faint glyph rain.
   Engram violet/cyan palette. Pure vanilla JS — no external libs.     */

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

  // reveal order: hub, then ring1, then ring2
  var nodeOrder = nodes.map(function (n) { return n.id; });
  nodeOrder.sort(function (a, b) {
    var rank = { hub: 0, r1: 1, r2: 2 };
    return rank[nodes[a].kind] - rank[nodes[b].kind];
  });

  // ── 2 · render SVG skeleton ─────────────────────────────────────
  function mk(t) { return document.createElementNS(SVGNS, t); }

  var svg = document.getElementById("hero-svg");
  if (!svg) return;
  var gGlow = mk("g"), gEdges = mk("g"), gParticles = mk("g"), gNodes = mk("g");
  gGlow.style.filter = "blur(9px)";          // soft neon bloom layer, beneath all
  svg.appendChild(gGlow); svg.appendChild(gEdges); svg.appendChild(gParticles); svg.appendChild(gNodes);
  svg.style.transformOrigin = "50% 48%";
  svg.style.willChange = "transform";

  // dynamic per-node state: offset (ox,oy) + velocity (vx,vy) for repulsion
  nodes.forEach(function (n) { n.ox = 0; n.oy = 0; n.vx = 0; n.vy = 0; n.vis = 0; });

  // edges — plain lines, opacity-revealed, endpoints follow displaced nodes
  edges.forEach(function (e) {
    var ln = mk("line");
    ln.setAttribute("stroke", e.cross ? "rgba(139,124,246,0.55)" : "rgba(52,211,238,0.6)");
    ln.setAttribute("stroke-width", e.main ? 1.4 : 0.9);
    ln.setAttribute("stroke-linecap", "round");
    ln.setAttribute("opacity", "0");
    e.el = ln; e.vis = 0;
    gEdges.appendChild(ln);
    // one travelling particle per edge
    var pt = mk("circle");
    pt.setAttribute("r", e.main ? 2.2 : 1.6);
    pt.setAttribute("fill", e.cross ? V : C);
    pt.setAttribute("opacity", "0");
    e.particle = pt; e.pPhase = Math.random();
    gParticles.appendChild(pt);
  });

  // nodes — bloom blob (blurred layer) + crisp group (halo, core, ring, label)
  nodes.forEach(function (n) {
    var glow = mk("circle");
    glow.setAttribute("r", n.r * 2.4); glow.setAttribute("fill", n.color);
    glow.setAttribute("opacity", "0");
    gGlow.appendChild(glow); n.glowEl = glow;

    var g = mk("g");
    g.setAttribute("class", "gnode");
    g.style.opacity = 0;
    g.style.transformOrigin = "0 0";           // scale about the node centre
    // halo
    var halo = mk("circle");
    halo.setAttribute("r", n.r + 6); halo.setAttribute("fill", n.color); halo.setAttribute("opacity", "0.14");
    g.appendChild(halo);
    // core
    var core = mk("circle");
    core.setAttribute("r", n.r); core.setAttribute("fill", n.color);
    g.appendChild(core);
    // ring + label for hub/r1
    if (n.kind !== "r2") {
      var rg = mk("circle");
      rg.setAttribute("r", n.r + 3); rg.setAttribute("fill", "none");
      rg.setAttribute("stroke", n.color); rg.setAttribute("stroke-width", "1"); rg.setAttribute("opacity", "0.5");
      g.appendChild(rg);
      var tx = mk("text");
      tx.textContent = n.label;
      tx.setAttribute("x", 0); tx.setAttribute("y", n.r + 15);
      tx.setAttribute("text-anchor", "middle");
      tx.setAttribute("class", "glabel " + (n.kind === "hub" ? "hub" : ""));
      g.appendChild(tx);
    }
    n.g = g; n.halo = halo;
    gNodes.appendChild(g);
  });

  // ── 3 · autonomous build timeline ───────────────────────────────
  var counterEl = document.getElementById("node-count");
  var progressEl = document.getElementById("build-progress");

  var LEAD = 480;      // ms before the first node appears
  var STAGGER = 120;   // ms between successive nodes
  var POP = 600;       // ms for one node / edge to ease in
  nodeOrder.forEach(function (id, i) { nodes[id].revealAt = LEAD + i * STAGGER; });
  edges.forEach(function (e) { e.revealAt = Math.max(nodes[e.a].revealAt, nodes[e.b].revealAt) + 80; });
  var BUILD_MS = LEAD + nodes.length * STAGGER + POP;

  var buildStart = null;
  function startBuild() { if (buildStart === null) buildStart = performance.now(); }

  function smooth(x) { return x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x); }
  function outBack(x) { if (x >= 1) return 1; var c1 = 1.70158, c3 = c1 + 1, y = x - 1; return 1 + c3 * y * y * y + c1 * y * y; }
  function nodeVis(n) {
    if (reduce) return 1;
    if (buildStart === null) return 0;
    return Math.min(1, Math.max(0, (performance.now() - buildStart - n.revealAt) / POP));
  }

  // ── 4 · cursor repulsion + subtle parallax lean ─────────────────
  var cur = { x: 0, y: 0, on: false };
  function toSvg(clientX, clientY) {
    var r = svg.getBoundingClientRect();
    return { x: (clientX - r.left) / r.width * W, y: (clientY - r.top) / r.height * H };
  }
  if (!reduce) {
    svg.addEventListener("pointermove", function (ev) {
      var c = toSvg(ev.clientX, ev.clientY); cur.x = c.x; cur.y = c.y; cur.on = true;
    }, { passive: true });
    svg.addEventListener("pointerleave", function () { cur.on = false; });
  }
  var pxTgt = 0, pyTgt = 0, pxCur = 0, pyCur = 0;
  if (!reduce) addEventListener("pointermove", function (ev) {
    pxTgt = (ev.clientX / window.innerWidth - 0.5) * 2;
    pyTgt = (ev.clientY / window.innerHeight - 0.5) * 2;
  }, { passive: true });

  var REP_R = 90, REP_PUSH = 1.9, SPRING = 0.09, DAMP = 0.86;

  function frame() {
    var t = now();
    var built = reduce ? 1 : (buildStart === null ? 0 : smooth(Math.min(1, (performance.now() - buildStart) / BUILD_MS)));
    var visCount = 0;

    // nodes: reveal + repulsion physics + draw
    nodes.forEach(function (n) {
      n.vis = nodeVis(n);
      if (n.vis > 0.5) visCount++;

      if (reduce) { n.ox = 0; n.oy = 0; }
      else {
        var fx = -SPRING * n.ox, fy = -SPRING * n.oy;
        if (cur.on && n.vis > 0.05) {
          var dx = (n.x + n.ox) - cur.x, dy = (n.y + n.oy) - cur.y;
          var d = Math.sqrt(dx * dx + dy * dy) || 0.001;
          if (d < REP_R) { var force = (1 - d / REP_R) * REP_PUSH; fx += dx / d * force; fy += dy / d * force; }
        }
        n.vx = (n.vx + fx) * DAMP; n.vy = (n.vy + fy) * DAMP;
        n.ox += n.vx; n.oy += n.vy;
      }

      var X = n.x + n.ox, Y = n.y + n.oy;
      var sc = 0.2 + 0.8 * outBack(n.vis);
      n.g.style.opacity = Math.min(1, n.vis * 1.3);
      n.g.style.transform = "translate(" + X.toFixed(2) + "px," + Y.toFixed(2) + "px) scale(" + sc.toFixed(3) + ")";
      var breathe = 0.1 + 0.09 * (0.5 + 0.5 * Math.sin(t * 1.7 + n.id));
      n.halo.setAttribute("opacity", (breathe * n.vis).toFixed(3));
      var gb = n.kind === "hub" ? 0.6 : n.kind === "r1" ? 0.42 : 0.3;
      n.glowEl.setAttribute("cx", X.toFixed(2)); n.glowEl.setAttribute("cy", Y.toFixed(2));
      n.glowEl.setAttribute("opacity", (gb * n.vis).toFixed(3));
    });

    // edges: follow displaced endpoints, reveal by opacity, flow particles
    edges.forEach(function (ed) {
      var na = nodes[ed.a], nb = nodes[ed.b];
      var ev = reduce ? 1 : (buildStart === null ? 0 : Math.min(1, Math.max(0, (performance.now() - buildStart - ed.revealAt) / POP)));
      ed.vis = ev;
      var ax = na.x + na.ox, ay = na.y + na.oy, bx = nb.x + nb.ox, by = nb.y + nb.oy;
      ed.el.setAttribute("x1", ax.toFixed(2)); ed.el.setAttribute("y1", ay.toFixed(2));
      ed.el.setAttribute("x2", bx.toFixed(2)); ed.el.setAttribute("y2", by.toFixed(2));
      ed.el.setAttribute("opacity", smooth(ev).toFixed(3));
      if (reduce || ev < 0.9) { ed.particle.setAttribute("opacity", "0"); return; }
      var f = (t * (ed.main ? 0.28 : 0.2) + ed.pPhase) % 1;
      ed.particle.setAttribute("cx", (ax + (bx - ax) * f).toFixed(2));
      ed.particle.setAttribute("cy", (ay + (by - ay) * f).toFixed(2));
      ed.particle.setAttribute("opacity", (0.85 * Math.sin(f * Math.PI)).toFixed(2));
    });

    if (counterEl) counterEl.textContent = visCount;
    if (progressEl) progressEl.style.width = (built * 100).toFixed(1) + "%";

    // subtle whole-graph lean toward the pointer + micro push-in while building
    var s = reduce ? 1 : (0.965 + 0.035 * built);
    if (!reduce) { pxCur += (pxTgt - pxCur) * 0.06; pyCur += (pyTgt - pyCur) * 0.06; }
    svg.style.transform = "translate(" + (-pxCur * 9).toFixed(1) + "px," + (-pyCur * 7).toFixed(1) + "px) scale(" + s.toFixed(3) + ")";
    gGlow.style.transform = "translate(" + (-pxCur * 5).toFixed(1) + "px," + (-pyCur * 4).toFixed(1) + "px)";

    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // kick off the build when the hero enters view (fallback timer too)
  if (!reduce) {
    var heroEl = document.getElementById("top");
    if ("IntersectionObserver" in window && heroEl) {
      var io = new IntersectionObserver(function (ents) {
        ents.forEach(function (en) { if (en.isIntersecting) { startBuild(); io.disconnect(); } });
      }, { threshold: 0.3 });
      io.observe(heroEl);
    }
    setTimeout(startBuild, 900);
  }

  // ── Apple-style: light up the key word in each section title on view ──
  (function () {
    var hls = [].slice.call(document.querySelectorAll("h2 .hl"));
    if (!hls.length) return;
    if (reduce || !("IntersectionObserver" in window)) {
      hls.forEach(function (el) { el.classList.add("lit"); });
      return;
    }
    var hlIO = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("lit"); hlIO.unobserve(en.target); }
      });
    }, { threshold: 0.9, rootMargin: "0px 0px -10% 0px" });
    hls.forEach(function (el) { hlIO.observe(el); });
  })();

  // ── 5 · hero headline — words blur-in, then the key word lights up ──
  (function () {
    var h1 = document.getElementById("hero-h1");
    if (!h1) return;
    var words = [].slice.call(h1.querySelectorAll(".w"));
    var key = h1.querySelector(".hl");
    if (reduce || !words.length) {
      h1.classList.add("in"); if (key) key.classList.add("lit"); return;
    }
    words.forEach(function (w, i) { w.style.animationDelay = (140 + i * 95) + "ms"; });
    requestAnimationFrame(function () { requestAnimationFrame(function () { h1.classList.add("in"); }); });
    setTimeout(function () { if (key) key.classList.add("lit"); }, 140 + words.length * 95 + 640);
  })();

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
      qEl.textContent = ""; var i = 0;
      (function step() {
        if (i >= q.length) { setTimeout(done, 280); return; }   // beat before results
        var ch = q[i++]; qEl.textContent += ch;
        var d = 24 + Math.random() * 42;                        // humanised jitter
        if (ch === " ") d = 12;                                 // faster across spaces
        else if (ch === "(" || ch === ")" || ch === ",") d = 95;
        else if (ch === '"' || ch === "?") d = 165;             // linger on quotes / ?
        setTimeout(step, d);
      })();
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
