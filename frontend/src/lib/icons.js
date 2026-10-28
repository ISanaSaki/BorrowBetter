/** Inline SVG icons (24×24, stroke-based) — no icon font, no extra requests. */

import { raw } from './html.js';

const PATHS = {
  leaf: '<path d="M20 4c0 8.4-5.4 13-13 13H4.2C4.2 8.6 9.6 4 17.4 4H20z"/><path d="M4.5 19.5C7 15 10.2 11.8 15 9.4"/>',
  search: '<circle cx="11" cy="11" r="6.4"/><path d="M15.8 15.8L20.5 20.5"/>',
  bell: '<path d="M18.2 9.4a6.2 6.2 0 1 0-12.4 0c0 4.8-1.8 6-1.8 6h16s-1.8-1.2-1.8-6"/><path d="M10.4 19.6a1.9 1.9 0 0 0 3.2 0"/>',
  chevron: '<path d="M6.5 9.5L12 15l5.5-5.5"/>',
  chevronLeft: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
  chevronRight: '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
  check: '<path d="M4.5 12.5l5 5 10-11"/>',
  clock: '<circle cx="12" cy="12" r="8.4"/><path d="M12 7.6V12l3 2"/>',
  calendar: '<rect x="3.5" y="5.2" width="17" height="15.3" rx="2.4"/><path d="M8 3.2v4M16 3.2v4M3.5 10.6h17"/>',
  user: '<circle cx="12" cy="8.6" r="3.8"/><path d="M4.6 20.4c1.4-3.6 4-5.4 7.4-5.4s6 1.8 7.4 5.4"/>',
  shield: '<path d="M12 3.2l7 2.9v5.4c0 4.4-3 7.5-7 9.3-4-1.8-7-4.9-7-9.3V6.1z"/><path d="M9 12.2l2 2 4-4.2"/>',
  close: '<path d="M6 6l12 12M18 6L6 18"/>',
  warning: '<path d="M12 3.6L21.4 20H2.6z"/><path d="M12 9.2V14M12 17v.2"/>',
  info: '<circle cx="12" cy="12" r="8.4"/><path d="M12 11v5.4M12 7.8v.2"/>',
  edit: '<path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3z"/><path d="M13.5 6.5l3 3"/>',
  trash: '<path d="M4 7h16M9.5 7V4.8h5V7M6.5 7l1 13h9l1-13"/><path d="M10 11v6M14 11v6"/>',
  logout: '<path d="M14.5 4.5H6a1.5 1.5 0 0 0-1.5 1.5v12A1.5 1.5 0 0 0 6 19.5h8.5"/><path d="M17 8.5l3.5 3.5L17 15.5M20 12h-8"/>',
  wrench: '<path d="M15.6 8.2a3.9 3.9 0 0 1-5.1 5.1L5.4 18.4 3.6 16.6l5.1-5.1a3.9 3.9 0 0 1 5.1-5.1l-2.5 2.5 1.8 1.8 2.5-2.5z"/>',
  tent: '<path d="M2.4 19.8h19.2L12 4.2z"/><path d="M12 19.8v-8.4"/><path d="M9.2 19.8L12 15l2.8 4.8"/>',
  suitcase: '<rect x="2.8" y="7" width="18.4" height="12.6" rx="2.4"/><path d="M9 7V5.4A1.6 1.6 0 0 1 10.6 3.8h2.8A1.6 1.6 0 0 1 15 5.4V7M9.4 19.6v1.6M14.6 19.6v1.6"/>',
  house: '<path d="M3.8 10.6L12 3.8l8.2 6.8v8.4a1.4 1.4 0 0 1-1.4 1.4h-4.2v-6H9.4v6H5.2a1.4 1.4 0 0 1-1.4-1.4z"/>',
  grid: '<rect x="3.6" y="3.6" width="7" height="7" rx="1.6"/><rect x="13.4" y="3.6" width="7" height="7" rx="1.6"/><rect x="3.6" y="13.4" width="7" height="7" rx="1.6"/><rect x="13.4" y="13.4" width="7" height="7" rx="1.6"/>',
  drill: '<rect x="3.4" y="8.2" width="8" height="6.2" rx="1.5"/><path d="M11.4 11.3h8.2M6.4 14.4V19h3"/><path d="M14.2 8.2V5.6h2.6v2.6"/>',
  ladder: '<path d="M8 3v18M16 3v18M8 7h8M8 11.5h8M8 16h8"/>',
  backpack: '<path d="M8 8.6a4 4 0 0 1 8 0V20H8z"/><path d="M5.8 11h12.4v6.6a2.4 2.4 0 0 1-2.4 2.4H8.2a2.4 2.4 0 0 1-2.4-2.4z"/><path d="M9.6 4.6c0 1 .4 1.6 1 2M14.4 4.6c0 1-.4 1.6-1 2M12 13.6v3.2"/>',
  projector: '<rect x="3" y="7.6" width="18" height="8.8" rx="2.4"/><circle cx="16.2" cy="12" r="2.2"/><path d="M20.4 16.4l1.4 2.8M7 7.6V5.2"/>',
  camera: '<path d="M3.4 8.6h3l1.6-2.4h8l1.6 2.4h3v10.2H3.4z"/><circle cx="12" cy="13.6" r="3.4"/>',
  toolbox: '<rect x="3" y="9" width="18" height="11" rx="2"/><path d="M9 9V6.4h6V9M3 13.4h18"/><path d="M10.6 13.4h2.8v3h-2.8z"/>',
  lamp: '<path d="M4 11h9l3.2-3.2v8.4L13 13H4z"/><path d="M17 9l4-1M17 15l4 1M17 12h5"/>',
  dish: '<circle cx="12" cy="12.6" r="7.4"/><circle cx="12" cy="12.6" r="3.6"/><path d="M12 2.4v1.8"/>',
  speaker: '<rect x="6" y="2.8" width="12" height="18.4" rx="3"/><circle cx="12" cy="15" r="3.2"/><circle cx="12" cy="7.6" r="1.2"/>',
  empty: '<path d="M4 7h16v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 12h16"/>',
  spark: '<path d="M12 3l1.9 5.3L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.7z"/>',
  star: '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8L3.5 9.7l5.9-.8z"/>',
  copy: '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 6v8A1.5 1.5 0 0 0 6 15.5h2.5"/>',
};

const CATEGORY_ICON = {
  tools: 'drill',
  electronics: 'projector',
  outdoor: 'tent',
  household: 'dish',
  other: 'grid',
};

export function icon(name, className = '') {
  const path = PATHS[name] || PATHS.grid;
  return raw(`<svg class="icon ${className}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${path}</svg>`);
}

export function categoryIcon(category, className = '') {
  return icon(CATEGORY_ICON[category] || 'grid', className);
}
