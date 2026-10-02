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
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recipes import RECIPES  # noqa: E402

SITE = "Recetas en 20 minutos"
# Dirección pública de la web (para sitemap.xml). Cámbiala si la publicas en otro sitio.
SITE_URL = "https://jangg24.github.io/recetasen20min/"
VERSION = datetime.date.today().strftime("%Y%m%d")
FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,300..700,0..100,0..1;"
         "1,9..144,300..700,0..100,0..1&family=Inter+Tight:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@"
         "0,8..60,300..600;1,8..60,300..600&display=swap")

e = html.escape
LICENSE_NAMES = {"cc0": "CC0", "pdm": "Dominio público", "by": "CC BY", "by-sa": "CC BY-SA"}


FRACS = {0.25: "¼", 0.5: "½", 0.75: "¾"}


def fmt_qty(v):
    """Mismo formato que main.js: enteros y fracciones de cocina (¼, ½, ¾)."""
    whole, frac = int(v), round(v - int(v), 2)
    if frac == 0:
        return str(whole)
    f = FRACS.get(frac, str(round(frac, 2)))
    return f if whole == 0 else f"{whole} {f}"


def ingredient_html(text):
    """[200] → cantidad escalable, [3-4] → rango, {uno|varios} → concordancia."""
    out, last = [], 1.0
    for tok in re.split(r"(\[[^\]]+\]|\{[^}]+\})", text):
        if tok.startswith("["):
            lo, _, hi = tok[1:-1].partition("-")
            last = float(hi or lo)
            unit = "w" if re.match(r"\s*(g|ml)\b", text[text.index(tok) + len(tok):]) else "n"
            shown = fmt_qty(float(lo)) + ("–" + fmt_qty(float(hi)) if hi else "")
            q2 = f' data-q2="{hi}"' if hi else ""
            out.append(f'<b class="q" data-q="{lo}"{q2} data-u="{unit}">{shown}</b>')
        elif tok.startswith("{"):
            one, many = tok[1:-1].split("|")
            out.append(f'<span class="pl" data-one="{e(one)}" data-many="{e(many)}">{e(many if last > 1 else one)}</span>')
        else:
            out.append(e(tok))
    return "".join(out)


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
        vt = f' style="view-transition-name: foto-{r["slug"]}"' if cls in ("card-fig", "recipe-fig") else ""
        return (f'<figure class="{cls}"{vt}><img src="{src}?v={VERSION}" alt="{e(r["title"])}" {load}>{cap}</figure>')
    return (f'<figure class="{cls} is-empty" role="img" aria-label="Foto pendiente: {e(r["title"])}">'
            f'<span class="ph-mark" aria-hidden="true">{r["total"]}′</span>'
            f'<span class="ph-name">{e(r["title"])}</span></figure>')


import unicodedata

# Ingredientes que hacen que una receta no sea vegetariana (sin carne ni pescado)
NO_VEG = ["guanciale", "panceta", "gambas", "salmón", "pollo", "atún", "jamón", "anchoa", "bacon", "chorizo", "carne"]


def is_veg(r):
    text = " ".join(r["ingredients"]).lower()
    return not any(w in text for w in NO_VEG)


def norm(t):
    """Texto en minúsculas y sin tildes, para el buscador."""
    t = re.sub(r"[\[\]{}|]", " ", t.lower())
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def search_text(r):
    return norm(" ".join([r["title"], r["category"], r["summary"]] + r["ingredients"]))


VEG_NOTE = ("Vegetariana: sin carne ni pescado. Algunos quesos se elaboran con cuajo animal; "
            "si te importa, revisa la etiqueta.")


def personas(n):
    return f"{n} persona" if n == 1 else f"{n} personas"


