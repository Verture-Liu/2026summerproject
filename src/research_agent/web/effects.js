/* PaleoRigor — Sequence Glass effects.
   Purely presentational: a slow field of DNA bases behind the page, where the
   bases beside a fragment break are drawn as damaged (C→T, G→A), and a moving
   dataflow while a run is in progress. It reads the page's state; it never
   changes what the app does. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ───────────────────────────────────────── the sequence field ── */
  const canvas = $("seqField");
  const ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;
  const COLUMN = 16, LINE = 17, LENGTH = 240;
  let width = 0, height = 0, columns = [], frameId = 0;

  const random = (seed) => {
    let state = seed >>> 0;
    return () => ((state = (state * 1664525 + 1013904223) >>> 0) / 4294967296);
  };
  const seed = () => {
    const next = random(5);
    columns = [];
    for (let x = 6; x < width; x += COLUMN) {
      const bases = [];
      for (let i = 0; i < LENGTH; i += 1) bases.push(next() < 0.045 ? " " : "ACGT"[(next() * 4) | 0]);
      columns.push({x, bases, speed: 0.008 + next() * 0.018, offset: next() * 1000, alpha: 0.07 + next() * 0.09});
    }
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
    ctx.font = '500 12px "Fira Code", "SF Mono", Menlo, Consolas, monospace';
    ctx.textAlign = "center";
    for (const column of columns) {
      const shift = column.offset + time * column.speed;
      const first = Math.floor(shift / LINE);
      for (let row = 0; row < height / LINE + 2; row += 1) {
        const k = (first + row) % LENGTH;
        const base = column.bases[k];
        if (base === " ") continue;
        const y = row * LINE - (shift % LINE);
        const atBreak = column.bases[(k + 1) % LENGTH] === " " || column.bases[(k - 1 + LENGTH) % LENGTH] === " ";
        if (atBreak) {
          ctx.globalAlpha = 0.42; ctx.fillStyle = "#e0603f";
          ctx.fillText(base === "C" ? "T" : base === "G" ? "A" : base, column.x, y);
        } else {
          ctx.globalAlpha = column.alpha; ctx.fillStyle = "#15213a";
          ctx.fillText(base, column.x, y);
        }
      }
    }
    ctx.globalAlpha = 1;
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

  /* ─────────────────────── the dataflow moves while a run is in progress ── */
  const execute = $("execute"), flow = $("flowStage");
  if (execute && flow) {
    const sync = () => flow.classList.toggle("is-running", execute.getAttribute("aria-busy") === "true");
    new MutationObserver(sync).observe(execute, {attributes: true, attributeFilter: ["aria-busy"]});
  }
})();
