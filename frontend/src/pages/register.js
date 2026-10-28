/** Register page. */

import { html, htmlToString } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { isLoggedIn, register } from '../store/auth.js';
import { validateEmail, validateFullName, validatePassword, validatePhone } from '../lib/validate.js';
import { showToast } from '../components/toast.js';

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

  function showErrors(errors) {
    root.querySelectorAll('[data-error-for]').forEach((hint) => {
      hint.textContent = '';
    });
    Object.entries(errors).forEach(([field, message]) => {
      const hint = root.querySelector(`[data-error-for="${field}"]`);
      if (hint) hint.textContent = message;
      root.querySelector(`[name="${field}"]`)?.classList.add('is-invalid');
    });
    const first = Object.keys(errors)[0];
    root.querySelector(`[name="${first}"]`)?.focus();
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorBox.innerHTML = '';
    root.querySelectorAll('[data-error-for]').forEach((hint) => {
      hint.textContent = '';
    });

    const data = new FormData(form);
    const payload = {
      full_name: String(data.get('full_name') || '').trim(),
      email: String(data.get('email') || '').trim().toLowerCase(),
      phone: String(data.get('phone') || '').trim() || null,
      password: String(data.get('password') || ''),
    };
    const confirmPassword = String(data.get('confirm_password') || '');

    const errors = {};
    const nameError = validateFullName(payload.full_name);
    const emailError = validateEmail(payload.email);
    const passwordError = validatePassword(payload.password);
    const phoneError = validatePhone(payload.phone || '');

    if (nameError) errors.full_name = nameError;
    if (emailError) errors.email = emailError;
    if (passwordError) errors.password = passwordError;
    if (phoneError) errors.phone = phoneError;
    if (payload.password !== confirmPassword) errors.confirm_password = 'رمز عبور و تکرار آن یکسان نیست.';

    if (Object.keys(errors).length) {
      showErrors(errors);
      return;
    }

    submit.disabled = true;
    submit.classList.add('is-loading');
    try {
      const user = await register(payload);
      showToast(`حسابت ساخته شد، ${user.full_name.split(' ')[0]}!`);
      navigate(redirect);
    } catch (error) {
      if (error?.name === 'AbortError') return;
      if (error.details?.fields) showErrors(error.details.fields);
      errorBox.innerHTML = htmlToString(html`<div class="inline-alert" role="alert">${icon('warning')}<span>${error.message}</span></div>`);
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
  const loginHref = `#/login${redirect !== '/' ? `?redirect=${encodeURIComponent(redirect)}` : ''}`;
  return html`
    <div class="auth-page">
      <div class="container auth-layout auth-layout-single">
        <div class="auth-card">
          <span class="pill">${icon('user')} عضویت</span>
          <h1>ساخت حساب در BorrowBetter</h1>
          <p class="muted">با یک حساب می‌توانی هم وسیله قرض بگیری و هم وسیله‌ات را امانت بدهی.</p>

          <div data-error></div>

          <form data-form novalidate>
            <label class="field">
              <span>نام و نام خانوادگی</span>
              <input name="full_name" type="text" autocomplete="name" maxlength="80" placeholder="مثلاً اسرا محمدی" required>
              <small class="field-error" data-error-for="full_name"></small>
            </label>

            <label class="field">
              <span>ایمیل</span>
              <input name="email" type="email" autocomplete="email" placeholder="name@example.com" required>
              <small class="field-error" data-error-for="email"></small>
            </label>

            <label class="field">
              <span>شمارهٔ موبایل (اختیاری)</span>
              <input name="phone" type="tel" inputmode="numeric" autocomplete="tel" maxlength="11" placeholder="۰۹۱۲…">
              <small class="field-error" data-error-for="phone"></small>
            </label>

            <div class="form-row">
              <label class="field">
                <span>رمز عبور</span>
                <input name="password" type="password" autocomplete="new-password" placeholder="حداقل ۸ کاراکتر" required>
                <small class="field-error" data-error-for="password"></small>
              </label>
              <label class="field">
                <span>تکرار رمز عبور</span>
                <input name="confirm_password" type="password" autocomplete="new-password" placeholder="دوباره بنویس" required>
                <small class="field-error" data-error-for="confirm_password"></small>
              </label>
            </div>

            <p class="field-hint">رمز باید حداقل ۸ کاراکتر و شامل حرف و رقم باشد.</p>

            <button type="submit" class="btn btn-primary btn-block" data-submit>ساخت حساب</button>
          </form>

          <p class="auth-foot muted">حساب داری؟ <a class="link" href="${loginHref}">وارد شو</a></p>
        </div>
      </div>
    </div>
  `;
}
