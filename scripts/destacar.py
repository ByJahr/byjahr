"""Selecciona qué obra publicada aparece en la portada."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'src/config.json'
CONTENT = ROOT / 'src/content'

def choices():
    collections = {}
    for path in (CONTENT / 'colecciones').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        if not data.get('oculta'):
            collections[data['slug']] = data['titulo']

    works = []
    for path in (CONTENT / 'obras').glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        collection = data.get('collection') or data.get('coleccion')
        if (collection not in collections or data.get('draft') or data.get('published') is False
                or data.get('estado_publicacion', 'publicada') != 'publicada'):
            continue
        slug = data.get('slug') or path.stem
        title = data.get('title') or data['titulo']
        works.append((collections[collection], data.get('order', data.get('orden', 0)), title, slug))
    return sorted(works, key=lambda work: (work[0], work[1], work[2].casefold()))

def main():
    works = choices()
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    current = config.get('obra_destacada')
    print('Obra destacada de la portada\n')
    print(' 0. Quitar la obra destacada')
    for index, (collection, _, title, slug) in enumerate(works, 1):
        marker = ' (actual)' if slug == current else ''
        print(f'{index:2}. {title} — {collection}{marker}')
    while True:
        answer = input('\nNúmero de la obra (Enter para cancelar): ').strip()
        if not answer:
            return
        if answer.isascii() and answer.isdecimal() and len(answer) <= 6:
            index = int(answer)
            if 0 <= index <= len(works):
                break
        print(f'Escribe un número entre 0 y {len(works)}.')
    config['obra_destacada'] = works[index - 1][3] if index else ''
    CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Destacada: {works[index - 1][2]}' if index else 'Portada sin obra destacada.')

if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print('\nSelección cancelada.')
