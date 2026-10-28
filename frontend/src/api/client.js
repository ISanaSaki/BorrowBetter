/**
 * API client.
 *
 * - Unwraps the `{data, meta}` / `{error}` envelope described in TEAM-SPEC §7.
 * - Sends the JWT from sessionStorage (one session per browser tab — decision D3).
 * - Never rewrites field names: the frontend speaks the backend's snake_case contract.
 */

import { TOKEN_KEY, MOCK_KEY } from '../constants.js';
import { mockRequest } from './mock/index.js';

const env = import.meta.env || {};
export const API_BASE = String(env.VITE_API_BASE || 'http://localhost:8000/api/v1').replace(/\/+$/, '');

export class ApiError extends Error {
  constructor({ code = 'INTERNAL_ERROR', message = 'خطای نامشخص', details = null, status = 0 }) {
    super(localizeMessage(code, message));
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
    this.status = status;
    this.rawMessage = message;
  }
}

/**
 * The API may answer with English messages (the backend keeps some of them in
 * English). The UI is Persian-only, so known codes always get a Persian text;
 * a Persian server message is kept as-is.
 */
const FA_MESSAGES = {
  VALIDATION_ERROR: 'ورودی نامعتبر است. فیلدها را بررسی کن.',
  UNAUTHORIZED: 'برای این کار باید وارد حساب شوی.',
  INVALID_CREDENTIALS: 'ایمیل یا رمز عبور اشتباه است.',
  FORBIDDEN: 'شما به این بخش دسترسی ندارید.',
  CANNOT_BOOK_OWN_ITEM: 'نمی‌توانی وسیلهٔ خودت را رزرو کنی.',
  NOT_FOUND: 'موردی با این شناسه پیدا نشد.',
  EMAIL_ALREADY_EXISTS: 'این ایمیل قبلاً ثبت شده است.',
  SLOT_CONFLICT: 'این بازه قبلاً رزرو شده است. یکی از بازه‌های پیشنهادی را انتخاب کن.',
  INVALID_TRANSITION: 'این درخواست در وضعیت فعلی قابل تغییر نیست.',
  ITEM_INACTIVE: 'این وسیله دیگر برای امانت فعال نیست.',
  ITEM_HAS_ACTIVE_RESERVATIONS: 'ابتدا رزروهای فعال این وسیله را تعیین تکلیف کن.',
  RANGE_TOO_WIDE: 'بازهٔ درخواستی بیش از حد بزرگ است.',
  TIMEOUT: 'پاسخی از سرور نرسید. دوباره تلاش کن.',
  NETWORK_ERROR: 'ارتباط با سرور برقرار نشد.',
  INTERNAL_ERROR: 'خطای غیرمنتظره‌ای رخ داد. دوباره تلاش کن.',
};

function localizeMessage(code, message) {
  if (message && /[\u0600-\u06FF]/.test(message)) return message;
  return FA_MESSAGES[code] || message || FA_MESSAGES.INTERNAL_ERROR;
}

export function getToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** `?mock=1` turns the in-browser mock on for this tab; `?mock=0` turns it off. */
export function isMockEnabled() {
  const param = new URLSearchParams(window.location.search).get('mock');
  try {
    if (param === '1') sessionStorage.setItem(MOCK_KEY, '1');
    if (param === '0') sessionStorage.removeItem(MOCK_KEY);
    return sessionStorage.getItem(MOCK_KEY) === '1';
  } catch {
    return param === '1';
  }
}

function withQuery(path, query) {
  const url = new URLSearchParams();
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    url.set(key, String(value));
  });
  const qs = url.toString();
  return qs ? `${path}?${qs}` : path;
}

function abortError() {
  return new DOMException('Aborted', 'AbortError');
}

async function fetchWithTimeout(url, options, signal, timeoutMs) {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  const forwardAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) {
      clearTimeout(timer);
      throw abortError();
    }
    signal.addEventListener('abort', forwardAbort, { once: true });
  }

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (signal?.aborted) throw abortError();
    if (timedOut) throw new ApiError({ code: 'TIMEOUT', message: 'پاسخی از سرور نرسید. دوباره تلاش کن.' });
    throw new ApiError({ code: 'NETWORK_ERROR', message: 'ارتباط با سرور برقرار نشد.' });
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', forwardAbort);
  }
}

function notifyUnauthorized() {
  window.dispatchEvent(new CustomEvent('bb:unauthorized'));
}

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

/**
 * @param {string} path e.g. "/items/3"
 * @param {{method?: string, body?: object, query?: object, auth?: boolean, signal?: AbortSignal, timeout?: number}} options
 * @returns {Promise<{data: any, meta: any}>}
 */
export async function request(path, { method = 'GET', body, query, auth = true, signal, timeout = 12000 } = {}) {
  const token = auth ? getToken() : null;

  if (isMockEnabled()) {
    const result = await mockRequest({ method, path, query, body, token, signal });
    if (result.status >= 400) {
      const error = result.body?.error || {};
      if (result.status === 401 && auth) notifyUnauthorized();
      throw new ApiError({
        code: error.code || 'INTERNAL_ERROR',
        message: error.message || 'خطا در دریافت داده',
        details: error.details ?? null,
        status: result.status,
      });
    }
    return { data: result.body?.data ?? null, meta: result.body?.meta ?? null };
  }

  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetchWithTimeout(
    `${API_BASE}${withQuery(path, query)}`,
    { method, headers, body: body === undefined ? undefined : JSON.stringify(body) },
    signal,
    timeout,
  );

  const payload = await parseBody(response);

  if (!response.ok) {
    const error = payload?.error || {};
    if (response.status === 401 && auth) notifyUnauthorized();
    throw new ApiError({
      code: error.code || (response.status === 422 ? 'VALIDATION_ERROR' : 'INTERNAL_ERROR'),
      message: error.message || 'درخواست انجام نشد. دوباره تلاش کن.',
      details: error.details ?? null,
      status: response.status,
    });
  }

  return { data: payload?.data ?? null, meta: payload?.meta ?? null };
}
