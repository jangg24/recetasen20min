#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera el sitio estático a partir de tools/recipes.py y assets/credits.json.

    python3 tools/build.py

Crea/actualiza: index.html, receta-<slug>.html y creditos.html en la raíz.
Si una foto (assets/img/<slug>.webp) no existe todavía, la página muestra un
marco tipográfico en su lugar, sin enlaces rotos.
"""

import datetime
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recipes import RECIPES  # noqa: E402

SITE = "Recetas en 20 minutos"
VERSION = datetime.date.today().strftime("%Y%m%d")
FONTS = ("https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..800;"
         "1,6..96,400..800&family=Inter+Tight:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@"
         "0,8..60,300..600;1,8..60,300..600&display=swap")

e = html.escape
LICENSE_NAMES = {"cc0": "CC0", "pdm": "Dominio público", "by": "CC BY", "by-sa": "CC BY-SA"}


def load_credits():
    p = ROOT / "assets" / "credits.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


CREDITS = load_credits()


def img_path(slug):
    rel = f"assets/img/{slug}.webp"
    return rel if (ROOT / rel).exists() else None


def figure(r, cls, eager=False, sizes=""):
    """Foto del plato o, si aún no existe, un marco tipográfico."""
    src = img_path(r["slug"])
    if src:
        load = 'loading="eager" fetchpriority="high" decoding="sync"' if eager else 'loading="lazy" decoding="async"'
        cap = ""
        c = CREDITS.get(r["slug"])
        if c and cls == "recipe-fig":
            lic = LICENSE_NAMES.get(c.get("license", ""), c.get("license", "").upper())
            cap = (f'<figcaption>Foto ilustrativa: «{e(c.get("title") or "Sin título")}», '
                   f'{e(c.get("creator") or "autor desconocido")} · {e(lic)} {e(c.get("license_version") or "")} · '
                   f'<a href="creditos.html">créditos</a></figcaption>')
        return (f'<figure class="{cls}"><img src="{src}?v={VERSION}" alt="{e(r["title"])}" {load}>{cap}</figure>')
    return (f'<figure class="{cls} is-empty" role="img" aria-label="Foto pendiente: {e(r["title"])}">'
            f'<span class="ph-mark" aria-hidden="true">{r["total"]}′</span>'
            f'<span class="ph-name">{e(r["title"])}</span></figure>')


def dial(total, big=False):
    """Anillo que muestra los minutos de la receta sobre 20."""
    frac = min(total, 20) / 20
    cls = "dial dial--big" if big else "dial"
    return (f'<span class="{cls}" style="--frac:{frac:.3f}" aria-label="{total} minutos">'
            f'<svg viewBox="0 0 44 44" aria-hidden="true"><circle class="dial-track" cx="22" cy="22" r="19"/>'
            f'<circle class="dial-fill" cx="22" cy="22" r="19" pathLength="100"/></svg>'
            f'<span class="dial-num">{total}<small>min</small></span></span>')


def head(title, desc, preload=None):
    pre = f'\n  <link rel="preload" as="image" href="{preload}?v={VERSION}" fetchpriority="high">' if preload else ""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="#f6f1e7">
  <link rel="icon" href="assets/favicon.svg?v={VERSION}" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="styles.css?v={VERSION}">{pre}
  <script defer src="lib/manifest.js?v={VERSION}"></script>
  <script defer src="main.js?v={VERSION}"></script>
</head>"""


def masthead(active=""):
    return f"""
<a class="skip" href="#contenido">Saltar al contenido</a>
<div class="progress" aria-hidden="true"><span></span></div>
<header class="masthead">
  <a class="brand" href="index.html" aria-label="{SITE}, inicio">
    <span class="brand-num">20′</span><span class="brand-txt">Recetas en <em>20 minutos</em></span>
  </a>
  <nav class="nav" aria-label="Principal">
    <a href="index.html#recetas"{' aria-current="page"' if active == 'recetas' else ''}>Recetas</a>
    <a href="index.html#utensilios">Utensilios</a>
    <a href="index.html#tiempos">Cómo medimos el tiempo</a>
  </nav>
</header>"""


