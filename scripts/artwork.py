"""Validate raster art and export web copies without EXIF."""
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageCms, ImageOps

FORMATS = {'.jpg':'JPEG', '.jpeg':'JPEG', '.png':'PNG', '.webp':'WEBP', '.avif':'AVIF'}
MAX_INPUT = 8 * 1024 * 1024
MAX_OUTPUT = 2 * 1024 * 1024

def read_art(path, *, original=False):
    path = Path(path)
    expected = FORMATS.get(path.suffix.lower())
    if not expected:
        raise ValueError('extensión no permitida (JPEG, PNG, WebP o AVIF)')
    if not original and path.stat().st_size > MAX_INPUT:
        raise ValueError('imagen de más de 8 MiB: exporta una copia para la web')
    with Image.open(path) as source:
        if source.format != expected or getattr(source,'n_frames',1) != 1:
            raise ValueError('el archivo debe ser una imagen estática del formato indicado')
        if not original and source.width * source.height > 36_000_000:
            raise ValueError('la imagen supera 36 megapíxeles')
        source.load()
        image = ImageOps.exif_transpose(source)
        alpha = image.convert('RGBA').getchannel('A') if 'A' in image.getbands() or 'transparency' in image.info else None
        profile = image.info.get('icc_profile')
        if profile:
            image = ImageCms.profileToProfile(image.convert('RGB') if alpha else image,
                       ImageCms.ImageCmsProfile(BytesIO(profile)),ImageCms.createProfile('sRGB'),outputMode='RGB')
        else:
            image = image.convert('RGB')
        if alpha and alpha.getextrema()[0] < 255:
            image.putalpha(alpha)
        return image

def export_art(image, folder, stem):
    folder.mkdir(parents=True,exist_ok=True)
    image.thumbnail((2400, 4800), Image.Resampling.LANCZOS)
    width = image.width
    variants = []
    for size in sorted({min(480,width),min(960,width),min(1600,width),width}):
        copy = image.copy()
        copy.thumbnail((size,image.height),Image.Resampling.LANCZOS)
        name = f'{stem}.webp' if size == width else f'{stem}-{copy.width}w.webp'
        target = folder/name
        copy.save(target,'WEBP',quality=90,method=6,exact=True)
        if target.stat().st_size > MAX_OUTPUT:
            raise ValueError(f'{name}: la copia supera 2 MiB; prepara una exportación más ligera')
        variants.append((name,copy.width,copy.height))
    return variants
