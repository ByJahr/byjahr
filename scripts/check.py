from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build_site import BASE, OUT

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href','src') and value:
                self.urls.append(value)
            if key == 'srcset' and value:
                self.urls.extend(part.strip().split()[0] for part in value.split(','))
            if key == 'id':
                self.ids.add(value)

pages = {}
for file in OUT.rglob('*.html'):
    parser = Links()
    parser.feed(file.read_text())
    pages[file] = parser
if not pages or OUT/'404.html' not in pages:
    raise SystemExit('Compila primero; se esperaba HTML y 404.')
errors = []
for source, parser in pages.items():
    for value in parser.urls:
        parts = urlsplit(value)
        if parts.scheme or parts.netloc: continue
        if not parts.path:
            target = source
        elif not parts.path.startswith(BASE):
            errors.append(f'{source}: ruta fuera de la base: {value}')
            continue
        else:
            target = OUT / unquote(parts.path[len(BASE):])
            if parts.path.endswith('/'): target /= 'index.html'
        if not target.is_file() or (parts.fragment and target in pages and unquote(parts.fragment) not in pages[target].ids):
            errors.append(f'{source}: enlace o recurso roto: {value}')
if errors: raise SystemExit('\n'.join(errors))
print(f'Rutas, recursos y anclas comprobados en {len(pages)} páginas.')
