/** Catalog: landing page (marketing + list) and the dedicated list page. */

import { html, htmlToString, delegate } from '../lib/html.js';
import { icon } from '../lib/icons.js';
import { formatNumber } from '../lib/format.js';
import { toQuery } from '../lib/query.js';
import { itemsApi } from '../api/endpoints.js';
import { CATEGORIES, CATEGORY_LABEL, PAGE_SIZE, SORT_OPTIONS } from '../constants.js';
import { itemCard } from '../components/item-card.js';
import { emptyState, errorState, skeletonGrid } from '../components/states.js';
import { pagination } from '../components/pagination.js';
import { heroArt } from '../components/art.js';

const CATEGORY_ICONS = { all: 'grid', tools: 'wrench', electronics: 'projector', outdoor: 'tent', household: 'house', other: 'grid' };

const PRICE_OPTIONS = [
  { value: '', label: 'هر قیمتی' },
  { value: '50000', label: 'تا ۵۰ هزار تومان' },
  { value: '100000', label: 'تا ۱۰۰ هزار تومان' },
  { value: '200000', label: 'تا ۲۰۰ هزار تومان' },
  { value: '500000', label: 'تا ۵۰۰ هزار تومان' },
];

export async function render(ctx) {
  const { root, query, path, signal } = ctx;
  const landing = path === '/';
  const state = {
    q: query.q || '',
    category: query.category || 'all',
    priceMax: query.price_max || '',
    sort: query.sort || 'newest',
    page: Number(query.page) || 1,
  };

  root.innerHTML = htmlToString(shell(state, landing));

  const grid = root.querySelector('[data-grid]');
  const paginationHost = root.querySelector('[data-pagination]');
  const countHost = root.querySelector('[data-count]');
  const searchInputs = Array.from(root.querySelectorAll('[data-search]'));

  let requestController = null;
  let debounceTimer = null;

  function syncUrl() {
    const params = {};
    if (state.q.trim()) params.q = state.q.trim();
    if (state.category !== 'all') params.category = state.category;
    if (state.priceMax) params.price_max = state.priceMax;
    if (state.sort !== 'newest') params.sort = state.sort;
    if (state.page > 1) params.page = state.page;
    const qs = toQuery(params);
    history.replaceState(null, '', `#${path}${qs ? `?${qs}` : ''}`);
  }

  function syncCategoryButtons() {
    root.querySelectorAll('[data-cat]').forEach((button) => {
      button.classList.toggle('is-active', button.dataset.cat === state.category);
    });
  }

  function setSearch(value, { immediate = false } = {}) {
    state.q = value;
    searchInputs.forEach((input) => {
      if (input.value !== value) input.value = value;
    });
    clearTimeout(debounceTimer);
    const run = () => {
      state.page = 1;
      syncUrl();
      load();
    };
    if (immediate) run();
    else debounceTimer = setTimeout(run, 320);
  }

  async function load() {
    requestController?.abort();
    requestController = new AbortController();
    const onAbort = () => requestController.abort();
    signal?.addEventListener('abort', onAbort, { once: true });

    if (grid.childElementCount === 0) {
      grid.innerHTML = htmlToString(skeletonGrid(6));
    } else {
      grid.classList.add('is-loading');
    }
    paginationHost.innerHTML = '';

    try {
      const { data, meta } = await itemsApi.list(
        {
          q: state.q.trim() || undefined,
          category: state.category !== 'all' ? state.category : undefined,
          price_max: state.priceMax || undefined,
          sort: state.sort,
          page: state.page,
          limit: PAGE_SIZE,
        },
        requestController.signal,
      );

      renderList(data, meta);
      grid.classList.remove('is-loading');
    } catch (error) {
      if (error?.name === 'AbortError') return;
      grid.classList.remove('is-loading');
      grid.innerHTML = htmlToString(errorState({ message: error.message }));
      grid.querySelector('[data-retry]')?.addEventListener('click', load);
      countHost.textContent = '';
    } finally {
      signal?.removeEventListener('abort', onAbort);
    }
  }

  function renderList(items, meta) {
    countHost.textContent = `${formatNumber(meta?.total ?? items.length)} وسیله`;

    if (!items.length) {
      grid.innerHTML = htmlToString(
        emptyState({
          title: 'چیزی با این فیلترها پیدا نشد',
          text: 'عبارت کوتاه‌تری امتحان کن یا فیلتر دسته و قیمت را بردار.',
          iconName: 'search',
          action: html`<button type="button" class="btn btn-ghost" data-reset>پاک کردن فیلترها</button>`,
        }),
      );
      paginationHost.innerHTML = '';
      return;
    }

    grid.innerHTML = items.map((item) => itemCard(item).toString()).join('');
    paginationHost.innerHTML = htmlToString(
      pagination({ page: meta?.page ?? state.page, totalPages: meta?.total_pages ?? 1, total: meta?.total }),
    );
  }

  function resetFilters() {
    state.q = '';
    state.category = 'all';
    state.priceMax = '';
    state.sort = 'newest';
    state.page = 1;
    searchInputs.forEach((input) => {
      input.value = '';
    });
    root.querySelector('[data-price]').value = '';
    root.querySelector('[data-sort]').value = 'newest';
    syncCategoryButtons();
    syncUrl();
    load();
  }

  delegate(root, 'click', '[data-cat]', (event, button) => {
    state.category = button.dataset.cat;
    state.page = 1;
    syncCategoryButtons();
    syncUrl();
    load();
    if (landing) root.querySelector('#items')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  delegate(root, 'click', '[data-page]', (event, button) => {
    const page = Number(button.dataset.page);
    if (!page) return;
    state.page = page;
    syncUrl();
    load();
    root.querySelector('#items')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  delegate(root, 'click', '[data-reset]', resetFilters);

  root.querySelector('[data-search-form]')?.addEventListener('submit', (event) => {
    event.preventDefault();
    const input = event.currentTarget.querySelector('input');
    setSearch(input.value, { immediate: true });
    root.querySelector('#items')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  searchInputs.forEach((input) => {
    input.addEventListener('input', (event) => setSearch(event.target.value));
  });

  root.querySelector('[data-sort]')?.addEventListener('change', (event) => {
    state.sort = event.target.value;
    state.page = 1;
    syncUrl();
    load();
  });

  root.querySelector('[data-price]')?.addEventListener('change', (event) => {
    state.priceMax = event.target.value;
    state.page = 1;
    syncUrl();
    load();
  });

  await load();

  return () => {
    clearTimeout(debounceTimer);
    requestController?.abort();
  };
}

function shell(state, landing) {
  return html`
    ${landing ? hero(state) : listHeader(state)}
    ${landing ? trustStrip() : ''}

    <section class="section ${landing ? '' : 'section-tight'}" id="items">
      <div class="container">
        ${landing
          ? html`<div class="section-head">
              <div>
                <h2>وسایل محبوب</h2>
                <p>چند وسیلهٔ آماده از همسایه‌های محله، برای شروع.</p>
              </div>
              <div class="section-tools">
                <span class="result-count" data-count></span>
                <a class="link-more" href="#/items">همهٔ وسایل ${icon('arrow')}</a>
              </div>
            </div>`
          : html`<div class="section-head">
              <div>
                <h1 class="page-title">همهٔ وسایل</h1>
                <p>هر چیزی که همسایه‌ها برای امانت گذاشته‌اند.</p>
              </div>
              <span class="result-count" data-count></span>
            </div>`}

        <div class="filter-row">
          <div class="search-inline">
            ${icon('search')}
            <label class="sr-only" for="catalog-search">جست‌وجو در وسایل</label>
            <input id="catalog-search" type="search" data-search placeholder="نام وسیله را بنویس…" value="${state.q}" autocomplete="off">
          </div>

          <div class="chips" role="group" aria-label="دسته‌بندی">
            <button type="button" class="chip ${state.category === 'all' ? 'is-active' : ''}" data-cat="all">همه</button>
            ${CATEGORIES.map(
              (category) => html`
                <button type="button" class="chip ${state.category === category ? 'is-active' : ''}" data-cat="${category}">
                  ${CATEGORY_LABEL[category]}
                </button>
              `,
            )}
          </div>

          <div class="filter-end">
            <label class="select">
              <span class="sr-only">سقف قیمت</span>
              <select data-price>
                ${PRICE_OPTIONS.map(
                  (option) => html`<option value="${option.value}" ${option.value === state.priceMax ? 'selected' : ''}>${option.label}</option>`,
                )}
              </select>
              ${icon('chevron')}
            </label>
            <label class="select">
              <span class="sr-only">مرتب‌سازی</span>
              <select data-sort>
                ${SORT_OPTIONS.map(
                  (option) => html`<option value="${option.value}" ${option.value === state.sort ? 'selected' : ''}>${option.label}</option>`,
                )}
              </select>
              ${icon('chevron')}
            </label>
          </div>
        </div>

        <div class="item-grid" data-grid aria-live="polite"></div>
        <div data-pagination></div>
      </div>
    </section>

    ${landing ? howSection() : ''}
    ${landing ? communitySection() : ''}
  `;
}

function hero(state) {
  return html`
    <section class="hero">
      <div class="container hero-grid">
        <div class="hero-copy">
          <span class="pill">${icon('leaf')} جامعهٔ امانت محلی</span>
          <h1>هر چیزی لازم داری،<br><span class="accent">از همسایه‌ات قرض بگیر.</span></h1>
          <p class="hero-lead">دریل، چادر، چمدان و وسایل روزمره را از همسایه‌هایت اجاره کن؛ کمتر بخر، کمتر دور بریز و جامعهٔ قوی‌تری بساز.</p>

          <form class="hero-search" data-search-form role="search">
            ${icon('search')}
            <label class="sr-only" for="hero-q">جست‌وجو</label>
            <input id="hero-q" type="search" data-search placeholder="دنبال چه وسیله‌ای هستی؟ مثلاً دریل" value="${state.q}" autocomplete="off">
            <button type="submit" class="btn btn-primary">جست‌وجو</button>
          </form>

          <div class="hero-cats" role="group" aria-label="دسته‌بندی وسایل">
            ${['all', ...CATEGORIES].slice(0, 6).map(
              (category) => html`
                <button type="button" class="cat ${state.category === category ? 'is-active' : ''}" data-cat="${category}">
                  <span class="cat-icon">${icon(CATEGORY_ICONS[category] || 'grid')}</span>
                  <span>${category === 'all' ? 'همه' : CATEGORY_LABEL[category]}</span>
                </button>
              `,
            )}
          </div>
        </div>

        <figure class="hero-visual">
          ${heroArt()}
          <img
            class="hero-photo"
            src="img/hero.jpg"
            alt="چادر مسافرتی کنار دریاچه و کوه"
            fetchpriority="high"
            decoding="async"
            data-img-fallback
          >
          <figcaption class="hero-note">${icon('leaf')} چیزهای خوب، بهتر به اشتراک گذاشته می‌شوند</figcaption>
        </figure>
      </div>
    </section>
  `;
}

function listHeader(state) {
  return html`
    <section class="page-head">
      <div class="container">
        <nav class="crumbs" aria-label="مسیر">
          <a href="#/">خانه</a><span>/</span><strong>وسایل</strong>
        </nav>
        <p class="muted page-head-note">${state.q ? `نتایج جست‌وجو برای «${state.q}»` : 'همهٔ وسایل آمادهٔ امانت'}</p>
      </div>
    </section>
  `;
}

function trustStrip() {
  const items = [
    { iconName: 'shield', title: 'صرفه‌جویی در هزینه', text: 'هر چیزی که لازم داری، بدون خرید گران‌قیمت.' },
    { iconName: 'user', title: 'حمایت از جامعه', text: 'همسایه‌ها را به هم وصل می‌کنیم و اعتماد می‌سازیم.' },
    { iconName: 'leaf', title: 'کاهش ضایعات', text: 'کمتر بخر، کمتر دور بریز؛ فردای سبزتر.' },
    { iconName: 'check', title: 'شفاف و قابل‌اعتماد', text: 'هر درخواست، تأیید و تحویل سابقه دارد.' },
  ];
  return html`
    <section class="trust" aria-label="مزیت‌ها">
      <div class="container trust-grid">
        ${items.map(
          (item) => html`
            <div class="trust-item">
              <span class="trust-icon">${icon(item.iconName)}</span>
              <div><h2>${item.title}</h2><p>${item.text}</p></div>
            </div>
          `,
        )}
      </div>
    </section>
  `;
}

function howSection() {
  const steps = [
    { iconName: 'search', title: 'وسیله را پیدا کن', text: 'دسته را بگرد یا نام وسیله را جست‌وجو کن.' },
    { iconName: 'calendar', title: 'بازه را انتخاب کن', text: 'روز و ساعت شروع و پایان را در تقویم شمسی بزن.' },
    { iconName: 'shield', title: 'صاحب وسیله تأیید می‌کند', text: 'درخواستت مستقیم برای صاحب وسیله می‌رود.' },
    { iconName: 'check', title: 'تحویل بگیر و برگردان', text: 'بعد از امانت، بازگشت را ثبت کن تا بازه آزاد شود.' },
  ];
  return html`
    <section class="section how" id="how">
      <div class="container">
        <div class="section-head">
          <div><h2>چطور کار می‌کند</h2><p>چهار قدم ساده تا اولین امانت.</p></div>
        </div>
        <ol class="steps">
          ${steps.map(
            (step, index) => html`
              <li class="step">
                <span class="step-icon">${icon(step.iconName)}</span>
                <span class="step-num">${(index + 1).toLocaleString('fa-IR')}</span>
                <h3>${step.title}</h3>
                <p>${step.text}</p>
              </li>
            `,
          )}
        </ol>
      </div>
    </section>
  `;
}

function communitySection() {
  return html`
    <section class="section" id="community">
      <div class="container community-grid">
        <div class="card community-info">
          <div class="stats-row">
            <div class="stat"><span class="stat-icon">${icon('user')}</span><div><strong>۴</strong><span>همسایهٔ فعال</span></div></div>
            <div class="stat"><span class="stat-icon">${icon('toolbox')}</span><div><strong>۱۲</strong><span>وسیلهٔ آماده</span></div></div>
            <div class="stat"><span class="stat-icon">${icon('leaf')}</span><div><strong>۵</strong><span>دستهٔ وسایل</span></div></div>
          </div>
          <blockquote class="quote">
            <p>«برای سفر آخر هفته چادر و چراغ‌قوه پیدا کردم؛ لازم نبود چیزی بخرم و همسایهٔ طبقهٔ بالا هم از این کار خوشحال شد.»</p>
            <footer>
              <span class="avatar avatar-sm">س</span>
              <div><strong>سارا محمدی</strong><span>کاربر BorrowBetter</span></div>
            </footer>
          </blockquote>
        </div>

        <div class="community-art">
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
          <div class="community-overlay">
            <span class="tag-light">به جامعهٔ ما بپیوند</span>
            <h3>وسایل بهتر، فردای سبزتر.</h3>
            <a class="btn btn-light" href="#/items">دیدن وسایل ${icon('arrow')}</a>
          </div>
        </div>
      </div>
    </section>
  `;
}