def dial(total, big=False):
    """Anillo que muestra los minutos de la receta sobre 20."""
    frac = min(total, 20) / 20
    cls = "dial dial--big" if big else "dial"
    return (f'<span class="{cls}" style="--frac:{frac:.3f}" aria-label="{total} minutos">'
            f'<svg viewBox="0 0 44 44" aria-hidden="true"><circle class="dial-track" cx="22" cy="22" r="19"/>'
            f'<circle class="dial-fill" cx="22" cy="22" r="19" pathLength="100"/></svg>'
            f'<span class="dial-num">{total}<small>min</small></span></span>')


def head(title, desc, preload=None, meta=""):
    pre = f'\n  <link rel="preload" as="image" href="{preload}?v={VERSION}" fetchpriority="high">' if preload else ""
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f6f1e7" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#171411" media="(prefers-color-scheme: dark)">
  <link rel="icon" href="assets/favicon.svg?v={VERSION}" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="styles.css?v={VERSION}">{pre}
  <script defer src="lib/manifest.js?v={VERSION}"></script>
  <script defer src="lib/recetas.js?v={VERSION}"></script>
  <script defer src="main.js?v={VERSION}"></script>{meta}
</head>"""


def plain_ingredient(raw):
    """Texto del ingrediente para la cantidad original, sin marcas ([200], {uno|varios})."""
    return html.unescape(re.sub(r"<[^>]+>", "", ingredient_html(raw)))


def img_size(rel):
    try:
        from PIL import Image
        with Image.open(ROOT / rel) as im:
            return im.size
    except Exception:
        return None


def og_image(img_rel):
    """Copia JPG de 1200×630 para la vista previa al compartir: WhatsApp y algunas redes
    no muestran siempre WebP. Devuelve la ruta relativa o None."""
    if not img_rel:
        return None
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return img_rel
    out = f"assets/og/{Path(img_rel).stem}.jpg"
    dst = ROOT / out
    if not dst.exists() or dst.stat().st_mtime < (ROOT / img_rel).stat().st_mtime:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(ROOT / img_rel) as im:
            # En fotos verticales, el plato suele estar en la parte superior: se recorta más arriba
            centre = (0.5, 0.3) if im.height > im.width else (0.5, 0.5)
            ImageOps.fit(im.convert("RGB"), (1200, 630), Image.LANCZOS, centering=centre).save(
                dst, "JPEG", quality=82, optimize=True, progressive=True)
    return out


def social_meta(title, desc, path, img_rel, kind="website", ld=None):
    """Vista previa al compartir (Open Graph / Twitter), URL canónica y datos estructurados."""
    url = SITE_URL + path
    out = [f'<link rel="canonical" href="{e(url)}">',
           f'<meta property="og:site_name" content="{e(SITE)}">',
           '<meta property="og:locale" content="es_ES">',
           f'<meta property="og:type" content="{kind}">',
           f'<meta property="og:title" content="{e(title)}">',
           f'<meta property="og:description" content="{e(desc)}">',
           f'<meta property="og:url" content="{e(url)}">']
    img_rel = og_image(img_rel)
    if img_rel:
        out.append(f'<meta property="og:image" content="{e(SITE_URL + img_rel)}">')
        size = img_size(img_rel)
        if size:
            out.append(f'<meta property="og:image:width" content="{size[0]}">')
            out.append(f'<meta property="og:image:height" content="{size[1]}">')
        out.append(f'<meta property="og:image:alt" content="{e(title)}">')
        out.append('<meta name="twitter:card" content="summary_large_image">')
    else:
        out.append('<meta name="twitter:card" content="summary">')
    if ld:
        out.append('<script type="application/ld+json">' +
                   json.dumps(ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>")
    return "".join("\n  " + x for x in out)


def recipe_ld(r):
    """Datos de receta para Google (schema.org/Recipe). Solo datos que están en la receta:
    sin valoraciones, calorías ni nada que no exista."""
    url = SITE_URL + f"receta-{r['slug']}.html"
    ld = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["title"],
        "description": r["summary"],
        "url": url,
        "author": {"@type": "Organization", "name": SITE, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE, "url": SITE_URL},
        "totalTime": f"PT{r['total']}M",
        "recipeYield": personas(r["servings"]),
        "recipeCategory": r["category"],
        "keywords": ", ".join([r["category"].lower(), "receta rápida", f"{r['total']} minutos"]
                              + (["vegetariana"] if is_veg(r) else [])),
        "recipeIngredient": [plain_ingredient(x) for x in r["ingredients"]],
        "tool": [{"@type": "HowToTool", "name": t} for t in r["tools"]],
        "recipeInstructions": [
            {"@type": "HowToStep", "position": n, "text": text, "url": f"{url}#paso-{n}"}
            for n, (text, _m) in enumerate(r["steps"], 1)],
    }
    if img_path(r["slug"]):
        ld["image"] = [SITE_URL + img_path(r["slug"])]
    if is_veg(r):
        ld["suitableForDiet"] = "https://schema.org/VegetarianDiet"
    return ld


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
    <a href="index.html#nevera" class="nav-opt">¿Qué tengo en la nevera?</a>
    <a href="index.html#tiempos" class="nav-opt">Cómo medimos el tiempo</a>
    <a href="lista.html" class="nav-list"{' aria-current="page"' if active == 'lista' else ''}>Lista de la compra<span class="nav-count" data-list-count hidden></span></a>
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


STAPLES = "sal, pimienta, aceite y azúcar"


def fridge_html():
    """Buscador por ingredientes: botones fijos en el HTML, resultados con JS."""
    keys = sorted({k for r in RECIPES for k in r["need"]}, key=lambda k: k.lower())
    chips = "".join(f'<button type="button" class="chip chip--ing" data-ing="{e(k)}" aria-pressed="false">{e(k)}</button>' for k in keys)
    return f"""  <section class="section fridge" id="nevera">
    <header class="section-head">
      <p class="kicker">Buscador por ingredientes</p>
      <h2>¿Qué tengo en la <em>nevera</em>?</h2>
      <p class="section-lede">Marca lo que tienes en casa y te decimos qué recetas puedes hacer y qué te falta para las demás. Solo contamos los ingredientes principales; damos por hecho que tienes {STAPLES}.</p>
    </header>
    <div class="chips chips--ing" role="group" aria-label="Ingredientes que tengo">{chips}</div>
    <div class="fridge-bar js-only"><span data-fridge-count>Nada marcado todavía</span><button type="button" class="linkbtn" data-fridge-clear>Borrar selección</button></div>
    <div class="fridge-results" data-fridge-results aria-live="polite"></div>
    <noscript><p class="section-lede">Este buscador necesita JavaScript activado.</p></noscript>
  </section>"""


def build_data():
    """lib/recetas.js: datos para el buscador y la lista de la compra."""
    data = [{"slug": r["slug"], "title": r["title"], "category": r["category"], "servings": r["servings"],
             "total": r["total"], "need": r["need"], "ingredients": r["ingredients"],
             "img": img_path(r["slug"]), "veg": is_veg(r)} for r in RECIPES]
    js = ("/* Generado por tools/build.py: no editar a mano. */\n(function () {\n  window.__RECETAS__ = "
          + json.dumps(data, ensure_ascii=False, indent=1) + ";\n})();\n")
    (ROOT / "lib" / "recetas.js").write_text(js, encoding="utf-8")


def build_404():
    out = head(f"Página no encontrada · {SITE}", "Esta página no existe.")
    out += f"""
