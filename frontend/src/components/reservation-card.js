/** Reservation card used in "درخواست‌های من". */

import { html } from '../lib/html.js';
import { icon, categoryIcon } from '../lib/icons.js';
import { formatRange, formatRelative, formatToman } from '../lib/format.js';
import { statusBadge, statusTimeline } from './status.js';

const ACTIONS = [
  { key: 'approve', label: 'تأیید درخواست', variant: 'primary', icon: 'check' },
  { key: 'reject', label: 'رد کردن', variant: 'ghost', icon: 'close' },
  { key: 'cancel', label: 'لغو درخواست', variant: 'ghost', icon: 'close' },
  { key: 'handover', label: 'تحویل دادم', variant: 'soft', icon: 'toolbox' },
  { key: 'return', label: 'بازگرداندن', variant: 'primary', icon: 'shield' },
];

export function reservationCard(reservation, { me } = {}) {
  const isBorrower = Boolean(me && reservation.borrower_id === me.id);
  const permissions = reservation.permissions || {};
  const item = reservation.item;
  const availableActions = ACTIONS.filter((action) => permissions[`can_${action.key}`]);

  return html`
    <article class="reservation-card" data-reservation="${reservation.id}">
      <header class="reservation-head">
        <div class="reservation-item">
          <span class="reservation-thumb">${categoryIcon(item?.category || 'other')}</span>
          <div class="reservation-titles">
            <a class="reservation-title" href="#/items/${reservation.item_id}">${item?.title || 'وسیله'}</a>
            <span class="reservation-role">${isBorrower ? 'درخواست تو' : 'درخواست برای وسیلهٔ تو'}</span>
          </div>
        </div>
        ${statusBadge(reservation.status)}
      </header>

      <div class="reservation-facts">
        <div>
          <span>بازه</span>
          <strong>${formatRange(reservation.start_at, reservation.end_at)}</strong>
        </div>
        <div>
          <span>هزینهٔ کل</span>
          <strong>${formatToman(reservation.total_price)}</strong>
        </div>
        <div>
          <span>ثبت</span>
          <strong>${formatRelative(reservation.created_at)}</strong>
        </div>
      </div>

      ${reservation.message
        ? html`<p class="reservation-message">
            ${icon('info')}
            <span>${reservation.message}</span>
          </p>`
        : ''}

      ${statusTimeline(reservation.status)}

      ${availableActions.length
        ? html`<div class="reservation-actions">
            ${availableActions.map(
              (action) => html`
                <button
                  type="button"
                  class="btn btn-${action.variant} btn-sm"
                  data-action="${action.key}"
                  data-id="${reservation.id}"
                >
                  ${icon(action.icon)}
                  ${action.label}
                </button>
              `,
            )}
          </div>`
        : ''}

      ${reservation.decision_note
        ? html`<p class="reservation-note">یادداشت صاحب وسیله: ${reservation.decision_note}</p>`
        : ''}
      ${reservation.cancel_reason
        ? html`<p class="reservation-note">دلیل لغو: ${reservation.cancel_reason}</p>`
        : ''}
    </article>
  `;
}
