# @byjahr

Portafolio de fantasía oscura, archivo de colecciones y Bestiario. Python genera HTML estático; CSS y JavaScript nativos se encargan del diseño y los filtros. Las fichas son JSON. La compilación usa Pillow para procesar imágenes.

## Agregar dibujos desde VS Code

Coloca tus archivos finales directamente en `img/`.

| Nombre de archivo | Destino |
| --- | --- |
| `Fender.jpg` o cualquier nombre de personaje | Caoz con Todo |
| `1.JPG`, `2.jpg`, etc. | Inktober 2026, en orden numérico |
| `B_1.jpg`, `B_2.png`, etc. | Bestiario, en orden numérico |

Admite JPEG, PNG, WebP y AVIF. Evita tener dos archivos con el mismo nombre base. Las fichas usan el nombre del archivo como punto de partida. Puedes editar el título, el texto alternativo y el resto de sus datos en `src/content/obras/` o `src/content/criaturas/`. Para ocultar una obra, usa `published: false`. Para ocultar una criatura, usa `estado_publicacion: "borrador"`. Borrar un original de `img/` no retira su copia publicada.

Instala las dependencias la primera vez:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Después de agregar archivos, ejecuta:

```sh
python scripts/import_art.py
SITE_BASE=/byjahr/ python scripts/build_site.py build
SITE_BASE=/byjahr/ python scripts/check.py
python scripts/preview.py
```

Revisa la web en http://127.0.0.1:8021/byjahr/. La importación deja los originales intactos y crea copias WebP sin metadatos privados. Git ignora `img/` y conserva las copias de `public/images/artworks/` junto con sus fichas. Si vuelves a importar un original editado con el mismo nombre, se actualiza la copia y se conservan los cambios editoriales de la ficha.

## Colecciones e identidad

Duplica `plantillas/coleccion.json` en `src/content/colecciones/`. Usa un slug único y el mismo slug en las obras asociadas. Cambia `titulo` para renombrar la colección conservando su dirección. Usa `oculta: true` para retirar la colección y sus obras del sitio. Conserva los slugs `bestiario` y `caoz-con-todo` para sus funciones especiales. Las portadas opcionales van en `public/images/colecciones/`.

Edita `src/config.json` para añadir biografía, declaración artística, influencias, proceso, retrato con texto alternativo, redes sociales y correo profesional. Cada elemento de `redes_sociales` admite `nombre`, `usuario` y `url` HTTPS. El favicon provisional se puede sustituir apuntando `favicon` a otro archivo de `public/`. Edita `categorias` para mantener las categorías permitidas.

## Publicar cambios

El repositorio es **ByJahr/byjahr**. Cada push a `main` inicia [GitHub Actions](https://github.com/ByJahr/byjahr/actions).

```sh
git add src/content public/images/artworks
git commit -m "Agregar ilustraciones"
git push origin main
```

## Elegir la obra destacada

Ejecuta `python3 scripts/destacar.py` y escribe el número de la ilustración que quieres en portada. Usa `0` para dejar la portada sin obra destacada. El selector guarda la elección en `src/config.json`. Para publicarla, haz commit de ese archivo y sube los cambios a `main`.
