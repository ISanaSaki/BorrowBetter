/** Shared list states: skeletons, empty and error blocks. */

import { html, raw } from '../lib/html.js';
import { icon } from '../lib/icons.js';

export function skeletonGrid(count = 6) {
  return raw(
    Array.from({ length: count })
      .map(
        () => `
        <div class="item-card skeleton" aria-hidden="true">
          <div class="sk-media"></div>
          <div class="sk-body">
            <span class="sk-line w30"></span>
            <span class="sk-line"></span>
            <span class="sk-line w60"></span>
            <span class="sk-line w40"></span>
          </div>
        </div>`,
      )
      .join(''),
  );
}

export function skeletonRows(count = 3) {
  return raw(
    Array.from({ length: count })
      .map(
        () => `
        <div class="skeleton-row" aria-hidden="true">
          <span class="sk-thumb"></span>
          <div class="sk-lines">
            <span class="sk-line w60"></span>
            <span class="sk-line w40"></span>
            <span class="sk-line w30"></span>
          </div>
        </div>`,
      )
      .join(''),
  );
}

export function emptyState({ title, text = '', action = null, iconName = 'empty' }) {
  return html`
    <div class="state-card">
      <span class="state-icon">${icon(iconName)}</span>
      <h2>${title}</h2>
      ${text ? html`<p>${text}</p>` : ''}
      ${action ? html`<div class="state-action">${action}</div>` : ''}
    </div>
  `;
}

export function errorState({ message, retryLabel = 'تلاش دوباره' }) {
  return html`
    <div class="state-card state-card-error" role="alert">
      <span class="state-icon state-icon-error">${icon('warning')}</span>
      <h2>مشکلی پیش آمد</h2>
      <p>${message}</p>
      <div class="state-action">
        <button type="button" class="btn btn-primary" data-retry>${retryLabel}</button>
      </div>
    </div>
  `;
}

export function inlineError(message) {
  return html`
    <div class="inline-alert" role="alert">${icon('warning')}<span>${message}</span></div>
  `;
}
