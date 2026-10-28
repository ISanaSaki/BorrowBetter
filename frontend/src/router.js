/**
 * Hash router with auth guards, lazy page chunks, transitions and cancellation.
 */

import { buildHash, parseHash } from './lib/query.js';
import { isLoggedIn } from './store/auth.js';
import { errorState } from './components/states.js';
import { focusHeading, htmlToString, scrollToTop } from './lib/html.js';

const routes = [
  { path: '/', load: () => import('./pages/catalog.js'), title: 'وسایل' },
  { path: '/items', load: () => import('./pages/catalog.js'), title: 'وسایل' },
  { path: '/items/new', load: () => import('./pages/item-form.js'), auth: true, title: 'ثبت وسیله' },
  { path: '/items/:id/edit', load: () => import('./pages/item-form.js'), auth: true, title: 'ویرایش وسیله' },
  { path: '/items/:id', load: () => import('./pages/item.js'), title: 'جزئیات وسیله' },
  { path: '/login', load: () => import('./pages/login.js'), title: 'ورود' },
  { path: '/register', load: () => import('./pages/register.js'), title: 'ثبت‌نام' },
  { path: '/my/items', load: () => import('./pages/my-items.js'), auth: true, title: 'وسایل من' },
  { path: '/my/requests', load: () => import('./pages/my-requests.js'), auth: true, title: 'درخواست‌های من' },
  { path: '/ai', load: () => import('./pages/coming-soon.js'), title: 'دستیار هوشمند' },
  { path: '/404', load: () => import('./pages/not-found.js'), title: 'صفحه پیدا نشد' },
];

let outlet = null;
let current = { cleanup: null, controller: null };
let renderToken = 0;
let progressBar = null;

function matchPath(pattern, path) {
  const patternParts = pattern.split('/').filter(Boolean);
  const pathParts = path.split('/').filter(Boolean);
  if (patternParts.length !== pathParts.length) return null;
  const params = {};
  for (let index = 0; index < patternParts.length; index += 1) {
    const expected = patternParts[index];
    const actual = pathParts[index];
    if (expected.startsWith(':')) {
      params[expected.slice(1)] = decodeURIComponent(actual);
    } else if (expected !== actual) {
      return null;
    }
  }
  return params;
}

function resolve(path) {
  for (const route of routes) {
    const params = matchPath(route.path, path);
    if (params) return { route, params };
  }
  return null;
}

function setProgress(active) {
  if (!progressBar) return;
  progressBar.classList.toggle('is-active', active);
}

function showError(message) {
  const wrapper = document.createElement('div');
  wrapper.className = 'page';
  wrapper.innerHTML = htmlToString(errorState({ message }));
  outlet.replaceChildren(wrapper);
  wrapper.querySelector('[data-retry]')?.addEventListener('click', () => render());
}

export function navigate(path, { replace = false } = {}) {
  const hash = path.startsWith('#') ? path : buildHash(path);
  if (replace) {
    history.replaceState(null, '', hash);
    return;
  }
  if (window.location.hash === hash) render();
  else window.location.hash = hash;
}

export function currentPath() {
  return parseHash().path;
}

export async function render() {
  const { path, query } = parseHash();
  const matched = resolve(path);

  if (!matched) {
    window.location.replace(buildHash('/404', { from: path }));
    return;
  }

  if (matched.route.auth && !isLoggedIn()) {
    window.location.replace(buildHash('/login', { redirect: path }));
    return;
  }

  current.controller?.abort();
  current.cleanup?.();
  current.cleanup = null;
  const controller = new AbortController();
  current.controller = controller;
  const token = ++renderToken;

  setProgress(true);
  document.body.classList.add('is-routing');

  try {
    const module = await matched.route.load();
    if (token !== renderToken) return;

    document.title = `${matched.route.title} · BorrowBetter`;

    const pageRoot = document.createElement('div');
    pageRoot.className = 'page page-enter';
    outlet.replaceChildren(pageRoot);

    const cleanup = await module.render({
      root: pageRoot,
      params: matched.params,
      query,
      path,
      signal: controller.signal,
      navigate,
    });

    if (token !== renderToken) {
      if (typeof cleanup === 'function') cleanup();
      return;
    }
    current.cleanup = typeof cleanup === 'function' ? cleanup : null;
    requestAnimationFrame(() => pageRoot.classList.add('is-in'));

    if (!query.scroll) {
      scrollToTop();
      focusHeading(pageRoot);
    }
  } catch (error) {
    if (error?.name === 'AbortError') return;
    console.error('[router]', error);
    showError(error?.message || 'صفحه بارگذاری نشد. دوباره تلاش کن.');
  } finally {
    if (token === renderToken) {
      setProgress(false);
      document.body.classList.remove('is-routing');
    }
  }
}

export function initRouter({ outlet: outletElement }) {
  outlet = outletElement;
  progressBar = document.createElement('div');
  progressBar.className = 'route-progress';
  progressBar.setAttribute('aria-hidden', 'true');
  document.body.append(progressBar);

  window.addEventListener('hashchange', render);
  window.addEventListener('popstate', render);

  if (!window.location.hash) {
    history.replaceState(null, '', buildHash('/'));
  }
  render();
}
