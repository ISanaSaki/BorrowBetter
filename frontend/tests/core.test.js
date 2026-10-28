import test from 'node:test';
import assert from 'node:assert/strict';

import { toUtcIso, fromIsoToTehran, hoursBetween, addDaysIso } from '../src/lib/datetime.js';
import { jalaliParts, monthDays, dayLabel, todayCivil } from '../src/lib/jalali.js';
import { validateEmail, validatePassword, validateBookingRange, validateItemForm } from '../src/lib/validate.js';
import { parseHash, buildHash, toQuery } from '../src/lib/query.js';
import { formatMoney, formatRange } from '../src/lib/format.js';

test('Tehran wall clock converts to UTC with a fixed +03:30 offset', () => {
  assert.equal(toUtcIso(2026, 11, 1, 10, 0), '2026-11-01T06:30:00Z');
  assert.equal(toUtcIso(2026, 11, 1, 0, 0), '2026-10-31T20:30:00Z');
});

test('UTC ISO converts back to the same Tehran wall clock', () => {
  const iso = toUtcIso(2026, 11, 2, 14, 30);
  const parts = fromIsoToTehran(iso);
  assert.deepEqual(
    { y: parts.y, m: parts.m, d: parts.d, h: parts.h, minute: parts.minute },
    { y: 2026, m: 11, d: 2, h: 14, minute: 30 },
  );
});

test('hoursBetween is exact for whole days', () => {
  const start = toUtcIso(2026, 11, 1, 10);
  assert.equal(hoursBetween(start, addDaysIso(start, 1)), 24);
});

test('Jalali month grid is contiguous and stays inside the month', () => {
  const { days } = monthDays(1405, 8);
  assert.ok(days.length >= 29 && days.length <= 31);
  const first = jalaliParts(days[0]);
  const last = jalaliParts(days[days.length - 1]);
  assert.equal(first.m, 8);
  assert.equal(first.d, 1);
  assert.equal(last.m, 8);
  assert.equal(last.d, days.length);
});

test('today maps to a valid Jalali triple', () => {
  const parts = jalaliParts(todayCivil());
  assert.ok(parts.y > 1400 && parts.y < 1500);
  assert.ok(parts.m >= 1 && parts.m <= 12);
  assert.ok(parts.d >= 1 && parts.d <= 31);
});

test('dayLabel is Persian and starts with a weekday', () => {
  const label = dayLabel(monthDays(1405, 8).days[0]);
  assert.match(label, /^(شنبه|یکشنبه|دوشنبه|سه‌شنبه|چهارشنبه|پنجشنبه|جمعه) /);
});

test('email validation rejects malformed input', () => {
  assert.equal(validateEmail('a@b.co'), null);
  assert.ok(validateEmail('not-an-email'));
  assert.ok(validateEmail(''));
});

test('password requires 8+ chars with letter and digit', () => {
  assert.equal(validatePassword('Demo1234!'), null);
  assert.ok(validatePassword('short1'));
  assert.ok(validatePassword('allletters'));
  assert.ok(validatePassword('12345678'));
});

test('booking range enforces order, duration and the future', () => {
  const future = new Date(Date.now() + 3 * 86400000);
  const start = future.toISOString();
  const end = new Date(future.getTime() + 4 * 3600000).toISOString();
  assert.equal(validateBookingRange(start, end), null);
  assert.ok(validateBookingRange(end, start));
  assert.ok(validateBookingRange(start, new Date(future.getTime() + 31 * 86400000).toISOString()));
  assert.ok(validateBookingRange(new Date(Date.now() - 86400000).toISOString(), end));
});

test('item form validation mirrors the API limits', () => {
  const valid = { title: 'دریل برقی', description: '', category: 'tools', condition: 'good', price_per_day: 50000, image_url: '' };
  assert.deepEqual(validateItemForm(valid), {});

  const invalid = { ...valid, title: 'ا', price_per_day: -1, category: 'nope' };
  const errors = validateItemForm(invalid);
  assert.ok(errors.title);
  assert.ok(errors.price_per_day);
  assert.ok(errors.category);
});

test('hash routing round-trips paths and queries', () => {
  const parsed = parseHash('#/items/3?tab=all&q=drill');
  assert.equal(parsed.path, '/items/3');
  assert.equal(parsed.query.tab, 'all');
  assert.equal(parsed.query.q, 'drill');

  const built = buildHash('/items', { q: 'دریل', category: 'tools' });
  assert.ok(built.startsWith('#/items?'));
  assert.ok(built.includes('category=tools'));
  assert.equal(toQuery({ a: 1, b: '', c: null }), 'a=1');
});

test('money and range formatting are Persian', () => {
  assert.equal(formatMoney(50000), '۵۰٬۰۰۰');
  const range = formatRange('2026-11-01T06:30:00Z', '2026-11-01T10:30:00Z');
  assert.match(range, /۱۰:۰۰/);
  assert.match(range, /۱۴:۰۰/);
});
