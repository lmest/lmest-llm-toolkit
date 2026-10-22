/* Small offline runtime for navigation and optional user-triggered reveals. */
(function () {
  "use strict";

  const slides = Array.from(document.querySelectorAll(".lmest-slide"));
  const stage = document.querySelector("#lmest-stage");
  const count = document.querySelector("[data-lmest-count]");
  const progress = document.querySelector("[data-lmest-progress]");
  const progressTrack = progress && progress.parentElement;
  if (!stage || slides.length === 0) return;

  let active = 0;
  const clamp = (value) => Math.max(0, Math.min(slides.length - 1, value));

  function go(target, options) {
    const opts = options || {};
    const next = clamp(Number(target) - 1);
    active = Number.isFinite(next) ? next : 0;
    slides.forEach((slide, index) => {
      const selected = index === active;
      slide.classList.toggle("is-active", selected);
      slide.setAttribute("aria-hidden", selected ? "false" : "true");
      slide.querySelectorAll(".lmest-animate").forEach((item) => {
        item.classList.remove("is-revealed");
        if (selected) requestAnimationFrame(() => item.classList.add("is-revealed"));
      });
    });
    if (count) count.textContent = `${active + 1} / ${slides.length}`;
    if (progress) progress.style.width = `${((active + 1) / slides.length) * 100}%`;
    if (progressTrack) {
      progressTrack.setAttribute("aria-valuemin", "1");
      progressTrack.setAttribute("aria-valuemax", String(slides.length));
      progressTrack.setAttribute("aria-valuenow", String(active + 1));
    }
    stage.setAttribute("aria-label", `Slide ${active + 1} de ${slides.length}`);
    if (!opts.fromAddress && window.history && window.history.replaceState) {
      window.history.replaceState(null, "", `#slide-${active + 1}`);
    }
    return active + 1;
  }

  function next() { return go(active + 2); }
  function previous() { return go(active); }
  function fullscreen() {
    if (!document.fullscreenElement && stage.requestFullscreen) return stage.requestFullscreen();
    if (document.exitFullscreen) return document.exitFullscreen();
  }

  document.querySelectorAll('[data-lmest-action="next"]').forEach((button) => button.addEventListener("click", next));
  document.querySelectorAll('[data-lmest-action="previous"]').forEach((button) => button.addEventListener("click", previous));
  document.querySelectorAll('[data-lmest-action="fullscreen"]').forEach((button) => button.addEventListener("click", fullscreen));

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-lmest-reveal]");
    if (!button) return;
    const target = document.querySelector(button.getAttribute("data-lmest-reveal"));
    if (!target) return;
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", expanded ? "false" : "true");
    target.hidden = expanded;
    target.classList.toggle("is-visible", !expanded);
  });

  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const target = event.target;
    if (target && (target.isContentEditable || /INPUT|TEXTAREA|SELECT/.test(target.tagName))) return;
    if (["ArrowRight", "ArrowDown", "PageDown", " "].includes(event.key)) { event.preventDefault(); next(); }
    else if (["ArrowLeft", "ArrowUp", "PageUp"].includes(event.key)) { event.preventDefault(); previous(); }
    else if (event.key === "Home") { event.preventDefault(); go(1); }
    else if (event.key === "End") { event.preventDefault(); go(slides.length); }
    else if (event.key.toLowerCase() === "f") fullscreen();
  });

  let touchStart = null;
  stage.addEventListener("touchstart", (event) => { touchStart = event.changedTouches[0].clientX; }, { passive: true });
  stage.addEventListener("touchend", (event) => {
    if (touchStart === null) return;
    const delta = event.changedTouches[0].clientX - touchStart;
    if (Math.abs(delta) > 60) (delta < 0 ? next : previous)();
    touchStart = null;
  }, { passive: true });

  const hashSlide = window.location.hash.match(/^#slide-(\d+)$/);
  const querySlide = new URLSearchParams(window.location.search).get("slide");
  go(Number(querySlide || (hashSlide && hashSlide[1]) || 1), { fromAddress: true });
  window.LMEstDeck = { go, next, previous, fullscreen, count: slides.length, get current() { return active + 1; } };
})();
