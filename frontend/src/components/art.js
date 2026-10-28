/** Decorative SVG scenes (hero + community banner). Local, tiny, no image requests. */

import { html, raw } from '../lib/html.js';

export function heroArt() {
  return raw(`
    <svg class="hero-scene" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#e8f1e2"/><stop offset="60%" stop-color="#f4f7ea"/><stop offset="1" stop-color="#fbfaf1"/>
        </linearGradient>
        <linearGradient id="lake" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#dfece0"/><stop offset="1" stop-color="#c9ddcb"/>
        </linearGradient>
        <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#7fa073"/><stop offset="1" stop-color="#4e7a55"/>
        </linearGradient>
      </defs>
      <rect width="800" height="600" fill="url(#sky)"/>
      <circle cx="612" cy="146" r="54" fill="#f3e8c8"/>
      <circle cx="612" cy="146" r="78" fill="#f3e8c8" opacity=".28"/>
      <path d="M0 322 L128 196 L206 268 L286 190 L392 322 Z" fill="#cbdcc6"/>
      <path d="M128 196 L168 240 L96 240 Z" fill="#f2f5ea"/>
      <path d="M286 190 L320 228 L252 228 Z" fill="#f2f5ea"/>
      <path d="M330 322 L470 186 L580 288 L668 210 L800 322 Z" fill="#bccfb6"/>
      <path d="M470 186 L506 226 L436 226 Z" fill="#f2f5ea"/>
      <rect y="310" width="800" height="44" fill="#eaf1e4" opacity=".75"/>
      <path d="M0 372 C 110 330, 214 344, 322 384 C 442 428, 596 372, 800 352 L800 600 L0 600 Z" fill="#a7c39d"/>
      <path d="M0 424 C 140 404, 286 440, 436 430 C 590 420, 700 436, 800 426 L800 512 L0 512 Z" fill="url(#lake)"/>
      <g stroke="#bcd4c0" stroke-width="2.4" opacity=".85" stroke-linecap="round">
        <path d="M110 458h118"/><path d="M286 476h84"/><path d="M470 462h132"/><path d="M206 492h96"/><path d="M560 490h110"/>
      </g>
      <path d="M0 508 C 120 486, 250 512, 402 512 C 556 512, 676 492, 800 506 L800 600 L0 600 Z" fill="url(#grass)"/>
      <path d="M0 556 C 172 536, 318 562, 498 554 C 640 548, 716 556, 800 550 L800 600 L0 600 Z" fill="#40694a"/>
      <g fill="#2f5f43">
        <path d="M74 522l24-62 24 62z"/><path d="M104 522l19-46 19 46z"/>
        <path d="M180 530l20-52 20 52z"/>
        <path d="M672 518l22-58 22 58z"/><path d="M702 518l17-42 17 42z"/>
        <path d="M744 528l19-48 19 48z"/>
      </g>
      <g>
        <path d="M404 500 L536 348 L668 500 Z" fill="#1f5f42"/>
        <path d="M494 500 L536 348 L578 500 Z" fill="#15482f"/>
        <path d="M536 348V310" stroke="#15482f" stroke-width="4" stroke-linecap="round"/>
        <path d="M404 500l-24 15M668 500l24 15" stroke="#2f5f43" stroke-width="2.6" stroke-linecap="round"/>
      </g>
      <g fill="#1a5238">
        <rect x="596" y="476" width="26" height="26" rx="3"/>
        <rect x="599" y="470" width="26" height="7" rx="3.5" fill="#2f5f43"/>
      </g>
      <circle cx="609" cy="489" r="5" fill="#f3e8c8"/>
    </svg>
  `);
}

export function communityArt() {
  return raw(`
    <svg class="community-scene" viewBox="0 0 600 460" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <rect width="600" height="460" fill="#14452f"/>
      <circle cx="470" cy="96" r="52" fill="#e9d9a8" opacity=".22"/>
      <path d="M0 300 L120 190 L220 286 L300 206 L400 300 Z" fill="#1c5338" opacity=".75"/>
      <path d="M300 320 L420 200 L520 300 L600 240 L600 460 L0 460 L0 340 Z" fill="#0f3a27"/>
      <path d="M250 360 L330 250 L410 360 Z" fill="#e8f0e2"/>
      <path d="M304 360 L330 250 L356 360 Z" fill="#b9cfb6"/>
      <circle cx="330" cy="392" r="14" fill="#f3e8c8" opacity=".9"/>
      <path d="M214 402h240" stroke="#3d7355" stroke-width="3" stroke-linecap="round"/>
    </svg>
  `);
}

export function heroNote() {
  return html`<span class="hero-note">${'چیزهای خوب، بهتر به اشتراک گذاشته می‌شوند'}</span>`;
}
