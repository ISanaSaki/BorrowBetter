/** Owner dashboard: my items with counters and quick actions. */

import { html, htmlToString, delegate } from '../lib/html.js';
import { icon, categoryIcon } from '../lib/icons.js';
import { formatNumber, formatToman } from '../lib/format.js';
import { CATEGORY_LABEL, CONDITION_LABEL } from '../constants.js';
import { itemsApi } from '../api/endpoints.js';
import { showToast } from '../components/toast.js';
import { confirmDialog } from '../components/modal.js';
import { emptyState, errorState, skeletonRows } from '../components/states.js';
import { pagination } from '../components/pagination.js';

export async function render({ root, signal }) {
  let page = 1;

  root.innerHTML = htmlToString(html`
    <div class="container dashboard">
      <div class="page-head-inline">
        <div>
          <p class="eyebrow">داشبورد صاحب وسیله</p>
          <h1>وسایل من</h1>
        </div>
        <a class="btn btn-primary" href="#/items/new">${icon('plus')} ثبت وسیله</a>
      </div>
      <div data-stats class="dashboard-stats"></div>
      <div class="panel" data-panel>
        ${skeletonRows(3)}
      </div>
      <div data-pagination></div>
    </div>
  `);

  const panel = root.querySelector('[data-panel]');
  const statsHost = root.querySelector('[data-stats]');
  const paginationHost = root.querySelector('[data-pagination]');

  async function load() {
    panel.innerHTML = htmlToString(skeletonRows(3));
    try {
      const { data, meta } = await itemsApi.myItems({ page, limit: 12 }, signal);
      renderStats(data);
      renderList(data);
      paginationHost.innerHTML = htmlToString(
        pagination({
          page: meta?.page ?? 1,
          totalPages: meta?.total_pages ?? 1,
          total: meta?.total,
        }),
      );
    } catch (error) {
      if (error?.name === 'AbortError') return;
      panel.innerHTML = htmlToString(errorState({ message: error.message }));
      panel.querySelector('[data-retry]')?.addEventListener('click', load);
    }
  }

  function renderStats(items) {
    const pending = items.reduce((sum, item) => sum + (item.pending_requests_count || 0), 0);
    const active = items.reduce((sum, item) => sum + (item.active_reservations_count || 0), 0);
    const total = items.length;
    statsHost.innerHTML = htmlToString(html`
      <div class="stat-card"><span class="stat-icon">${icon('toolbox')}</span><div><strong>${formatNumber(total)}</strong><span>وسیله</span></div></div>
      <div class="stat-card"><span class="stat-icon">${icon('calendar')}</span><div><strong>${formatNumber(pending)}</strong><span>در انتظار تأیید</span></div></div>
      <div class="stat-card"><span class="stat-icon">${icon('check')}</span><div><strong>${formatNumber(active)}</strong><span>در حال امانت</span></div></div>
    `);
  }

  function renderList(items) {
    if (!items.length) {
      panel.innerHTML = htmlToString(
        emptyState({
          title: 'هنوز وسیله‌ای ثبت نکرده‌ای',
          text: 'اولین وسیله‌ات را ثبت کن و اجازه بده همسایه‌ها از آن استفاده کنند.',
          iconName: 'toolbox',
          action: html`<a class="btn btn-primary" href="#/items/new">${icon('plus')} ثبت وسیله</a>`,
        }),
      );
      return;
    }

    panel.innerHTML = htmlToString(html`
      <ul class="my-items">
        ${items.map(
          (item) => html`
            <li class="my-item ${item.is_active ? '' : 'is-inactive'}">
              <span class="my-item-thumb">${categoryIcon(item.category)}</span>
              <div class="my-item-body">
                <div class="my-item-head">
                  <a class="my-item-title" href="#/items/${item.id}">${item.title}</a>
                  ${item.is_active
                    ? html`<span class="badge badge-ok">فعال</span>`
                    : html`<span class="badge badge-soft">غیرفعال</span>`}
                </div>
                <p class="my-item-meta">
                  ${CATEGORY_LABEL[item.category] || item.category} · ${CONDITION_LABEL[item.condition] || item.condition} · ${formatToman(item.price_per_day)}
                </p>
                <div class="my-item-counts">
                  <span>${icon('clock')} ${formatNumber(item.pending_requests_count || 0)} در انتظار تأیید</span>
                  <span>${icon('check')} ${formatNumber(item.active_reservations_count || 0)} در حال امانت</span>
                </div>
              </div>
              <div class="my-item-actions">
                <a class="btn btn-ghost btn-sm" href="#/my/requests?role=lender">${icon('calendar')} درخواست‌ها</a>
                <a class="btn btn-ghost btn-sm" href="#/items/${item.id}/edit">${icon('edit')} ویرایش</a>
                <button type="button" class="btn btn-ghost btn-sm" data-toggle="${item.id}" data-active="${item.is_active}">
                  ${item.is_active ? 'غیرفعال کن' : 'فعال کن'}
                </button>
                <button type="button" class="btn btn-danger-ghost btn-sm" data-delete="${item.id}" data-title="${item.title}">
                  ${icon('trash')} حذف
                </button>
              </div>
            </li>
          `,
        )}
      </ul>
    `);
  }

  delegate(root, 'click', '[data-delete]', async (event, button) => {
    event.preventDefault();
    const confirmed = await confirmDialog({
      title: 'حذف وسیله',
      message: `«${button.dataset.title}» از کاتالوگ حذف می‌شود. اگر رزرو فعال داشته باشد، حذف انجام نمی‌شود.`,
      confirmText: 'حذف کن',
      danger: true,
    });
    if (!confirmed) return;
    try {
      await itemsApi.remove(Number(button.dataset.delete));
      showToast('وسیله حذف شد.', { type: 'info' });
      load();
    } catch (error) {
      showToast(error.message, { type: 'error' });
    }
  });

  delegate(root, 'click', '[data-toggle]', async (event, button) => {
    event.preventDefault();
    const id = Number(button.dataset.toggle);
    const nextActive = button.dataset.active !== 'true';
    button.disabled = true;
    try {
      await itemsApi.update(id, { is_active: nextActive });
      showToast(nextActive ? 'وسیله فعال شد.' : 'وسیله غیرفعال شد.');
      load();
    } catch (error) {
      showToast(error.message, { type: 'error' });
    } finally {
      button.disabled = false;
    }
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
