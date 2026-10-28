/** Application bootstrap: shell, header/footer, toast and router. */

import './styles/index.css';

import { createHeader } from './components/header.js';
import { footerTemplate } from './components/footer.js';
import { initToast, showToast } from './components/toast.js';
import { initRouter } from './router.js';
import { ensureUser, logout } from './store/auth.js';
import { htmlToElement } from './lib/html.js';

const app = document.querySelector('#app');

const header = createHeader();
app.append(header.element);

const main = document.createElement('main');
main.id = 'main';
main.className = 'site-main';

const view = document.createElement('div');
view.id = 'view';
view.className = 'view';
main.append(view);
app.append(main);
app.append(htmlToElement(footerTemplate()));

initToast(document.querySelector('#toast-root'));

// If a photo is missing, drop the <img> so the illustrated fallback shows instead.
document.addEventListener(
  'error',
  (event) => {
    const target = event.target;
    if (target instanceof HTMLImageElement && target.hasAttribute('data-img-fallback')) {
      target.remove();
    }
  },
  true,
);

window.addEventListener('bb:auth', () => header.update());
window.addEventListener('hashchange', () => header.update());

window.addEventListener('bb:unauthorized', () => {
  logout();
  showToast('نشست شما منقضی شد؛ دوباره وارد شو.', { type: 'error' });
  if (!window.location.hash.startsWith('#/login')) {
    const redirect = window.location.hash.replace(/^#/, '') || '/';
    window.location.hash = `#/login?redirect=${encodeURIComponent(redirect)}`;
  }
});

// Resolve the current user before the first render so ownership checks are accurate.
ensureUser()
  .catch(() => null)
  .finally(() => {
    header.update();
    initRouter({ outlet: view });
  });

// Exposed for the demo console (mock mode only).
window.__bb = { resetMock: () => window.__bbResetMock?.() };