<body class="page-404">{masthead()}
<main id="contenido" class="notfound">
  <p class="notfound-num" aria-hidden="true">404′</p>
  <h1 class="recipe-title">Esta página <em>no existe</em></h1>
  <p class="recipe-lede">Puede que el enlace esté mal escrito o que la página se haya movido. Las recetas siguen en su sitio.</p>
  <div class="actions">
    <a class="btn" href="index.html#recetas">Ver las recetas</a>
    <a class="btn btn--line" href="index.html#nevera">¿Qué tengo en la nevera?</a>
  </div>
</main>"""
    out += footer()
    (ROOT / "404.html").write_text(out, encoding="utf-8")


def build_sitemap():
    today = datetime.date.today().isoformat()
    pages = ["", "lista.html", "creditos.html"] + [f"receta-{r['slug']}.html" for r in RECIPES]
    urls = "".join(f"  <url><loc>{SITE_URL}{p}</loc><lastmod>{today}</lastmod></url>\n" for p in pages)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")


def build_list():
    out = head(f"Lista de la compra · {SITE}", "Lista de la compra con los ingredientes de las recetas que elijas.",
               meta=social_meta(f"Lista de la compra · {SITE}", "Junta los ingredientes de las recetas que elijas en una sola lista.",
                                "lista.html", img_path(RECIPES[0]["slug"])))
    out += f"""
