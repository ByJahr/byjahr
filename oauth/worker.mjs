const COOKIE = '__Host-byjahr-oauth';
const encoder = new TextEncoder();
const random = () => Array.from(crypto.getRandomValues(new Uint8Array(32)),
  byte => byte.toString(16).padStart(2, '0')).join('');
const jsonForScript = value => JSON.stringify(value).replace(/</g, '\\u003c');
const expireCookie = COOKIE + '=; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=0';
const safeHeaders = {
  'Cache-Control': 'no-store',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
};

function reply(siteOrigin, kind, payload) {
  const nonce = random();
  const message = 'authorization:github:' + kind + ':' + JSON.stringify(payload);
  const body = `<!doctype html><html lang="es"><meta charset="utf-8"><title>Acceso a GitHub</title>
    <p>Regresa al administrador para continuar.</p><script nonce="${nonce}">
    const origin = ${jsonForScript(siteOrigin)};
    const openerWindow = window.opener;
    if (openerWindow) {
      window.addEventListener('message', function finish(event) {
        if (event.origin !== origin || event.source !== openerWindow || event.data !== 'authorizing:github') return;
        window.removeEventListener('message', finish);
        openerWindow.postMessage(${jsonForScript(message)}, origin);
      });
      openerWindow.postMessage('authorizing:github', origin);
    }
    </script></html>`;
  return new Response(body, {headers: {
    ...safeHeaders, 'Content-Type': 'text/html; charset=utf-8', 'Set-Cookie': expireCookie,
    'Content-Security-Policy': `default-src 'none'; script-src 'nonce-${nonce}'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`,
  }});
}

async function github(path, token) {
  const response = await fetch('https://api.github.com' + path, {headers:{
    Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json',
    'User-Agent': 'byjahr-cms-oauth',
  }});
  if (!response.ok) throw new Error('GitHub rechazó la comprobación de permisos.');
  return response.json();
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== 'GET' || !['/auth','/callback'].includes(url.pathname)) {
      return new Response('Ruta no disponible.', {status:404,headers:safeHeaders});
    }
    if (!env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET ||
        !env.OAUTH_ORIGIN || url.origin !== env.OAUTH_ORIGIN) {
      return new Response('Acceso sin configurar.', {status:503,headers:safeHeaders});
    }
    const callback = env.OAUTH_ORIGIN + '/callback';
    const deny = message => reply(env.SITE_ORIGIN,'error',{message});
    if (url.pathname === '/auth') {
      if (url.searchParams.get('provider') !== 'github' ||
          url.searchParams.get('site_id') !== new URL(env.SITE_ORIGIN).hostname) {
        return new Response('Origen no permitido.', {status:403,headers:safeHeaders});
      }
      const state = random();
      const verifier = random();
      const digest = new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(verifier)));
      const challenge = btoa(String.fromCharCode(...digest)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
      const params = new URLSearchParams({client_id:env.GITHUB_CLIENT_ID,redirect_uri:callback,
        scope:'public_repo',state,code_challenge:challenge,code_challenge_method:'S256'});
      return new Response(null,{status:302,headers:{...safeHeaders,
        Location:'https://github.com/login/oauth/authorize?' + params,
        'Set-Cookie':`${COOKIE}=${state}.${verifier}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=600`,
      }});
    }
    const cookie = request.headers.get('Cookie')?.split('; ').find(value => value.startsWith(COOKIE + '='));
    const [state,verifier] = (cookie?.slice(COOKIE.length + 1) || '').split('.');
    const code = url.searchParams.get('code');
    if (!code || !/^[a-f0-9]{64}$/.test(state) || !/^[a-f0-9]{64}$/.test(verifier || '') ||
        state !== url.searchParams.get('state')) return deny('La sesión expiró o no pudo verificarse. Intenta iniciar sesión otra vez.');
    try {
      const response = await fetch('https://github.com/login/oauth/access_token',{method:'POST',
        headers:{Accept:'application/json','Content-Type':'application/x-www-form-urlencoded'},
        body:new URLSearchParams({client_id:env.GITHUB_CLIENT_ID,client_secret:env.GITHUB_CLIENT_SECRET,
          redirect_uri:callback,code,code_verifier:verifier}),
      });
      const data = await response.json();
      if (!response.ok || !data.access_token) return deny('GitHub no autorizó el inicio de sesión.');
      const user = await github('/user',data.access_token);
      const allowed = env.ALLOWED_LOGINS.toLowerCase().split(',').map(login => login.trim());
      if (!allowed.includes(user.login.toLowerCase())) return deny('Esta cuenta no está autorizada.');
      const repo = await github('/repos/ByJahr/byjahr',data.access_token);
      if (!repo.permissions?.push) return deny('La cuenta no tiene permiso de escritura en el repositorio.');
      return reply(env.SITE_ORIGIN,'success',{token:data.access_token,provider:'github'});
    } catch {
      return deny('No se pudo completar la autenticación con GitHub.');
    }
  },
};
