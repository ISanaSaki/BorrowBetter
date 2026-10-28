/** Sticky application header with auth-aware navigation. */

import { html, htmlToElement } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { NAV } from '../constants.js';
import { getUser, isLoggedIn, subscribe, logout } from '../store/auth.js';
import { isMockEnabled } from '../api/client.js';
import { showToast } from './toast.js';
import { parseHash } from '../lib/query.js';

export function createHeader() {
  const element = htmlToElement(html`<header class="site-header"></header>`);
  let unsubscribe = null;

  function template() {
    const loggedIn = isLoggedIn();
    const user = getUser();
    const mock = isMockEnabled();
    const { path } = parseHash();

    return html`
      <div class="container header-inner">
        <a class="brand" href="#/" aria-label="BorrowBetter، خانه">
          <span class="brand-mark">${icon('leaf')}</span>
          <span class="brand-text">
            <strong>BorrowBetter</strong>
            <small>امانت بین همسایه‌ها</small>
          </span>
        </a>

        <nav class="main-nav" aria-label="ناوبری اصلی">
          ${NAV.filter((item) => !item.auth || loggedIn).map(
            (item) => html`
              <a href="${item.href}" class="${isActive(item, path) ? 'is-active' : ''}">${item.label}</a>
            `,
          )}
        </nav>

        <div class="header-tools">
          ${mock ? html`<span class="mock-pill" title="داده‌ها نمونه‌اند و به سرور وصل نیستی">حالت نمونه</span>` : ''}
          ${user
            ? html`
                <div class="user-menu" data-user-menu>
                  <button type="button" class="user-menu-trigger" aria-haspopup="menu" aria-expanded="false">
                    <span class="avatar avatar-sm">${(user.full_name || '؟').trim().charAt(0)}</span>
                    <span class="user-menu-name">${(user.full_name || '').split(' ')[0]}</span>
                    ${icon('chevron')}
                  </button>
                  <div class="user-menu-panel" role="menu">
                    <div class="user-menu-head">
                      <strong>${user.full_name}</strong>
                      <span>${user.email}</span>
                    </div>
                    <a role="menuitem" href="#/my/items">${icon('toolbox')} وسایل من</a>
                    <a role="menuitem" href="#/my/requests">${icon('calendar')} درخواست‌های من</a>
                    <button type="button" role="menuitem" data-action="logout">${icon('logout')} خروج از حساب</button>
                  </div>
                </div>
              `
            : html`<a class="btn btn-ghost btn-sm" href="#/login">ورود</a>`}
          <a class="btn btn-primary btn-sm header-cta" href="#/items/new">
            ${icon('plus')}
            <span>ثبت وسیله</span>
          </a>
        </div>
      </div>
    `;
  }

  function isActive(item, path) {
    if (item.match === '/') return path === '/';
    return path === item.match || path.startsWith(`${item.match}/`);
  }

  function bind() {
    const menu = element.querySelector('[data-user-menu]');
    const trigger = menu?.querySelector('.user-menu-trigger');

    trigger?.addEventListener('click', (event) => {
      event.stopPropagation();
      const open = menu.classList.toggle('is-open');
      trigger.setAttribute('aria-expanded', String(open));
    });

    element.querySelector('[data-action="logout"]')?.addEventListener('click', () => {
      logout();
      showToast('از حساب خارج شدی', { type: 'info' });
      if (window.location.hash.startsWith('#/my')) window.location.hash = '#/';
    });
  }

  function render() {
    element.innerHTML = template().toString();
    bind();
  }

  function closeMenus(event) {
    if (!event.target.closest?.('[data-user-menu]')) {
      element.querySelector('[data-user-menu]')?.classList.remove('is-open');
      element.querySelector('.user-menu-trigger')?.setAttribute('aria-expanded', 'false');
    }
  }

  render();
  unsubscribe = subscribe(render);
  document.addEventListener('click', closeMenus);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenus({ target: document.body });
  });

  return {
    element,
    update: render,
    destroy() {
      unsubscribe?.();
      document.removeEventListener('click', closeMenus);
    },
  };
}
