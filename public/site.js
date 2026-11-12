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
