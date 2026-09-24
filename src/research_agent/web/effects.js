/* PaleoRigor — Neural HUD effects.
   Purely presentational: the neural field behind the page, the light that
   follows the pointer across a module, the radar that counts completed
   stages, and particles on the dataflow while a run is in progress.
   It reads the page's state; it never changes what the app does. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ─────────────────────────────────────────── the neural field ── */
  const canvas = $("neuralField");
  const ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;
  let width = 0, height = 0, points = [], pulses = [], frameId = 0, lastPulse = 0;
  let mouseX = -9999, mouseY = -9999;
  const LINK = 150, LINK2 = LINK * LINK, REACH = 190;

  const seed = () => {
    const count = Math.max(40, Math.min(110, Math.round((width * height) / 16000)));
    points = Array.from({length: count}, () => ({
      x: Math.random() * width, y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.5 + 0.9, cyan: Math.random() < 0.38
    }));
    pulses = [];
  };
  const resize = () => {
    if (!ctx) return;
    const ratio = Math.min(2, window.devicePixelRatio || 1);
    width = canvas.clientWidth; height = canvas.clientHeight;
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    seed();
  };
  const draw = (time) => {
    ctx.clearRect(0, 0, width, height);
    for (const p of points) {
      const dx = mouseX - p.x, dy = mouseY - p.y;
      if (dx * dx + dy * dy < REACH * REACH) { p.vx += dx * 0.000035; p.vy += dy * 0.000035; }
      const speed = Math.hypot(p.vx, p.vy);
      if (speed > 0.9) { p.vx *= 0.9 / speed; p.vy *= 0.9 / speed; }
      if (speed < 0.08) { p.vx += (Math.random() - 0.5) * 0.04; p.vy += (Math.random() - 0.5) * 0.04; }
      p.vx *= 0.996; p.vy *= 0.996;
      p.x += p.vx; p.y += p.vy;
      if (p.x < -20) p.x = width + 20; else if (p.x > width + 20) p.x = -20;
      if (p.y < -20) p.y = height + 20; else if (p.y > height + 20) p.y = -20;
    }
    ctx.lineWidth = 1;
    for (let i = 0; i < points.length; i++) {
      const a = points[i];
      for (let j = i + 1; j < points.length; j++) {
        const b = points[j], dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy;
        if (d2 < LINK2) {
          const alpha = (1 - d2 / LINK2) * 0.28;
          ctx.strokeStyle = a.cyan || b.cyan ? `rgba(63,226,255,${alpha})` : `rgba(150,125,255,${alpha})`;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    for (const p of points) {
      const d = Math.hypot(p.x - mouseX, p.y - mouseY);
      if (d < REACH) {
        ctx.strokeStyle = `rgba(63,226,255,${(1 - d / REACH) * 0.5})`;
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(mouseX, mouseY); ctx.stroke();
      }
    }
    if (time - lastPulse > 140 && pulses.length < 22 && points.length) {
      lastPulse = time;
      const a = points[(Math.random() * points.length) | 0];
      let best = null, bestD2 = LINK2;
      for (const b of points) {
        if (b === a) continue;
        const dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy;
        if (d2 < bestD2 && Math.random() < 0.55) { bestD2 = d2; best = b; }
      }
      if (best) pulses.push({a, b: best, k: 0, step: 0.012 + Math.random() * 0.02});
    }
    for (let i = pulses.length - 1; i >= 0; i--) {
      const q = pulses[i];
      q.k += q.step;
      if (q.k >= 1) { pulses.splice(i, 1); continue; }
      const x = q.a.x + (q.b.x - q.a.x) * q.k, y = q.a.y + (q.b.y - q.a.y) * q.k;
      const glow = ctx.createRadialGradient(x, y, 0, x, y, 8);
      glow.addColorStop(0, "rgba(200,248,255,.95)"); glow.addColorStop(1, "rgba(63,226,255,0)");
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2); ctx.fill();
    }
    for (const p of points) {
      ctx.fillStyle = p.cyan ? "rgba(128,238,255,.9)" : "rgba(178,160,255,.85)";
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
    }
  };
  const loop = (time) => { draw(time); frameId = window.requestAnimationFrame(loop); };
  const start = () => {
    if (!ctx) return;
    window.cancelAnimationFrame(frameId);
    if (reduceMotion) { draw(0); return; }
    frameId = window.requestAnimationFrame(loop);
  };
  if (ctx) {
    resize();
    start();
    window.addEventListener("resize", () => { resize(); if (reduceMotion) draw(0); });
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) window.cancelAnimationFrame(frameId); else start();
    });
  }

  /* ───────────────────────────── pointer: field pull and module light ── */
  if (finePointer && !reduceMotion) {
    window.addEventListener("pointermove", (event) => { mouseX = event.clientX; mouseY = event.clientY; }, {passive: true});
    document.addEventListener("pointerleave", () => { mouseX = -9999; mouseY = -9999; });
    document.querySelectorAll(".card").forEach((card) => {
      card.addEventListener("pointermove", (event) => {
        const box = card.getBoundingClientRect();
        card.style.setProperty("--mx", `${event.clientX - box.left}px`);
        card.style.setProperty("--my", `${event.clientY - box.top}px`);
      });
    });
  }

  /* ─────────────────────────── the radar counts completed stages ── */
  const RING = 527.8;
  const core = $("core"), ring = $("coreRing"), number = $("coreNum"), strip = $("progressSteps");
  const updateCore = () => {
    if (!core || !strip) return;
    const stages = [...strip.querySelectorAll(".progress-step")];
    const done = stages.filter((stage) => stage.classList.contains("done")).length;
    const failed = stages.some((stage) => stage.classList.contains("failed"));
    number.replaceChildren(document.createTextNode(String(done)));
    const total = document.createElement("i");
    total.textContent = `/${stages.length}`;
    number.append(total);
    ring.style.strokeDashoffset = String(RING * (1 - done / Math.max(1, stages.length)));
    core.classList.toggle("complete", stages.length > 0 && done === stages.length);
    core.classList.toggle("failed", failed);
  };
  if (strip) {
    new MutationObserver(updateCore).observe(strip, {subtree: true, attributes: true, attributeFilter: ["class"]});
    updateCore();
  }

  /* ─────────────────────── particles on the dataflow while running ── */
  const execute = $("execute"), flow = $("flowStage");
  if (execute && flow) {
    const sync = () => flow.classList.toggle("is-running", execute.getAttribute("aria-busy") === "true");
    new MutationObserver(sync).observe(execute, {attributes: true, attributeFilter: ["aria-busy"]});
  }
})();
