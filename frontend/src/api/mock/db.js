/**
 * In-browser demo database (only active with `?mock=1`).
 *
 * The snapshot lives in localStorage so two browser tabs (one per user) share
 * the same data, while the auth token stays in sessionStorage — this is what
 * makes the two-account demo in TEAM-SPEC §1.5 possible.
 */

import { DAY_MS, tehranParts, toUtcIso, addDaysIso, nowIso } from '../../lib/datetime.js';

const DB_KEY = 'bb_mock_db_v2';

function tehranDayIso(offsetDays, hour, minute = 0) {
  const { y, m, d } = tehranParts();
  const civil = new Date(Date.UTC(y, m - 1, d) + offsetDays * DAY_MS);
  return toUtcIso(civil.getUTCFullYear(), civil.getUTCMonth() + 1, civil.getUTCDate(), hour, minute);
}

function seedDb() {
  const now = new Date();
  const createdAt = (daysAgo) => new Date(now.getTime() - daysAgo * DAY_MS).toISOString();

  const users = [
    { id: 1, email: 'sana@demo.ir', password: 'Demo1234!', full_name: 'ثنا کریمی', phone: '09120000001', created_at: createdAt(80) },
    { id: 2, email: 'asra@demo.ir', password: 'Demo1234!', full_name: 'اسرا محمدی', phone: null, created_at: createdAt(60) },
    { id: 3, email: 'shaghayegh@demo.ir', password: 'Demo1234!', full_name: 'شقایق رضایی', phone: null, created_at: createdAt(40) },
    { id: 4, email: 'demo@demo.ir', password: 'Demo1234!', full_name: 'کاربر دمو', phone: null, created_at: createdAt(10) },
  ];

  const items = [
    { id: 1, owner_id: 1, title: 'دریل برقی شارژی', description: 'دریل شارژی ۲۰ ولت با دو باتری، شارژر و کیف حمل؛ مناسب دیوار، چوب و فلز.', category: 'tools', condition: 'good', price_per_day: 50000, image: 'drill.jpg' },
    { id: 2, owner_id: 1, title: 'پیچ‌گوشتی برقی', description: 'پیچ‌گوشتی شارژی با دو باتری و کیف حمل.', category: 'tools', condition: 'good', price_per_day: 30000, image: 'screwdriver.jpg' },
    { id: 3, owner_id: 1, title: 'نردبان آلومینیومی ۴ متری', description: 'نردبان تاشو سبک، مناسب کارهای خانه و تعمیرات.', category: 'tools', condition: 'fair', price_per_day: 40000, image: 'ladder.jpg' },
    { id: 4, owner_id: 2, title: 'جعبه‌ابزار کامل', description: 'آچار، پیچ‌گوشتی، انبردست و متر؛ همه در یک جعبه.', category: 'tools', condition: 'new', price_per_day: 25000, image: 'toolbox.jpg' },
    { id: 5, owner_id: 1, title: 'پروژکتور خانگی', description: 'پروژکتور ۱۰۸۰p با کابل HDMI؛ مناسب فیلم و ارائه.', category: 'electronics', condition: 'good', price_per_day: 90000, image: 'projector.jpg' },
    { id: 6, owner_id: 3, title: 'دوربین عکاسی کانن', description: 'دوربین DSLR با لنز ۱۸–۵۵ و کارت حافظه.', category: 'electronics', condition: 'new', price_per_day: 250000, image: 'camera.jpg' },
    { id: 7, owner_id: 2, title: 'بلندگوی بلوتوثی', description: 'بلندگوی قابل حمل با باتری ۱۲ ساعته.', category: 'electronics', condition: 'good', price_per_day: 20000, image: 'speaker.jpg' },
    { id: 8, owner_id: 1, title: 'چادر مسافرتی ۴ نفره', description: 'چادر ضدآب با اسکلت فلزی و کیف حمل.', category: 'outdoor', condition: 'good', price_per_day: 70000, image: 'tent.jpg' },
    { id: 9, owner_id: 2, title: 'کوله‌پشتی کوهنوردی', description: 'کوله ۶۰ لیتری با باران‌گیر.', category: 'outdoor', condition: 'fair', price_per_day: 35000, image: 'backpack.jpg' },
    { id: 10, owner_id: 1, title: 'چراغ‌قوهٔ کمپینگ', description: 'چراغ‌قوهٔ شارژی با نور قوی و پایهٔ آویز.', category: 'outdoor', condition: 'new', price_per_day: 10000, image: 'lantern.jpg' },
    { id: 11, owner_id: 3, title: 'ماشین لباسشویی', description: 'لباسشویی ۷ کیلویی؛ مناسب اسباب‌کشی یا تعمیرات.', category: 'household', condition: 'good', price_per_day: 300000, image: 'washing-machine.jpg' },
    { id: 12, owner_id: 2, title: 'ست ظروف مهمانی', description: 'ست ظروف یک‌بارمصرف مهمانی همراه با کارد و چنگال چوبی.', category: 'household', condition: 'good', price_per_day: 15000, image: 'dishes.jpg' },
  ].map((item, index) => {
    const { image, ...rest } = item;
    return {
      ...rest,
      image_url: image ? `img/items/${image}` : null,
      is_active: true,
      created_at: createdAt(11 - index),
      updated_at: createdAt(11 - index),
    };
  });

  const reservations = [
    {
      id: 1,
      item_id: 8,
      borrower_id: 2,
      start_at: tehranDayIso(1, 10),
      end_at: tehranDayIso(1, 14),
      status: 'approved',
      total_price: 70000,
      message: 'برای سفر آخر هفته لازمش دارم.',
      decision_note: null,
      cancel_reason: null,
      returned_by: null,
      created_at: createdAt(0.2),
      updated_at: createdAt(0.1),
      approved_at: createdAt(0.1),
      handover_at: null,
      returned_at: null,
      closed_at: null,
    },
    {
      id: 2,
      item_id: 6,
      borrower_id: 2,
      start_at: tehranDayIso(-8, 9),
      end_at: tehranDayIso(-8, 18),
      status: 'returned',
      total_price: 250000,
      message: null,
      decision_note: null,
      cancel_reason: null,
      returned_by: 'borrower',
      created_at: createdAt(10),
      updated_at: createdAt(8),
      approved_at: createdAt(9.5),
      handover_at: createdAt(-8),
      returned_at: createdAt(-8),
      closed_at: null,
    },
    {
      id: 3,
      item_id: 1,
      borrower_id: 3,
      start_at: tehranDayIso(3, 10),
      end_at: tehranDayIso(3, 14),
      status: 'pending',
      total_price: 50000,
      message: 'برای نصب قفسه لازمش دارم.',
      decision_note: null,
      cancel_reason: null,
      returned_by: null,
      created_at: createdAt(0.05),
      updated_at: createdAt(0.05),
      approved_at: null,
      handover_at: null,
      returned_at: null,
      closed_at: null,
    },
  ];

  return { version: 1, seq: { user: 5, item: 13, reservation: 4 }, users, items, reservations };
}

export function loadDb() {
  try {
    const stored = localStorage.getItem(DB_KEY);
    if (stored) return JSON.parse(stored);
  } catch {
    /* corrupted storage falls back to a fresh seed */
  }
  const fresh = seedDb();
  saveDb(fresh);
  return fresh;
}

export function saveDb(db) {
  try {
    localStorage.setItem(DB_KEY, JSON.stringify(db));
  } catch {
    /* storage might be full or disabled; the demo still works in memory */
  }
}

export function resetDb() {
  const fresh = seedDb();
  saveDb(fresh);
  return fresh;
}

export function nextId(db, name) {
  const id = db.seq[name] ?? 1;
  db.seq[name] = id + 1;
  return id;
}

export { DB_KEY, seedDb, addDaysIso, nowIso };
