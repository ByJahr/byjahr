from cms import generate_admin
from artwork import read_art, export_art
import argparse
import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlsplit
from xml.sax.saxutils import escape as xml

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
PUBLIC = Path('public')
OUT = Path('dist')
BASE = os.getenv('SITE_BASE', '').strip('/')
BASE = '/' + BASE + '/' if BASE else '/'
SITE = os.getenv('SITE_URL', '').rstrip('/')
e = lambda x: html.escape(str(x), quote=True)
url = lambda path='': BASE + quote(path.lstrip('/'), safe='/')
slug_pattern = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
errors = []
groups = {}
cfg = json.loads(Path('src/config.json').read_text())
statuses = ('Ilustración', 'Lore parcial', 'Entrada completa')

def asset(path):
    return (isinstance(path, str) and bool(path) and not Path(path).is_absolute()
            and (PUBLIC / path).resolve().is_relative_to(PUBLIC.resolve())
            and (PUBLIC / path).is_file())

def external(value):
    return isinstance(value, str) and urlsplit(value).scheme == 'https' and bool(urlsplit(value).netloc)

def normalize_entry(group, path, data):
    if group in ('obras', 'criaturas'):
        data.setdefault('slug', path.stem)
        if not data['slug']:
            data['slug'] = path.stem
        if data.get('draft') or data.get('published') is False:
            data['estado_publicacion'] = 'borrador'
    if group == 'obras' and 'title' in data:
        aliases = {'title':'titulo','image':'imagen','collection':'coleccion','category':'categoria',
                   'year':'ano','description':'descripcion','date':'fecha','featured':'destacada',
                   'order':'orden','character':'personaje','campaign':'campana','technique':'tecnica',
                   'format':'formato','tags':'etiquetas','caption':'descripcion_ampliada',
                   'credits':'creditos','inktoberPrompt':'prompt','contentWarning':'aviso'}
        for source, target in aliases.items():
            if source in data:
                data[target] = data.pop(source)
        if 'ano' in data:
            data['ano'] = str(data['ano'])
        if 'categoria' in data:
            data['categoria'] = cfg['categorias_cms'].get(data['categoria'],data['categoria'])
        if not data.get('descripcion'):
            raise ValueError('falta la descripción breve')
        related = data.pop('externalLink','')
        if related:
            data['enlaces'] = [{'titulo':'Enlace relacionado','url':related}]
    if isinstance(data.get('imagen'),str):
        data['imagen'] = data['imagen'].removeprefix('/byjahr/').removeprefix('/')
    return data

