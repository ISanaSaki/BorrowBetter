/** Item card used by the catalog and the dashboard. */

import { html } from '../lib/html.js';
import { categoryIcon } from '../lib/icons.js';
import { formatMoney } from '../lib/format.js';
import { CATEGORY_LABEL, CONDITION_LABEL } from '../constants.js';

function media(item) {
  const glyph = html`<span class="media-fallback"><span class="item-glyph">${categoryIcon(item.category)}</span></span>`;
  if (!item.image_url) return glyph;
  return html`${glyph}<img class="card-image" src="${item.image_url}" alt="" loading="lazy" decoding="async" data-img-fallback>`;
}

export function itemCard(item, { href = `#/items/${item.id}` } = {}) {
  const owner = item.owner?.full_name || '';
  return html`
    <article class="item-card">
      <a class="item-card-link" href="${href}">
        <div class="card-media ${item.image_url ? 'has-image' : ''}" data-tint="${item.category}">
          ${media(item)}
          <span class="badge badge-soft card-condition">${CONDITION_LABEL[item.condition] || ''}</span>
        </div>
        <div class="card-body">
          <span class="card-cat">${CATEGORY_LABEL[item.category] || item.category}</span>
          <h3 class="card-title">${item.title}</h3>
          <p class="card-meta">حداقل ۱ ساعت<span class="sep"></span>تحویل حضوری</p>
          <div class="card-foot">
            <span class="price-line">
              <span class="price">${formatMoney(item.price_per_day)}</span>
              <span class="unit">تومان / روز</span>
            </span>
            ${owner
              ? html`<span class="card-owner">
                  <span class="avatar avatar-xs">${owner.trim().charAt(0)}</span>
                  ${owner}
                </span>`
              : ''}
          </div>
        </div>
      </a>
    </article>
  `;
}
