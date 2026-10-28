/**
 * Jalali (Persian) date-range picker with hour selects.
 *
 * Everything the user sees is Persian and Tehran-based; the value exposed to
 * the API is always UTC ISO-8601 with `Z`.
 */

import { html, htmlToElement } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import {
  MONTHS,
  WEEKDAY_SHORT,
  addDays,
  dayLabel,
  faDigits,
  jalaliParts,
  monthDays,
  shiftMonth,
  todayCivil,
  weekdayIndex,
} from '../lib/jalali.js';
import { HOUR_MS, civilHourToUtcIso, fromIsoToTehran } from '../lib/datetime.js';
import { formatMoney } from '../lib/format.js';
import { validateBookingRange } from '../lib/validate.js';

const HOURS = Array.from({ length: 15 }, (_, index) => index + 7); // 07:00 … 21:00
const MAX_FUTURE_DAYS = 180;

function hourLabel(hour) {
  return `${faDigits(String(hour).padStart(2, '0'))}:۰۰`;
}

export function createDateRangePicker({ pricePerDay = 0, onChange } = {}) {
  const today = todayCivil();
  const maxDate = addDays(today, MAX_FUTURE_DAYS);
  const nowParts = jalaliParts(today);

  const state = {
    viewY: nowParts.y,
    viewM: nowParts.m,
    start: null,
    end: null,
    startHour: 10,
    endHour: 14,
  };

  const element = htmlToElement(html`<div class="dp"></div>`);

  function emit() {
    onChange?.(value());
  }

  function value() {
    if (!state.start || !state.end) {
      return { valid: false, reason: 'روز شروع و روز پایان را انتخاب کن.', startAt: null, endAt: null, hours: 0, days: 0, total: 0 };
    }
    const startAt = civilHourToUtcIso(state.start, state.startHour);
    const endAt = civilHourToUtcIso(state.end, state.endHour);

    const rangeError = validateBookingRange(startAt, endAt);
    if (rangeError) {
      return { valid: false, reason: rangeError, startAt, endAt, hours: 0, days: 0, total: 0 };
    }

    const hours = (new Date(endAt).getTime() - new Date(startAt).getTime()) / HOUR_MS;
    const days = Math.max(1, Math.ceil(hours / 24));
    return {
      valid: true,
      reason: null,
      startAt,
      endAt,
      hours,
      days,
      total: pricePerDay * days,
    };
  }

  function render() {
    const { start: firstDay, days } = monthDays(state.viewY, state.viewM);
    const offset = weekdayIndex(firstDay);
    const current = value();

    element.innerHTML = html`
      <div class="dp-head">
        <button type="button" class="icon-btn icon-btn-sm" data-dp="prev" aria-label="ماه قبل">${icon('chevronRight')}</button>
        <div class="dp-title">
          <strong>${MONTHS[state.viewM - 1]}</strong>
          <span>${faDigits(state.viewY)}</span>
        </div>
        <button type="button" class="icon-btn icon-btn-sm" data-dp="next" aria-label="ماه بعد">${icon('chevronLeft')}</button>
      </div>

      <div class="dp-week" aria-hidden="true">
        ${WEEKDAY_SHORT.map((label) => html`<span>${label}</span>`)}
      </div>

      <div class="dp-grid" role="grid" aria-label="تقویم">
        ${Array.from({ length: offset }, () => html`<span class="dp-day is-empty"></span>`)}
        ${days.map((ts) => {
          const parts = jalaliParts(ts);
          const disabled = ts < today || ts > maxDate;
          const classes = ['dp-day'];
          if (disabled) classes.push('is-disabled');
          if (ts === today) classes.push('is-today');
          if (state.start === ts) classes.push('is-start');
          if (state.end === ts) classes.push('is-end');
          if (state.start && state.end && ts > state.start && ts < state.end) classes.push('in-range');
          return html`
            <button
              type="button"
              class="${classes.join(' ')}"
              data-day="${ts}"
              ${disabled ? 'disabled' : ''}
              aria-label="${dayLabel(ts)}"
              aria-pressed="${state.start === ts || state.end === ts}"
            >${faDigits(parts.d)}</button>
          `;
        })}
      </div>

      <div class="dp-times">
        <label class="time-field">
          <span>ساعت شروع</span>
          <span class="select">
            <select data-dp="start-hour" aria-label="ساعت شروع">
              ${HOURS.map(
                (hour) => html`<option value="${hour}" ${hour === state.startHour ? 'selected' : ''}>${hourLabel(hour)}</option>`,
              )}
            </select>
            ${icon('chevron')}
          </span>
        </label>
        <label class="time-field">
          <span>ساعت پایان</span>
          <span class="select">
            <select data-dp="end-hour" aria-label="ساعت پایان">
              ${HOURS.map(
                (hour) => html`<option value="${hour}" ${hour === state.endHour ? 'selected' : ''}>${hourLabel(hour)}</option>`,
              )}
            </select>
            ${icon('chevron')}
          </span>
        </label>
      </div>

      <div class="dp-foot ${current.valid ? 'is-valid' : ''}">
        ${current.valid
          ? html`
              <span class="dp-summary">
                ${faDigits(current.days)} روز · ${formatMoney(current.total)} تومان
              </span>
              <button type="button" class="dp-clear" data-dp="clear">پاک کردن</button>
            `
          : html`<span class="dp-hint">${icon('info')} ${current.reason}</span>`}
      </div>
    `.toString();

    element.querySelector('[data-dp="start-hour"]').value = String(state.startHour);
    element.querySelector('[data-dp="end-hour"]').value = String(state.endHour);
  }

  function selectDay(ts) {
    if (ts < today || ts > maxDate) return;

    if (!state.start || (state.start && state.end)) {
      state.start = ts;
      state.end = null;
    } else if (ts >= state.start) {
      state.end = ts;
      if (ts === state.start && state.endHour <= state.startHour) {
        state.endHour = Math.min(21, state.startHour + 1);
      }
    } else {
      state.start = ts;
      state.end = null;
    }

    render();
    emit();
  }

  element.addEventListener('click', (event) => {
    const nav = event.target.closest('[data-dp]');
    if (nav) {
      const action = nav.dataset.dp;
      if (action === 'prev' || action === 'next') {
        const next = shiftMonth(state.viewY, state.viewM, action === 'next' ? 1 : -1);
        state.viewY = next.y;
        state.viewM = next.m;
        render();
      }
      if (action === 'clear') {
        state.start = null;
        state.end = null;
        render();
        emit();
      }
      return;
    }

    const day = event.target.closest('[data-day]');
    if (day) selectDay(Number(day.dataset.day));
  });

  element.addEventListener('change', (event) => {
    const field = event.target.closest('[data-dp]');
    if (!field) return;
    const hour = Number(field.value);
    if (field.dataset.dp === 'start-hour') state.startHour = hour;
    if (field.dataset.dp === 'end-hour') state.endHour = hour;
    render();
    emit();
  });

  render();

  return {
    element,
    value,
    setRange(startIso, endIso) {
      const start = fromIsoToTehran(startIso);
      const end = fromIsoToTehran(endIso);
      if (!start || !end) return;
      state.start = Date.UTC(start.y, start.m - 1, start.d);
      state.end = Date.UTC(end.y, end.m - 1, end.d);
      state.startHour = start.h;
      state.endHour = end.h;
      state.viewY = start.y;
      state.viewM = start.m;
      render();
      emit();
    },
    reset() {
      state.start = null;
      state.end = null;
      render();
      emit();
    },
  };
}
