/** Locked enums and labels (mirror of TEAM-SPEC §4.3). */

export const NAV = [
  { href: '#/', label: 'خانه', match: '/' },
  { href: '#/items', label: 'وسایل', match: '/items' },
  { href: '#/my/requests', label: 'درخواست‌ها', match: '/my/requests', auth: true },
  { href: '#/my/items', label: 'وسایل من', match: '/my/items', auth: true },
];

export const TOKEN_KEY = 'bb_token';
export const USER_KEY = 'bb_user';
export const MOCK_KEY = 'bb_mock';

export const STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  ACTIVE: 'active',
  RETURNED: 'returned',
  REJECTED: 'rejected',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
};

export const STATUSES = Object.values(STATUS);

export const STATUS_LABEL = {
  pending: 'در انتظار تأیید',
  approved: 'تأیید شده',
  active: 'در حال امانت',
  returned: 'بازگشت داده شده',
  rejected: 'رد شده',
  cancelled: 'لغو شده',
  expired: 'منقضی شده',
};

/** Maps to the badge tone classes in styles/components.css */
export const STATUS_TONE = {
  pending: 'warn',
  approved: 'info',
  active: 'ok',
  returned: 'soft',
  rejected: 'danger',
  cancelled: 'soft',
  expired: 'soft',
};

export const TERMINAL_STATUSES = [STATUS.RETURNED, STATUS.REJECTED, STATUS.CANCELLED, STATUS.EXPIRED];

export const BLOCKING_STATUSES = [STATUS.PENDING, STATUS.APPROVED, STATUS.ACTIVE];

export const CATEGORIES = ['tools', 'electronics', 'outdoor', 'household', 'other'];

export const CATEGORY_LABEL = {
  tools: 'ابزار',
  electronics: 'دیجیتال و برق',
  outdoor: 'کمپینگ و فضای باز',
  household: 'خانه و آشپزخانه',
  other: 'سایر',
};

export const CONDITIONS = ['new', 'good', 'fair', 'worn'];

export const CONDITION_LABEL = {
  new: 'نو',
  good: 'در حد نو',
  fair: 'کارکرده',
  worn: 'فرسوده',
};

export const ROLE_LABEL = {
  borrower: 'متقاضی',
  lender: 'صاحب وسیله',
  all: 'همه',
};

export const SORT_OPTIONS = [
  { value: 'newest', label: 'تازه‌ترین' },
  { value: 'price_asc', label: 'ارزان‌ترین' },
  { value: 'price_desc', label: 'گران‌ترین' },
];

export const PAGE_SIZE = 9;

export const FEATURES = {
  // AI is explicitly out of scope for the first release (decision D9).
  ai: false,
};
