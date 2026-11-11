(async () => {
  const status = document.getElementById('status');
  try {
    const response = await fetch('config.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('No se pudo cargar la configuración.');
    const config = await response.json();
    const local = ['localhost', '127.0.0.1'].includes(location.hostname);
    if (!local && !config.backend.base_url) {
      status.textContent = 'El acceso con GitHub todavía no está configurado.';
      return;
    }
    if (!window.CMS) throw new Error('No se pudo cargar Decap CMS.');
    if (local) config.local_backend = { url: 'http://localhost:8081/api/v1' };
    CMS.registerEventListener({
      name: 'preSave',
      handler: ({ entry }) => {
        const data = entry.get('data');
        const photo = data.get('image') || data.get('imagen');
        if (photo && !(data.get('alt') || '').trim()) {
          throw new Error('Añade un texto alternativo a la imagen.');
        }
        if (photo && !/\.(webp|png|jpe?g|avif)$/i.test(photo)) {
          throw new Error('Usa una imagen WebP, PNG, JPEG o AVIF.');
        }
        const existing = entry.get('slug');
        if (existing && data.get('slug') && existing !== data.get('slug') && entry.get('isModification')) {
          throw new Error('Conserva el identificador de las fichas existentes para preservar sus URL.');
        }
      }
    });
    document.getElementById('setup').remove();
    CMS.init({ config });
  } catch (error) {
    status.textContent = error.message;
  }
})();
