/** Placeholder for the AI assistant, which is out of scope for this release (D9). */

import { html, htmlToString } from '../lib/html.js';
import { icon } from '../lib/icons.js';

export async function render({ root }) {
  root.innerHTML = htmlToString(html`
    <div class="container coming-soon">
      <div class="state-card coming-soon-card">
        <span class="state-icon">${icon('spark')}</span>
        <span class="badge badge-soft">به‌زودی</span>
        <h1>دستیار هوشمند BorrowBetter</h1>
        <p>
          جست‌وجوی معنایی («چیزی برای کمپینگ») با TF-IDF محلی در نسخهٔ بعدی اضافه می‌شود.
          قرارداد API آن از قبل در سند تیم مشخص شده است، اما عمداً از نسخهٔ اول بیرون مانده.
        </p>
        <div class="state-action">
          <a class="btn btn-primary" href="#/items">دیدن وسایل</a>
        </div>
      </div>
    </div>
  `);
}
