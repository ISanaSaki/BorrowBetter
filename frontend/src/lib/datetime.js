/**
 * Time-zone helpers.
 *
 * The product stores every timestamp in UTC (TEAM-SPEC §0, rule 8) and only
 * Tehran is used for display and for interpreting user input. Iran has no
 * daylight saving time since 2022, so a fixed offset is both correct and
 * deterministic (never depend on the viewer's machine time-zone).
 */

export const TEHRAN_OFFSET_MINUTES = 210; // UTC+03:30
const OFFSET_MS = TEHRAN_OFFSET_MINUTES * 60000;
export const HOUR_MS = 3600000;
export const DAY_MS = 86400000;

const partsFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Tehran',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

/** Current wall-clock time in Tehran. */
export function tehranParts(date = new Date()) {
  const parts = partsFormatter.formatToParts(date);
  const get = (type) => Number(parts.find((part) => part.type === type).value);
  return { y: get('year'), m: get('month'), d: get('day'), h: get('hour') % 24, minute: get('minute') };
}

/** Tehran wall-clock (y, m, d, h, min) → UTC ISO-8601 string with `Z`. */
export function toUtcIso(y, m, d, hour = 0, minute = 0) {
  const utcMs = Date.UTC(y, m - 1, d, hour, minute) - OFFSET_MS;
  return new Date(utcMs).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

/**
 * Civil date (UTC-midnight timestamp, e.g. from lib/jalali) + Tehran wall-clock
 * hour → UTC ISO. Use this whenever the date already is a civil timestamp.
 */
export function civilHourToUtcIso(civilTs, hour = 0, minute = 0) {
  const utcMs = civilTs + hour * HOUR_MS + minute * 60000 - OFFSET_MS;
  return new Date(utcMs).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

/** ISO string → Tehran wall-clock parts, handy for prefilling inputs. */
export function fromIsoToTehran(iso) {
  if (!iso) return null;
  return tehranParts(new Date(iso));
}

export function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

export function hoursBetween(startIso, endIso) {
  return (new Date(endIso).getTime() - new Date(startIso).getTime()) / HOUR_MS;
}

export function addDaysIso(iso, days) {
  return new Date(new Date(iso).getTime() + days * DAY_MS).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

/** Current Tehran civil date as a UTC-midnight timestamp (used by the calendar). */
export function todayCivilTs() {
  const { y, m, d } = tehranParts();
  return Date.UTC(y, m - 1, d);
}
