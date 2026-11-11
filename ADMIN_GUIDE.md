# Administrar el archivo de ilustración

El editor está en https://byjahr.github.io/byjahr/admin/. Usa la cuenta GitHub **ByJahr**. Mientras falte la conexión OAuth, la página indica que el acceso no está configurado.

1. En **Obras → Nueva obra**, selecciona o arrastra una copia web final. Usa WebP, PNG, JPEG o AVIF de hasta 8 MiB y 36 megapíxeles. Conserva el maestro fuera del proyecto. En el campo de referencia interna puedes anotar el nombre de origen, siempre que no contenga datos personales.
2. Completa título, descripción, texto alternativo, colección, categoría y año. El identificador se genera a partir del título cuando queda vacío. Escribe etiquetas separadas por comas, por ejemplo, el nombre del personaje y el tema de la obra.
3. Para guardar una ficha sin mostrarla, deja **Borrador** activo o **Visible en el sitio** apagado y guarda. Las fichas y archivos guardados de esta forma quedan en el repositorio público y no se incluyen en el sitio. Mantén el material privado en la carpeta local de recepción.
4. Para publicar, apaga **Borrador**, activa **Visible en el sitio** y guarda. El editor crea un commit en `main`. En [Actions](https://github.com/ByJahr/byjahr/actions), espera a que termine **Publicar en GitHub Pages**. El tiempo depende de GitHub. Si ves una versión anterior, recarga la página después de que aparezca el resultado exitoso.
5. Para corregir u ocultar una ficha, ábrela de nuevo, edita sus campos y guarda. Para ocultar, apaga **Visible en el sitio**. Elige **Destacar en portada** para mostrar una obra ahí. Si hay varias, gana la de menor orden y, en empate, la más reciente.
6. **Criaturas** tiene su propio formulario. Puedes publicar la ilustración con un nombre, descripción y texto alternativo, y añadir lore y estadísticas más adelante. En **Colecciones**, los identificadores se mantienen fijos para conservar las URL.

El sitio crea copias WebP responsivas al compilar, conserva las proporciones y la transparencia, y omite EXIF y otros metadatos del original en las copias desplegadas. El archivo subido sí queda en Git. Para evitar publicar metadatos privados en el repositorio, exporta una copia web sin ellos antes de subirla.

Para importar varias obras, reúne solo las copias finales aprobadas en `artwork-inbox/`, excluida de Git. Si hay varias candidatas, identifica la versión aprobada antes de cargarla. Importa una ficha por imagen y conserva la referencia al original en el campo correspondiente. El sitio genera el nombre público `coleccion-slug.webp`. En Git, usa preferentemente ese mismo nombre para la copia que subas.

## Si algo falla

- **La obra no aparece.** Revisa **Visible**, **Borrador**, la visibilidad de la colección y el resultado de Actions. El despliegue anterior sigue activo si una validación falla. Corrige la ficha o reemplaza el archivo y vuelve a guardar.
- **Imagen rechazada.** Confirma que el formato real coincide con la extensión y que la copia de origen está debajo de 8 MiB. Reduce el tamaño si el resultado de producción supera 2 MiB. No cambies la extensión manualmente.
- **Volver a una versión previa.** Desde VS Code, revisa el historial de la ficha y restaura su contenido en un nuevo commit. Para revertir todo un cambio editorial, usa `git revert SHA_DEL_COMMIT` y sube el nuevo commit. No reescribas el historial de la rama.
- **Salir o revocar acceso.** Cierra sesión en el editor. La credencial del editor solo vive en la memoria de esa pestaña. Para invalidarla en GitHub, abre [Aplicaciones OAuth autorizadas](https://github.com/settings/applications), busca **ByJahr Editor** y revoca su autorización.

## Activación inicial de GitHub

El repositorio es **ByJahr/byjahr** y la rama **main**. La autenticación usa una aplicación OAuth de GitHub y un Worker en Cloudflare. El alcance `public_repo` permite operar repositorios públicos a los que la cuenta ya tiene acceso y es más amplio que un solo repositorio. El Worker solo entrega acceso a cuentas autorizadas y comprueba permiso de escritura en **ByJahr/byjahr**.

1. En Cloudflare, inicia sesión y consulta tu subdominio de Workers. El servicio se llama `byjahr-cms-oauth`. Su origen exacto será `https://byjahr-cms-oauth.TU_SUBDOMINIO.workers.dev`. Usa ese origen, sin barra final, donde se indique abajo.
2. Con la cuenta ByJahr, abre [Registrar OAuth App](https://github.com/settings/applications/new). Usa **ByJahr Editor** como nombre, `https://byjahr.github.io/byjahr/admin/` como **Homepage URL** y `https://byjahr-cms-oauth.TU_SUBDOMINIO.workers.dev/callback` como **Authorization callback URL**. Genera el secreto desde GitHub.
3. En el proyecto, con Node.js instalado, entra en `oauth/`. Autoriza Wrangler con tu cuenta de Cloudflare. Carga cada valor mediante el diálogo seguro de Wrangler. No compartas el secreto en el chat ni en archivos de Git.

   ```sh
   cd oauth
   npx wrangler login
   npx wrangler deploy
   npx wrangler secret put OAUTH_ORIGIN
   npx wrangler secret put GITHUB_CLIENT_ID
   npx wrangler secret put GITHUB_CLIENT_SECRET
   ```

   Para `OAUTH_ORIGIN`, usa el origen del paso 1. Los otros dos valores salen de GitHub. El Worker responde con acceso sin configurar hasta tener los tres valores.
4. En [Variables de Actions del repositorio](https://github.com/ByJahr/byjahr/settings/variables/actions), crea la variable **CMS_OAUTH_ORIGIN** con el mismo origen del Worker. Esta URL es pública. Ejecuta **Run workflow** en [Publicar en GitHub Pages](https://github.com/ByJahr/byjahr/actions/workflows/pages.yml).
5. Abre el administrador público, pulsa **Login with GitHub** y autoriza con **ByJahr**. Si no se abre la ventana, permite ventanas emergentes para el sitio. Prueba primero guardando una ficha de prueba oculta y verificando el commit y Actions.

El Worker limita el intercambio con el editor a `https://byjahr.github.io`, comprueba estado y PKCE, y mantiene el secreto en Cloudflare. `oauth/.dev.vars.example` enumera las variables sin valores.
