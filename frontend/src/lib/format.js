/** Number, money and date formatting. All display values are Persian. */

const moneyFormatter = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 });
const numberFormatter = new Intl.NumberFormat('fa-IR');

const dateTimeFormatter = new Intl.DateTimeFormat('fa-IR', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: 'Asia/Tehran',
});

const dateFormatter = new Intl.DateTimeFormat('fa-IR', {
  dateStyle: 'medium',
  timeZone: 'Asia/Tehran',
});

const timeFormatter = new Intl.DateTimeFormat('fa-IR', {
  timeStyle: 'short',
  timeZone: 'Asia/Tehran',
});

export const formatMoney = (value) => moneyFormatter.format(Number(value) || 0);
export const formatNumber = (value) => numberFormatter.format(Number(value) || 0);
export const formatToman = (value) => `${formatMoney(value)} تومان`;

export function formatDateTime(iso) {
  if (!iso) return '—';
  return dateTimeFormatter.format(new Date(iso));
}

export function formatDate(iso) {
  if (!iso) return '—';
  return dateFormatter.format(new Date(iso));
}

export function formatTime(iso) {
  if (!iso) return '—';
  return timeFormatter.format(new Date(iso));
}

/** "۱۰ آبان ۱۴۰۵، ۱۰:۰۰ تا ۱۴:۰۰" or a cross-day range. */
export function formatRange(startIso, endIso) {
  if (!startIso || !endIso) return '—';
  const start = new Date(startIso);
  const end = new Date(endIso);
  const sameDay = dateFormatter.format(start) === dateFormatter.format(end);
  if (sameDay) {
    return `${formatDate(startIso)}، ${timeFormatter.format(start)} تا ${timeFormatter.format(end)}`;
  }
  return `${formatDateTime(startIso)} تا ${formatDateTime(endIso)}`;
}

export function formatRelative(iso, now = Date.now()) {
  if (!iso) return '';
  const diff = now - new Date(iso).getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return 'همین حالا';
  if (minutes < 60) return `${formatNumber(minutes)} دقیقه پیش`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${formatNumber(hours)} ساعت پیش`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${formatNumber(days)} روز پیش`;
  return formatDate(iso);
}
