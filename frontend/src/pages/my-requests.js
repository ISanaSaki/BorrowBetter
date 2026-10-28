/** My reservations with role tabs, status filter and permission-based actions. */

import { html, htmlToString, delegate } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { STATUS, STATUS_LABEL } from '../constants.js';
import { reservationsApi } from '../api/endpoints.js';
import { getUser } from '../store/auth.js';
import { showToast } from '../components/toast.js';
import { confirmDialog, promptDialog } from '../components/modal.js';
import { emptyState, errorState, skeletonRows } from '../components/states.js';
import { pagination } from '../components/pagination.js';
import { reservationCard } from '../components/reservation-card.js';

const ROLES = [
  { value: 'borrower', label: 'درخواست‌های من' },
  { value: 'lender', label: 'درخواست‌های وسیله‌هایم' },
  { value: 'all', label: 'همه' },
];

const STATUS_FILTERS = [
  { value: '', label: 'همهٔ وضعیت‌ها' },
  ...Object.values(STATUS).map((status) => ({ value: status, label: STATUS_LABEL[status] })),
];

export async function render({ root, query, signal }) {
  const me = getUser();
  let role = query.role || 'borrower';
  let status = query.status || '';
  let page = 1;
  const reservationsById = new Map();

  root.innerHTML = htmlToString(html`
    <div class="container dashboard">
      <div class="page-head-inline">
        <div>
          <p class="eyebrow">پیگیری رزروها</p>
          <h1>درخواست‌های من</h1>
        </div>
        <a class="btn btn-primary" href="#/items">${icon('search')} دیدن وسایل</a>
      </div>

      <div class="tabs" role="tablist" aria-label="نقش">
        ${ROLES.map(
          (item) => html`
            <button type="button" role="tab" class="tab ${item.value === role ? 'is-active' : ''}" data-role="${item.value}" aria-selected="${item.value === role}">
              ${item.label}
            </button>
          `,
        )}
      </div>

      <div class="toolbar">
        <label class="select">
          <span class="sr-only">فیلتر وضعیت</span>
          <select data-status>
            ${STATUS_FILTERS.map(
              (option) => html`<option value="${option.value}" ${option.value === status ? 'selected' : ''}>${option.label}</option>`,
            )}
          </select>
          ${icon('chevron')}
        </label>
        <span class="result-count" data-count></span>
      </div>

      <div class="reservation-list" data-list aria-live="polite"></div>
      <div data-pagination></div>
    </div>
  `);

  const list = root.querySelector('[data-list]');
  const paginationHost = root.querySelector('[data-pagination]');
  const countHost = root.querySelector('[data-count]');

  function syncUrl() {
    const params = new URLSearchParams();
    if (role !== 'borrower') params.set('role', role);
    if (status) params.set('status', status);
    const qs = params.toString();
    history.replaceState(null, '', `#/my/requests${qs ? `?${qs}` : ''}`);
  }

  async function load() {
    list.innerHTML = htmlToString(skeletonRows(3));
    paginationHost.innerHTML = '';
    try {
      const { data, meta } = await reservationsApi.mine({ role, status: status || undefined, page, limit: 6 }, signal);
      reservationsById.clear();
      data.forEach((reservation) => reservationsById.set(reservation.id, reservation));
      renderList(data, meta);
    } catch (error) {
      if (error?.name === 'AbortError') return;
      list.innerHTML = htmlToString(errorState({ message: error.message }));
      list.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  function renderList(items, meta) {
    countHost.textContent = `${(meta?.total ?? items.length).toLocaleString('fa-IR')} درخواست`;

    if (!items.length) {
      list.innerHTML = htmlToString(
        emptyState({
          title: 'درخواستی در این بخش نیست',
          text: role === 'lender'
            ? 'وقتی کسی وسیله‌ات را درخواست کند، اینجا می‌بینی.'
            : 'از کاتالوگ یک وسیله انتخاب کن و اولین درخواستت را ثبت کن.',
          iconName: 'calendar',
          action: html`<a class="btn btn-primary" href="#/items">دیدن وسایل</a>`,
        }),
      );
      return;
    }

    list.innerHTML = items.map((reservation) => reservationCard(reservation, { me }).toString()).join('');
    paginationHost.innerHTML = htmlToString(
      pagination({ page: meta?.page ?? 1, totalPages: meta?.total_pages ?? 1, total: meta?.total }),
    );
  }

  async function runAction(action, reservation) {
    if (action === 'approve' || action === 'reject') {
      const note = await promptDialog({
        title: action === 'approve' ? 'تأیید درخواست' : 'رد درخواست',
        message: `${reservation.item?.title || 'وسیله'} — ${reservation.borrower?.full_name || 'متقاضی'}`,
        label: 'یادداشت برای متقاضی (اختیاری)',
        placeholder: action === 'approve' ? 'مثلاً: تحویل در ورودی ساختمان.' : 'مثلاً: این بازه خودم لازمش دارم.',
        confirmText: action === 'approve' ? 'تأیید کن' : 'رد کن',
      });
      if (note === null) return;
      const payload = { decision_note: note || null };
      await (action === 'approve' ? reservationsApi.approve(reservation.id, payload) : reservationsApi.reject(reservation.id, payload));
      showToast(action === 'approve' ? 'درخواست تأیید شد.' : 'درخواست رد شد.', { type: action === 'approve' ? 'success' : 'info' });
      return;
    }

    if (action === 'cancel') {
      const reason = await promptDialog({
        title: 'لغو درخواست',
        message: 'این بازه آزاد می‌شود و طرف دیگر مطلع نمی‌شود (در نسخهٔ بعدی اعلان اضافه می‌شود).',
        label: 'دلیل لغو (اختیاری)',
        confirmText: 'لغو کن',
      });
      if (reason === null) return;
      await reservationsApi.cancel(reservation.id, { cancel_reason: reason || null });
      showToast('درخواست لغو شد.', { type: 'info' });
      return;
    }

    if (action === 'handover') {
      const confirmed = await confirmDialog({
        title: 'ثبت تحویل',
        message: 'مطمئنی وسیله را به متقاضی تحویل داده‌ای؟ وضعیت به «در حال امانت» تغییر می‌کند.',
        confirmText: 'تحویل دادم',
      });
      if (!confirmed) return;
      await reservationsApi.handover(reservation.id);
      showToast('تحویل ثبت شد.');
      return;
    }

    if (action === 'return') {
      const confirmed = await confirmDialog({
        title: 'ثبت بازگشت',
        message: 'با ثبت بازگشت، بازه آزاد می‌شود و رزرو بسته می‌شود.',
        confirmText: 'بازگشت ثبت شود',
      });
      if (!confirmed) return;
      const returnedBy = reservation.lender?.id === me?.id ? 'lender' : 'borrower';
      await reservationsApi.returnItem(reservation.id, { returned_by: returnedBy });
      showToast('بازگشت ثبت شد.');
    }
  }

  delegate(list, 'click', '[data-action]', async (event, button) => {
    event.preventDefault();
    const reservation = reservationsById.get(Number(button.dataset.id));
    if (!reservation) return;
    button.disabled = true;
    try {
      await runAction(button.dataset.action, reservation);
      await load();
    } catch (error) {
      if (error?.name === 'AbortError') return;
      showToast(error.message, { type: 'error' });
      if (error.code === 'INVALID_TRANSITION') await load();
    } finally {
      button.disabled = false;
    }
  });

  delegate(root, 'click', '[data-role]', (event, button) => {
    role = button.dataset.role;
    page = 1;
    root.querySelectorAll('[data-role]').forEach((tab) => {
      const active = tab === button;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', String(active));
    });
    syncUrl();
    load();
  });

  root.querySelector('[data-status]')?.addEventListener('change', (event) => {
    status = event.target.value;
    page = 1;
    syncUrl();
    load();
  });

  delegate(root, 'click', '[data-page]', (event, button) => {
    const target = Number(button.dataset.page);
    if (!target) return;
    page = target;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    load();
  });

  await load();
}
