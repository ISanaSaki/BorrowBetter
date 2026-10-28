/**
 * Mock implementation of the BorrowBetter API (TEAM-SPEC §7).
 * It mirrors the real contract: snake_case, `{data, meta}` envelopes and the
 * same error codes, so switching to the FastAPI backend changes nothing in the UI.
 */

import { loadDb, saveDb, nextId, nowIso } from './db.js';
import { BLOCKING_STATUSES, CATEGORIES, STATUS, STATUS_LABEL } from '../../constants.js';
import { DAY_MS, hoursBetween } from '../../lib/datetime.js';
import {
  LIMITS,
  validateBookingRange,
  validateEmail,
  validateFullName,
  validateItemForm,
  validatePassword,
} from '../../lib/validate.js';

const ok = (data, meta) => ({ status: 200, body: meta ? { data, meta } : { data } });
const created = (data) => ({ status: 201, body: { data } });
const fail = (status, code, message, details = null) => ({ status, body: { error: { code, message, details } } });

const iso = (ms) => new Date(ms).toISOString().replace('.000Z', 'Z');
const toMs = (value) => new Date(value).getTime();
const overlaps = (aStart, aEnd, bStart, bEnd) => toMs(aStart) < toMs(bEnd) && toMs(bStart) < toMs(aEnd);

function userFromToken(db, token) {
  if (!token || !String(token).startsWith('mock:')) return null;
  return db.users.find((user) => user.id === Number(String(token).slice(5))) || null;
}

function userOut(user) {
  return {
    id: user.id,
    email: user.email,
    full_name: user.full_name,
    phone: user.phone ?? null,
    created_at: user.created_at,
  };
}

function ownerOut(user) {
  return user ? { id: user.id, full_name: user.full_name } : null;
}

function itemOut(db, item, withCounts = false) {
  const owner = db.users.find((user) => user.id === item.owner_id);
  const output = { ...item, owner: ownerOut(owner) };
  if (withCounts) {
    const reservations = db.reservations.filter((res) => res.item_id === item.id);
    output.active_reservations_count = reservations.filter((res) => ['approved', 'active'].includes(res.status)).length;
    output.pending_requests_count = reservations.filter((res) => res.status === 'pending').length;
  }
  return output;
}

function itemSummary(item) {
  return {
    id: item.id,
    title: item.title,
    image_url: item.image_url ?? null,
    price_per_day: item.price_per_day,
    owner_id: item.owner_id,
    category: item.category,
    condition: item.condition,
  };
}

function permissionsFor(reservation, item, me) {
  const isLender = Boolean(me && item && item.owner_id === me.id);
  const isBorrower = Boolean(me && reservation.borrower_id === me.id);
  return {
    can_approve: isLender && reservation.status === STATUS.PENDING,
    can_reject: isLender && reservation.status === STATUS.PENDING,
    can_cancel: (isLender || isBorrower) && [STATUS.PENDING, STATUS.APPROVED].includes(reservation.status),
    can_handover: isLender && reservation.status === STATUS.APPROVED,
    can_return: (isLender || isBorrower) && reservation.status === STATUS.ACTIVE,
  };
}

function reservationOut(db, reservation, me) {
  const item = db.items.find((entry) => entry.id === reservation.item_id);
  const borrower = db.users.find((user) => user.id === reservation.borrower_id);
  const lender = item ? db.users.find((user) => user.id === item.owner_id) : null;
  return {
    ...reservation,
    item: item ? itemSummary(item) : null,
    borrower: borrower ? { id: borrower.id, full_name: borrower.full_name, email: borrower.email } : null,
    lender: lender ? { id: lender.id, full_name: lender.full_name, email: lender.email } : null,
    permissions: permissionsFor(reservation, item, me),
  };
}

function blockingReservations(db, itemId) {
  return db.reservations.filter((res) => res.item_id === itemId && BLOCKING_STATUSES.includes(res.status));
}

function expireStale(db) {
  const cutoff = Date.now() - 24 * 3600000;
  let changed = false;
  db.reservations.forEach((res) => {
    if (res.status === STATUS.PENDING && toMs(res.created_at) < cutoff) {
      res.status = STATUS.EXPIRED;
      res.closed_at = nowIso();
      res.updated_at = nowIso();
      changed = true;
    }
  });
  return changed;
}

