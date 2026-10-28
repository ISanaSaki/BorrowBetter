/** Item detail + booking (Jalali range picker, 409 conflict handling). */

import { html, htmlToString } from '../lib/html.js';
import { icon, categoryIcon } from '../lib/icons.js';
import { formatMoney, formatRange, formatToman } from '../lib/format.js';
import { addDaysIso, nowIso } from '../lib/datetime.js';
import { CATEGORY_LABEL, CONDITION_LABEL } from '../constants.js';
import { itemsApi, reservationsApi } from '../api/endpoints.js';
import { getUser, isLoggedIn } from '../store/auth.js';
import { showToast } from '../components/toast.js';
import { confirmDialog } from '../components/modal.js';
import { errorState, skeletonGrid } from '../components/states.js';
import { createDateRangePicker } from '../components/date-range.js';

export async function render(ctx) {
  const { root, params, path, signal, navigate } = ctx;
  const itemId = Number(params.id);
  if (!Number.isFinite(itemId) || itemId <= 0) {
    root.innerHTML = htmlToString(errorState({ message: 'شناسهٔ وسیله معتبر نیست.' }));
    return;
  }

  root.innerHTML = htmlToString(html`
    <div class="container page-detail">
      <div class="detail-skeleton" aria-hidden="true">${skeletonGrid(2)}</div>
    </div>
  `);

  try {
    const [itemResponse, availabilityResponse] = await Promise.all([
      itemsApi.get(itemId, signal),
      itemsApi.availability(itemId, nowIso(), addDaysIso(nowIso(), 60), signal),
    ]);
    const item = itemResponse.data;
    const availability = availabilityResponse.data;
    root.innerHTML = htmlToString(layout(item, availability, path));
    wire(item, availability);
  } catch (error) {
    if (error?.name === 'AbortError') return;
    root.innerHTML = htmlToString(html`
      <div class="container page-detail">
        ${errorState({ message: error.message })}
        <div class="center-actions"><a class="btn btn-ghost" href="#/items">بازگشت به وسایل</a></div>
      </div>
    `);
    root.querySelector('[data-retry]')?.addEventListener('click', () => navigate(path));
  }

  function wire(item, availability) {
    const me = getUser();
    const isOwner = Boolean(me && item.owner_id === me.id);
    const bookingHost = root.querySelector('[data-booking]');
    const conflictHost = root.querySelector('[data-conflict]');
    const busyHost = root.querySelector('[data-busy]');

    if (busyHost) {
      busyHost.innerHTML = htmlToString(
        availability.busy.length
          ? html`<ul class="busy-list">
              ${availability.busy.slice(0, 6).map(
                (slot) => html`<li class="busy-item">${icon('calendar')}<span>${formatRange(slot.start_at, slot.end_at)}</span></li>`,
              )}
              ${availability.busy.length > 6
                ? html`<li class="busy-item is-more">و ${(availability.busy.length - 6).toLocaleString('fa-IR')} بازهٔ دیگر</li>`
                : ''}
            </ul>`
          : html`<p class="busy-empty">${icon('check')} تا ۶۰ روز آینده بازه‌ای رزرو نشده است.</p>`,
      );
    }

    if (isOwner) {
      bookingHost.innerHTML = htmlToString(ownerPanel(item));
      bookingHost.querySelector('[data-edit]')?.addEventListener('click', () => navigate(`/items/${item.id}/edit`));
      bookingHost.querySelector('[data-delete]')?.addEventListener('click', async () => {
        const confirmed = await confirmDialog({
          title: 'حذف وسیله',
          message: 'این وسیله از کاتالوگ حذف می‌شود. اگر رزرو فعال داشته باشد، حذف انجام نمی‌شود.',
          confirmText: 'حذف کن',
          danger: true,
        });
        if (!confirmed) return;
        try {
          await itemsApi.remove(item.id);
          showToast('وسیله حذف شد.', { type: 'info' });
          navigate('/my/items');
        } catch (error) {
          showToast(error.message, { type: 'error' });
        }
      });
      return;
    }

    const picker = createDateRangePicker({
      pricePerDay: item.price_per_day,
      onChange: (value) => {
        updateSummary(value);
      },
    });

    bookingHost.innerHTML = htmlToString(bookingPanel(item));
    bookingHost.querySelector('[data-picker]').append(picker.element);

    const summaryRange = bookingHost.querySelector('[data-sum-range]');
    const summaryDuration = bookingHost.querySelector('[data-sum-duration]');
    const summaryTotal = bookingHost.querySelector('[data-sum-total]');
    const submit = bookingHost.querySelector('[data-book]');
    const messageInput = bookingHost.querySelector('[data-message]');

    function updateSummary(value) {
      if (!value.valid) {
        summaryRange.textContent = 'انتخاب نشده';
        summaryDuration.textContent = '—';
        summaryTotal.textContent = '—';
        submit.disabled = true;
        submit.setAttribute('aria-disabled', 'true');
        return;
      }
      summaryRange.textContent = formatRange(value.startAt, value.endAt);
      summaryDuration.textContent = value.hours < 24 ? `${value.hours.toLocaleString('fa-IR')} ساعت` : `${value.days.toLocaleString('fa-IR')} روز`;
      summaryTotal.textContent = formatToman(value.total);
      submit.disabled = false;
      submit.removeAttribute('aria-disabled');
    }

    updateSummary(picker.value());

    submit.addEventListener('click', async () => {
      const value = picker.value();
      if (!value.valid) {
        showToast(value.reason, { type: 'error' });
        return;
      }
      if (!isLoggedIn()) {
        navigate(`/login?redirect=${encodeURIComponent(path)}`);
        return;
      }

      submit.disabled = true;
      submit.classList.add('is-loading');
      try {
        await reservationsApi.create({
          item_id: item.id,
          start_at: value.startAt,
          end_at: value.endAt,
          message: messageInput?.value.trim() || undefined,
        });
        showToast('درخواست ثبت شد؛ منتظر تأیید صاحب وسیله باش.', { type: 'success' });
        navigate('/my/requests?role=borrower');
      } catch (error) {
        if (error?.name === 'AbortError') return;
        if (error.code === 'SLOT_CONFLICT') {
          showConflict(error.details, value);
        } else {
          showToast(error.message, { type: 'error' });
        }
      } finally {
        submit.disabled = false;
        submit.classList.remove('is-loading');
      }
    });

    function showConflict(details, requested) {
      const suggestions = details?.suggestions || [];
      conflictHost.innerHTML = htmlToString(html`
        <div class="conflict" role="alert">
          <div class="conflict-head">
            <span class="state-icon state-icon-warn">${icon('warning')}</span>
            <div>
              <h2>این بازه همین حالا رزرو شد</h2>
              <p>
                بازهٔ درخواستی <b>${formatRange(requested.startAt, requested.endAt)}</b>
                با ${(details?.conflicts?.length || 1).toLocaleString('fa-IR')} رزرو دیگر تداخل دارد.
                یکی از بازه‌های آزاد را انتخاب کن.
              </p>
            </div>
          </div>
          <div class="conflict-body">
            ${details?.conflicts?.length
              ? html`<ul class="conflict-list">
                  ${details.conflicts.map(
                    (slot) => html`<li><span class="badge badge-danger">تداخل</span> ${formatRange(slot.start_at, slot.end_at)}</li>`,
                  )}
                </ul>`
              : ''}

            ${suggestions.length
              ? html`<p class="suggest-label">بازه‌های آزاد پیشنهادی:</p>
                <div class="suggests">
                  ${suggestions.map(
                    (slot) => html`
                      <button type="button" class="suggest" data-suggest-start="${slot.start_at}" data-suggest-end="${slot.end_at}">
                        <strong>${formatRange(slot.start_at, slot.end_at)}</strong>
                        <small>انتخاب این بازه</small>
                      </button>
                    `,
                  )}
                </div>`
              : html`<p class="muted">بازهٔ آزادی پیدا نشد؛ بازهٔ دیگری را در تقویم انتخاب کن.</p>`}

            <button type="button" class="btn btn-ghost btn-sm" data-scroll-picker>انتخاب بازهٔ دیگر</button>
          </div>
        </div>
      `);

      conflictHost.querySelectorAll('[data-suggest-start]').forEach((button) => {
        button.addEventListener('click', () => {
          picker.setRange(button.dataset.suggestStart, button.dataset.suggestEnd);
          conflictHost.innerHTML = '';
          bookingHost.scrollIntoView({ behavior: 'smooth', block: 'center' });
          showToast('بازهٔ جایگزین انتخاب شد');
        });
      });

      conflictHost.querySelector('[data-scroll-picker]')?.addEventListener('click', () => {
        bookingHost.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    }
  }
}

function layout(item, availability) {
  const owner = item.owner || {};
  const hasBusy = Boolean(availability?.busy?.length);

  return html`
    <div class="container page-detail">
      <nav class="crumbs" aria-label="مسیر صفحه">
        <a href="#/items">وسایل</a><span>/</span>
        <a href="#/items?category=${item.category}">${CATEGORY_LABEL[item.category] || 'دسته'}</a><span>/</span>
        <strong>${item.title}</strong>
      </nav>

      <div class="detail-grid">
        <div class="detail-main">
          <div class="gallery">
            <div class="gallery-main ${item.image_url ? 'has-image' : ''}" data-tint="${item.category}">
              <span class="media-fallback">${categoryIcon(item.category)}</span>
              ${item.image_url
                ? html`<img class="gallery-image" src="${item.image_url}" alt="${item.title}" decoding="async" data-img-fallback>`
                : ''}
            </div>
          </div>

          <div class="detail-head">
            <div class="badges">
              <span class="badge badge-soft">${CATEGORY_LABEL[item.category] || item.category}</span>
              <span class="badge badge-soft">${CONDITION_LABEL[item.condition] || item.condition}</span>
              ${hasBusy
                ? html`<span class="badge badge-warn"><span class="dot"></span> برخی بازه‌ها رزرو شده</span>`
                : html`<span class="badge badge-ok"><span class="dot"></span> قابل رزرو</span>`}
            </div>
            <h1>${item.title}</h1>
            <p class="detail-meta">
              ${icon('clock')}
              حداقل ۱ ساعت · حداکثر ۳۰ روز · بازهٔ نیمه‌باز
            </p>
          </div>

          <p class="detail-lead">${item.description || 'توضیحی برای این وسیله ثبت نشده است.'}</p>

          <dl class="specs">
            <div><dt>دسته</dt><dd>${CATEGORY_LABEL[item.category] || item.category}</dd></div>
            <div><dt>وضعیت</dt><dd>${CONDITION_LABEL[item.condition] || item.condition}</dd></div>
            <div><dt>قیمت روزانه</dt><dd>${formatToman(item.price_per_day)}</dd></div>
            <div><dt>حداقل مدت</dt><dd>۱ ساعت</dd></div>
            <div><dt>حداکثر مدت</dt><dd>۳۰ روز</dd></div>
            <div><dt>تحویل</dt><dd>حضوری، با هماهنگی</dd></div>
          </dl>

          <div class="owner-card">
            <span class="avatar avatar-lg">${(owner.full_name || '؟').trim().charAt(0)}</span>
            <div class="owner-text">
              <strong>${owner.full_name || 'صاحب وسیله'}</strong>
              <span>صاحب وسیله · عضو BorrowBetter</span>
            </div>
            <span class="badge badge-soft">تماس از طریق درخواست</span>
          </div>

          <section class="busy-section">
            <h2>بازه‌های رزروشده</h2>
            <p class="muted">این بازه‌ها تا ۶۰ روز آینده قفل شده‌اند.</p>
            <div data-busy></div>
          </section>
        </div>

        <aside class="booking" aria-label="رزرو وسیله" data-booking></aside>
      </div>

      <div data-conflict></div>
    </div>
  `;
}

function bookingPanel(item) {
  return html`
    <div class="booking-head">
      <div class="price-line"><span class="price">${formatMoney(item.price_per_day)}</span><span class="unit">تومان / روز</span></div>
      <span class="badge badge-soft">حداقل ۱ ساعت</span>
    </div>

    <div data-picker></div>

    <div class="booking-summary">
      <div><span>بازه</span><strong data-sum-range>انتخاب نشده</strong></div>
      <div><span>مدت</span><strong data-sum-duration>—</strong></div>
      <div class="sum-total"><span>هزینهٔ کل</span><strong data-sum-total>—</strong></div>
    </div>

    <label class="field field-compact">
      <span>یادداشت برای صاحب وسیله (اختیاری)</span>
      <textarea data-message rows="2" maxlength="500" placeholder="مثلاً: برای نصب قفسه لازمش دارم."></textarea>
    </label>

    <button type="button" class="btn btn-primary btn-block" data-book disabled aria-disabled="true">ثبت درخواست</button>
    <p class="fineprint">تا تأیید صاحب وسیله، مبلغی پرداخت نمی‌شود. بعد از تأیید، ۲۴ ساعت برای تحویل فرصت داری.</p>
  `;
}

function ownerPanel(item) {
  return html`
    <span class="pill">${icon('user')} این وسیلهٔ توست</span>
    <h2 class="booking-owner-title">${item.title}</h2>
    <p class="muted">می‌توانی اطلاعات را ویرایش کنی یا وسیله را از کاتالوگ حذف کنی.</p>
    <div class="booking-owner-actions">
      <button type="button" class="btn btn-primary btn-block" data-edit>${icon('edit')} ویرایش وسیله</button>
      <button type="button" class="btn btn-ghost btn-block" data-delete>${icon('trash')} حذف وسیله</button>
    </div>
    <p class="fineprint">درخواست‌های این وسیله را در «درخواست‌ها» با فیلتر صاحب وسیله ببین.</p>
  `;
}
