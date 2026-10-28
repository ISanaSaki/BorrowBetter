/**
 * Jalali (Persian) calendar helpers.
 *
 * Civil dates are represented as UTC-midnight timestamps. Formatting always
 * uses the `UTC` time zone so the calendar never shifts with the viewer's
 * machine time zone; "today" comes from Tehran explicitly.
 */

import { todayCivilTs, DAY_MS } from './datetime.js';

export const MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'];
export const WEEKDAYS = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه'];
export const WEEKDAY_SHORT = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
export const faDigits = (value) => String(value).replace(/\d/g, (digit) => FA_DIGITS[Number(digit)]);

const jalaliFormatter = new Intl.DateTimeFormat('en-u-ca-persian-nu-latn', {
  timeZone: 'UTC',
  year: 'numeric',
  month: 'numeric',
  day: 'numeric',
});

/** Persian calendar parts for a civil timestamp. */
export function jalaliParts(civilTs) {
  const parts = jalaliFormatter.formatToParts(new Date(civilTs));
  const get = (type) => Number(parts.find((part) => part.type === type).value);
  return { y: get('year'), m: get('month'), d: get('day') };
}

export function todayCivil() {
  return todayCivilTs();
}

export function civilOfToday() {
  return todayCivil();
}

/** First day (civil ts) of a Jalali month. */
export function monthStart(jy, jm) {
  const base = todayCivil();
  const baseParts = jalaliParts(base);
  let ts = base + Math.round((jy - baseParts.y) * 365.2422 + (jm - baseParts.m) * 30.4368) * DAY_MS;
  ts = Math.round(ts / DAY_MS) * DAY_MS;

  for (let i = 0; i < 90; i += 1) {
    const parts = jalaliParts(ts);
    if (parts.y === jy && parts.m === jm) break;
    const isBefore = parts.y < jy || (parts.y === jy && parts.m < jm);
    ts += isBefore ? DAY_MS : -DAY_MS;
  }
  return ts - (jalaliParts(ts).d - 1) * DAY_MS;
}

/** All civil days of a Jalali month plus its first day. */
export function monthDays(jy, jm) {
  const start = monthStart(jy, jm);
  const days = [];
  for (let ts = start; jalaliParts(ts).m === jm && days.length < 31; ts += DAY_MS) {
    days.push(ts);
  }
  return { start, days };
}

/** 0 = Saturday … 6 = Friday. */
export function weekdayIndex(civilTs) {
  return (new Date(civilTs).getUTCDay() + 1) % 7;
}

export function dayLabel(civilTs) {
  const parts = jalaliParts(civilTs);
  return `${WEEKDAYS[weekdayIndex(civilTs)]} ${faDigits(parts.d)} ${MONTHS[parts.m - 1]}`;
}

export function addDays(civilTs, days) {
  return civilTs + days * DAY_MS;
}

/** Move a civil date to the first day of the next/previous month. */
export function shiftMonth(jy, jm, delta) {
  let nextMonth = jm + delta;
  let nextYear = jy;
  if (nextMonth > 12) {
    nextMonth = 1;
    nextYear += 1;
  }
  if (nextMonth < 1) {
    nextMonth = 12;
    nextYear -= 1;
  }
  return { y: nextYear, m: nextMonth };
}
