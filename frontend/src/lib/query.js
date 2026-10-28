/** URL / hash helpers. The app uses hash routing: #/items/3?tab=all */

export function toQuery(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((entry) => search.append(key, String(entry)));
      return;
    }
    search.set(key, String(value));
  });
  return search.toString();
}

export function parseHash(hash = window.location.hash) {
  const clean = hash.replace(/^#/, '') || '/';
  const [pathPart, searchPart = ''] = clean.split('?');
  const path = pathPart.startsWith('/') ? pathPart : `/${pathPart}`;
  const query = Object.fromEntries(new URLSearchParams(searchPart));
  return { path: path.replace(/\/{2,}/g, '/'), query, search: searchPart };
}

export function buildHash(path, query = {}) {
  const qs = toQuery(query);
  return `#${path}${qs ? `?${qs}` : ''}`;
}

export function parseQueryString(search) {
  return Object.fromEntries(new URLSearchParams(search));
}

export function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
