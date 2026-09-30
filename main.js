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

  /* Selector de raciones: recalcula las cantidades de los ingredientes */
  var FRACS = { 25: "¼", 50: "½", 75: "¾" };
  function fmtQty(v) {
    var whole = Math.floor(v + 1e-9), frac = Math.round((v - whole) * 100);
    if (!frac) return String(whole);
    var f = FRACS[frac] || String(Math.round((v - whole) * 100) / 100);
    return whole ? whole + " " + f : f;
  }
  function roundQty(v, unit) {
    if (unit === "w") return v < 20 ? Math.max(1, Math.round(v)) : Math.round(v / 5) * 5;
    if (v < 1) return Math.max(0.25, Math.round(v * 4) / 4);
    return Math.round(v * 2) / 2;
  }

  function initServings() {
    var box = document.querySelector("[data-servings]");
    if (!box) return;
    var base = parseInt(box.getAttribute("data-base"), 10);
    var MIN = 1, MAX = 8;
    var valEl = box.querySelector(".stepper-val b");
    var wordEl = box.querySelector(".stepper-val span");
    var btns = box.querySelectorAll(".stepper-btn");
    var note = document.querySelector("[data-servings-note]");
    var labels = document.querySelectorAll("[data-servings-label]");
    var items = document.querySelectorAll(".checklist li");
    var n = base;
    try {
      var saved = parseInt(localStorage.getItem("r20:servings"), 10);
      if (saved >= MIN && saved <= MAX) n = saved;
    } catch (e) { /* sin almacenamiento */ }

    function render() {
      var k = n / base;
      items.forEach(function (li) {
        var last = 1;
        li.querySelectorAll(".q, .pl").forEach(function (el) {
          if (el.classList.contains("q")) {
            var u = el.getAttribute("data-u");
            var q2 = el.getAttribute("data-q2");
            var lo = parseFloat(el.getAttribute("data-q")) * k;
            /* En los rangos (p. ej. 3–4 dientes) se redondea a unidades enteras */
            lo = q2 && u === "n" ? Math.max(1, Math.round(lo)) : roundQty(lo, u);
            var txt = fmtQty(lo);
            last = lo;
            if (q2) {
              var hi = parseFloat(q2) * k;
              hi = u === "n" ? Math.max(1, Math.round(hi)) : roundQty(hi, u);
              if (hi > lo) { txt += "–" + fmtQty(hi); last = hi; }
            }
            el.textContent = txt;
          } else {
            el.textContent = last > 1 ? el.getAttribute("data-many") : el.getAttribute("data-one");
          }
        });
      });
      var word = n === 1 ? "persona" : "personas";
      valEl.textContent = n;
      wordEl.textContent = word;
      labels.forEach(function (l) { l.textContent = n + " " + word; });
      btns[0].disabled = n <= MIN;
      btns[1].disabled = n >= MAX;
      if (note) note.hidden = n === base;
    }

    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        n = Math.min(MAX, Math.max(MIN, n + parseInt(b.getAttribute("data-step"), 10)));
        try { localStorage.setItem("r20:servings", String(n)); } catch (e) { /* sin almacenamiento */ }
        render();
      });
    });
    render();
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
    safe(initServings, "initServings");
    safe(initPrint, "initPrint");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
