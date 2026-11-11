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

def validate():
    for field in ('instagram', 'tiktok'):
        if cfg.get(field) and not external(cfg[field]):
            errors.append(f'config.json: {field} debe ser una URL HTTPS')
    if cfg.get('email') and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', cfg['email']):
        errors.append('config.json: correo inválido')
    for field in ('favicon', 'retrato'):
        if cfg.get(field) and not asset(cfg[field]):
            errors.append(f'config.json: no existe {field}')
    if cfg.get('retrato') and not cfg.get('retrato_alt', '').strip():
        errors.append('config.json: falta retrato_alt')
    for group, fields in {
        'colecciones': ('slug','titulo','descripcion'),
        'obras': ('slug','titulo','imagen','alt','fecha','coleccion','categoria'),
        'criaturas': ('slug','nombre','imagen','descripcion'),
    }.items():
        found = {}
        for path in sorted(Path('src/content', group).glob('*.json')):
            def fail(msg): errors.append(f'{path}: {msg}')
            try:
                d = json.loads(path.read_text())
                if not isinstance(d, dict):
                    raise ValueError('se esperaba un objeto JSON')
                for field in fields:
                    if not isinstance(d.get(field), str) or not d[field].strip():
                        fail(f'falta {field} o está vacío')
                slug = d.get('slug', '')
                if not isinstance(slug, str) or not slug_pattern.fullmatch(slug):
                    fail('slug inválido; usa minúsculas, números y guiones')
                elif slug in found:
                    fail(f'slug duplicado: {slug}')
                else:
                    found[slug] = d
                for key, value in d.items():
                    if key in ('oculta', 'destacada'):
                        if not isinstance(value, bool): fail(f'{key} debe ser booleano')
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
                if d.get('imagen') and not asset(d['imagen']): fail('imagen inexistente o fuera de public/')
                if group == 'colecciones' and d.get('imagen') and not d.get('alt','').strip():
                    fail('falta alt de la portada')
                if d.get('fecha'):
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', d['fecha']): raise ValueError('fecha: usa AAAA-MM-DD')
                    date.fromisoformat(d['fecha'])
                if group == 'obras':
                    if d.get('coleccion') not in groups['colecciones']: fail('colección inexistente')
                    if d.get('categoria') not in cfg['categorias']: fail('categoría inválida')
                if group == 'criaturas' and d.get('estado') and d['estado'] not in statuses:
                    fail('estado inválido: ' + ', '.join(statuses))
            except (ValueError, TypeError, AttributeError, UnicodeError) as exc:
                fail(str(exc))
        groups[group] = found
    if errors: raise SystemExit('\n'.join(errors))

TITLE = 'Ilustración digital de fantasía oscura y relatos contados en tinta.'
NAV = [('portafolio/','Portafolio'),('colecciones/','Colecciones'),('bestiario/','Bestiario'),('sobre/','Sobre'),('contacto/','Contacto')]
COLS = {}
routes = []

def social():
    parts = [f'<a href="{e(cfg[k])}">{title} ↗</a>' for k,title in [('instagram','Instagram'),('tiktok','TikTok')] if cfg.get(k)]
    if cfg.get('email'):
        parts.append(f'<a href="mailto:{e(quote(cfg["email"],safe="@"))}">{e(cfg["email"])}</a>')
    return ' · '.join(parts)

