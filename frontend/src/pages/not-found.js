/** 404 page. */

import { html, htmlToString } from '../lib/html.js';
import { icon } from '../lib/icons.js';

export async function render({ root }) {
  root.innerHTML = htmlToString(html`
    <div class="container not-found">
      <span class="not-found-code">۴۰۴</span>
      <h1>این صفحه پیدا نشد</h1>
      <p class="muted">ممکن است آدرس عوض شده باشد یا وسیله حذف شده باشد.</p>
      <div class="not-found-actions">
        <a class="btn btn-primary" href="#/">${icon('arrow')} بازگشت به خانه</a>
        <a class="btn btn-ghost" href="#/items">دیدن همهٔ وسایل</a>
      </div>
    </div>
  `);
}