def validate():
    for network in cfg.get('redes_sociales', []):
        if not network.get('nombre') or not external(network.get('url')):
            errors.append('config.json: cada red necesita nombre y URL HTTPS')
    if cfg.get('email') and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', cfg['email']):
        errors.append('config.json: correo inválido')
    for field in ('favicon', 'retrato'):
        if cfg.get(field) and not asset(cfg[field]):
            errors.append(f'config.json: no existe {field}')
    if cfg.get('retrato') and not cfg.get('retrato_alt', '').strip():
        errors.append('config.json: falta retrato_alt')
    for group, fields in {
        'colecciones': ('slug','titulo','descripcion'),
        'obras': ('slug','titulo','imagen','alt','coleccion','categoria'),
        'criaturas': ('slug','nombre','imagen','descripcion'),
    }.items():
        found = {}
        for path in sorted(Path('src/content', group).glob('*.json')):
            def fail(msg): errors.append(f'{path}: {msg}')
            try:
                d = json.loads(path.read_text())
                if not isinstance(d, dict):
                    raise ValueError('se esperaba un objeto JSON')
                d = normalize_entry(group,path,d)
                for field in fields:
                    if not isinstance(d.get(field), str) or not d[field].strip():
                        fail(f'falta {field} o está vacío')
                slug = d.get('slug', '')
                if not isinstance(slug, str) or not slug_pattern.fullmatch(slug):
                    fail('slug inválido; usa minúsculas, números y guiones')
                elif slug in found:
                    fail(f'slug duplicado: {slug}')
                else:
                    if group == 'colecciones':
                        if slug != path.stem: fail('el identificador fijo debe coincidir con el archivo de colección')
                        d['_cms_file'] = path.as_posix()
                    found[slug] = d
                for key, value in d.items():
                    if key in ('oculta', 'destacada', 'draft', 'published'):
                        if not isinstance(value, bool): fail(f'{key} debe ser booleano')
                    elif key in ('orden','ancho','alto'):
                        if type(value) is not int or value < 0: fail(f'{key} debe ser un entero no negativo')
                    elif key == 'etiquetas':
                        if not isinstance(value,list) or not all(isinstance(x,str) for x in value): fail('etiquetas debe ser una lista de textos')
                    elif key in ('enlaces','variantes'):
                        if not isinstance(value,list):
                            fail(f'{key} debe ser una lista')
                        else:
                            widths = set()
                            for row in value:
                                if not isinstance(row,dict):
                                    fail(f'{key}: se esperaba un objeto')
                                elif key == 'enlaces':
                                    if not external(row.get('url')) or not isinstance(row.get('titulo'),str) or not row['titulo'].strip():
                                        fail('enlace inválido: usa titulo y url HTTPS')
                                else:
                                    width = row.get('ancho')
                                    if not asset(row.get('imagen')) or type(width) is not int or width <= 0 or width in widths:
                                        fail('variante inválida: usa imagen existente y ancho positivo único')
                                    else:
                                        widths.add(width)
                    elif not isinstance(value,str):
                        fail(f'{key} debe ser texto')
                if d.get('imagen'):
                    if not asset(d['imagen']):
                        fail('imagen inexistente o fuera de public/')
                    elif not d.get('alt','').strip():
                        fail('falta texto alternativo')
                    else:
                        read_art(PUBLIC / d['imagen'])
                for variant in d.get('variantes',[]):
                    if isinstance(variant,dict) and asset(variant.get('imagen')):
                        read_art(PUBLIC / variant['imagen'])
                if group == 'colecciones' and d.get('imagen') and not d.get('alt','').strip():
                    fail('falta alt de la portada')
                if d.get('fecha'):
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d['fecha']): raise ValueError('fecha: usa AAAA-MM-DD')
                    date.fromisoformat(d['fecha'])
                if bool(d.get('ancho')) != bool(d.get('alto')): fail('indica ancho y alto juntos')
                if group == 'obras':
                    if d.get('estado_publicacion','publicada') not in ('publicada','borrador'): fail('estado de publicación inválido')
                    if not d.get('fecha') and not re.fullmatch(r'[1-9][0-9]{3}',d.get('ano','')): fail('indica fecha o año de cuatro dígitos')
                    if d.get('ano') and (not re.fullmatch(r'[1-9][0-9]{3}',d['ano']) or (d.get('fecha') and d['fecha'][:4] != d['ano'])): fail('año inválido o distinto de la fecha')
                    if d.get('coleccion') not in groups['colecciones']: fail('colección inexistente')
                    if d.get('categoria') not in cfg['categorias'] + list(cfg['categorias_cms'].values()) + ['Ilustración','Escena','Estudio']: fail('categoría inválida')
                if group == 'criaturas' and d.get('estado') and d['estado'] not in statuses:
                    fail('estado inválido: ' + ', '.join(statuses))
            except (ValueError, TypeError, AttributeError, UnicodeError, OSError) as exc:
                fail(str(exc))
        groups[group] = found
    if errors: raise SystemExit('\n'.join(errors))

TITLE = 'Ilustración digital de fantasía oscura y relatos contados en tinta.'
NAV = [('portafolio/','Portafolio'),('colecciones/','Colecciones'),('bestiario/','Bestiario'),('sobre/','Sobre'),('contacto/','Contacto')]
COLS = {}
routes = []

def arrow(direction='diagonal'):
    paths = {'diagonal': 'M3 9l6-6M4 3h5v5', 'left': 'M10 6H2m4-4L2 6l4 4', 'right': 'M2 6h8M6 2l4 4-4 4'}
    return f'<svg class="link-arrow" aria-hidden="true" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.3"><path d="{paths[direction]}"/></svg>'

