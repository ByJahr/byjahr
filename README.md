# @byjahr

Portafolio de fantasía oscura, archivo de colecciones y Bestiario. Python genera HTML estático; CSS y JavaScript nativos se encargan del diseño y los filtros. Las fichas son JSON. No hay instalación de dependencias.

## En VS Code

Abre esta carpeta y usa la terminal integrada. Necesitas Python 3.9 o superior.

```sh
python3 --version
python3 scripts/build_site.py validate
python3 scripts/build_site.py build
python3 scripts/check.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Abre http://127.0.0.1:8000. Tras editar contenido, vuelve a compilar en otra terminal y recarga. La vista de producción se guarda en `dist/` y se regenera por completo.

## Primera obra

1. Exporta tu ilustración a WebP, JPEG o PNG; conserva la proporción y usa un nombre corto como `mi-obra.webp`. Colócala en `public/images/obras/`.
2. Ejecuta `cp plantillas/obra.json src/content/obras/mi-obra.json`.
3. Completa título, texto alternativo, fecha AAAA-MM-DD, categoría y colección. La imagen se indica como `images/obras/mi-obra.webp`, sin `public/`. El año se deriva de la fecha. Marca `destacada: true` para optar a la portada (gana la más reciente entre las destacadas).
4. Para variantes responsivas, exporta la misma imagen a varios anchos y agrega objetos como `{"imagen":"images/obras/mi-obra-640.webp","ancho":640}` en `variantes`. Incluye también la versión grande con su ancho real. El sitio sirve los archivos tal como se exportan. Los enlaces relacionados usan objetos `{"titulo":"Nombre","url":"https://…"}`.
5. Compila y revisa la ficha desde Portafolio. Para Caoz con Todo, duplica `personaje.json` o `escena.json` en la misma carpeta de obras y completa `personaje` y `campana` si aplica.

## Primera criatura

1. Guarda la imagen en `public/images/bestiario/`.
2. Ejecuta `cp plantillas/criatura.json src/content/criaturas/mi-criatura.json`.
3. Cambia el slug, rellena el nombre, la ruta de imagen y la descripción corta. Escribe un texto alternativo si la descripción no describe la imagen. Los demás campos son opcionales. El estado puede ser Ilustración, Lore parcial o Entrada completa; sin estado se muestra Ilustración. Añade estadísticas únicamente si son homebrew original compatible con 5e.
4. Compila y revisa la ficha desde Bestiario.

## Colecciones e identidad

Duplica `plantillas/coleccion.json` en `src/content/colecciones/`. Usa un slug único y el mismo slug en las obras asociadas. Cambia `titulo` para renombrar la colección conservando su dirección. Usa `oculta: true` para retirar la colección y sus obras del sitio. Conserva los slugs `bestiario` y `caoz-con-todo` para sus funciones especiales. Las portadas opcionales van en `public/images/colecciones/`.

Edita `src/config.json` para añadir biografía, declaración artística, influencias, proceso, retrato con texto alternativo, Instagram, TikTok y correo profesional. Los enlaces necesitan URL HTTPS. El favicon provisional se puede sustituir apuntando `favicon` a otro archivo de `public/`. Edita `categorias` para mantener las categorías permitidas.

## Primera publicación

En una terminal normal con permiso de escritura en esta carpeta y GitHub CLI autenticada:

```sh
git init -b main
git add .gitignore .github README.md public scripts src plantillas
git commit -m "Crear sitio oficial de @byjahr"
gh auth status
gh repo create byjahr-web --public --source=. --remote=origin
gh api --method POST "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pages" -f build_type=workflow
git push -u origin main
```

Si Git solicita nombre y correo, configura primero tu identidad local con `git config user.name` y `git config user.email`. Si GitHub exige un primer push para habilitar Pages, haz el push y después selecciona **Settings → Pages → Source → GitHub Actions**. Relanza el flujo desde **Actions → Publicar en GitHub Pages → Run workflow**. Si el repositorio ya existe, verifica su propietario y contenido antes de vincularlo. Consulta la URL que devuelve el trabajo de despliegue en Actions.

El flujo usa el origen y prefijo detectados por GitHub Pages para crear enlaces, canonicals, sitemap y Open Graph. En un sitio de proyecto, GitHub sirve `robots.txt` bajo el prefijo del repositorio; las reglas de rastreo del dominio se gestionan en su raíz.

## Publicar cambios

```sh
python3 scripts/build_site.py build
python3 scripts/check.py
git add src public
git commit -m "Actualizar archivo de ilustración"
git push
```

Cada push a `main` ejecuta el flujo de publicación. Si el flujo falla, abre su registro en Actions. Si una imagen no carga, verifica la ruta relativa y las mayúsculas. Si la compilación indica slug duplicado, corrige el slug en la ficha correspondiente. Si una fecha falla, usa AAAA-MM-DD y una fecha real. Para comprobar un prefijo de producción:

```sh
SITE_URL=https://ejemplo.github.io SITE_BASE=/byjahr-web python3 scripts/build_site.py build
SITE_BASE=/byjahr-web python3 scripts/check.py
```
