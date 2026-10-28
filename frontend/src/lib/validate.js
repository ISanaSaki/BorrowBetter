/** Client-side validation mirroring the backend rules (TEAM-SPEC §4, §6.2, §7). */

import { hoursBetween } from './datetime.js';
import { CATEGORIES, CONDITIONS } from '../constants.js';

export const LIMITS = {
  TITLE_MIN: 3,
  TITLE_MAX: 120,
  DESCRIPTION_MAX: 2000,
  MESSAGE_MAX: 500,
  NOTE_MAX: 500,
  PRICE_MAX: 100000000,
  MIN_HOURS: 1,
  MAX_DAYS: 30,
  FUTURE_DAYS: 180,
  PAST_TOLERANCE_MIN: 5,
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateEmail(value) {
  if (!value) return 'ایمیل را وارد کن.';
  if (!EMAIL_RE.test(value)) return 'ایمیل معتبر نیست.';
  return null;
}

export function validatePassword(value) {
  if (!value) return 'رمز عبور را وارد کن.';
  if (value.length < 8) return 'رمز عبور باید حداقل ۸ کاراکتر باشد.';
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) return 'رمز عبور باید هم حرف و هم رقم داشته باشد.';
  return null;
}

export function validateFullName(value) {
  const name = (value || '').trim();
  if (name.length < 2) return 'نام باید حداقل ۲ کاراکتر باشد.';
  if (name.length > 80) return 'نام نمی‌تواند بیشتر از ۸۰ کاراکتر باشد.';
  return null;
}

export function validatePhone(value) {
  if (!value) return null;
  if (!/^0\d{10}$/.test(value)) return 'شمارهٔ موبایل باید ۱۱ رقم و با ۰ شروع شود.';
  return null;
}

/** Item form → { field: message }. */
export function validateItemForm(values) {
  const errors = {};
  const title = (values.title || '').trim();
  if (title.length < LIMITS.TITLE_MIN) errors.title = `عنوان باید حداقل ${LIMITS.TITLE_MIN} کاراکتر باشد.`;
  else if (title.length > LIMITS.TITLE_MAX) errors.title = `عنوان نمی‌تواند بیشتر از ${LIMITS.TITLE_MAX} کاراکتر باشد.`;

  if ((values.description || '').length > LIMITS.DESCRIPTION_MAX) {
    errors.description = `توضیحات نمی‌تواند بیشتر از ${LIMITS.DESCRIPTION_MAX} کاراکتر باشد.`;
  }
  if (!CATEGORIES.includes(values.category)) errors.category = 'دسته را انتخاب کن.';
  if (values.condition && !CONDITIONS.includes(values.condition)) errors.condition = 'وضعیت وسیله معتبر نیست.';

  const price = Number(values.price_per_day);
  if (!Number.isInteger(price) || price < 0) errors.price_per_day = 'قیمت روزانه باید عدد صحیح و بزرگ‌تر از صفر باشد.';
  else if (price > LIMITS.PRICE_MAX) errors.price_per_day = 'قیمت روزانه بیش از حد مجاز است.';

  const imageUrl = (values.image_url || '').trim();
  if (imageUrl && !/^https?:\/\/.+/i.test(imageUrl)) errors.image_url = 'آدرس تصویر باید با http یا https شروع شود.';

  return errors;
}

/** Booking range → Persian message or null when valid. */
export function validateBookingRange(startIso, endIso, now = Date.now()) {  if (!startIso || !endIso) return 'بازه را انتخاب کن.';
  const start = new Date(startIso).getTime();
  const end = new Date(endIso).getTime();
  if (Number.isNaN(start) || Number.isNaN(end)) return 'تاریخ نامعتبر است.';
  if (end <= start) return 'پایان بازه باید بعد از شروع باشد.';

  const hours = hoursBetween(startIso, endIso);
  if (hours < LIMITS.MIN_HOURS) return 'حداقل مدت امانت ۱ ساعت است.';
  if (hours > LIMITS.MAX_DAYS * 24) return 'حداکثر مدت امانت ۳۰ روز است.';
  if (start < now - LIMITS.PAST_TOLERANCE_MIN * 60000) return 'شروع بازه نمی‌تواند در گذشته باشد.';
  if (start > now + LIMITS.FUTURE_DAYS * 86400000) return 'برای بیش از ۱۸۰ روز آینده نمی‌شود رزرو کرد.';
  return null;
}
