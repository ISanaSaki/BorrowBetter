/** Toast notifications (single stack, max three, auto-dismiss). */

import { icon } from '../lib/icons.js';
import { html, htmlToElement } from '../lib/html.js';

let root = null;
const MAX_TOASTS = 3;

export function initToast(rootElement) {
  root = rootElement;
}

export function showToast(message, { type = 'success', duration = 3200 } = {}) {
  if (!root) return;
  const iconName = type === 'error' ? 'warning' : type === 'info' ? 'info' : 'check';
  const element = htmlToElement(html`
    <div class="toast toast-${type}" role="status">
      ${icon(iconName)}
      <span>${message}</span>
    </div>
  `);
  root.append(element);

  while (root.children.length > MAX_TOASTS) root.firstElementChild?.remove();

  requestAnimationFrame(() => element.classList.add('is-on'));

  const remove = () => {
    element.classList.remove('is-on');
    setTimeout(() => element.remove(), 220);
  };
  const timer = setTimeout(remove, duration);
  element.addEventListener('click', () => {
    clearTimeout(timer);
    remove();
  });
}