<body class="page-list">{masthead('lista')}
<main id="contenido" class="shop">
  <p class="kicker"><a href="index.html#recetas">← Volver a las recetas</a></p>
  <h1 class="recipe-title">Lista de la <em>compra</em></h1>
  <p class="recipe-lede">Añade recetas desde su página con el botón «Añadir a la lista de la compra». Aquí se juntan sus ingredientes, con las cantidades sumadas cuando coinciden.</p>
  <div class="shop-empty" data-shop-empty>
    <p>Tu lista está vacía.</p>
    <a class="btn" href="index.html#recetas">Elegir recetas</a>
  </div>
  <div class="shop-grid" data-shop hidden>
    <section class="box">
      <h2 class="h-small">Recetas en la lista</h2>
      <ul class="shop-recipes" data-shop-recipes></ul>
    </section>
    <section class="box">
      <h2 class="h-small">Ingredientes <span data-shop-total></span></h2>
      <ul class="checklist" data-shop-items></ul>
      <p class="servings-note">Cantidades recalculadas y redondeadas a partir de cada receta. Los ingredientes sin cantidad (sal, pimienta…) aparecen una sola vez.</p>
      <div class="actions">
        <button type="button" class="btn" data-shop-share>Enviar lista</button>
        <button type="button" class="btn btn--line" data-shop-copy>Copiar</button>
        <button type="button" class="btn btn--line" data-shop-print>Imprimir</button>
        <button type="button" class="linkbtn" data-shop-clear>Vaciar lista</button>
        <span class="toast" role="status" aria-live="polite" data-toast></span>
      </div>
    </section>
  </div>
  <noscript><p>La lista de la compra necesita JavaScript activado.</p></noscript>
