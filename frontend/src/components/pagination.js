/** RTL-friendly pagination. */

import { html } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { clamp } from '../lib/query.js';

export function pagination({ page, totalPages, total }) {
  if (totalPages <= 1) return html`<nav class="pagination" hidden></nav>`;

  const current = clamp(page, 1, totalPages);
  const windowSize = 5;
  let start = Math.max(1, current - Math.floor(windowSize / 2));
  const end = Math.min(totalPages, start + windowSize - 1);
  if (end - start + 1 < windowSize) start = Math.max(1, end - windowSize + 1);

  const pages = [];
  for (let index = start; index <= end; index += 1) pages.push(index);

  return html`
    <nav class="pagination" aria-label="صفحه‌بندی">
      <button type="button" class="pager-btn" data-page="${current - 1}" ${current === 1 ? 'disabled' : ''} aria-label="صفحهٔ قبل">
        ${icon('chevronRight')}
      </button>
      ${start > 1
        ? html`<button type="button" class="pager-btn" data-page="1">۱</button><span class="pager-gap">…</span>`
        : ''}
      ${pages.map(
        (number) => html`
          <button
            type="button"
            class="pager-btn ${number === current ? 'is-current' : ''}"
            data-page="${number}"
            ${number === current ? 'aria-current="page"' : ''}
          >${number.toLocaleString('fa-IR')}</button>
        `,
      )}
      ${end < totalPages
        ? html`<span class="pager-gap">…</span><button type="button" class="pager-btn" data-page="${totalPages}">${totalPages.toLocaleString('fa-IR')}</button>`
        : ''}
      <button type="button" class="pager-btn" data-page="${current + 1}" ${current === totalPages ? 'disabled' : ''} aria-label="صفحهٔ بعد">
        ${icon('chevronLeft')}
      </button>
      ${typeof total === 'number'
        ? html`<span class="pager-total">${total.toLocaleString('fa-IR')} مورد</span>`
        : ''}
    </nav>
  `;
}
