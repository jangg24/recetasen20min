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
    var grid = document.querySelector("[data-grid]");
    if (!grid) return;
    var cards = grid.querySelectorAll(".card");
    var catChips = document.querySelectorAll(".chip[data-filter]");
    var timeChips = document.querySelectorAll(".chip[data-time]");
    var vegChip = document.querySelector("[data-veg-filter]");
    var favChip = document.querySelector("[data-fav-filter]");
    var input = document.querySelector("[data-search]");
    var countEl = document.querySelector("[data-results-count]");
    var noRes = document.querySelector("[data-no-results]");
    var st = { cat: "*", q: "", max: 0, veg: false, fav: false };

    function norm(t) {
      return t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    }
    function press(el, on) { el.classList.toggle("is-on", on); el.setAttribute("aria-pressed", on ? "true" : "false"); }

    function apply() {
      var favs = getFavs(), words = norm(st.q).split(/\s+/).filter(Boolean), n = 0;
      cards.forEach(function (card) {
        var q = card.getAttribute("data-q");
        var show = (st.cat === "*" || card.getAttribute("data-cat") === st.cat) &&
          (!st.max || parseInt(card.getAttribute("data-time"), 10) <= st.max) &&
          (!st.veg || card.getAttribute("data-veg") === "1") &&
          (!st.fav || favs.indexOf(card.getAttribute("data-slug")) !== -1) &&
          words.every(function (w) { return q.indexOf(w) !== -1; });
        card.hidden = !show;
        if (show) { card.classList.add("is-in"); n++; }
      });
      if (countEl) countEl.textContent = n === cards.length ? cards.length + " recetas" : n + (n === 1 ? " receta" : " recetas") + " de " + cards.length;
      if (noRes) {
        noRes.hidden = n > 0;
        noRes.querySelector("p").textContent = st.fav && !favs.length ?
          "Todavía no tienes favoritas: pulsa el corazón de una receta para guardarla." :
          "Ninguna receta coincide con esa búsqueda.";
      }
    }
    catChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        st.cat = chip.getAttribute("data-filter");
        catChips.forEach(function (c) { press(c, c === chip); });
        apply();
      });
    });
    timeChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        st.max = parseInt(chip.getAttribute("data-time"), 10);
        timeChips.forEach(function (c) { press(c, c === chip); });
        apply();
      });
    });
    if (vegChip) vegChip.addEventListener("click", function () { st.veg = !st.veg; press(vegChip, st.veg); apply(); });
    if (favChip) favChip.addEventListener("click", function () { st.fav = !st.fav; press(favChip, st.fav); apply(); });
    if (input) input.addEventListener("input", function () { st.q = input.value; apply(); });
    var reset = document.querySelector("[data-reset-filters]");
    if (reset) reset.addEventListener("click", function () {
      st = { cat: "*", q: "", max: 0, veg: false, fav: false };
      if (input) input.value = "";
      catChips.forEach(function (c) { press(c, c.getAttribute("data-filter") === "*"); });
      timeChips.forEach(function (c) { press(c, c.getAttribute("data-time") === "0"); });
      if (vegChip) press(vegChip, false);
      if (favChip) press(favChip, false);
      apply();
    });
    document.addEventListener("r20:favs", apply);
    apply();
  }

  /* Favoritos (se guardan en el navegador) */
  var FAV_KEY = "r20:favoritas";
  function getFavs() {
    try {
      var f = JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
      return Array.isArray(f) ? f : [];
    } catch (e) { return []; }
  }
  function initFavs() {
    var btns = document.querySelectorAll("[data-fav]");
    var countEl = document.querySelector("[data-fav-count]");
    function render() {
      var favs = getFavs();
      btns.forEach(function (b) {
        var on = favs.indexOf(b.getAttribute("data-fav")) !== -1;
        b.classList.toggle("is-on", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
        var t = b.querySelector(".fav-txt");
        if (t) t.textContent = on ? "Guardada" : "Guardar";
      });
      if (countEl) countEl.textContent = favs.length;
    }
    btns.forEach(function (b) {
      b.addEventListener("click", function (ev) {
        ev.preventDefault();
        var favs = getFavs(), slug = b.getAttribute("data-fav"), i = favs.indexOf(slug);
        if (i === -1) favs.push(slug); else favs.splice(i, 1);
        try { localStorage.setItem(FAV_KEY, JSON.stringify(favs)); } catch (e) { /* sin almacenamiento */ }
        render();
        if (typeof toast === "function" && b.classList.contains("btn--fav")) toast(i === -1 ? "Guardada en favoritas" : "Quitada de favoritas");
        document.dispatchEvent(new Event("r20:favs"));
      });
    });
    render();
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

  function bindTimer(btn) {
    (function () {
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
    })();
  }

  function initTimers() {
    document.querySelectorAll(".recipe-steps .timer").forEach(bindTimer);
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
      box.setAttribute("data-current", n);
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

  /* ---------- Utilidades compartidas ---------- */
  function store(key, val) {
    try {
      if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) { return null; }
  }
  function esc(t) {
    return String(t).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function recipes() { return window.__RECETAS__ || []; }
  function bySlug(slug) {
    return recipes().filter(function (r) { return r.slug === slug; })[0];
  }
  function personas(n) { return n + (n === 1 ? " persona" : " personas"); }
  function toast(msg) {
    var t = document.querySelector("[data-toast]");
    if (!t) return;
    t.textContent = msg;
    t.classList.add("is-on");
    clearTimeout(t._h);
    t._h = setTimeout(function () { t.classList.remove("is-on"); }, 2600);
  }
  function copyText(text, okMsg) {
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      toast(ok ? okMsg : "No se ha podido copiar");
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { toast(okMsg); }, fallback);
    } else fallback();
  }

  /* Cantidades de un ingrediente en texto: [200] g, [3-4], {uno|varios} */
  var TOKEN = /(\[[^\]]+\]|\{[^}]+\})/;
  function parseIngredient(raw) {
    var parts = raw.split(TOKEN), nums = [];
    parts.forEach(function (tok, i) {
      if (tok.charAt(0) === "[") {
        var r = tok.slice(1, -1).split("-");
        var unit = /^\s*(g|ml)\b/.test(parts[i + 1] || "") ? "w" : "n";
        nums.push({ lo: parseFloat(r[0]), hi: r[1] ? parseFloat(r[1]) : null, u: unit });
      }
    });
    return { parts: parts, nums: nums, key: raw.replace(/\[[^\]]+\]/g, "[#]") };
  }
  function renderParsed(p, nums, asHtml) {
    var k = 0, last = 1, out = "";
    p.parts.forEach(function (tok) {
      if (tok.charAt(0) === "[") {
        var q = nums[k++], txt;
        if (q.hi !== null) {
          var lo = q.u === "n" ? Math.max(1, Math.round(q.lo)) : roundQty(q.lo, q.u);
          var hi = q.u === "n" ? Math.max(1, Math.round(q.hi)) : roundQty(q.hi, q.u);
          txt = hi > lo ? fmtQty(lo) + "–" + fmtQty(hi) : fmtQty(lo);
          last = hi;
        } else {
          var v = roundQty(q.lo, q.u);
          txt = fmtQty(v); last = v;
        }
        out += asHtml ? "<b>" + txt + "</b>" : txt;
      } else if (tok.charAt(0) === "{") {
        var f = tok.slice(1, -1).split("|");
        out += esc(last > 1 ? f[1] : f[0]);
      } else out += asHtml ? esc(tok) : tok;
    });
    return out;
  }

  /* ---------- Compartir ---------- */
  function initShare() {
    var b = document.querySelector("[data-share]");
    if (!b) return;
    b.addEventListener("click", function () {
      var title = document.title, url = location.href;
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () { /* cancelado */ });
      } else copyText(url, "Enlace copiado: pégalo donde quieras compartirlo");
    });
  }

  /* ---------- Lista de la compra ---------- */
  var LIST_KEY = "r20:lista";
  function getList() {
    var l = store(LIST_KEY);
    return Array.isArray(l) ? l.filter(function (it) { return bySlug(it.slug); }) : [];
  }
  function setList(l) { store(LIST_KEY, l); updateListCount(); }
  function updateListCount() {
    var n = getList().length;
    document.querySelectorAll("[data-list-count]").forEach(function (el) {
      el.textContent = n; el.hidden = n === 0;
    });
  }

  function initAddToList() {
    var b = document.querySelector("[data-add-list]");
    if (!b) return;
    var slug = b.getAttribute("data-slug");
    var box = document.querySelector("[data-servings]");
    function current() { return parseInt((box && box.getAttribute("data-current")) || bySlug(slug).servings, 10); }
    function label() {
      var it = getList().filter(function (x) { return x.slug === slug; })[0];
      if (!it) b.textContent = "Añadir a la lista";
      else if (it.n === current()) b.textContent = "En tu lista · verla";
      else b.textContent = "Actualizar a " + personas(current());
      b.classList.toggle("is-in-list", !!it && it.n === current());
    }
    b.addEventListener("click", function () {
      var l = getList(), n = current();
      var it = l.filter(function (x) { return x.slug === slug; })[0];
      if (it && it.n === n) { location.href = "lista.html"; return; }
      if (it) it.n = n; else l.push({ slug: slug, n: n });
      setList(l);
      toast("Añadida a la lista para " + personas(n));
      label();
    });
    if (box) box.addEventListener("click", function () { setTimeout(label, 0); });
    label();
  }

  function buildShopping(list) {
    var map = {}, order = [];
    list.forEach(function (it) {
      var r = bySlug(it.slug), k = it.n / r.servings;
      r.ingredients.forEach(function (raw) {
        var p = parseIngredient(raw);
        var nums = p.nums.map(function (q) { return { lo: q.lo * k, hi: q.hi === null ? null : q.hi * k, u: q.u }; });
        var key = p.nums.length ? p.key : "t:" + raw.toLowerCase();
        if (!map[key]) { map[key] = { p: p, nums: nums, from: [r.title] }; order.push(key); return; }
        var m = map[key];
        if (m.from.indexOf(r.title) === -1) m.from.push(r.title);
        m.nums.forEach(function (q, i) {
          q.lo += nums[i].lo;
          if (q.hi !== null) q.hi += nums[i].hi;
        });
      });
    });
    return order.map(function (key) { return map[key]; });
  }

  function initShoppingPage() {
    var wrap = document.querySelector("[data-shop]");
    if (!wrap) return;
    var empty = document.querySelector("[data-shop-empty]");
    var recEl = document.querySelector("[data-shop-recipes]");
    var itemsEl = document.querySelector("[data-shop-items]");
    var totalEl = document.querySelector("[data-shop-total]");
    var CHECK_KEY = "r20:lista-hecho";
    var items = [];

    function render() {
      var list = getList();
      empty.hidden = list.length > 0;
      wrap.hidden = list.length === 0;
      if (!list.length) return;
      var checked = store(CHECK_KEY) || [];
      recEl.innerHTML = list.map(function (it, i) {
        var r = bySlug(it.slug);
        return '<li><a href="receta-' + r.slug + '.html">' + esc(r.title) + '</a>' +
          '<span class="shop-n"><button type="button" class="mini" data-n="-1" data-i="' + i + '" aria-label="Una ración menos">−</button>' +
          '<span>' + personas(it.n) + '</span>' +
          '<button type="button" class="mini" data-n="1" data-i="' + i + '" aria-label="Una ración más">+</button></span>' +
          '<button type="button" class="linkbtn" data-rm="' + i + '">Quitar</button></li>';
      }).join("");
      items = buildShopping(list);
      totalEl.textContent = items.length + " productos";
      itemsEl.innerHTML = items.map(function (m) {
        var txt = renderParsed(m.p, m.nums, false);
        var on = checked.indexOf(txt) !== -1;
        return '<li><label><input type="checkbox"' + (on ? " checked" : "") + ' data-txt="' + esc(txt) + '"><span>' +
          renderParsed(m.p, m.nums, true) + (m.from.length > 1 ? ' <small>(' + m.from.length + ' recetas)</small>' : "") +
          "</span></label></li>";
      }).join("");
    }
    function asText() {
      var list = getList();
      return "Lista de la compra\n\nRecetas: " + list.map(function (it) {
        return bySlug(it.slug).title + " (" + personas(it.n) + ")";
      }).join(", ") + "\n\n" + items.map(function (m) { return "- " + renderParsed(m.p, m.nums, false); }).join("\n");
    }
    recEl.addEventListener("click", function (ev) {
      var t = ev.target.closest("button");
      if (!t) return;
      var l = getList();
      if (t.hasAttribute("data-rm")) l.splice(+t.getAttribute("data-rm"), 1);
      else {
        var it = l[+t.getAttribute("data-i")];
        it.n = Math.min(8, Math.max(1, it.n + parseInt(t.getAttribute("data-n"), 10)));
      }
      setList(l); render();
    });
    itemsEl.addEventListener("change", function () {
      var done = [];
      itemsEl.querySelectorAll("input:checked").forEach(function (c) { done.push(c.getAttribute("data-txt")); });
      store(CHECK_KEY, done);
    });
    document.querySelector("[data-shop-copy]").addEventListener("click", function () { copyText(asText(), "Lista copiada"); });
    document.querySelector("[data-shop-print]").addEventListener("click", function () { window.print(); });
    document.querySelector("[data-shop-share]").addEventListener("click", function () {
      if (navigator.share) navigator.share({ title: "Lista de la compra", text: asText() }).catch(function () {});
      else copyText(asText(), "Tu navegador no permite enviar: la lista se ha copiado");
    });
    document.querySelector("[data-shop-clear]").addEventListener("click", function () {
      if (!confirm("¿Vaciar la lista de la compra?")) return;
      setList([]); store(CHECK_KEY, []); render();
    });
    render();
  }

  /* ---------- ¿Qué tengo en la nevera? ---------- */
  function initFridge() {
    var box = document.querySelector("[data-fridge-results]");
    if (!box) return;
    var chips = document.querySelectorAll(".chip--ing");
    var countEl = document.querySelector("[data-fridge-count]");
    var KEY = "r20:nevera";
    var have = store(KEY) || [];

    function render() {
      chips.forEach(function (c) {
        var on = have.indexOf(c.getAttribute("data-ing")) !== -1;
        c.classList.toggle("is-on", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      countEl.textContent = have.length ? (have.length === 1 ? "1 ingrediente marcado" : have.length + " ingredientes marcados") : "Nada marcado todavía";
      if (!have.length) {
        box.innerHTML = '<p class="fridge-hint">Marca al menos un ingrediente para ver resultados.</p>';
        return;
      }
      var res = recipes().map(function (r) {
        var missing = r.need.filter(function (n) { return have.indexOf(n) === -1; });
        return { r: r, missing: missing, match: r.need.length - missing.length };
      }).filter(function (x) { return x.match > 0; });
      res.sort(function (a, b) { return a.missing.length - b.missing.length || b.match - a.match; });
      if (!res.length) {
        box.innerHTML = '<p class="fridge-hint">Ninguna receta usa esos ingredientes como principales.</p>';
        return;
      }
      box.innerHTML = res.map(function (x) {
        var ok = !x.missing.length;
        return '<a class="fr' + (ok ? " fr--ok" : "") + '" href="receta-' + x.r.slug + '.html">' +
          (x.r.img ? '<img src="' + x.r.img + '" alt="" loading="lazy">' : '<span class="fr-ph"></span>') +
          '<span class="fr-body"><strong>' + esc(x.r.title) + '</strong>' +
          '<span class="fr-meta">' + (ok ? "Tienes todo lo principal" :
            "Te falta: " + esc(x.missing.join(", "))) + ' · ' + x.r.total + ' min</span></span>' +
          '<span class="fr-badge" aria-hidden="true">' + (ok ? "✓" : x.missing.length) + '</span></a>';
      }).join("");
    }
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        var ing = c.getAttribute("data-ing"), i = have.indexOf(ing);
        if (i === -1) have.push(ing); else have.splice(i, 1);
        store(KEY, have); render();
      });
    });
    document.querySelector("[data-fridge-clear]").addEventListener("click", function () {
      have = []; store(KEY, have); render();
    });
    render();
  }

  /* ---------- Modo cocina ---------- */
  function initCookMode() {
    var openBtn = document.querySelector("[data-cook]");
    if (!openBtn) return;
    var title = document.querySelector(".recipe-title").textContent;
    var stepsSrc = Array.prototype.slice.call(document.querySelectorAll(".recipe-steps .step"));
    var N = stepsSrc.length, cur = 0, lock = null, built = false;
    var dlg = document.createElement("dialog");
    dlg.className = "cook";
    dlg.setAttribute("aria-label", "Modo cocina: " + title);
    dlg.innerHTML =
      '<div class="cook-top"><span class="cook-title"></span><span class="cook-count"></span>' +
      '<button type="button" class="cook-close" aria-label="Salir del modo cocina">✕</button></div>' +
      '<div class="cook-bar"><span></span></div>' +
      '<div class="cook-stage"></div>' +
      '<div class="cook-nav"><button type="button" class="cook-prev">← Anterior</button>' +
      '<button type="button" class="cook-next">Siguiente →</button></div>' +
      '<p class="cook-lock" hidden>La pantalla se mantendrá encendida mientras cocinas.</p>';
    dlg.querySelector(".cook-title").textContent = title;
    var stage = dlg.querySelector(".cook-stage");
    var slides = [];

    function build() {
      if (built) return;
      built = true;
      var ings = Array.prototype.map.call(document.querySelectorAll(".checklist li > label > span"), function (s) {
        return "<li>" + esc(s.textContent.replace(/\s+/g, " ").trim()) + "</li>";
      }).join("");
      var tools = Array.prototype.map.call(document.querySelectorAll(".recipe-side .bullets")[0].children, function (li) {
        return "<li>" + esc(li.textContent) + "</li>";
      }).join("");
      var html = '<section class="cook-slide cook-intro"><p class="kicker">Antes de empezar</p><h2>Ten a mano</h2>' +
        '<div class="cook-cols"><div><h3>Ingredientes</h3><ul>' + ings + '</ul></div>' +
        '<div><h3>Utensilios</h3><ul>' + tools + '</ul></div></div></section>';
      stepsSrc.forEach(function (st, i) {
        var t = st.querySelector(".timer");
        html += '<section class="cook-slide"><span class="cook-n">' + (i + 1) + '</span><p class="cook-text">' +
          esc(st.querySelector(".step-body p").textContent) + "</p>" +
          (t ? '<button type="button" class="timer timer--big" data-min="' + t.getAttribute("data-min") + '"><span class="timer-ico" aria-hidden="true">◷</span><span class="timer-txt">Temporizador ' + t.getAttribute("data-min") + ' min</span></button>' : "") +
          "</section>";
      });
      html += '<section class="cook-slide cook-end"><span class="cook-done" aria-hidden="true">✓</span><h2>Receta terminada</h2>' +
        '<p>¡Que aproveche!</p><button type="button" class="btn cook-exit">Volver a la receta</button></section>';
      stage.innerHTML = html;
      slides = stage.querySelectorAll(".cook-slide");
      stage.querySelectorAll(".timer").forEach(bindTimer);
      stage.querySelector(".cook-exit").addEventListener("click", close);
    }
    function show(i) {
      cur = Math.max(0, Math.min(slides.length - 1, i));
      slides.forEach(function (s, k) { s.classList.toggle("is-on", k === cur); });
      var label = cur === 0 ? "Preparación" : cur <= N ? "Paso " + cur + " de " + N : "Terminado";
      dlg.querySelector(".cook-count").textContent = label;
      dlg.querySelector(".cook-bar span").style.transform = "scaleX(" + (cur / (slides.length - 1)) + ")";
      dlg.querySelector(".cook-prev").disabled = cur === 0;
      var next = dlg.querySelector(".cook-next");
      next.hidden = cur === slides.length - 1;
      next.textContent = cur === 0 ? "Empezar →" : cur === N ? "Terminar ✓" : "Siguiente →";
      next.focus({ preventScroll: true });
    }
    function wake() {
      if (!("wakeLock" in navigator) || document.visibilityState !== "visible") return;
      navigator.wakeLock.request("screen").then(function (l) {
        lock = l; dlg.querySelector(".cook-lock").hidden = false;
      }).catch(function () { /* no permitido */ });
    }
    function open() {
      build();
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
      document.documentElement.classList.add("is-cooking");
      show(0);
      wake();
    }
    function close() {
      if (dlg.close) dlg.close(); else dlg.removeAttribute("open");
    }
    dlg.addEventListener("close", function () {
      document.documentElement.classList.remove("is-cooking");
      if (lock) { lock.release().catch(function () {}); lock = null; }
    });
    document.addEventListener("visibilitychange", function () {
      if (dlg.open && document.visibilityState === "visible") wake();
    });
    dlg.querySelector(".cook-close").addEventListener("click", close);
    dlg.querySelector(".cook-prev").addEventListener("click", function () { show(cur - 1); });
    dlg.querySelector(".cook-next").addEventListener("click", function () { show(cur + 1); });
    dlg.addEventListener("keydown", function (ev) {
      if (ev.target.closest && ev.target.closest(".timer")) return;
      if (ev.key === "ArrowRight") { ev.preventDefault(); show(cur + 1); }
      if (ev.key === "ArrowLeft") { ev.preventDefault(); show(cur - 1); }
    });
    var x0 = null;
    stage.addEventListener("touchstart", function (ev) { x0 = ev.touches[0].clientX; }, { passive: true });
    stage.addEventListener("touchend", function (ev) {
      if (x0 === null) return;
      var dx = ev.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 60) show(cur + (dx < 0 ? 1 : -1));
      x0 = null;
    });
    document.body.appendChild(dlg);
    openBtn.addEventListener("click", open);
  }

  function initPrint() {
    var b = document.querySelector("[data-print]");
    if (b) b.addEventListener("click", function () { window.print(); });
  }

  function boot() {
    safe(initReveals, "initReveals");
    safe(initProgress, "initProgress");
    safe(initFavs, "initFavs");
    safe(initFilters, "initFilters");
    safe(initSteps, "initSteps");
    safe(initTimers, "initTimers");
    safe(initServings, "initServings");
    safe(initPrint, "initPrint");
    safe(updateListCount, "updateListCount");
    safe(initShare, "initShare");
    safe(initAddToList, "initAddToList");
    safe(initShoppingPage, "initShoppingPage");
    safe(initFridge, "initFridge");
    safe(initCookMode, "initCookMode");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
