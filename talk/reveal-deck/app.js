// Count-up numbers: any fragment with data-count animates 0 -> value when it appears.
function runCount(el) {
  const to = parseFloat(el.dataset.count);
  const dec = parseInt(el.dataset.dec || "0", 10);
  const ms = parseInt(el.dataset.ms || "900", 10);
  const suffix = el.dataset.suffix || "";
  const target = el.querySelector(".tv") || el;
  cancelAnimationFrame(el._raf);
  const t0 = performance.now();
  const step = (now) => {
    const p = Math.min(1, (now - t0) / ms);
    const eased = el.classList.contains("timer") ? p : 1 - Math.pow(1 - p, 3);
    target.textContent = (to * eased).toFixed(dec) + suffix;
    if (p < 1) el._raf = requestAnimationFrame(step);
  };
  el._raf = requestAnimationFrame(step);
}
function resetCount(el) {
  cancelAnimationFrame(el._raf);
  const dec = parseInt(el.dataset.dec || "0", 10);
  const target = el.querySelector(".tv") || el;
  target.textContent = (0).toFixed(dec) + (el.dataset.suffix || "");
}

Reveal.initialize({
  width: 1280,
  height: 720,
  margin: 0,
  minScale: 0.2,
  maxScale: 2.0,
  center: false,
  hash: true,
  slideNumber: "c/t",
  progress: true,
  controls: true,
  transition: "fade",
  transitionSpeed: "fast",
  backgroundTransition: "fade",
  fragments: true,
  pdfSeparateFragments: false,
  plugins: [RevealHighlight, RevealNotes],
}).then(() => {
  const counters = (f) => [f, ...f.querySelectorAll("[data-count]")].filter((x) => x.dataset.count !== undefined);
  Reveal.on("fragmentshown", (e) => e.fragments.forEach((f) => counters(f).forEach(runCount)));
  Reveal.on("fragmenthidden", (e) => e.fragments.forEach((f) => counters(f).forEach(resetCount)));
  // leaving a slide resets its counters so replays are clean
  Reveal.on("slidechanged", (e) => {
    if (e.previousSlide) e.previousSlide.querySelectorAll("[data-count]").forEach((el) => {
      if (!el.classList.contains("visible")) resetCount(el);
    });
  });
});