</main>"""
    out += footer()
    (ROOT / "lista.html").write_text(out, encoding="utf-8")


def card(r, i):
    return f"""
    <article class="card reveal" data-cat="{e(r['category'])}" data-slug="{r['slug']}" data-time="{r['total']}" data-veg="{1 if is_veg(r) else 0}" data-q="{e(search_text(r))}">
      <button type="button" class="fav js-only" data-fav="{r['slug']}" aria-pressed="false" aria-label="Guardar «{e(r['title'])}» en favoritos"><span aria-hidden="true">♥</span></button>
      <a class="card-link" href="receta-{r['slug']}.html">
        {figure(r, 'card-fig')}
        <div class="card-body">
          <p class="kicker"><span>{i:02d}</span> {e(r['category'])}</p>
          <h3 class="card-title">{e(r['title'])}</h3>
          <p class="card-sum">{e(r['summary'])}</p>
          <p class="card-meta">{dial(r['total'])}<span>{personas(r['servings'])} · {e(r['difficulty'])}</span>{'<span class="tag-veg" title="' + e(VEG_NOTE) + '">Vegetariana</span>' if is_veg(r) else ''}</p>
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
    top_tools = ", ".join(f"<strong>{e(n.lower() if i else n)}</strong> ({len(rs)} recetas)" for i, (n, rs) in enumerate(tools_sorted[:5]))
    marquee_items = "".join(f"<span>{e(r['title'])}</span><span aria-hidden='true'>✦</span>" for r in RECIPES)

    home_desc = "Recetas sencillas que se preparan en unos 20 minutos, con ingredientes, utensilios, tiempos y pasos detallados."
    home_ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": SITE_URL, "inLanguage": "es"},
        {"@context": "https://schema.org", "@type": "ItemList",
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE_URL + f"receta-{r['slug']}.html"}
                             for i, r in enumerate(RECIPES)]},
    ]
    out = head(f"{SITE} · Recetas paso a paso", home_desc, feat_img,
               social_meta(SITE, home_desc, "", feat_img, "website", home_ld))
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
      <span class="hero-clock" aria-hidden="true"><svg viewBox="0 0 200 200"><circle class="clock-track" cx="100" cy="100" r="92"/><circle class="clock-fill" cx="100" cy="100" r="92" pathLength="100"/></svg></span>
      {figure(feat, 'hero-fig', eager=True)}
      <span class="hero-cap"><span class="kicker">Para empezar</span><strong>{e(feat['title'])}</strong>{dial(feat['total'])}</span>
    </a>
  </section>

  <div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee_items}{marquee_items}</div></div>

  <section class="section" id="recetas">
    <header class="section-head">
      <p class="kicker">El recetario</p>
      <h2>Todas las recetas</h2>
      <div class="finder js-only">
        <label class="search" for="buscar">
          <span class="visually-hidden">Buscar recetas</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>
          <input id="buscar" type="search" placeholder="Busca un plato o ingrediente…" autocomplete="off" data-search>
        </label>
      </div>
      <div class="chips" role="group" aria-label="Filtrar por tipo">
        <button type="button" class="chip is-on" data-filter="*" aria-pressed="true">Todas</button>{filters}
      </div>
      <div class="chips chips--extra js-only" role="group" aria-label="Más filtros">
        <span class="chips-label">Tiempo</span>
        <button type="button" class="chip chip--sm is-on" data-time="0" aria-pressed="true">Cualquiera</button>
        <button type="button" class="chip chip--sm" data-time="10" aria-pressed="false">Hasta 10 min</button>
        <button type="button" class="chip chip--sm" data-time="15" aria-pressed="false">Hasta 15 min</button>
        <span class="chips-sep" aria-hidden="true"></span>
        <button type="button" class="chip chip--sm" data-veg-filter aria-pressed="false" title="{e(VEG_NOTE)}">Vegetarianas</button>
        <button type="button" class="chip chip--sm chip--fav" data-fav-filter aria-pressed="false"><span aria-hidden="true">♥</span> Favoritas <span data-fav-count>0</span></button>
      </div>
      <p class="results-count js-only" aria-live="polite" data-results-count></p>
    </header>
    <div class="grid" data-grid>{cards}
    </div>
    <div class="no-results" data-no-results hidden>
      <p>Ninguna receta coincide con esa búsqueda.</p>
      <button type="button" class="btn btn--line" data-reset-filters>Quitar filtros</button>
    </div>
  </section>

{fridge_html()}

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

  <section class="section section--tools" id="utensilios">
    <p class="kicker">Antes de empezar</p>
    <p class="tools-lede">Los utensilios que más vas a usar: {top_tools}.</p>
    <details class="tools-more">
      <summary>Ver los {len(tools_sorted)} utensilios de todas las recetas</summary>
      <ul class="tools">{tools_html}
      </ul>
    </details>
  </section>
