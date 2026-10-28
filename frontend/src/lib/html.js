/**
 * Tiny HTML templating helpers.
 * Every interpolated value is escaped unless it is wrapped with `raw()`.
 */

const ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ESCAPE_MAP[char]);
}

class SafeHtml {
  constructor(value) {
    this.value = String(value);
  }
  toString() {
    return this.value;
  }
}

/** Mark a string as trusted markup. Only use with markup you built yourself. */
export function raw(value) {
  return new SafeHtml(value);
}

function interpolate(value) {
  if (value === null || value === undefined || value === false) return '';
  if (value instanceof SafeHtml) return value.value;
  if (Array.isArray(value)) return value.map(interpolate).join('');
  return escapeHtml(value);
}

/** Tagged template: html`<p>${userInput}</p>` escapes userInput automatically. */
export function html(strings, ...values) {
  let out = strings[0];
  for (let i = 0; i < values.length; i += 1) {
    out += interpolate(values[i]) + strings[i + 1];
  }
  return new SafeHtml(out);
}

export function htmlToString(template) {
  return template instanceof SafeHtml ? template.value : String(template);
}

export function htmlToElement(template) {
  const node = document.createElement('template');
  node.innerHTML = htmlToString(template).trim();
  return node.content.firstElementChild;
}

export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

/** Delegated listener that survives partial re-renders. */
export function delegate(root, type, selector, handler) {
  const listener = (event) => {
    const target = event.target instanceof Element ? event.target.closest(selector) : null;
    if (target && root.contains(target)) handler(event, target);
  };
  root.addEventListener(type, listener);
  return () => root.removeEventListener(type, listener);
}

export function focusHeading(root) {
  const heading = root.querySelector('h1');
  if (!heading) return;
  heading.setAttribute('tabindex', '-1');
  heading.focus({ preventScroll: true });
}

export function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
}