def link(path, label, cls=''):
    return f'<a class="{cls}" href="{e(url(path))}">{e(label)}</a>'

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
<footer class="footer"><div class="wrap">{link('', '@byjahr','wordmark')}<span>Archivo de ilustración · Fantasía oscura</span><div>{social() or link('contacto/','Contacto')}</div></div></footer></body></html>"""
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
    return f'<img class="{cls}" src="{url(d["imagen"])}" alt="{e(d.get("alt") or d.get("descripcion",""))}" loading="{"eager" if eager else "lazy"}" decoding="async"{responsive}>'

def label(d): return d.get('titulo') or d['nombre']
def entrypath(d, beast=False): return ('bestiario/' if beast else 'portafolio/') + d['slug'] + '/'
def empty(msg): return f'<p class="empty">{e(msg)}</p>'

def collection_path(d):
    return 'bestiario/' if d['slug'] == 'bestiario' else f'colecciones/{d["slug"]}/'

def attr(d, field):
    if field == 'ano': return d.get('fecha','')[:4]
    return d.get(field,'') or ('Ilustración' if field == 'estado' else '')

def card(d, fields=(), beast=False):
    attrs = ' '.join(f'data-{k}="{e(attr(d,k))}"' for k,_ in fields)
    metadata = [COLS.get(d.get('coleccion'),{}).get('titulo',''),attr(d,'ano'),d.get('categoria','')]
    if beast: metadata = [attr(d,k) for k in ('tipo','tamano','entorno','amenaza','estado')]
    search = ' '.join(str(d.get(k,'')) for k in ('descripcion','tecnica','personaje','campana','intro'))
    return f'<article class="card" data-entry {attrs} data-search="{e(search)}">{img(d)}<p class="eyebrow">{e(" · ".join(filter(None,metadata)))}</p><h3>{link(entrypath(d,beast),label(d))}</h3><p>{e(d.get("descripcion",""))}</p></article>'

def gallery(items, fields=(), beast=False):
    if not items: return empty('Aún no hay entradas publicadas en este archivo.')
    form = ''
    if fields:
        controls = []
        for key, name in fields:
            opts = sorted({attr(d,key) for d in items} - {''})
            if not opts: continue
            values = ''.join(f'<option value="{e(o)}">{e(COLS[o]["titulo"] if key == "coleccion" else o)}</option>' for o in opts)
            controls.append(f'<label>{e(name)}<select name="{key}"><option value="">Todos</option>{values}</select></label>')
        form = '<form class="filters" data-filters hidden role="search"><label>Buscar<input name="q" type="search"></label>' + ''.join(controls) + '<button type="reset">Limpiar</button></form><p data-count aria-live="polite"></p><p class="empty" data-no-results hidden>No hay coincidencias.</p>'
    return form + '<div class="grid">' + ''.join(card(d,fields,beast) for d in items) + '</div>'

def section(title, content, more='', kicker=''):
    return f'<section class="section"><p class="eyebrow">{e(kicker)}</p><div class="section-head"><h2>{e(title)}</h2>{more}</div>{content}</section>'

def index(cols):
    return ''.join(f'<a class="collection" href="{url(collection_path(d))}"><span class="eyebrow">{i:02}</span><h3>{e(label(d))}</h3><p>{e(d["descripcion"])}</p><span class="arrow" aria-hidden="true">↗</span></a>' for i,d in enumerate(cols,1))

def textblocks(d, fields):
    return ''.join(f'<section><h2>{e(title)}</h2><p>{e(d[k])}</p></section>' for k,title in fields if d.get(k))

def detail(items, beast=False):
    for i,d in enumerate(items):
        p = entrypath(d,beast)
        section_name, section_path = ('Bestiario','bestiario/') if beast else ('Portafolio','portafolio/')
        if beast:
            intro = d.get('intro') or d['descripcion']
            fields = [('fisico','Descripción física'),('comportamiento','Comportamiento'),('habitat','Hábitat'),('leyenda','Historia o leyenda'),('habilidades','Habilidades'),('debilidades','Debilidades'),('senales','Señales de su presencia'),('uso','Uso en una historia o campaña'),('estadisticas','Homebrew original · compatible con 5e')]
            facts = [('tipo','Tipo'),('tamano','Tamaño'),('entorno','Entorno'),('amenaza','Amenaza o desafío'),('estado','Estado'),('creditos','Créditos'),('fecha','Fecha')]
        else:
            intro = d.get('descripcion','')
            fields = []
            facts = [('tecnica','Técnica'),('categoria','Categoría'),('personaje','Personaje'),('campana','Temporada o campaña'),('fecha','Fecha')]
        defs = ''.join(f'<dt>{title}</dt><dd>{e(attr(d,k))}</dd>' for k,title in facts if attr(d,k))
        if not beast:
            col = COLS[d['coleccion']]
            defs += f'<dt>Colección</dt><dd>{link(collection_path(col),label(col))}</dd>'
        related = ''.join(f'<li><a href="{e(x["url"])}">{e(x["titulo"])}</a></li>' for x in d.get('enlaces',[]))
        share = '<button data-share hidden type="button">Copiar enlace</button><input data-share-url hidden readonly aria-label="Enlace de la ficha"><p data-share-status role="status"></p>'
        pager = ''.join(link(entrypath(items[j],beast), prefix + label(items[j])) for j,prefix in [(i-1,'← Anterior: '),(i+1,'Siguiente: ')] if 0 <= j < len(items))
        desc = f'<p>{e(d["descripcion"])}</p>' if beast and d.get('intro') and d['intro'] != d['descripcion'] else ''
        page(p,label(d),d.get('descripcion') or label(d),
             head(section_name,label(d),intro) + f'<div class="detail">{img(d,True)}<div class="prose">{desc}<dl>{defs}</dl>{textblocks(d,fields)}{f"<ul>{related}</ul>" if related else ""}{share}</div></div><nav class="pager" aria-label="Entre fichas">{link(section_path,"Volver a " + section_name)}{pager}</nav>',
             d['imagen'],section_path)

def build():
    global COLS
    if OUT.is_symlink(): raise SystemExit('dist no puede ser un enlace simbólico')
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(PUBLIC,OUT,ignore=shutil.ignore_patterns('.gitkeep','.DS_Store'))
    cols = [x for x in groups['colecciones'].values() if not x.get('oculta')]
    order = ['bestiario','caoz-con-todo','inktober-2026','fanart','originales']
    cols.sort(key=lambda x: (order.index(x['slug']) if x['slug'] in order else len(order),label(x)))
    COLS = {x['slug']:x for x in cols}
    works = sorted([d for d in groups['obras'].values() if d['coleccion'] in COLS],key=lambda d:d['fecha'],reverse=True)
    beasts = sorted(groups['criaturas'].values(),key=label) if 'bestiario' in COLS else []
    featured = next((d for d in works if d.get('destacada')), works[0] if works else None)
    plate = f'<figure>{link(entrypath(featured),label(featured))}{img(featured,True)}</figure>' if featured else '<div class="plate"><div><p class="eyebrow">Lámina reservada</p><span>01</span><p>Obra destacada pendiente de publicación</p></div></div>'
    home = f'<section class="hero"><div><p class="eyebrow">Archivo visual · Fantasía oscura</p><h1>@byjahr</h1><p class="lede">{TITLE}</p>{link("portafolio/","Explorar portafolio ↗","cta")}</div>{plate}</section>'
    home += section('Colecciones',index(cols) or empty('No hay colecciones publicadas.'),link('colecciones/','Ver índice ↗'),'01 / Índice')
    home += section('Obras recientes',gallery(works[:3]),link('portafolio/','Ver portafolio ↗'),'02 / Portafolio')
    if 'bestiario' in COLS:
        home += section('Bestiario','<div class="band"><p class="lede">Un archivo de criaturas originales, de la primera ilustración a la ficha completa.</p>' + link('bestiario/','Abrir el Bestiario ↗','cta') + '</div>',kicker='03 / Fichas de campo')
    home += section('En otros lugares',social() or empty('Enlaces a Instagram y TikTok pendientes de publicación.'))
    page('', '@byjahr', TITLE,home,featured['imagen'] if featured else '')
    page('portafolio/','Portafolio',TITLE,head('Archivo visual','Portafolio','Explora todas las ilustraciones publicadas.') + gallery(works,[('coleccion','Colección'),('ano','Año'),('categoria','Categoría')]))
    page('colecciones/','Colecciones','Índice de colecciones de @byjahr.',head('Índice del archivo','Colecciones') + index(cols))
    for col in cols:
        if col['slug']=='bestiario': continue
        p = collection_path(col)
        fields = [('categoria','Formato'),('personaje','Personaje'),('campana','Temporada o campaña'),('ano','Año')] if col['slug']=='caoz-con-todo' else [('categoria','Categoría'),('ano','Año')]
        page(p,label(col),col['descripcion'],head('Colecciones',label(col),col['descripcion']) + img(col,True,'portrait') + gallery([d for d in works if d['coleccion']==col['slug']],fields),col.get('imagen',''),'colecciones/')
    col = COLS.get('bestiario')
    if col:
        illustrations = [d for d in works if d['coleccion']=='bestiario']
        extra = section('Ilustraciones del Bestiario',gallery(illustrations)) if illustrations else ''
        page('bestiario/',label(col),col['descripcion'],head('Fichas de campo',label(col),col['descripcion']) + img(col,True,'portrait') + gallery(beasts,[('tipo','Tipo'),('tamano','Tamaño'),('entorno','Entorno'),('amenaza','Amenaza'),('estado','Estado')],True) + extra,col.get('imagen',''))
    detail(works)
    detail(beasts,True)
    bio = {k:cfg.get(k) or 'Texto provisional: pendiente de completar por el artista.' for k in ('bio','declaracion','influencias','proceso')}
    portrait = img({'imagen':cfg.get('retrato'),'alt':cfg.get('retrato_alt','')},True,'portrait')
    page('sobre/','Sobre @byjahr',TITLE,head('El artista','Sobre @byjahr',TITLE) + portrait + '<div class="prose">' + textblocks(bio,[('bio','Biografía'),('declaracion','Declaración artística'),('influencias','Influencias'),('proceso','Técnica y proceso')]) + social() + '<p>' + link('contacto/','Contacto profesional') + '</p></div>',cfg.get('retrato',''))
    page('contacto/','Contacto','Colaboraciones y comisiones.',head('Correspondencia','Contacto','Para consultas de colaboraciones o comisiones.') + (social() or empty('Canales de contacto pendientes de publicación.')))
    page('404.html','Página no encontrada','No encontramos esta página.',head('Error 404','Lámina extraviada','Esta página no está en el archivo.') + link('portafolio/','Regresar al portafolio','cta'))
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{xml(SITE+url(p))}</loc></url>' for p in routes if SITE) + '</urlset>\n')
    (OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n' + (f'Sitemap: {SITE}{url("sitemap.xml")}\n' if SITE else ''))
    (OUT/'.nojekyll').touch()
    print(f'{len(routes)} rutas y 404 generadas en {OUT}/ (base {BASE})')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['validate','build'])
    args = parser.parse_args()
    validate()
    print('Contenido válido.')
    if args.command == 'build': build()
