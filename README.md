# Recetas en 20 minutos

Web estática (HTML, CSS y JavaScript sin dependencias) con 14 recetas explicadas paso a paso: ingredientes, utensilios, tiempo total y en qué se va ese tiempo, con temporizadores por paso.

Funciones: selector de raciones, modo cocina (paso a paso a pantalla completa, sin que se apague la pantalla), buscador «¿Qué tengo en la nevera?», lista de la compra (`lista.html`), botón de compartir, modo oscuro automático y transiciones entre páginas en los navegadores compatibles.

## Ver la web
Abre `index.html` en el navegador.

## Publicar en Hostinger
Sube al administrador de archivos (carpeta `public_html`) todo excepto `tools/`, `assets/photos/source/` y `README.md`. El archivo `.htaccess` evita que el navegador muestre versiones antiguas tras cada subida.

## Editar recetas
Las recetas están en `tools/recipes.py` (el campo `need` indica los ingredientes principales para el buscador de la nevera). Tras cambiarlas, ejecuta:

    python3 tools/build.py

## Fotos
Cada receta usa `assets/img/<slug>.webp`. Mientras falte una foto, la página muestra un marco con el nombre del plato. `tools/fotos.sh` descarga fotos con licencia libre desde Openverse y genera `creditos.html`; revisa cada imagen antes de publicarla.