function buildSuggestions(db, item, startIso, endIso, conflicts) {
  const start = toMs(startIso);
  const end = toMs(endIso);
  const duration = end - start;
  const now = Date.now() - LIMITS.PAST_TOLERANCE_MIN * 60000;
  const blocking = blockingReservations(db, item.id);
  const candidates = [];

  conflicts.forEach((conflict) => {
    const conflictStart = toMs(conflict.start_at);
    const conflictEnd = toMs(conflict.end_at);
    candidates.push([conflictEnd, conflictEnd + duration]);
    candidates.push([conflictStart - duration, conflictStart]);
  });
  candidates.push([start + DAY_MS, end + DAY_MS]);

  const chosen = [];
  candidates.forEach(([candidateStart, candidateEnd]) => {
    if (!Number.isFinite(candidateStart)) return;
    if (candidateStart < now || candidateEnd <= candidateStart) return;
    if (chosen.some((entry) => Math.abs(entry.start - candidateStart) < 60000)) return;
    const candidateIsoStart = iso(candidateStart);
    const candidateIsoEnd = iso(candidateEnd);
    const collides = blocking.some((res) => overlaps(res.start_at, res.end_at, candidateIsoStart, candidateIsoEnd));
    if (collides) return;
    chosen.push({ start: candidateStart, end: candidateEnd });
  });

  chosen.sort((a, b) => Math.abs(a.start - start) - Math.abs(b.start - start));
  return chosen.slice(0, 3).map((entry) => ({ start_at: iso(entry.start), end_at: iso(entry.end) }));
}

function paginate(list, page = 1, limit = 20) {
  const safePage = Math.max(1, Number(page) || 1);
  const safeLimit = Math.min(100, Math.max(1, Number(limit) || 20));
  const total = list.length;
  const totalPages = Math.max(1, Math.ceil(total / safeLimit));
  return {
    data: list.slice((safePage - 1) * safeLimit, safePage * safeLimit),
    meta: {
      page: safePage,
      limit: safeLimit,
      total,
      total_pages: totalPages,
      has_next: safePage < totalPages,
    },
  };
}

/** Availability windows are wider than a booking (up to 90 days, TEAM-SPEC §7.24). */
function availabilityWindowError(fromIso, toIso) {
  const from = toMs(fromIso);
  const to = toMs(toIso);
  if (!Number.isFinite(from) || !Number.isFinite(to) || to <= from) return 'بازهٔ زمانی نامعتبر است.';
  if (to - from > 90 * DAY_MS) return 'بازهٔ درخواستی بیش از ۹۰ روز است.';
  return null;
}

function readOnlyItems(db) {
  return db.items.filter((item) => item.is_active);
}

function matchesQuery(item, query) {
  const q = (query.q || '').trim().toLowerCase();
  if (!q) return true;
  return item.title.toLowerCase().includes(q) || item.description.toLowerCase().includes(q);
}

function sortItems(items, sort) {
  const list = items.slice();
  if (sort === 'price_asc') return list.sort((a, b) => a.price_per_day - b.price_per_day || b.id - a.id);
  if (sort === 'price_desc') return list.sort((a, b) => b.price_per_day - a.price_per_day || b.id - a.id);
  return list.sort((a, b) => toMs(b.created_at) - toMs(a.created_at) || b.id - a.id);
}

function validateItemFields(values) {
  const errors = validateItemForm(values);
  const details = {};
  Object.entries(errors).forEach(([field, message]) => {
    details[field] = message;
  });
  return Object.keys(details).length ? details : null;
}

