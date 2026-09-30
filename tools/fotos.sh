#!/usr/bin/env bash
# Descarga una foto con licencia libre (Openverse) por receta, la convierte a
# WebP y regenera las páginas. Necesita acceso a api.openverse.org y a los
# servidores de imágenes (Wikimedia, Flickr...).
# Revisa SIEMPRE cada foto antes de publicar: la búsqueda puede devolver
# imágenes que no corresponden al plato.
set -e
cd "$(dirname "$0")/.."
Q=$(python3 -c "import sys,json; sys.path.insert(0,'tools'); from recipes import RECIPES; print(json.dumps([{'id':r['slug'],'query':r['image_query'],'size':'large'} for r in RECIPES]))")
python3 tools/openverse_fetch.py --inline-queries "$Q" --target assets/photos/source --credits assets/credits.json
python3 tools/webp_convert.py --src assets/photos/source --dst assets/img
python3 tools/build.py
