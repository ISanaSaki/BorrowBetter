/** Login page with the demo accounts helper (mock mode only). */

import { html, htmlToString } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { isLoggedIn, login } from '../store/auth.js';
import { isMockEnabled } from '../api/client.js';
import { showToast } from '../components/toast.js';

const DEMO_ACCOUNTS = [
  { email: 'asra@demo.ir', name: 'اسرا', role: 'متقاضی' },
  { email: 'sana@demo.ir', name: 'ثنا', role: 'صاحب وسیله' },
  { email: 'shaghayegh@demo.ir', name: 'شقایق', role: 'صاحب وسیله' },
];

export async function render({ root, query, navigate }) {
  const redirect = sanitizeRedirect(query.redirect);
  if (isLoggedIn()) {
    navigate(redirect);
    return;
  }

  root.innerHTML = htmlToString(page(redirect));

  const form = root.querySelector('[data-form]');
  const submit = root.querySelector('[data-submit]');
  const errorBox = root.querySelector('[data-error]');
  const emailInput = form.querySelector('[name="email"]');
  const passwordInput = form.querySelector('[name="password"]');

  root.querySelectorAll('[data-demo]').forEach((button) => {
    button.addEventListener('click', () => {
      emailInput.value = button.dataset.demo;
      passwordInput.value = 'Demo1234!';
      passwordInput.focus();
    });
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.innerHTML = '';
    form.classList.remove('is-shaking');

    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value;

    if (!email || !password) {
      errorBox.innerHTML = htmlToString(html`<div class="inline-alert" role="alert">${icon('warning')}<span>ایمیل و رمز عبور را وارد کن.</span></div>`);
      return;
    }

    submit.disabled = true;
    submit.classList.add('is-loading');
    try {
      const user = await login(email, password);
      showToast(`خوش آمدی ${user.full_name.split(' ')[0]}!`);
      navigate(redirect);
    } catch (error) {
      if (error?.name === 'AbortError') return;
      const message = error.status === 401 ? 'ایمیل یا رمز عبور اشتباه است.' : error.message;
      errorBox.innerHTML = htmlToString(html`<div class="inline-alert" role="alert">${icon('warning')}<span>${message}</span></div>`);
      form.classList.add('is-shaking');
    } finally {
      submit.disabled = false;
      submit.classList.remove('is-loading');
    }
  });
}

function sanitizeRedirect(value) {
  if (!value || typeof value !== 'string') return '/';
  if (!value.startsWith('/') || value.startsWith('//')) return '/';
  return value;
}

function page(redirect) {
  const mock = isMockEnabled();
  const registerHref = `#/register${redirect !== '/' ? `?redirect=${encodeURIComponent(redirect)}` : ''}`;

  return html`
    <div class="auth-page">
      <div class="container auth-layout">
        <div class="auth-card">
          <span class="pill">${icon('user')} حساب کاربری</span>
          <h1>ورود به BorrowBetter</h1>
          <p class="muted">برای ثبت درخواست یا گذاشتن وسیله، وارد حساب خودت شو.</p>

          <div data-error></div>

          <form data-form novalidate>
            <label class="field">
              <span>ایمیل</span>
              <input name="email" type="email" autocomplete="username" placeholder="name@example.com" required>
            </label>
            <label class="field">
              <span>رمز عبور</span>
              <input name="password" type="password" autocomplete="current-password" placeholder="••••••••" required>
            </label>
            <div class="field-row">
              <label class="check"><input type="checkbox" checked> مرا به خاطر بسپار</label>
              <span class="muted small">در این تب فعال می‌مانی</span>
            </div>
            <button type="submit" class="btn btn-primary btn-block" data-submit>ورود</button>
          </form>

          <p class="auth-foot muted">حساب نداری؟ <a class="link" href="${registerHref}">ثبت‌نام کن</a></p>

          ${mock
            ? html`
                <div class="demo-box">
                  <p class="demo-box-title">${icon('info')} حساب‌های نمونه (فقط در حالت نمایشی)</p>
                  <div class="demo-accounts">
                    ${DEMO_ACCOUNTS.map(
                      (account) => html`
                        <button type="button" class="demo-account" data-demo="${account.email}">
                          <span class="avatar avatar-sm">${account.name.charAt(0)}</span>
                          <span>
                            <strong>${account.name}</strong>
                            <small>${account.role}</small>
                          </span>
                        </button>
                      `,
                    )}
                  </div>
                  <p class="demo-hint">رمز همه: <code>Demo1234!</code></p>
                </div>
              `
            : ''}
        </div>

        <aside class="auth-aside">
          <div class="auth-aside-card">
            <span class="auth-aside-icon">${icon('shield')}</span>
            <h2>امانت امن، بین همسایه‌ها</h2>
            <p>هر درخواست باید توسط صاحب وسیله تأیید شود و تحویل و بازگشت ثبت می‌شود.</p>
            <ul class="auth-points">
              <li>${icon('check')} بازهٔ زمانی دقیق، بدون تداخل</li>
              <li>${icon('check')} تأیید صاحب وسیله قبل از تحویل</li>
              <li>${icon('check')} پیام روشن اگر بازه پر شده باشد</li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  `;
}