function applyTransition(reservation, action, body) {
  const stamp = nowIso();
  reservation.updated_at = stamp;

  if (action === 'approve') {
    reservation.status = STATUS.APPROVED;
    reservation.approved_at = stamp;
    reservation.decision_note = body?.decision_note ?? null;
  }
  if (action === 'reject') {
    reservation.status = STATUS.REJECTED;
    reservation.closed_at = stamp;
    reservation.decision_note = body?.decision_note ?? null;
  }
  if (action === 'cancel') {
    reservation.status = STATUS.CANCELLED;
    reservation.closed_at = stamp;
    reservation.cancel_reason = body?.cancel_reason ?? null;
  }
  if (action === 'handover') {
    reservation.status = STATUS.ACTIVE;
    reservation.handover_at = stamp;
  }
  if (action === 'return') {
    reservation.status = STATUS.RETURNED;
    reservation.returned_at = stamp;
    reservation.returned_by = body?.returned_by ?? null;
  }
}

const TRANSITIONS = {
  approve: { from: [STATUS.PENDING], to: STATUS.APPROVED, role: 'lender', verb: 'تأیید' },
  reject: { from: [STATUS.PENDING], to: STATUS.REJECTED, role: 'lender', verb: 'رد' },
  cancel: { from: [STATUS.PENDING, STATUS.APPROVED], to: STATUS.CANCELLED, role: 'both', verb: 'لغو' },
  handover: { from: [STATUS.APPROVED], to: STATUS.ACTIVE, role: 'lender', verb: 'تحویل' },
  return: { from: [STATUS.ACTIVE], to: STATUS.RETURNED, role: 'both', verb: 'بازگرداندن' },
};