</main>"""
    out += footer()
    (ROOT / "index.html").write_text(out, encoding="utf-8")


def build_recipe(r, idx):
    prev_r = RECIPES[idx - 1]
    next_r = RECIPES[(idx + 1) % len(RECIPES)]
    img = img_path(r["slug"])
    ingredients = "".join(
        f'<li><label><input type="checkbox"><span>{ingredient_html(x)}</span></label></li>' for x in r["ingredients"])
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

    out = head(f"{r['title']} · {SITE}", r["summary"], img,
               social_meta(r["title"], r["summary"], f"receta-{r['slug']}.html", img, "article", recipe_ld(r)))
    out += f"""
<body class="page-recipe" data-slug="{r['slug']}">{masthead()}
<main id="contenido">
  <article class="recipe">
    <header class="recipe-head">
      <p class="kicker"><a href="index.html#recetas">Recetas</a> · {e(r['category'])}</p>
      <h1 class="recipe-title">{e(r['title'])}</h1>
      <p class="recipe-lede">{e(r['summary'])}</p>
      <dl class="facts">
        <div class="fact fact--time">{dial(r['total'], big=True)}<div><dt>Tiempo total</dt><dd>unos {r['total']} minutos</dd></div></div>
        <div class="fact"><dt>Raciones</dt><dd><span data-servings-label>{personas(r['servings'])}</span></dd></div>
        <div class="fact"><dt>Dificultad</dt><dd>{e(r['difficulty'])}</dd></div>
        <div class="fact"><dt>Pasos</dt><dd>{len(r['steps'])}</dd></div>{'<div class="fact fact--veg"><dt>Tipo</dt><dd title="' + e(VEG_NOTE) + '">Vegetariana</dd></div>' if is_veg(r) else ''}
      </dl>
      <div class="actions js-only">
        <button type="button" class="btn" data-cook>Empezar a cocinar <span aria-hidden="true">→</span></button>
        <button type="button" class="btn btn--line" data-add-list data-slug="{r['slug']}">Añadir a la lista</button>
        <button type="button" class="btn btn--line btn--fav" data-fav="{r['slug']}" aria-pressed="false"><span aria-hidden="true">♥</span> <span class="fav-txt">Guardar</span></button>
        <button type="button" class="btn btn--line" data-share>Compartir</button>
        <span class="toast" role="status" aria-live="polite" data-toast></span>
      </div>
    </header>
    {figure(r, 'recipe-fig', eager=True)}

    <div class="recipe-grid">
      <aside class="recipe-side">
        <section class="box">
          <h2 class="h-small">Ingredientes</h2>
          <div class="servings" data-servings data-base="{r['servings']}">
            <span class="servings-label" id="raciones-{r['slug']}">Raciones</span>
            <div class="stepper" role="group" aria-labelledby="raciones-{r['slug']}">
              <button type="button" class="stepper-btn" data-step="-1" aria-label="Una ración menos">−</button>
              <output class="stepper-val" aria-live="polite"><b>{r['servings']}</b> <span>{personas(r['servings']).split(' ')[1]}</span></output>
              <button type="button" class="stepper-btn" data-step="1" aria-label="Una ración más">+</button>
            </div>
          </div>
          <p class="servings-note" data-servings-note hidden>Las cantidades se han recalculado a partir de la receta original para {personas(r['servings'])} y están redondeadas. Los pasos y los tiempos están pensados para {personas(r['servings'])}: con más cantidad puede que necesites un recipiente más grande, cocinar por tandas y algunos minutos más.</p>
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
    out = head(f"Créditos fotográficos · {SITE}", "Autoría y licencias de las fotografías de la web.",
               meta=social_meta(f"Créditos fotográficos · {SITE}", "Autoría y licencias de las fotografías de la web.",
                                "creditos.html", None))
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
    build_data()
    build_list()
    build_404()
    build_sitemap()
    missing = [r["slug"] for r in RECIPES if not img_path(r["slug"])]
    print(f"OK · {len(RECIPES)} recetas · v={VERSION}")
    if missing:
        print("Fotos pendientes:", ", ".join(missing))
