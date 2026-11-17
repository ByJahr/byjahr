const form = document.querySelector('[data-filters]');
if (form) {
  const cards = [...document.querySelectorAll('[data-entry]')];
  const update = () => {
    const data = new FormData(form);
    let count = 0;
    for (const card of cards) {
      card.hidden = [...data].some(([key, value]) => value && card.dataset[key] !== value);
      count += Number(!card.hidden);
    }
    document.querySelector('[data-count]').textContent = count + (count === 1 ? ' resultado' : ' resultados');
    document.querySelector('[data-no-results]').hidden = count > 0;
  };
  form.hidden = false;
  form.addEventListener('change', update);
  update();
}
const share = document.querySelector('[data-share]');
if (share) {
  share.hidden = false;
  share.addEventListener('click', async () => {
    const url = document.querySelector('link[rel=canonical]')?.href || location.href;
    try {
      await navigator.clipboard.writeText(url);
      document.querySelector('[data-share-status]').textContent = 'Enlace copiado.';
    } catch {
      const field = document.querySelector('[data-share-url]');
      field.hidden = false;
      field.value = url;
      field.select();
      document.querySelector('[data-share-status]').textContent = 'Copia el enlace seleccionado.';
    }
  });
}

const plateViewer = document.querySelector('.bestiary-viewer');
if (plateViewer && typeof plateViewer.showModal === 'function') {
  const title = plateViewer.querySelector('h2');
  const image = plateViewer.querySelector('img');
  const zoom = plateViewer.querySelector('[data-plate-zoom]');
  const viewport = plateViewer.querySelector('.bestiary-viewer-body');
  let opener;

  document.querySelectorAll('[data-plate]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      opener = link;
      title.textContent = link.dataset.plate;
      image.alt = (link.querySelector('img') || link.closest('figure')?.querySelector('img'))?.alt || title.textContent;
      image.src = link.href;
      plateViewer.showModal();
    });
  });

  zoom.addEventListener('click', () => {
    const enlarged = plateViewer.toggleAttribute('data-zoomed');
    zoom.setAttribute('aria-pressed', String(enlarged));
    zoom.textContent = enlarged ? 'Ajustar' : 'Ampliar';
    viewport.scrollTo(0, 0);
  });

  plateViewer.addEventListener('close', () => {
    plateViewer.removeAttribute('data-zoomed');
    zoom.setAttribute('aria-pressed', 'false');
    zoom.textContent = 'Ampliar';
    image.removeAttribute('src');
    opener?.focus();
  });
}
