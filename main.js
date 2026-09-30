(function () {
  "use strict";

  var doc = document.documentElement;
  doc.classList.add("js");

  function safe(fn, name) {
    try { fn(); } catch (err) { console.warn("[" + name + "]", err); }
  }

  /* Aparición al hacer scroll (threshold bajo + red de seguridad de 6 s) */
  function initReveals() {
    var items = document.querySelectorAll(".reveal, .dial");
    if (!("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.02, rootMargin: "0px 0px -6% 0px" });
    items.forEach(function (el) { io.observe(el); });
    setTimeout(function () {
      items.forEach(function (el) { el.classList.add("is-in"); });
    }, 6000);
  }

  /* Barra de progreso de lectura */
  function initProgress() {
    var bar = document.querySelector(".progress span");
    if (!bar) return;
    var ticking = false;
    function update() {
      var max = doc.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, window.scrollY / max) : 0;
      bar.style.transform = "scaleX(" + p + ")";
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* Filtro de recetas por tipo */
  function initFilters() {
    var chips = document.querySelectorAll(".chip[data-filter]");
    var cards = document.querySelectorAll("[data-grid] .card");
    if (!chips.length) return;
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var f = chip.getAttribute("data-filter");
        chips.forEach(function (c) {
          c.classList.toggle("is-on", c === chip);
          c.setAttribute("aria-pressed", c === chip ? "true" : "false");
        });
        cards.forEach(function (card) {
          var show = f === "*" || card.getAttribute("data-cat") === f;
          card.hidden = !show;
          if (show) card.classList.add("is-in");
        });
      });
    });
  }

  /* Marcar pasos como hechos (se guarda en el navegador) */
  function initSteps() {
    var steps = document.querySelectorAll(".step");
    if (!steps.length) return;
    var key = "r20:" + location.pathname;
    var saved = [];
    try { saved = JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { saved = []; }
    function persist() {
      var done = [];
      steps.forEach(function (s, i) { if (s.classList.contains("is-done")) done.push(i); });
      try { localStorage.setItem(key, JSON.stringify(done)); } catch (e) { /* sin almacenamiento */ }
    }
    steps.forEach(function (step, i) {
      if (saved.indexOf(i) !== -1) step.classList.add("is-done");
      step.setAttribute("title", "Haz clic para marcar el paso como hecho");
      step.addEventListener("click", function (ev) {
        if (ev.target.closest(".timer")) return;
        step.classList.toggle("is-done");
        persist();
      });
    });
  }

  /* Temporizadores por paso */
  function beep() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      var ctx = new Ctx();
      [0, 0.35, 0.7].forEach(function (t) {
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = 880;
        g.gain.setValueAtTime(0.0001, ctx.currentTime + t);
        g.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.28);
        o.connect(g); g.connect(ctx.destination);
        o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.3);
      });
    } catch (e) { /* sin audio */ }
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
  }

  function fmt(s) {
    var m = Math.floor(s / 60), r = s % 60;
    return m + ":" + (r < 10 ? "0" : "") + r;
  }

  function initTimers() {
    document.querySelectorAll(".timer").forEach(function (btn) {
      var txt = btn.querySelector(".timer-txt");
      var label = txt.textContent;
      var total = parseInt(btn.getAttribute("data-min"), 10) * 60;
      var id = null, end = 0;
      function reset() {
        clearInterval(id); id = null;
        btn.classList.remove("is-running", "is-finished");
        txt.textContent = label;
      }
      function tick() {
        var left = Math.max(0, Math.round((end - Date.now()) / 1000));
        txt.textContent = fmt(left) + " · detener";
        if (left <= 0) {
          clearInterval(id); id = null;
          btn.classList.remove("is-running");
          btn.classList.add("is-finished");
          txt.textContent = "¡Tiempo! · reiniciar";
          beep();
        }
      }
      btn.addEventListener("click", function () {
        if (id || btn.classList.contains("is-finished")) { reset(); return; }
        end = Date.now() + total * 1000;
        btn.classList.add("is-running");
        tick();
        id = setInterval(tick, 500);
      });
    });
  }

  function initPrint() {
    var b = document.querySelector("[data-print]");
    if (b) b.addEventListener("click", function () { window.print(); });
  }

  function boot() {
    safe(initReveals, "initReveals");
    safe(initProgress, "initProgress");
    safe(initFilters, "initFilters");
    safe(initSteps, "initSteps");
    safe(initTimers, "initTimers");
    safe(initPrint, "initPrint");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