export function handleRoute({ method, path, query = {}, body = null, token = null }) {
  const db = loadDb();
  let dirty = expireStale(db);
  const me = userFromToken(db, token);
  const segments = path.split('/').filter(Boolean);
  const now = nowIso();

  const finish = (result) => {
    if (dirty) saveDb(db);
    return result;
  };

  const requireAuth = () => (me ? null : fail(401, 'UNAUTHORIZED', 'برای این کار باید وارد حساب شوی.'));

  /* ------------------------------------------------------------- auth */
  if (method === 'POST' && segments[0] === 'auth' && segments[1] === 'login') {
    const email = String(body?.email || '').trim().toLowerCase();
    const password = String(body?.password || '');
    const user = db.users.find((entry) => entry.email === email);
    if (!user || user.password !== password) {
      return fail(401, 'INVALID_CREDENTIALS', 'ایمیل یا رمز عبور اشتباه است.');
    }
    return finish(ok({ access_token: `mock:${user.id}`, token_type: 'bearer', expires_in: 86400, user: userOut(user) }));
  }

  if (method === 'POST' && segments[0] === 'auth' && segments[1] === 'register') {
    const email = String(body?.email || '').trim().toLowerCase();
    const errors = {};
    const emailError = validateEmail(email);
    const passwordError = validatePassword(body?.password);
    const nameError = validateFullName(body?.full_name);
    if (emailError) errors.email = emailError;
    if (passwordError) errors.password = passwordError;
    if (nameError) errors.full_name = nameError;
    if (Object.keys(errors).length) return fail(422, 'VALIDATION_ERROR', 'ورودی نامعتبر است.', { fields: errors });

    if (db.users.some((entry) => entry.email === email)) {
      return fail(409, 'EMAIL_ALREADY_EXISTS', 'این ایمیل قبلاً ثبت شده است.');
    }

    const user = {
      id: nextId(db, 'user'),
      email,
      password: String(body.password),
      full_name: String(body.full_name).trim(),
      phone: body.phone ? String(body.phone) : null,
      created_at: now,
    };
    db.users.push(user);
    dirty = true;
    return finish(created({ access_token: `mock:${user.id}`, token_type: 'bearer', expires_in: 86400, user: userOut(user) }));
  }

  if (method === 'GET' && segments[0] === 'me' && segments.length === 1) {
    const denied = requireAuth();
    if (denied) return denied;
    return finish(ok(userOut(me)));
  }

  /* -------------------------------------------------------- categories */
  if (method === 'GET' && segments[0] === 'categories') {
    const data = CATEGORIES.map((category) => ({
      value: category,
      count: readOnlyItems(db).filter((item) => item.category === category).length,
    }));
    return finish(ok(data));
  }

  /* ------------------------------------------------------------- items */
  if (method === 'GET' && segments[0] === 'items' && segments.length === 1) {
    let list = readOnlyItems(db);
    if (query.owner_id) list = list.filter((item) => item.owner_id === Number(query.owner_id));
    if (query.category) list = list.filter((item) => item.category === query.category);
    if (query.condition) list = list.filter((item) => item.condition === query.condition);
    if (query.price_max !== undefined && query.price_max !== '') list = list.filter((item) => item.price_per_day <= Number(query.price_max));
    list = list.filter((item) => matchesQuery(item, query));

    if (query.available_from || query.available_to) {
      if (!query.available_from || !query.available_to) {
        return fail(422, 'VALIDATION_ERROR', 'برای فیلتر تاریخ، شروع و پایان بازه لازم است.', {
          fields: { available_to: 'بازهٔ زمانی کامل نیست.' },
        });
      }
      const rangeError = availabilityWindowError(query.available_from, query.available_to);
      if (rangeError) return fail(422, 'VALIDATION_ERROR', rangeError, { fields: { available_from: rangeError } });
      list = list.filter((item) => !blockingReservations(db, item.id).some((res) => overlaps(res.start_at, res.end_at, query.available_from, query.available_to)));
    }

    const sorted = sortItems(list, query.sort);
    const page = paginate(sorted, query.page, query.limit);
    return finish(ok(page.data.map((item) => itemOut(db, item)), page.meta));
  }

  if (method === 'POST' && segments[0] === 'items' && segments.length === 1) {
    const denied = requireAuth();
    if (denied) return denied;
    const payload = {
      title: String(body?.title || '').trim(),
      description: String(body?.description || ''),
      category: body?.category,
      condition: body?.condition || 'good',
      price_per_day: Number(body?.price_per_day ?? 0),
      image_url: body?.image_url ? String(body.image_url) : null,
    };
    const fields = validateItemFields(payload);
    if (fields) return fail(422, 'VALIDATION_ERROR', 'ورودی نامعتبر است.', { fields });

    const item = {
      id: nextId(db, 'item'),
      owner_id: me.id,
      ...payload,
      is_active: true,
      created_at: now,
      updated_at: now,
    };
    db.items.push(item);
    dirty = true;
    return finish(created(itemOut(db, item)));
  }

  if (segments[0] === 'items' && segments[1] && segments.length >= 2) {
    const item = db.items.find((entry) => entry.id === Number(segments[1]));
    if (!item) return finish(fail(404, 'NOT_FOUND', 'وسیله پیدا نشد.'));
    const isOwner = Boolean(me && item.owner_id === me.id);

    if (segments[2] === 'availability' && method === 'GET') {
      const from = query.from || now;
      const to = query.to || iso(toMs(now) + 30 * DAY_MS);
      const rangeError = availabilityWindowError(from, to);
      if (rangeError) return finish(fail(422, 'VALIDATION_ERROR', rangeError, { fields: { from: rangeError } }));
      if (hoursBetween(from, to) > 90 * 24) {
        return finish(fail(422, 'RANGE_TOO_WIDE', 'بازهٔ درخواستی بیش از ۹۰ روز است.', { max_days: 90 }));
      }
      const busy = blockingReservations(db, item.id)
        .filter((res) => overlaps(res.start_at, res.end_at, from, to))
        .sort((a, b) => toMs(a.start_at) - toMs(b.start_at));
      if (busy.length > 100) {
        return finish(fail(422, 'RANGE_TOO_WIDE', 'بازه بیش از حد شلوغ است؛ بازهٔ کوتاه‌تری انتخاب کن.'));
      }
      return finish(ok({
        item_id: item.id,
        from,
        to,
        is_available: busy.length === 0,
        min_duration_hours: LIMITS.MIN_HOURS,
        max_duration_days: LIMITS.MAX_DAYS,
        busy: busy.map((res) => ({ start_at: res.start_at, end_at: res.end_at })),
        server_time: now,
      }));
    }

    if (method === 'GET' && segments.length === 2) {
      if (!item.is_active && !isOwner) return finish(fail(404, 'NOT_FOUND', 'وسیله پیدا نشد.'));
      return finish(ok(itemOut(db, item)));
    }

    if (method === 'PATCH' && segments.length === 2) {
      const denied = requireAuth();
      if (denied) return denied;
      if (!isOwner) return finish(fail(403, 'FORBIDDEN', 'فقط صاحب وسیله می‌تواند آن را ویرایش کند.'));

      const merged = {
        title: body?.title !== undefined ? String(body.title).trim() : item.title,
        description: body?.description !== undefined ? String(body.description) : item.description,
        category: body?.category !== undefined ? body.category : item.category,
        condition: body?.condition !== undefined ? body.condition : item.condition,
        price_per_day: body?.price_per_day !== undefined ? Number(body.price_per_day) : item.price_per_day,
        image_url: body?.image_url !== undefined ? (body.image_url ? String(body.image_url) : null) : item.image_url,
      };
      const fields = validateItemFields(merged);
      if (fields) return finish(fail(422, 'VALIDATION_ERROR', 'ورودی نامعتبر است.', { fields }));

      Object.assign(item, merged);
      if (body?.is_active !== undefined) item.is_active = Boolean(body.is_active);
      item.updated_at = now;
      dirty = true;
      return finish(ok(itemOut(db, item)));
    }

    if (method === 'DELETE' && segments.length === 2) {
      const denied = requireAuth();
      if (denied) return denied;
      if (!isOwner) return finish(fail(403, 'FORBIDDEN', 'فقط صاحب وسیله می‌تواند آن را حذف کند.'));
      if (blockingReservations(db, item.id).length) {
        return finish(fail(409, 'ITEM_HAS_ACTIVE_RESERVATIONS', 'ابتدا رزروهای فعال این وسیله را تعیین تکلیف کن.'));
      }
      item.is_active = false;
      item.updated_at = now;
      dirty = true;
      return finish(ok({ id: item.id, is_active: false }));
    }
  }

  /* --------------------------------------------------------- my items */
  if (method === 'GET' && segments[0] === 'me' && segments[1] === 'items') {
    const denied = requireAuth();
    if (denied) return denied;
    const list = db.items
      .filter((item) => item.owner_id === me.id)
      .sort((a, b) => toMs(b.created_at) - toMs(a.created_at));
    const page = paginate(list, query.page, query.limit || 20);
    return finish(ok(page.data.map((item) => itemOut(db, item, true)), page.meta));
  }

  /* ------------------------------------------------------ reservations */
  if (method === 'POST' && segments[0] === 'reservations' && segments.length === 1) {
    const denied = requireAuth();
    if (denied) return denied;

    const startAt = body?.start_at;
    const endAt = body?.end_at;
    const rangeError = validateBookingRange(startAt, endAt);
    if (rangeError) {
      return fail(422, 'VALIDATION_ERROR', rangeError, {
        fields: { start_at: rangeError, end_at: rangeError },
      });
    }
    if (String(body?.message || '').length > LIMITS.MESSAGE_MAX) {
      return fail(422, 'VALIDATION_ERROR', 'پیام نمی‌تواند بیشتر از ۵۰۰ کاراکتر باشد.', {
        fields: { message: 'حداکثر ۵۰۰ کاراکتر.' },
      });
    }

    const item = db.items.find((entry) => entry.id === Number(body?.item_id));
    if (!item) return finish(fail(404, 'NOT_FOUND', 'وسیله پیدا نشد.'));
    if (!item.is_active) return finish(fail(409, 'ITEM_INACTIVE', 'این وسیله دیگر فعال نیست.'));
    if (item.owner_id === me.id) {
      return finish(fail(403, 'CANNOT_BOOK_OWN_ITEM', 'نمی‌توانی وسیلهٔ خودت را رزرو کنی.'));
    }

    const conflicts = blockingReservations(db, item.id)
      .filter((res) => overlaps(res.start_at, res.end_at, startAt, endAt))
      .sort((a, b) => toMs(a.start_at) - toMs(b.start_at));

    if (conflicts.length) {
      const details = {
        item_id: item.id,
        requested: { start_at: startAt, end_at: endAt },
        conflicts: conflicts.map((res) => ({ start_at: res.start_at, end_at: res.end_at })),
        suggestions: buildSuggestions(db, item, startAt, endAt, conflicts),
      };
      return finish(fail(409, 'SLOT_CONFLICT', 'این بازه قبلاً رزرو شده است. یکی از بازه‌های پیشنهادی را انتخاب کن.', details));
    }

    const hours = hoursBetween(startAt, endAt);
    const days = Math.max(1, Math.ceil(hours / 24));
    const reservation = {
      id: nextId(db, 'reservation'),
      item_id: item.id,
      borrower_id: me.id,
      start_at: startAt,
      end_at: endAt,
      status: STATUS.PENDING,
      total_price: item.price_per_day * days,
      message: body?.message ? String(body.message) : null,
      decision_note: null,
      cancel_reason: null,
      returned_by: null,
      created_at: now,
      updated_at: now,
      approved_at: null,
      handover_at: null,
      returned_at: null,
      closed_at: null,
    };
    db.reservations.push(reservation);
    dirty = true;
    return finish(created(reservationOut(db, reservation, me)));
  }

  if (method === 'GET' && segments[0] === 'me' && segments[1] === 'reservations') {
    const denied = requireAuth();
    if (denied) return denied;
    const role = query.role || 'all';
    let list = db.reservations.filter((res) => {
      if (role === 'borrower') return res.borrower_id === me.id;
      if (role === 'lender') {
        const item = db.items.find((entry) => entry.id === res.item_id);
        return Boolean(item && item.owner_id === me.id);
      }
      const item = db.items.find((entry) => entry.id === res.item_id);
      return res.borrower_id === me.id || Boolean(item && item.owner_id === me.id);
    });
    if (query.status) list = list.filter((res) => res.status === query.status);
    list = list.sort((a, b) => toMs(b.created_at) - toMs(a.created_at));
    const page = paginate(list, query.page, query.limit || 10);
    return finish(ok(page.data.map((res) => reservationOut(db, res, me)), page.meta));
  }

  if (segments[0] === 'reservations' && segments[1]) {
    const reservation = db.reservations.find((res) => res.id === Number(segments[1]));
    if (!reservation) return finish(fail(404, 'NOT_FOUND', 'درخواست پیدا نشد.'));
    const item = db.items.find((entry) => entry.id === reservation.item_id);
    const isOwner = Boolean(me && item && item.owner_id === me.id);
    const isBorrower = Boolean(me && reservation.borrower_id === me.id);

    if (method === 'GET' && segments.length === 2) {
      const denied = requireAuth();
      if (denied) return denied;
      if (!isOwner && !isBorrower) return finish(fail(403, 'FORBIDDEN', 'شما به این رزرو دسترسی ندارید.'));
      return finish(ok(reservationOut(db, reservation, me)));
    }

    if (method === 'POST' && segments[2]) {
      const denied = requireAuth();
      if (denied) return denied;
      const action = segments[2];
      const transition = TRANSITIONS[action];
      if (!transition) return finish(fail(404, 'NOT_FOUND', 'عملیات ناشناخته است.'));

      const allowedRole = transition.role === 'both' ? isOwner || isBorrower : isOwner;
      if (!allowedRole) {
        const message = transition.role === 'both'
          ? 'فقط طرفین این رزرو می‌توانند این کار را انجام دهند.'
          : `فقط صاحب وسیله می‌تواند این درخواست را ${transition.verb} کند.`;
        return finish(fail(403, 'FORBIDDEN', message));
      }

      if (!transition.from.includes(reservation.status)) {
        return finish(fail(409, 'INVALID_TRANSITION', `این درخواست در وضعیت «${STATUS_LABEL[reservation.status]}» است و قابل ${transition.verb} نیست.`, {
          reservation_id: reservation.id,
          current_status: reservation.status,
          attempted_action: action,
        }));
      }

      if (action === 'return' && !['lender', 'borrower'].includes(body?.returned_by)) {
        return finish(fail(422, 'VALIDATION_ERROR', 'مشخص کن وسیله را چه کسی برگرداند.', {
          fields: { returned_by: 'یکی از lender یا borrower لازم است.' },
        }));
      }

      applyTransition(reservation, action, body || {});
      dirty = true;
      return finish(ok(reservationOut(db, reservation, me)));
    }
  }

  return finish(fail(404, 'NOT_FOUND', 'مسیر پیدا نشد.'));
}
