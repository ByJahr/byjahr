const form = document.querySelector('[data-filters]');
if (form) {
  const cards = [...document.querySelectorAll('[data-entry]')];
  const normalize = s => s.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
  const update = () => {
    const data = new FormData(form);
    const query = normalize(String(data.get('q')).trim());
    let count = 0;
    for (const card of cards) {
      card.hidden = !normalize(card.textContent + ' ' + card.dataset.search).includes(query)
        || [...data].some(([key, val]) => key !== 'q' && val && card.dataset[key] !== val);
      count += Number(!card.hidden);
    }
    document.querySelector('[data-count]').textContent = count + (count === 1 ? ' resultado' : ' resultados');
    document.querySelector('[data-no-results]').hidden = count > 0;
  };
  form.hidden = false;
  form.addEventListener('input', update);
  form.addEventListener('reset', () => setTimeout(update));
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
