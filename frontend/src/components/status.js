/** Status badge + reservation timeline (labels come from constants.js). */

import { html } from '../lib/html.js';
import { STATUS, STATUS_LABEL, STATUS_TONE } from '../constants.js';
import { icon } from '../lib/icons.js';

export function statusBadge(status) {
  const tone = STATUS_TONE[status] || 'soft';
  return html`<span class="badge badge-${tone}"><span class="dot"></span>${STATUS_LABEL[status] || status}</span>`;
}

const STEPS = [
  { status: STATUS.PENDING, label: 'ثبت درخواست', icon: 'calendar' },
  { status: STATUS.APPROVED, label: 'تأیید صاحب وسیله', icon: 'check' },
  { status: STATUS.ACTIVE, label: 'تحویل وسیله', icon: 'toolbox' },
  { status: STATUS.RETURNED, label: 'بازگشت وسیله', icon: 'shield' },
];

const NEGATIVE = [STATUS.REJECTED, STATUS.CANCELLED, STATUS.EXPIRED];

export function statusTimeline(status) {
  if (NEGATIVE.includes(status)) {
    const tone = STATUS_TONE[status];
    return html`
      <div class="timeline-terminal">
        <span class="badge badge-${tone}">${STATUS_LABEL[status]}</span>
        <span class="timeline-terminal-text">این درخواست بسته شده است.</span>
      </div>
    `;
  }

  const index = STEPS.findIndex((step) => step.status === status);
  const activeIndex = index === -1 ? 0 : index;

  return html`
    <ol class="timeline">
      ${STEPS.map((step, stepIndex) => {
        const state = stepIndex < activeIndex ? 'is-done' : stepIndex === activeIndex ? 'is-current' : '';
        return html`
          <li class="timeline-step ${state}">
            <span class="timeline-dot">${state === 'is-done' ? icon('check') : ''}</span>
            <span class="timeline-label">${step.label}</span>
          </li>
        `;
      })}
    </ol>
  `;
}
