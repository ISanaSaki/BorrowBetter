/** Create / edit an item (owner only). */

import { html, htmlToString } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { CATEGORIES, CATEGORY_LABEL, CONDITIONS, CONDITION_LABEL } from '../constants.js';
import { validateItemForm } from '../lib/validate.js';
import { itemsApi } from '../api/endpoints.js';
import { getUser } from '../store/auth.js';
import { showToast } from '../components/toast.js';
import { confirmDialog } from '../components/modal.js';
import { errorState, inlineError } from '../components/states.js';

export async function render({ root, params, signal, navigate }) {
  const isEdit = Boolean(params.id);
  const itemId = Number(params.id);
  let item = null;

  root.innerHTML = htmlToString(html`<div class="container form-page"><div class="form-card">${'در حال بارگذاری…'}</div></div>`);

  if (isEdit) {
    try {
      const response = await itemsApi.get(itemId, signal);
      item = response.data;
    } catch (error) {
      if (error?.name === 'AbortError') return;
      root.innerHTML = htmlToString(html`
        <div class="container form-page">${errorState({ message: error.message })}</div>
      `);
      root.querySelector('[data-retry]')?.addEventListener('click', () => navigate(`/items/${itemId}/edit`));
      return;
    }

    const me = getUser();
    if (!me || item.owner_id !== me.id) {
      root.innerHTML = htmlToString(html`
        <div class="container form-page">
          <div class="state-card">
            <span class="state-icon state-icon-error">${icon('warning')}</span>
            <h1>این وسیله مال تو نیست</h1>
            <p>فقط صاحب وسیله می‌تواند آن را ویرایش کند.</p>
            <div class="state-action"><a class="btn btn-primary" href="#/items/${itemId}">بازگشت به وسیله</a></div>
          </div>
        </div>
      `);
      return;
    }
  }

  const values = {
    title: item?.title || '',
    description: item?.description || '',
    category: item?.category || '',
    condition: item?.condition || 'good',
    price_per_day: item?.price_per_day ?? '',
    image_url: item?.image_url || '',
    is_active: item?.is_active ?? true,
  };

  root.innerHTML = htmlToString(formPage(values, Boolean(isEdit), itemId));

  const form = root.querySelector('[data-form]');
  const submit = root.querySelector('[data-submit]');
  const errorBox = root.querySelector('[data-form-error]');

  function showErrors(errors) {
    root.querySelectorAll('[data-error-for]').forEach((hint) => {
      hint.textContent = '';
    });
    Object.entries(errors).forEach(([field, message]) => {
      const hint = root.querySelector(`[data-error-for="${field}"]`);
      if (hint) hint.textContent = message;
      const input = root.querySelector(`[name="${field}"]`);
      input?.classList.add('is-invalid');
      input?.setAttribute('aria-invalid', 'true');
    });
    const firstField = Object.keys(errors)[0];
    root.querySelector(`[name="${firstField}"]`)?.focus();
  }

  function clearErrors() {
    root.querySelectorAll('[data-error-for]').forEach((hint) => {
      hint.textContent = '';
    });
    root.querySelectorAll('.is-invalid').forEach((input) => {
      input.classList.remove('is-invalid');
      input.removeAttribute('aria-invalid');
    });
    errorBox.innerHTML = '';
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearErrors();

    const data = new FormData(form);
    const payload = {
      title: String(data.get('title') || '').trim(),
      description: String(data.get('description') || '').trim(),
      category: String(data.get('category') || ''),
      condition: String(data.get('condition') || 'good'),
      price_per_day: Number(data.get('price_per_day') || 0),
      image_url: String(data.get('image_url') || '').trim() || null,
    };

    const errors = validateItemForm(payload);
    if (Object.keys(errors).length) {
      showErrors(errors);
      return;
    }

    submit.disabled = true;
    submit.classList.add('is-loading');
    try {
      if (isEdit) {
        const updatePayload = { ...payload };
        if (data.has('is_active')) updatePayload.is_active = data.get('is_active') === 'on';
        const response = await itemsApi.update(itemId, updatePayload);
        showToast('تغییرات ذخیره شد.');
        navigate(`/items/${response.data.id}`);
      } else {
        const response = await itemsApi.create(payload);
        showToast('وسیله ثبت شد و در کاتالوگ دیده می‌شود.');
        navigate(`/items/${response.data.id}`);
      }
    } catch (error) {
      if (error?.name === 'AbortError') return;
      if (error.code === 'VALIDATION_ERROR' && error.details?.fields) {
        showErrors(error.details.fields);
      } else {
        errorBox.innerHTML = htmlToString(inlineError(error.message));
      }
      showToast(error.message, { type: 'error' });
    } finally {
      submit.disabled = false;
      submit.classList.remove('is-loading');
    }
  });

  root.querySelector('[data-delete]')?.addEventListener('click', async () => {
    const confirmed = await confirmDialog({
      title: 'حذف وسیله',
      message: 'این وسیله از کاتالوگ حذف می‌شود. اگر رزرو فعال داشته باشد، حذف انجام نمی‌شود.',
      confirmText: 'حذف کن',
      danger: true,
    });
    if (!confirmed) return;
    try {
      await itemsApi.remove(itemId);
      showToast('وسیله حذف شد.', { type: 'info' });
      navigate('/my/items');
    } catch (error) {
      showToast(error.message, { type: 'error' });
    }
  });
}