def social(primary=False, show_handle=True):
    parts = []
    for index, network in enumerate(cfg.get('redes_sociales', [])):
        cls = 'cta' if primary and index == 0 else ''
        name = network['nombre']
        if show_handle and network.get('usuario'):
            name += ' · ' + network['usuario']
        parts.append(
            f'<a class="{cls}" href="{e(network["url"])}" target="_blank" '
            f'rel="noopener noreferrer">{e(name)}{arrow()}</a>'
        )
    return '<div class="social-links">' + ''.join(parts) + '</div>' if parts else ''

def link(path, label, cls='', direction=None):
    icon = arrow(direction) if direction else ''
    return f'<a class="{cls}" href="{e(url(path))}">{e(label)}{icon}</a>'

def page(path, title, description, body, image='', current=None):
    current = path if current is None else current
    nav = ''.join(f'<a href="{e(url(p))}"{" aria-current=page" if current == p else ""}>{label}</a>' for p,label in NAV if p != 'bestiario/' or 'bestiario' in COLS)
    full = '@byjahr · Ilustración de fantasía oscura' if not path else f'{title} · @byjahr'
    absolute = SITE + url(path)
    meta = f'<link rel="canonical" href="{e(absolute)}"><meta property="og:url" content="{e(absolute)}">' if SITE and path != '404.html' else ''
    if image and SITE:
        meta += f'<meta property="og:image" content="{e(SITE + url(image))}">'
    if path == '404.html':
        meta += '<meta name="robots" content="noindex">'
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(full)}"><meta property="og:description" content="{e(description)}"><meta property="og:type" content="website"><meta property="og:locale" content="es_MX">{meta}
<link rel="icon" href="{url(cfg['favicon'])}"><link rel="stylesheet" href="{url('style.css')}"><script defer src="{url('site.js')}"></script></head>
<body><a class="skip" href="#contenido">Saltar al contenido</a><header class="mast"><div class="wrap">
{link('', '@byjahr','wordmark')}<nav class="desktop nav" aria-label="Principal">{nav}</nav>
<details class="mobile"><summary>Menú</summary><nav class="nav" aria-label="Principal móvil">{nav}</nav></details></div></header>
<main id="contenido" tabindex="-1" class="wrap">{body}</main>
<footer class="footer"><div class="wrap">{link('', '@byjahr','wordmark')}<span>Archivo de ilustración · Fantasía oscura</span><div>{social(show_handle=False) or link('contacto/','Contacto')}</div></div></footer></body></html>"""
    dest = OUT / (path if path.endswith('.html') else path + 'index.html')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(doc, encoding='utf-8')
    if path != '404.html': routes.append(path)

def head(kicker, title, desc=''):
    return f'<header class="page-head"><p class="eyebrow">{e(kicker)}</p><h1>{e(title)}</h1><p class="lede">{e(desc)}</p></header>'

def img(d, eager=False, cls=''):
    if not d.get('imagen'): return ''
    variants = d.get('variantes', [])
    srcset = ', '.join(f'{url(v["imagen"])} {v["ancho"]}w' for v in variants)
    responsive = f' srcset="{e(srcset)}" sizes="(max-width: 740px) 94vw, 48vw"' if variants else ''
    dimensions = f' width="{d["ancho"]}" height="{d["alto"]}"' if d.get('ancho') and d.get('alto') else ''
    return f'<img{dimensions} class="{cls}" src="{url(d["imagen"])}" alt="{e(d.get("alt") or d.get("descripcion",""))}" loading="{"eager" if eager else "lazy"}" decoding="async"{responsive}>'

def label(d): return d.get('titulo') or d['nombre']
def entrypath(d, beast=False): return ('bestiario/' if beast else 'portafolio/') + d['slug'] + '/'
def empty(msg): return f'<p class="empty">{e(msg)}</p>'

def collection_path(d):
    return 'bestiario/' if d['slug'] == 'bestiario' else f'colecciones/{d["slug"]}/'

def attr(d, field):
    if field == 'ano': return d.get('ano') or d.get('fecha','')[:4]
    return d.get(field,'') or ('Ilustración' if field == 'estado' else '')

def card(d, fields=(), beast=False):
    attrs = ' '.join(f'data-{k}="{e(attr(d,k))}"' for k,_ in fields)
    metadata = [COLS.get(d.get('coleccion'),{}).get('titulo',''),attr(d,'ano'),d.get('categoria','')]
    if beast: metadata = [attr(d,k) for k in ('tipo','tamano','entorno','amenaza','estado')]
    search = ' '.join(str(d.get(k,'')) for k in ('descripcion','descripcion_ampliada','tecnica','personaje','campana','intro','prompt'))
    search += ' ' + ' '.join(d.get('etiquetas', []))
    return f'<article class="card" data-entry {attrs} data-search="{e(search)}">{img(d)}<p class="eyebrow">{e(" · ".join(filter(None,metadata)))}</p><h3>{link(entrypath(d,beast),label(d))}</h3><p>{e(d.get("descripcion",""))}</p></article>'

def gallery(items, fields=(), beast=False, empty_content=''):
    if not items: return empty_content
    form = ''
    if fields:
        controls = []
        for key, name in fields:
            opts = sorted({attr(d,key) for d in items} - {''})
            if len(opts) < 2: continue
            values = ''.join(f'<option value="{e(o)}">{e(COLS[o]["titulo"] if key == "coleccion" else o)}</option>' for o in opts)
            controls.append(f'<label>{e(name)}<select name="{key}"><option value="">Todos</option>{values}</select></label>')
        form = '<form class="filters" data-filters hidden role="search"><label>Buscar<input name="q" type="search"></label>' + ''.join(controls) + '<button type="reset">Limpiar</button></form><p data-count aria-live="polite"></p><p class="empty" data-no-results hidden>No hay coincidencias.</p>'
    return form + '<div class="grid">' + ''.join(card(d,fields,beast) for d in items) + '</div>'

def section(title, content, more='', kicker=''):
    return f'<section class="section"><p class="eyebrow">{e(kicker)}</p><div class="section-head"><h2>{e(title)}</h2>{more}</div>{content}</section>'

def index(cols):
    return ''.join(f'<a class="collection" href="{url(collection_path(d))}"><span class="eyebrow">{i:02}</span><h3>{e(label(d))}</h3><p>{e(d["descripcion"])}</p><span class="arrow" aria-hidden="true">{arrow()}</span></a>' for i,d in enumerate(cols,1))

def textblocks(d, fields):
    return ''.join(f'<section><h2>{e(title)}</h2><p>{e(d[k])}</p></section>' for k,title in fields if d.get(k))

def detail(items, beast=False):
    for i,d in enumerate(items):
        p = entrypath(d,beast)
        section_name, section_path = ('Bestiario','bestiario/') if beast else ('Portafolio','portafolio/')
        if beast:
            intro = d.get('intro') or d['descripcion']
            fields = [('fisico','Descripción física'),('comportamiento','Comportamiento'),('habitat','Hábitat'),('leyenda','Historia o leyenda'),('habilidades','Habilidades'),('debilidades','Debilidades'),('senales','Señales de su presencia'),('uso','Uso en una historia o campaña'),('rasgos','Rasgos'),('acciones','Acciones'),('estadisticas','Homebrew original · compatible con 5e')]
            facts = [('tipo','Tipo'),('tamano','Tamaño'),('entorno','Entorno'),('amenaza','Amenaza o desafío'),('estado','Estado'),('creditos','Créditos'),('fecha','Fecha')]
        else:
            intro = d.get('descripcion','')
            fields = [('descripcion_ampliada','Sobre la obra')]
            facts = [('formato','Formato'),('creditos','Créditos'),('ano','Año'),('tecnica','Técnica'),('categoria','Categoría'),('personaje','Personaje'),('campana','Temporada o campaña'),('fecha','Fecha'),('prompt','Prompt de Inktober')]
        defs = ''.join(f'<dt>{title}</dt><dd>{e(attr(d,k))}</dd>' for k,title in facts if attr(d,k))
        if not beast:
            col = COLS[d['coleccion']]
            defs += f'<dt>Colección</dt><dd>{link(collection_path(col),label(col))}</dd>'
        related = ''.join(f'<li><a href="{e(x["url"])}">{e(x["titulo"])}</a></li>' for x in d.get('enlaces',[]))
        if not beast:
            others = [candidate for candidate in items if candidate is not d and
                      (candidate['coleccion'] == d['coleccion'] or
                       set(candidate.get('etiquetas', [])) & set(d.get('etiquetas', [])) or
                       (d.get('personaje') and candidate.get('personaje') == d['personaje']))][:3]
            if others:
                related += ''.join(f'<li>{link(entrypath(candidate),label(candidate))}</li>' for candidate in others)
        share = '<button data-share hidden type="button">Copiar enlace</button><input data-share-url hidden readonly aria-label="Enlace de la ficha"><p data-share-status role="status"></p>'
        pager = ''.join(link(entrypath(items[j],beast), prefix + label(items[j]), direction=direction) for j,prefix,direction in [(i-1,'Anterior: ','left'),(i+1,'Siguiente: ','right')] if 0 <= j < len(items))
        desc = f'<p>{e(d["descripcion"])}</p>' if beast and d.get('intro') and d['intro'] != d['descripcion'] else ''
        if d.get('aviso'):
            desc += f'<p class="empty"><strong>Aviso de contenido:</strong> {e(d["aviso"])}</p>'
        enlarged = f'<a class="art-link" href="{url(d["imagen"])}" target="_blank" rel="noopener noreferrer">{img(d,True)}<span>Ver imagen a tamaño completo {arrow()}</span></a>'
        page(p,label(d),d.get('descripcion') or label(d),
             head(section_name,label(d),intro) + f'<div class="detail">{enlarged}<div class="prose">{desc}<dl>{defs}</dl>{textblocks(d,fields)}{f"<ul>{related}</ul>" if related else ""}{share}</div></div><nav class="pager" aria-label="Entre fichas">{link(section_path,"Volver a " + section_name)}{pager}</nav>',
             d['imagen'],section_path)

def build():
    global COLS
    if OUT.is_symlink(): raise SystemExit('dist no puede ser un enlace simbólico')
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(PUBLIC,OUT,ignore=shutil.ignore_patterns('.gitkeep','.DS_Store','images','uploads'))
    cols = [x for x in groups['colecciones'].values() if not x.get('oculta')]
    order = ['bestiario','caoz-con-todo','inktober-2026','fanart','originales']
    cols.sort(key=lambda x: (x.get('orden', order.index(x['slug']) if x['slug'] in order else len(order)),label(x)))
    COLS = {x['slug']:x for x in cols}
    works = sorted([d for d in groups['obras'].values() if d['coleccion'] in COLS and d.get('estado_publicacion','publicada') == 'publicada'], key=lambda d: (-d.get('orden',0), d.get('fecha') or attr(d,'ano')), reverse=True)
    beasts = sorted([d for d in groups['criaturas'].values()
                     if d.get('estado_publicacion','publicada') == 'publicada'], key=label) if 'bestiario' in COLS else []
    generate_admin(OUT, cfg, groups['colecciones'])
    for item in cols + works + beasts:
        if not item.get('imagen'):
            continue
        collection = item.get('coleccion') or ('bestiario' if item in beasts else item['slug'])
        folder = Path('images/artworks') / collection
        prefix = 'portada-' if item in cols else 'criatura-' if item in beasts else ''
        stem = f"{collection}-{prefix}{item['slug']}"
        variants = export_art(read_art(PUBLIC / item['imagen']), OUT / folder, stem)
        filename, item['ancho'], item['alto'] = variants[-1]
        item['imagen'] = (folder / filename).as_posix()
        item['variantes'] = [dict(imagen=(folder / name).as_posix(),ancho=w) for name,w,_ in variants]
    featured = next((d for d in works if d.get('destacada')), None)
    plate = f'<figure>{link(entrypath(featured),label(featured))}{img(featured,True)}</figure>' if featured else ''
    hero_class = "hero" if featured else "hero hero-text"
    home = f'<section class="{hero_class}"><div><p class="eyebrow">Archivo visual · Fantasía oscura</p><h1>@byjahr</h1><p class="lede">{TITLE}</p>{link("portafolio/","Explorar portafolio","cta","diagonal")}</div>{plate}</section>'
    home += section('Colecciones',index(cols) or empty('No hay colecciones publicadas.'),link('colecciones/','Ver índice',direction='diagonal'),'01 / Índice')
    if works: home += section('Obras recientes',gallery(works[:3]),link('portafolio/','Ver portafolio',direction='diagonal'),'02 / Portafolio')
    if 'bestiario' in COLS:
        home += section('Bestiario','<div class="band"><p class="lede">Un archivo de criaturas originales, de la primera ilustración a la ficha completa.</p>' + link('bestiario/','Abrir el Bestiario','cta','diagonal') + '</div>',kicker='03 / Fichas de campo')
    home += section('Sigue el proceso',f'<p>{e(cfg["redes"])}</p>' + social(True))
    page('', '@byjahr', cfg['descripcion'],home,featured['imagen'] if featured else '')
    page('portafolio/','Portafolio',TITLE,head('Archivo visual','Portafolio','Explora todas las ilustraciones publicadas.') + gallery(works,[('coleccion','Colección'),('ano','Año'),('categoria','Categoría')],empty_content=empty('El archivo está comenzando a tomar forma. Las primeras ilustraciones se publicarán aquí muy pronto.')))
    page('colecciones/','Colecciones','Índice de colecciones de @byjahr.',head('Índice del archivo','Colecciones') + index(cols))
    for col in cols:
        if col['slug']=='bestiario': continue
        p = collection_path(col)
        fields = [('categoria','Formato'),('personaje','Personaje'),('campana','Temporada o campaña'),('ano','Año')] if col['slug']=='caoz-con-todo' else [('categoria','Categoría'),('ano','Año')]
        page(p,label(col),col['descripcion'],head('Colecciones',label(col),col['descripcion']) + img(col,True,'portrait') + gallery([d for d in works if d['coleccion']==col['slug']],fields,empty_content=empty(col['vacio']) if col.get('vacio') else ''),col.get('imagen',''),'colecciones/')
    col = COLS.get('bestiario')
    if col:
        illustrations = [d for d in works if d['coleccion']=='bestiario']
        extra = section('Ilustraciones del Bestiario',gallery(illustrations)) if illustrations else ''
        page('bestiario/',label(col),col['descripcion'],head('Fichas de campo',label(col),col['descripcion']) + img(col,True,'portrait') + gallery(beasts,[('tipo','Tipo'),('tamano','Tamaño'),('entorno','Entorno'),('amenaza','Amenaza'),('estado','Estado')],True,empty(col['vacio']) + '<p>El Bestiario reunirá criaturas originales ilustradas en tinta, desde sus primeros avistamientos hasta sus fichas completas de campo.</p>') + extra,col.get('imagen',''))
    detail(works)
    detail(beasts,True)
    profile = textblocks(cfg, [('bio','Biografía'),('declaracion','Declaración artística')])
    profile += f'<blockquote lang="en">{e(cfg["lema"])}</blockquote>'
    profile += textblocks(cfg, [('influencias','Influencias')])
    profile += f'<section><h2>Técnica y proceso</h2><p>{e(cfg["proceso"])}</p><p>{e(cfg["proceso_continuacion"])}</p></section>'
    profile += f'<section><h2>Contacto profesional</h2><p>{e(cfg["contacto_profesional"])}</p>{social(True)}</section>'
    page('sobre/','Sobre el proyecto',cfg['introduccion'],head('El artista','Sobre el proyecto',cfg['introduccion']) + f'<div class="prose">{profile}</div>')
    contact = f'<div class="prose">{social(True)}<p>{e(cfg["comisiones"])}</p></div>'
    page('contacto/','Contacto',cfg['contacto'],head('Correspondencia','Contacto',cfg['contacto']) + contact)
    page('404.html','Página no encontrada','No encontramos esta página.',head('Error 404','Lámina extraviada','Esta página no está en el archivo.') + link('portafolio/','Regresar al portafolio','cta'))
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{xml(SITE+url(p))}</loc></url>' for p in routes if SITE) + '</urlset>\n')
    (OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: {url("admin/")}\n' + (f'Sitemap: {SITE}{url("sitemap.xml")}\n' if SITE else ''))
    (OUT/'.nojekyll').touch()
    print(f'{len(routes)} rutas y 404 generadas en {OUT}/ (base {BASE})')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['validate','build'])
    args = parser.parse_args()
    validate()
    print('Contenido válido.')
    if args.command == 'build': build()