def footer():
    credit_line = ('Fotografías con licencia Creative Commons o de dominio público. '
                   '<a href="creditos.html">Créditos fotográficos →</a>') if CREDITS else \
                  '<a href="creditos.html">Créditos fotográficos →</a>'
    return f"""
<footer class="footer">
  <div class="footer-inner">
    <p class="footer-brand"><span class="brand-num">20′</span> {SITE}</p>
    <p class="footer-note">Los tiempos son aproximados: dependen de tu cocina, de tus utensilios y de la práctica que tengas.</p>
    <p class="footer-credits">{credit_line}</p>
  </div>
</footer>
</body>
</html>
"""


def card(r, i):
    return f"""
    <article class="card reveal" data-cat="{e(r['category'])}">
      <a class="card-link" href="receta-{r['slug']}.html">
        {figure(r, 'card-fig')}
        <div class="card-body">
          <p class="kicker"><span>{i:02d}</span> {e(r['category'])}</p>
          <h3 class="card-title">{e(r['title'])}</h3>
          <p class="card-sum">{e(r['summary'])}</p>
          <p class="card-meta">{dial(r['total'])}<span>{r['servings']} personas · {e(r['difficulty'])}</span></p>
        </div>
      </a>
    </article>"""


def build_index():
    cats = []
    for r in RECIPES:
        if r["category"] not in cats:
            cats.append(r["category"])
    feat = RECIPES[0]
    feat_img = img_path(feat["slug"])

    # Utensilios: cuántas recetas usan cada uno (dato calculado, no inventado)
    tool_count = {}
    for r in RECIPES:
        for t in r["tools"]:
            key = t.split(" (")[0]
            tool_count.setdefault(key, []).append(r)
    tools_sorted = sorted(tool_count.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    filters = "".join(f'<button type="button" class="chip" data-filter="{e(c)}">{e(c)}</button>' for c in cats)
    cards = "".join(card(r, i + 1) for i, r in enumerate(RECIPES))
    tools_html = "".join(
        f'<li><span class="tool-name">{e(name)}</span><span class="tool-count">{len(rs)} de {len(RECIPES)}</span></li>'
        for name, rs in tools_sorted)
    marquee_items = "".join(f"<span>{e(r['title'])}</span><span aria-hidden='true'>✦</span>" for r in RECIPES)

    out = head(f"{SITE} · Recetas paso a paso",
               "Recetas sencillas que se preparan en unos 20 minutos, con ingredientes, utensilios, tiempos y pasos detallados.",
               feat_img)
    out += f"""
<body class="page-home">{masthead('recetas')}
<main id="contenido">
  <section class="hero">
    <div class="hero-type">
      <p class="kicker">{len(RECIPES)} recetas · paso a paso</p>
      <h1 class="hero-title">Cocina de verdad<br>en <em>veinte minutos</em>.</h1>
      <p class="hero-lede">Recetas sencillas explicadas paso a paso, con los ingredientes, el tiempo y los utensilios que necesitas antes de encender el fuego.</p>
      <a class="btn" href="#recetas">Ver las recetas <span aria-hidden="true">↓</span></a>
    </div>
    <a class="hero-feature" href="receta-{feat['slug']}.html">
      {figure(feat, 'hero-fig', eager=True)}
      <span class="hero-cap"><span class="kicker">Para empezar</span><strong>{e(feat['title'])}</strong>{dial(feat['total'])}</span>
    </a>
    <div class="hero-clock" aria-hidden="true">
      <svg viewBox="0 0 200 200"><circle class="clock-track" cx="100" cy="100" r="92"/><circle class="clock-fill" cx="100" cy="100" r="92" pathLength="100"/></svg>
      <span>20′</span>
    </div>
  </section>

  <div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee_items}{marquee_items}</div></div>

  <section class="section" id="recetas">
    <header class="section-head">
      <p class="kicker">El recetario</p>
      <h2>Todas las recetas</h2>
      <div class="chips" role="group" aria-label="Filtrar por tipo">
        <button type="button" class="chip is-on" data-filter="*">Todas</button>{filters}
      </div>
    </header>
    <div class="grid" data-grid>{cards}
    </div>
  </section>

  <section class="section section--split" id="tiempos">
    <div class="split-num" aria-hidden="true">¿20?</div>
    <div class="split-body reveal">
      <p class="kicker">Cómo medimos el tiempo</p>
      <h2>Qué incluyen los minutos de cada receta</h2>
      <p>El tiempo indicado va desde que empiezas a preparar los ingredientes hasta que el plato está servido, contando con que ya los tienes comprados. Cuando una receta necesita calentar agua, ese tiempo está incluido.</p>
      <p>Son tiempos aproximados. Una placa de inducción, una de gas o una vitrocerámica no calientan igual, y el grosor de un lomo de pescado o la marca de la pasta cambian los minutos. Cada receta explica en qué se va el tiempo para que puedas ajustarlo en tu cocina.</p>
      <p>En los pasos que tienen una duración concreta encontrarás un temporizador que puedes poner en marcha desde la propia página.</p>
    </div>
  </section>

  <section class="section" id="utensilios">
    <header class="section-head">
      <p class="kicker">Antes de empezar</p>
      <h2>Los utensilios que vas a usar</h2>
      <p class="section-lede">Esta es la lista completa de utensilios que aparecen en las recetas, ordenada por las veces que se usan.</p>
    </header>
    <ul class="tools reveal">{tools_html}
    </ul>
  </section>
</main>"""
    out += footer()
    (ROOT / "index.html").write_text(out, encoding="utf-8")


def build_recipe(r, idx):
    prev_r = RECIPES[idx - 1]
    next_r = RECIPES[(idx + 1) % len(RECIPES)]
    img = img_path(r["slug"])
    ingredients = "".join(
        f'<li><label><input type="checkbox"><span>{e(x)}</span></label></li>' for x in r["ingredients"])
    tools = "".join(f"<li>{e(x)}</li>" for x in r["tools"])
    breakdown = "".join(f"<li>{e(x)}</li>" for x in r["time_breakdown"])
    steps = ""
    for n, (text, mins) in enumerate(r["steps"], 1):
        timer = ""
        if mins:
            timer = (f'<button type="button" class="timer" data-min="{mins}" aria-live="polite">'
                     f'<span class="timer-ico" aria-hidden="true">◷</span>'
                     f'<span class="timer-txt">Temporizador {mins} min</span></button>')
        steps += (f'\n        <li class="step" id="paso-{n}"><span class="step-n" aria-hidden="true">{n:02d}</span>'
                  f'<div class="step-body"><p>{e(text)}</p>{timer}</div></li>')
    tips = ""
    if r.get("tips"):
        tips = ('<aside class="tips"><h2 class="h-small">Notas</h2><ul>'
                + "".join(f"<li>{e(t)}</li>" for t in r["tips"]) + "</ul></aside>")
    related = "".join(card(x, RECIPES.index(x) + 1) for x in [prev_r, next_r] if x is not r)

    out = head(f"{r['title']} · {SITE}", r["summary"], img)
    out += f"""
<body class="page-recipe">{masthead()}
<main id="contenido">
  <article class="recipe">
    <header class="recipe-head">
      <p class="kicker"><a href="index.html#recetas">Recetas</a> · {e(r['category'])}</p>
      <h1 class="recipe-title">{e(r['title'])}</h1>
      <p class="recipe-lede">{e(r['summary'])}</p>
      <dl class="facts">
        <div class="fact fact--time">{dial(r['total'], big=True)}<div><dt>Tiempo total</dt><dd>unos {r['total']} minutos</dd></div></div>
        <div class="fact"><dt>Raciones</dt><dd>{r['servings']} personas</dd></div>
        <div class="fact"><dt>Dificultad</dt><dd>{e(r['difficulty'])}</dd></div>
        <div class="fact"><dt>Pasos</dt><dd>{len(r['steps'])}</dd></div>
      </dl>
    </header>
    {figure(r, 'recipe-fig', eager=True)}

    <div class="recipe-grid">
      <aside class="recipe-side">
        <section class="box">
          <h2 class="h-small">Ingredientes <span>para {r['servings']}</span></h2>
          <ul class="checklist">{ingredients}</ul>
        </section>
        <section class="box">
          <h2 class="h-small">Utensilios</h2>
          <ul class="bullets">{tools}</ul>
        </section>
        <section class="box">
          <h2 class="h-small">En qué se va el tiempo</h2>
          <ul class="bullets">{breakdown}</ul>
        </section>
        <button type="button" class="btn btn--ghost" data-print>Imprimir receta</button>
      </aside>
      <section class="recipe-steps">
        <h2 class="h-small">Paso a paso</h2>
        <ol class="steps">{steps}
        </ol>
        {tips}
      </section>
    </div>
  </article>

  <section class="section section--related">
    <header class="section-head"><p class="kicker">Sigue cocinando</p><h2>Otras recetas</h2></header>
    <div class="grid grid--two">{related}
    </div>
  </section>
</main>"""
    out += footer()
    (ROOT / f"receta-{r['slug']}.html").write_text(out, encoding="utf-8")




def build_credits():
    by_slug = {r["slug"]: r for r in RECIPES}
    if CREDITS:
        items = ""
        for key, c in CREDITS.items():
            dish = by_slug.get(key, {}).get("title", key)
            creator = e(c.get("creator") or "Autor desconocido")
            if c.get("creator_url"):
                creator = f'<a href="{e(c["creator_url"])}" target="_blank" rel="noopener">{creator}</a>'
            lic = LICENSE_NAMES.get(c.get("license", ""), c.get("license", "").upper())
            ver = c.get("license_version") or ""
            items += (f'<li><strong>{e(dish)}</strong> — «{e(c.get("title") or "Sin título")}», de {creator}'
                      f' ({e(c.get("source") or "")}). '
                      f'<a href="{e(c["license_url"])}" target="_blank" rel="noopener">{e(lic)} {e(ver)}</a> · '
                      f'<a href="{e(c["foreign_landing_url"])}" target="_blank" rel="noopener">Ver original ↗</a></li>')
        body = (f'<p>Las fotografías de las recetas proceden de <a href="https://openverse.org" target="_blank" rel="noopener">Openverse</a> '
                f'y se publican bajo licencias Creative Commons o de dominio público. Son fotos ilustrativas del plato: '
                f'no están hechas siguiendo exactamente estas recetas.</p><ul class="credits-list">{items}</ul>')
    else:
        body = "<p>Todavía no hay fotografías publicadas en esta web.</p>"
    out = head(f"Créditos fotográficos · {SITE}", "Autoría y licencias de las fotografías de la web.")
    out += f"""
<body class="page-credits">{masthead()}
<main id="contenido" class="credits">
  <p class="kicker"><a href="index.html">← Volver al inicio</a></p>
  <h1 class="recipe-title">Créditos fotográficos</h1>
  {body}
</main>"""
    out += footer()
    (ROOT / "creditos.html").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    build_index()
    for i, r in enumerate(RECIPES):
        build_recipe(r, i)
    build_credits()
    missing = [r["slug"] for r in RECIPES if not img_path(r["slug"])]
    print(f"OK · {len(RECIPES)} recetas · v={VERSION}")
    if missing:
        print("Fotos pendientes:", ", ".join(missing))
