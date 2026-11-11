"""Build the Decap editor configuration from the site's data."""
import json
import os
import re
from pathlib import Path

def field(name, label, widget='string', required=False, **options):
    return dict(name=name, label=label, widget=widget, required=required, **options)

def generate_admin(out, config, collections):
    def text(name, label): return field(name, label, 'text')
    slug = field('slug', 'Identificador de la URL', pattern=[
        '^[a-z0-9]+(?:-[a-z0-9]+)*$', 'Usa minúsculas, números y guiones.'],
        hint='Al crear puedes dejarlo vacío para generarlo del título. Conserva la URL al editar.')
    image = field('imagen', 'Ilustración', 'image', True, choose_url=False)
    alt = field('alt', 'Texto alternativo', required=True)
    draft = field('draft','Borrador', 'boolean', default=True)
    published = field('published','Visible en el sitio', 'boolean', default=False)
    works = [
        field('title','Título', required=True), slug, dict(image, name='image'), alt,
        field('collection','Colección','select',True, options=[dict(label=c['titulo'],value=c['slug']) for c in collections.values()]),
        field('category','Categoría','select',True,options=[dict(value=k,label=v) for k,v in config['categorias_cms'].items()]),
        field('year','Año','number',True,value_type='int',min=1000,max=9999),
        field('description','Descripción breve','text',True), published, draft,
        field('date','Fecha','datetime',date_format='YYYY-MM-DD',time_format=False,format='YYYY-MM-DD',default=''),
        field('featured','Destacar en portada','boolean',default=False),
        field('order','Orden','number',value_type='int',min=0,default=0),
        field('character','Personaje'), field('campaign','Campaña o temporada'),
        field('inktoberPrompt','Prompt de Inktober'), field('technique','Técnica'),
        field('format','Formato'), field('tags','Etiquetas','list'),
        text('caption','Texto ampliado'), field('credits','Créditos'),
        field('externalLink','Enlace relacionado (HTTPS)'), text('contentWarning','Aviso de contenido'),
        field('sourceFile','Nombre del archivo original (referencia interna)'),
    ]
    beasts = [field('nombre','Nombre',required=True),slug,image,alt,
              field('descripcion','Descripción breve','text',True),published,draft]
    beasts += [field(key,label) for key,label in [('tipo','Tipo'),('tamano','Tamaño'),('entorno','Entorno'),('amenaza','Amenaza o desafío'),('creditos','Créditos')]]
    beasts += [field('estado','Estado','select',options=['Ilustración','Lore parcial','Entrada completa'])]
    beasts += [text(key,label) for key,label in [
        ('intro','Introducción'),('fisico','Descripción física'),('comportamiento','Comportamiento'),
        ('habitat','Hábitat'),('leyenda','Leyenda'),('habilidades','Habilidades'),('debilidades','Debilidades'),
        ('senales','Señales de presencia'),('rasgos','Rasgos'),('acciones','Acciones'),
        ('estadisticas','Estadísticas homebrew compatibles con 5e'),('uso','Uso narrativo')]]
    def folder(name,label,title,fields):
        return dict(name=name,label=label,folder='src/content/'+name,create=True,delete=False,
                    extension='json',format='json',identifier_field=title,slug='{{slug}}',
                    editor={'preview':False},fields=fields)
    files = []
    for slug_key, entry in collections.items():
        files.append(dict(name=slug_key,label=entry['titulo'],file=entry['_cms_file'],fields=[
            field('slug','Identificador fijo','hidden',default=slug_key),
            field('titulo','Nombre',required=True),field('descripcion','Descripción','text',True),
            dict(image,label='Portada',required=False),dict(alt,required=False),text('vacio','Texto si está vacía'),
            field('orden','Orden','number',value_type='int',min=0),
            field('oculta','Ocultar colección','boolean',default=False)]))
    backend = dict(name='github',repo='ByJahr/byjahr',branch='main',auth_endpoint='auth')
    origin = os.getenv('CMS_OAUTH_ORIGIN','').strip().rstrip('/')
    if origin:
        if not re.fullmatch(r'https://[a-z0-9.-]+',origin):
            raise ValueError('CMS_OAUTH_ORIGIN debe ser un origen HTTPS sin ruta.')
        backend['base_url'] = origin
    cms = dict(backend=backend,locale='es',media_folder='public/uploads',public_folder='/uploads',
               display_url='https://byjahr.github.io/byjahr/',slug=dict(encoding='ascii',clean_accents=True),
               collections=[folder('obras','Obras','title',works),folder('criaturas','Criaturas','nombre',beasts),
                            dict(name='colecciones',label='Colecciones',editor={'preview':False},files=files)])
    (out/'admin/config.json').write_text(json.dumps(cms,ensure_ascii=False,indent=2),encoding='utf-8')