function formPage(values, isEdit, itemId) {
  return html`
    <div class="container form-page">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <a href="#/">خانه</a><span>/</span>
        <a href="#/my/items">وسایل من</a><span>/</span>
        <strong>${isEdit ? 'ویرایش' : 'ثبت وسیله'}</strong>
      </nav>

      <div class="form-card">
        <div class="form-head">
          <span class="pill">${icon('toolbox')} ${isEdit ? 'ویرایش وسیله' : 'وسیلهٔ جدید'}</span>
          <h1>${isEdit ? 'اطلاعات وسیله را ویرایش کن' : 'چه چیزی را برای امانت می‌گذاری؟'}</h1>
          <p class="muted">هرچه اطلاعات دقیق‌تر باشد، همسایه‌ها راحت‌تر تصمیم می‌گیرند.</p>
        </div>

        <div data-form-error></div>

        <form class="form-grid" data-form novalidate>
          <label class="field field-span">
            <span>عنوان وسیله <b class="req">*</b></span>
            <input name="title" type="text" maxlength="120" value="${values.title}" placeholder="مثلاً دریل برقی بوش" required>
            <small class="field-error" data-error-for="title"></small>
          </label>

          <label class="field">
            <span>دسته <b class="req">*</b></span>
            <span class="select">
              <select name="category" required>
                <option value="" ${values.category ? '' : 'selected'} disabled>انتخاب کن…</option>
                ${CATEGORIES.map(
                  (category) => html`<option value="${category}" ${values.category === category ? 'selected' : ''}>${CATEGORY_LABEL[category]}</option>`,
                )}
              </select>
              ${icon('chevron')}
            </span>
            <small class="field-error" data-error-for="category"></small>
          </label>

          <label class="field">
            <span>وضعیت</span>
            <span class="select">
              <select name="condition">
                ${CONDITIONS.map(
                  (condition) => html`<option value="${condition}" ${values.condition === condition ? 'selected' : ''}>${CONDITION_LABEL[condition]}</option>`,
                )}
              </select>
              ${icon('chevron')}
            </span>
            <small class="field-error" data-error-for="condition"></small>
          </label>

          <label class="field">
            <span>قیمت روزانه (تومان) <b class="req">*</b></span>
            <input name="price_per_day" type="number" min="0" step="1000" inputmode="numeric" value="${values.price_per_day}" placeholder="۵۰۰۰۰" required>
            <small class="field-error" data-error-for="price_per_day"></small>
          </label>

          <label class="field">
            <span>آدرس تصویر (اختیاری)</span>
            <input name="image_url" type="url" value="${values.image_url}" placeholder="https://…" autocomplete="off">
            <small class="field-error" data-error-for="image_url"></small>
          </label>

          <label class="field field-span">
            <span>توضیحات</span>
            <textarea name="description" rows="4" maxlength="2000" placeholder="شرایط وسیله، لوازم همراه و نکته‌های مهم را بنویس.">${values.description}</textarea>
            <small class="field-error" data-error-for="description"></small>
          </label>

          ${isEdit
            ? html`
                <label class="check field-span">
                  <input type="checkbox" name="is_active" ${values.is_active ? 'checked' : ''}>
                  این وسیله در کاتالوگ نمایش داده شود
                </label>
              `
            : ''}

          <div class="form-actions field-span">
            <button type="submit" class="btn btn-primary" data-submit>
              ${icon('check')} ${isEdit ? 'ذخیرهٔ تغییرات' : 'ثبت وسیله'}
            </button>
            <a class="btn btn-ghost" href="${isEdit ? `#/items/${itemId}` : '#/my/items'}">انصراف</a>
            ${isEdit
              ? html`<button type="button" class="btn btn-danger-ghost" data-delete>${icon('trash')} حذف</button>`
              : ''}
          </div>
        </form>
      </div>
    </div>
  `;
}
