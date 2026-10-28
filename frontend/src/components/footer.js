/** Site footer: links, socials and a call to action. */

import { html } from '../lib/html.js';
import { icon } from '../lib/icons.js';

export function footerTemplate() {
  return html`
    <footer class="site-footer">
      <div class="container footer-grid">
        <div class="footer-brand">
          <a class="brand brand-light" href="#/">
            <span class="brand-mark">${icon('leaf')}</span>
            <span class="brand-text">
              <strong>BorrowBetter</strong>
              <small>امانت بین همسایه‌ها</small>
            </span>
          </a>
          <p>وسایل کم‌استفاده را با همسایه‌ها به اشتراک بگذار؛ کمتر بخر، بیشتر استفاده کن.</p>
          <div class="socials" aria-label="شبکه‌های اجتماعی">
            <a href="#/" aria-label="اینستاگرام">${icon('camera')}</a>
            <a href="#/" aria-label="لینکدین">${icon('user')}</a>
            <a href="#/" aria-label="تلگرام">${icon('speaker')}</a>
          </div>
        </div>

        <nav class="footer-col" aria-label="کاوش">
          <h2>کاوش</h2>
          <a href="#/items">وسایل</a>
          <a href="#/">خانه</a>
          <a href="#/items?sort=newest">تازه‌ترین‌ها</a>
        </nav>

        <nav class="footer-col" aria-label="حساب">
          <h2>حساب</h2>
          <a href="#/login">ورود</a>
          <a href="#/register">ثبت‌نام</a>
          <a href="#/items/new">ثبت وسیله</a>
        </nav>

        <div class="footer-cta">
          <h2>وسیله‌ای داری که بلااستفاده است؟</h2>
          <p>در چند دقیقه ثبتش کن و اجازه بده همسایه‌ها از آن استفاده کنند.</p>
          <a class="btn btn-light btn-sm" href="#/items/new">${icon('plus')} ثبت وسیله</a>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="container footer-bottom-inner">
          <span>© ۱۴۰۵ BorrowBetter — ساخته‌شده برای جامعهٔ محلی.</span>
          <span class="footer-note">دادهٔ نمایشی · طراحی راست‌چین</span>
        </div>
      </div>
    </footer>
  `;
}
