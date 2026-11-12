"""Import approved files from img/ without changing the originals."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from PIL import Image

from artwork import FORMATS, MAX_INPUT, read_art

ROOT = Path(__file__).resolve().parents[1]

def classify(stem):
    beast = re.fullmatch(r'b_(\d+)', stem, re.IGNORECASE)
    if beast:
        number = int(beast[1])
        return 'criaturas', 'bestiario', f'b-{number}', f'Criatura {number}', number
    if re.fullmatch(r'\d+', stem):
        number = int(stem)
        return 'obras', 'inktober-2026', f'inktober-{number}', f'Inktober · {number:02}', number
    slug = unicodedata.normalize('NFKD', stem).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    if not slug:
        raise ValueError(f'No se puede obtener un identificador de {stem!r}.')
    return 'obras', 'caoz-con-todo', slug, stem.replace('_', ' '), 0

def import_images():
    folder = ROOT / 'img'
    if not folder.is_dir():
        return
    candidates = {}
    for source in sorted(folder.iterdir()):
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in FORMATS:
            continue
        group, collection, slug, title, order = classify(source.stem)
        key = (group, slug)
        if key in candidates:
            raise ValueError(f'Dos imágenes para {slug}: {candidates[key][0].name} y {source.name}.')
        candidates[key] = (source, collection, title, order)
    imported = 0
    for (group, slug), (source, collection, title, order) in candidates.items():
        entry = ROOT / 'src/content' / group / f'{slug}.json'
        relative = Path('images/artworks') / collection / f'{slug}.webp'
        target = ROOT / 'public' / relative
        digest = sha256(source)
        if entry.exists():
            data = json.loads(entry.read_text(encoding='utf-8'))
            if data.get('sourceFile') != source.name:
                raise ValueError(f'{source.name} coincide con una ficha existente: {entry.name}.')
            if data.get('sourceDigest') == digest and target.is_file():
                continue
        elif group == 'criaturas':
            data = dict(slug=slug,nombre=title,imagen=relative.as_posix(),alt=f'Ilustración del Bestiario, lámina {order}.',
                        descripcion='Ilustración del Bestiario.',orden=order)
        else:
            named = collection == 'caoz-con-todo'
            data = dict(slug=slug,title=title,image=relative.as_posix(),alt=(
                        f'Ilustración de {title}, de Caoz con Todo.' if named else f'Ilustración {order} de Inktober 2026.'),
                        collection=collection,category='personaje' if named else 'inktober',
                        description='Ilustración de Caoz con Todo.' if named else 'Ilustración de Inktober 2026.',
                        published=True,order=order)
            if named:
                data['character'] = title
            else:
                data['year'] = 2026
        image = read_art(source, original=True)
        image.thumbnail((2400,4800), Image.Resampling.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp')
        try:
            image.save(temporary, 'WEBP', quality=94, method=4, exact=True)
            if temporary.stat().st_size > MAX_INPUT:
                raise ValueError(f'La copia web de {source.name} supera el tamaño permitido.')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        data.update(sourceFile=source.name,sourceDigest=digest)
        entry.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        imported += 1
    print(f'Imágenes importadas o actualizadas: {imported}.')

def sha256(source):
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

if __name__ == '__main__':
    try:
        import_images()
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
