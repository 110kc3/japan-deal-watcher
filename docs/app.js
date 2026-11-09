/**
 * AgyDeal – Japan Deal & Auction Sniping Radar
 * Mobile-First Android PWA & GitHub Pages Application
 */

// Application State
const state = {
  data: null,
  currentView: 'auctions', // 'auctions' | 'mercari'
  selectedCategory: 'all',
  batteryZeroOnly: false,
  sureDealsOnly: false,
  searchQuery: '',
  sortOrder: 'time_asc',
  cart: [],
  activeCalcDeal: null,
  deferredPrompt: null
};

// LocalStorage Cart Key
const CART_STORAGE_KEY = 'agydeal_cart_v2';

// DOM Elements
const elements = {
  feedContainer: document.getElementById('feedContainer'),
  loadingState: document.getElementById('loadingState'),
  categoryPills: document.getElementById('categoryPills'),
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  batteryZeroOnlyToggle: document.getElementById('batteryZeroOnlyToggle'),
  sureDealsOnlyToggle: document.getElementById('sureDealsOnlyToggle'),
  sortSelect: document.getElementById('sortSelect'),
  
  // Ticker
  tickerJpyRate: document.getElementById('tickerJpyRate'),
  tickerStorageDays: document.getElementById('tickerStorageDays'),
  auctionsCountBadge: document.getElementById('auctionsCountBadge'),
  mercariCountBadge: document.getElementById('mercariCountBadge'),
  totalDealsPill: document.getElementById('totalDealsPill'),
  
  // Cart
  cartBadgeCount: document.getElementById('cartBadgeCount'),
  stickyCartBar: document.getElementById('stickyCartBar'),
  barCartCount: document.getElementById('barCartCount'),
  barBatteryText: document.getElementById('barBatteryText'),
  barCartProfit: document.getElementById('barCartProfit'),
  openCartBtn: document.getElementById('openCartBtn'),
  cartBarTrigger: document.getElementById('cartBarTrigger'),
  
  // Calculator Modal
  calcModal: document.getElementById('calcModal'),
  closeCalcBtn: document.getElementById('closeCalcBtn'),
  closeCalcBtnBottom: document.getElementById('closeCalcBtnBottom'),
  calcItemBanner: document.getElementById('calcItemBanner'),
  calcItemTitle: document.getElementById('calcItemTitle'),
  calcItemSub: document.getElementById('calcItemSub'),
  calcBidInput: document.getElementById('calcBidInput'),
  calcBidRange: document.getElementById('calcBidRange'),
  calcBidPlnPreview: document.getElementById('calcBidPlnPreview'),
  calcResaleInput: document.getElementById('calcResaleInput'),
  calcCatSelect: document.getElementById('calcCatSelect'),
  calcAddCartBtn: document.getElementById('calcAddCartBtn'),
  
  // Calc Breakdown
  resRawPln: document.getElementById('resRawPln'),
  resZenFee: document.getElementById('resZenFee'),
  resDepositFee: document.getElementById('resDepositFee'),
  resShippingShare: document.getElementById('resShippingShare'),
  resVatPln: document.getElementById('resVatPln'),
  resTotalLanded: document.getElementById('resTotalLanded'),
  resNetProfit: document.getElementById('resNetProfit'),
  resRoiPct: document.getElementById('resRoiPct'),
  calcVerdictBanner: document.getElementById('calcVerdictBanner'),
  calcVerdictText: document.getElementById('calcVerdictText'),

  // Cart Modal
  cartModal: document.getElementById('cartModal'),
  closeCartBtn: document.getElementById('closeCartBtn'),
  closeCartBtnBottom: document.getElementById('closeCartBtnBottom'),
  clearCartBtn: document.getElementById('clearCartBtn'),
  cartItemsList: document.getElementById('cartItemsList'),
  iataCountLabel: document.getElementById('iataCountLabel'),
  iataProgressFill: document.getElementById('iataProgressFill'),
  iataHintText: document.getElementById('iataHintText'),
  cartStatItems: document.getElementById('cartStatItems'),
  cartStatLanded: document.getElementById('cartStatLanded'),
  cartStatResale: document.getElementById('cartStatResale'),
  cartStatProfit: document.getElementById('cartStatProfit'),

  // PWA Install Button
  installPwaBtn: document.getElementById('installPwaBtn')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  loadSavedCart();
  registerServiceWorker();
  setupPwaInstallPrompt();
  setupEventListeners();
  fetchDealsData();
  handleUrlShortcuts();
});

// Register PWA Service Worker
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js')
      .then((reg) => console.log('[PWA] Service Worker registered:', reg.scope))
      .catch((err) => console.warn('[PWA] Service Worker failed:', err));
  }
}

// Setup PWA "Install App" prompt on Android
function setupPwaInstallPrompt() {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    state.deferredPrompt = e;
    if (elements.installPwaBtn) {
      elements.installPwaBtn.style.display = 'inline-flex';
      elements.installPwaBtn.addEventListener('click', () => {
        elements.installPwaBtn.style.display = 'none';
        state.deferredPrompt.prompt();
        state.deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('[PWA] User accepted the install prompt');
          }
          state.deferredPrompt = null;
        });
      });
    }
  });

  window.addEventListener('appinstalled', () => {
    console.log('[PWA] App successfully installed');
    if (elements.installPwaBtn) elements.installPwaBtn.style.display = 'none';
  });
}

// Fetch compiled data feed from ./data/deals.json
async function fetchDealsData() {
  try {
    const response = await fetch('./data/deals.json?v=' + Date.now());
    if (!response.ok) throw new Error('Network response not ok: ' + response.status);
    const data = await response.json();
    state.data = data;
    renderAppHeader(data.meta);
    renderDeals();
  } catch (error) {
    console.error('Error fetching deals.json:', error);
    elements.feedContainer.innerHTML = `
      <div class="empty-cart-hint">
        <p class="text-red">⚠️ Błąd ładowania danych radaru</p>
        <small>${error.message}. Sprawdź czy plik docs/data/deals.json istnieje.</small>
      </div>
    `;
  }
}

// Render Top Tickers & Header Stats
function renderAppHeader(meta) {
  if (!meta) return;
  const rates = meta.exchange_rates || {};
  if (rates.rate_jpy) {
    elements.tickerJpyRate.textContent = `${(rates.rate_jpy * 100).toFixed(2)} zł`;
  }
  const storage = meta.storage_window || {};
  if (storage.days_remaining !== undefined) {
    elements.tickerStorageDays.textContent = `${storage.days_remaining} dni`;
  }
  const counts = meta.counts || {};
  elements.auctionsCountBadge.textContent = counts.yahoo_auctions || 0;
  elements.mercariCountBadge.textContent = counts.mercari_deals || 0;
  elements.totalDealsPill.textContent = counts.total_active || 0;
}

// Setup Event Listeners
function setupEventListeners() {
  // View Switcher (Auctions vs Mercari vs Calc)
  document.querySelectorAll('.view-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const view = tab.dataset.view;
      if (view === 'calculator') {
        openCalculator();
        return;
      }
      document.querySelectorAll('.view-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      state.currentView = view;
      syncBottomNav(view);
      renderDeals();
    });
  });

  // Bottom Navigation Bar
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', () => {
      const nav = item.dataset.nav;
      if (nav === 'calc') {
        openCalculator();
        return;
      }
      if (nav === 'cart') {
        openCart();
        return;
      }
      document.querySelectorAll('.nav-item').forEach((n) => n.classList.remove('active'));
      item.classList.add('active');
      state.currentView = nav;
      syncTopTabs(nav);
      renderDeals();
    });
  });

  // Search input
  elements.searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    elements.clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';
    renderDeals();
  });

  elements.clearSearchBtn.addEventListener('click', () => {
    elements.searchInput.value = '';
    state.searchQuery = '';
    elements.clearSearchBtn.style.display = 'none';
    renderDeals();
  });

  // Category Pills
  elements.categoryPills.querySelectorAll('.pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      elements.categoryPills.querySelectorAll('.pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.selectedCategory = pill.dataset.cat;
      renderDeals();
    });
  });

  // Battery Zero Only Toggle
  elements.batteryZeroOnlyToggle.addEventListener('change', (e) => {
    state.batteryZeroOnly = e.target.checked;
    renderDeals();
  });

  // Sure Deals (S-Tier & A-Tier) Only Toggle
  if (elements.sureDealsOnlyToggle) {
    elements.sureDealsOnlyToggle.addEventListener('change', (e) => {
      state.sureDealsOnly = e.target.checked;
      renderDeals();
    });
  }

  // Sort Order Select
  elements.sortSelect.addEventListener('change', (e) => {
    state.sortOrder = e.target.value;
    renderDeals();
  });

  // Cart Triggers
  elements.openCartBtn.addEventListener('click', openCart);
  elements.cartBarTrigger.addEventListener('click', openCart);
  elements.closeCartBtn.addEventListener('click', closeCart);
  elements.closeCartBtnBottom.addEventListener('click', closeCart);
  elements.clearCartBtn.addEventListener('click', clearCart);

  // Calculator Triggers
  elements.closeCalcBtn.addEventListener('click', closeCalculator);
  elements.closeCalcBtnBottom.addEventListener('click', closeCalculator);
  elements.calcBidInput.addEventListener('input', (e) => {
    elements.calcBidRange.value = e.target.value;
    runCalculator();
  });
  elements.calcBidRange.addEventListener('input', (e) => {
    elements.calcBidInput.value = e.target.value;
    runCalculator();
  });
  elements.calcResaleInput.addEventListener('input', runCalculator);
  elements.calcCatSelect.addEventListener('change', runCalculator);
  elements.calcAddCartBtn.addEventListener('click', addCalculationToCart);
}

// Sync Navigation states
function syncTopTabs(view) {
  document.querySelectorAll('.view-tab').forEach((t) => {
    t.classList.toggle('active', t.dataset.view === view);
  });
}
function syncBottomNav(view) {
  document.querySelectorAll('.nav-item').forEach((n) => {
    n.classList.toggle('active', n.dataset.nav === view);
  });
}

// URL query parameter shortcuts (PWA manifest launch)
function handleUrlShortcuts() {
  const urlParams = new URLSearchParams(window.location.search);
  const tab = urlParams.get('tab');
  const action = urlParams.get('action');

  if (tab === 'mercari') {
    state.currentView = 'mercari';
    syncTopTabs('mercari');
    syncBottomNav('mercari');
  }
  if (action === 'calc') {
    setTimeout(openCalculator, 300);
  }
  if (action === 'cart') {
    setTimeout(openCart, 300);
  }
}

// ==========================================================================
// Deal Rendering Engine
// ==========================================================================
function renderDeals() {
  if (!state.data) return;

  const isAuctions = state.currentView === 'auctions';
  let deals = isAuctions ? state.data.auctions : state.data.mercari_deals;

  if (!deals || deals.length === 0) {
    elements.feedContainer.innerHTML = `
      <div class="empty-cart-hint">
        <p>Brak ofert w tej sekcji</p>
      </div>
    `;
    return;
  }

  // 1. Filter by Category
  if (state.selectedCategory !== 'all') {
    deals = deals.filter((d) => d.category_id === state.selectedCategory);
  }

  // 2. Filter by Battery (Zero only)
  if (state.batteryZeroOnly) {
    deals = deals.filter((d) => !d.has_battery);
  }

  // 2b. Filter by Sure Deals (S-Tier & A-Tier only)
  if (state.sureDealsOnly) {
    deals = deals.filter((d) => d.verdict_code === 'S_TIER_SURE_ARBITRAGE' || d.verdict_code === 'A_TIER_SOLID_DEAL');
  }

  // 3. Filter by Search Query
  if (state.searchQuery) {
    const q = state.searchQuery;
    deals = deals.filter((d) => {
      const title = (d.model || '').toLowerCase();
      const color = (d.color || '').toLowerCase();
      const note = (d.custom_note || '').toLowerCase();
      const cat = (d.category_name || '').toLowerCase();
      return title.includes(q) || color.includes(q) || note.includes(q) || cat.includes(q);
    });
  }

  // 4. Sort Deals
  deals = sortDealsList(deals, state.sortOrder);

  // 5. Render HTML Cards
  if (deals.length === 0) {
    elements.feedContainer.innerHTML = `
      <div class="empty-cart-hint">
        <p>Brak wyników spełniających wybrane kryteria.</p>
        <small>Spróbuj zmienić filtr kategorii lub wyczyść pole wyszukiwania.</small>
      </div>
    `;
    return;
  }

  elements.feedContainer.innerHTML = deals.map((deal) => renderDealCard(deal, isAuctions)).join('');

  // Attach card event listeners
  attachCardEvents();
}

// Sort deals list helper
function sortDealsList(list, order) {
  const items = [...list];
  switch (order) {
    case 'time_asc':
      return items.sort((a, b) => {
        const timeA = (a.time_remaining_minutes !== undefined && a.time_remaining_minutes !== null) ? a.time_remaining_minutes : 999999;
        const timeB = (b.time_remaining_minutes !== undefined && b.time_remaining_minutes !== null) ? b.time_remaining_minutes : 999999;
        if (timeA !== timeB) {
          return timeA - timeB;
        }
        return (b.est_margin_pln || 0) - (a.est_margin_pln || 0);
      });
    case 'verdict_desc':
      const tierWeight = {
        'S_TIER_SURE_ARBITRAGE': 5,
        'A_TIER_SOLID_DEAL': 4,
        'MERCARI_INSTANT_BUY': 3,
        'B_TIER_MARGINAL': 2,
        'C_TIER_OVERHEATED': 1
      };
      return items.sort((a, b) => {
        const wA = tierWeight[a.verdict_code] || 0;
        const wB = tierWeight[b.verdict_code] || 0;
        if (wB !== wA) return wB - wA;
        return (b.expected_margin_pln || b.est_margin_pln || 0) - (a.expected_margin_pln || a.est_margin_pln || 0);
      });
    case 'pred_margin_desc':
      return items.sort((a, b) => (b.expected_margin_pln || b.est_margin_pln || 0) - (a.expected_margin_pln || a.est_margin_pln || 0));
    case 'margin_desc':
      return items.sort((a, b) => (b.est_margin_pln || 0) - (a.est_margin_pln || 0));
    case 'roi_desc':
      return items.sort((a, b) => (b.roi_percent || 0) - (a.roi_percent || 0));
    case 'price_asc':
      return items.sort((a, b) => (a.price_jpy || 0) - (b.price_jpy || 0));
    case 'discount_desc':
      return items.sort((a, b) => (b.arbitrage_discount_pct || 0) - (a.arbitrage_discount_pct || 0));
    case 'cap_desc':
      return items.sort((a, b) => (b.max_bid_jpy || 0) - (a.max_bid_jpy || 0));
    default:
      return items;
  }
}

// HTML Card Generator
function renderDealCard(deal, isAuction) {
  const isZeroBattery = !deal.has_battery;
  const batteryBadge = isZeroBattery
    ? `<span class="pill-badge battery-zero">🟢 0% Li-Ion</span>`
    : `<span class="pill-badge battery-liion">🔴 1 Li-Ion</span>`;

  const platformTag = isAuction
    ? `<span class="platform-tag">Yahoo! Aukcje</span>`
    : `<span class="platform-tag mercari">Mercari</span>`;

  // Remaining Time & Price Authenticity Ribbon
  let timeRibbon = '';
  if (isAuction) {
    const mins = (deal.time_remaining_minutes !== undefined && deal.time_remaining_minutes !== null) ? deal.time_remaining_minutes : 9999;
    const formatted = deal.time_remaining_formatted || `${mins} min`;
    let timeClass = 'time-ribbon-normal';
    let icon = '⏳';
    let stageTitle = 'Wczesna oferta (cena wzrośnie)';

    if (mins <= 60) {
      timeClass = 'time-ribbon-urgent';
      icon = '🔥';
      stageTitle = 'Faza Końcowa – Prawdziwa cena rynkowa!';
    } else if (mins <= 360) {
      timeClass = 'time-ribbon-soon';
      icon = '⚡';
      stageTitle = 'Ostatnie godziny – Walka snajperów';
    } else if (mins <= 1440) {
      timeClass = 'time-ribbon-medium';
      icon = '⏰';
      stageTitle = 'Średnia faza – Wzrost przed końcem';
    }

    timeRibbon = `
      <div class="time-ribbon ${timeClass}">
        <div class="time-ribbon-left">
          <span class="time-ribbon-icon">${icon}</span>
          <span class="time-ribbon-val">Koniec za: <strong>${formatted}</strong></span>
        </div>
        <div class="time-ribbon-right">
          <span class="time-ribbon-stage">${deal.price_stage_note || stageTitle}</span>
        </div>
      </div>
    `;
  } else {
    timeRibbon = `
      <div class="time-ribbon time-ribbon-mercari">
        <div class="time-ribbon-left">
          <span class="time-ribbon-icon">🛍️</span>
          <span class="time-ribbon-val"><strong>Kup Teraz (Stała Cena)</strong></span>
        </div>
        <div class="time-ribbon-right">
          <span class="time-ribbon-stage">Cena 100% potwierdzona – bez licytacji</span>
        </div>
      </div>
    `;
  }

  // Condition-Aware Prediction & Market Deal Recommendation Box
  let predictionBox = '';
  if (isAuction && deal.predicted_closure_jpy) {
    const gapText = deal.closure_gap_jpy > 0
      ? `+${deal.closure_gap_jpy.toLocaleString()} JPY (+${deal.closure_gap_pct}%)`
      : 'Cena końcowa osiągnięta';
    const gapColor = deal.closure_gap_jpy > 0 ? '#f59e0b' : '#10b981';
    const profitColor = (deal.expected_margin_pln >= 80) ? '#10b981' : ((deal.expected_margin_pln >= 25) ? '#f59e0b' : '#ef4444');

    predictionBox = `
      <div class="prediction-box">
        <div class="prediction-header">
          <div class="prediction-title">
            <span class="prediction-icon">🔮</span>
            <div class="prediction-title-text">
              <span class="pred-sublabel">Oczekiwana Cena Końcowa (落札相場):</span>
              <strong class="prediction-price">${deal.predicted_closure_jpy.toLocaleString()} JPY <small>(~${(deal.predicted_closure_pln || 0).toFixed(0)} zł)</small></strong>
            </div>
          </div>
          <span class="prediction-gap" style="color:${gapColor}; font-weight:600; font-size:0.75rem;">${gapText}</span>
        </div>

        <div class="prediction-stats-row">
          <div class="pred-stat-col">
            <span class="pred-stat-label">Stan / Klasa:</span>
            <span class="pred-stat-val" style="color:${deal.condition_badge_color || '#e2e8f0'}; font-weight:600;">
              ${deal.condition_short_label || 'B. Dobry'}
            </span>
          </div>
          <div class="pred-stat-col">
            <span class="pred-stat-label">Zysk przy Prognozie:</span>
            <span class="pred-stat-val" style="color:${profitColor}; font-weight:700;">
              +${(deal.expected_margin_pln || 0).toFixed(0)} zł (+${(deal.expected_roi_pct || 0).toFixed(0)}%)
            </span>
          </div>
          <div class="pred-stat-col">
            <span class="pred-stat-label">Limit Snajpera:</span>
            <span class="pred-stat-val text-amber font-bold">${(deal.max_sniper_bid_jpy || deal.max_bid_jpy || 0).toLocaleString()} JPY</span>
          </div>
        </div>

        <div class="prediction-verdict ${deal.verdict_badge_class || 'verdict-b-tier'}">
          <div class="verdict-tag">${deal.verdict_label || 'ANALIZA RYNKOWA'}</div>
          <p class="verdict-msg">${deal.recommendation_text || ''}</p>
        </div>
      </div>
    `;
  }

  // Closure Price Banner for Auctions
  let closureBanner = '';
  if (isAuction && deal.closed_price_min_jpy && deal.closed_price_max_jpy) {
    closureBanner = `
      <div class="auction-closure-banner">
        <div>
          <span class="closure-label">Cena zamknięcia (落札相場):</span>
          <span class="closure-range">${deal.closed_price_min_jpy.toLocaleString()} – ${deal.closed_price_max_jpy.toLocaleString()} JPY</span>
        </div>
        ${deal.arbitrage_discount_pct ? `<span class="closure-discount">-${deal.arbitrage_discount_pct}% vs Mercari</span>` : ''}
      </div>
    `;
  }

  // Sniping Cap Banner
  let capBanner = '';
  if (isAuction && deal.max_bid_jpy) {
    capBanner = `
      <div class="cap-banner">
        <span class="cap-title">🎯 Twardy Limit Snajpera:</span>
        <span class="cap-val">${deal.max_bid_jpy.toLocaleString()} JPY</span>
      </div>
    `;
  }

  // Action Buttons with 1-Click Polish Market Verification & Snipers
  let actionButtons = '';
  const allegroBtn = deal.links && deal.links.allegro_search
    ? `<a href="${deal.links.allegro_search}" target="_blank" rel="noopener" class="btn-action allegro-btn">🇵🇱 Allegro Ceny</a>`
    : '';
  const olxBtn = deal.links && deal.links.olx_search
    ? `<a href="${deal.links.olx_search}" target="_blank" rel="noopener" class="btn-action olx-btn">🇵🇱 OLX Oferty</a>`
    : '';

  if (isAuction) {
    actionButtons = `
      <a href="${deal.links.zenmarket_sniper || deal.links.zenmarket_ending_soon}" target="_blank" rel="noopener" class="btn-action primary">
        🎯 Licytuj w ZenMarket
      </a>
      <a href="${deal.links.yahoo_direct || deal.links.yahoo_closed_archive}" target="_blank" rel="noopener" class="btn-action secondary">
        🇯🇵 Yahoo Aukcja
      </a>
      ${allegroBtn}
      ${olxBtn}
      <a href="${deal.links.zenmarket_ending_soon}" target="_blank" rel="noopener" class="btn-action secondary">
        ⏰ Kończące się
      </a>
      <a href="${deal.links.zenmarket_lowest_bid}" target="_blank" rel="noopener" class="btn-action secondary">
        🪙 Od 1 JPY
      </a>
      <a href="${deal.links.yahoo_closed_archive}" target="_blank" rel="noopener" class="btn-action secondary">
        📊 Archiwum Yahoo
      </a>
      <button class="btn-action accent-blue btn-calc-trigger" data-deal-id="${deal.id}" data-type="auction">
        🧮 Przelicz Snajpera
      </button>
      <button class="btn-action secondary full-width btn-add-cart" data-deal-id="${deal.id}" data-type="auction">
        ➕ Dodaj do paczki konsolidacyjnej
      </button>
    `;
  } else {
    const zenStreamBtn = deal.links && deal.links.zenmarket_search_mercari
      ? `<a href="${deal.links.zenmarket_search_mercari}" target="_blank" rel="noopener" class="btn-action secondary">🔍 Strumień Mercari</a>`
      : '';
    const mercLiveBtn = deal.links && deal.links.mercari_live_search
      ? `<a href="${deal.links.mercari_live_search}" target="_blank" rel="noopener" class="btn-action secondary">🇯🇵 Mercari Live</a>`
      : '';

    actionButtons = `
      <a href="${deal.links.zenmarket_buy}" target="_blank" rel="noopener" class="btn-action primary">
        🛒 Kup w ZenMarket
      </a>
      <a href="${deal.links.mercari_direct}" target="_blank" rel="noopener" class="btn-action secondary">
        🇯🇵 Mercari Direct
      </a>
      ${zenStreamBtn}
      ${mercLiveBtn}
      ${allegroBtn}
      ${olxBtn}
      <button class="btn-action accent-blue btn-calc-trigger" data-deal-id="${deal.id}" data-type="mercari">
        🧮 Sprawdź Koszty Landed
      </button>
      <button class="btn-action secondary btn-add-cart" data-deal-id="${deal.id}" data-type="mercari">
        ➕ Do paczki
      </button>
    `;
  }

  // AI Vision Photo Inspection Section (Danshari & Mystery Lots)
  let inspectionSection = '';
  if (deal.photo_inspection && deal.photo_inspection.inspected) {
    const pi = deal.photo_inspection;
    const gems = pi.top_gems || [];
    const gemsHtml = gems.map(g => {
      const barrierBadge = g.language_barrier === 'high' 
        ? '<span class="pill-badge" style="background:rgba(239,68,68,0.2); color:#fca5a5; font-size:0.62rem;" title="100% JP Tekst">⚠️ Tekst JP</span>'
        : (g.language_barrier === 'medium' 
            ? '<span class="pill-badge" style="background:rgba(245,158,11,0.2); color:#fcd34d; font-size:0.62rem;">🇯🇵 Dialogi JP</span>'
            : '<span class="pill-badge" style="background:rgba(16,185,129,0.2); color:#6ee7b7; font-size:0.62rem;">🌐 Brak Bariery</span>');
      
      const alUrl = g.allegro_search_url || `https://allegro.pl/listing?string=${encodeURIComponent(g.title)}+Japonia`;
      const olxUrl = g.olx_search_url || `https://www.olx.pl/oferty/q-${encodeURIComponent(g.title.toLowerCase().replace(/ /g, '-'))}-japonia/`;

      return `
        <div class="gem-badge-row">
          <div class="gem-info-col">
            <span class="gem-title">💎 ${g.title} (${g.platform})</span>
            <div style="display:flex; gap:4px; align-items:center; margin-top:2px;">
              ${barrierBadge}
              <span style="font-size:0.62rem; color:#94a3b8;">${g.rarity || ''}</span>
            </div>
            ${g.language_note ? `<small class="gem-note">${g.language_note}</small>` : ''}
          </div>
          <div class="gem-price-col">
            <span class="gem-val">~${g.est_pl_value} zł</span>
            <div class="gem-links">
              <a href="${alUrl}" target="_blank" rel="noopener" class="gem-link-badge">Allegro ↗</a>
              <a href="${olxUrl}" target="_blank" rel="noopener" class="gem-link-badge">OLX ↗</a>
            </div>
          </div>
        </div>
      `;
    }).join('');

    const breakEvenHtml = pi.break_even_gem
      ? `<div class="inspection-breakeven">💡 ${pi.break_even_gem}</div>`
      : '';

    inspectionSection = `
      <div class="inspection-box">
        <div class="inspection-header" onclick="this.parentElement.classList.toggle('expanded')">
          <div class="inspection-title">
            <span class="inspection-icon">🔍</span>
            <span><strong>Inspekcja Zdjęcia AI:</strong> ${pi.lot_type_name || 'Pakiet'} (${pi.total_items_spotted || 0} szt.)</span>
          </div>
          <span class="inspection-chevron">▼</span>
        </div>
        <div class="inspection-details">
          <div class="inspection-battery">${pi.battery_notes || '🟢 0% Li-Ion'}</div>
          ${breakEvenHtml}
          ${gemsHtml ? `<div class="inspection-gems-list"><strong>Wykryte Skarby w Kartonie (Rygorystyczna Wycena NTSC-J):</strong>${gemsHtml}</div>` : ''}
        </div>
      </div>
    `;
  }

  const allegroPrice = deal.allegro_archive_pln ? deal.allegro_archive_pln.toFixed(0) : Math.round(deal.est_pl_value * 1.08);
  const olxPrice = deal.olx_haggled_pln ? deal.olx_haggled_pln.toFixed(0) : Math.round(deal.est_pl_value * 0.90);
  const isJapaneseGame = (deal.category_id && (deal.category_id.includes('game') || deal.category_id.includes('danshari') || deal.category_id.includes('retro_games'))) || Boolean(deal.photo_inspection);

  return `
    <article class="deal-card" id="card-${deal.id}">
      <div class="deal-card-media">
        <img src="${deal.image_url || './assets/images/placeholder.svg'}" alt="${deal.model}" class="deal-card-img" loading="lazy" onerror="this.src='./assets/images/placeholder.svg'" />
        <span class="media-platform-badge ${isAuction ? 'badge-yahoo' : 'badge-mercari'}">
          ${isAuction ? '🔨 Yahoo! Aukcja' : '🛍️ Mercari'}
        </span>
        ${deal.arbitrage_discount_pct ? `<span class="media-discount-badge">-${deal.arbitrage_discount_pct}% vs BIN</span>` : ''}
        ${isAuction && deal.time_remaining_formatted ? `<span class="media-time-badge ${deal.time_remaining_minutes <= 60 ? 'urgent' : ''}">⏳ ${deal.time_remaining_formatted}</span>` : ''}
      </div>

      <div class="card-header">
        ${platformTag}
        <div class="badge-row">
          ${batteryBadge}
          <span class="pill-badge" style="background:#1e293b; color:#94a3b8;">${deal.condition_badge || 'Sprawny'}</span>
          ${deal.condition_short_label ? `<span class="pill-badge" style="background:rgba(255,255,255,0.06); color:${deal.condition_badge_color || '#38bdf8'}; font-weight:700; border:1px solid ${deal.condition_badge_color || '#38bdf8'}40;">${deal.condition_short_label}</span>` : ''}
        </div>
      </div>

      ${timeRibbon}
      ${predictionBox}

      <div class="card-main">
        <h4 class="card-title">${deal.model}</h4>
        ${deal.color ? `<div class="card-color">${deal.color}</div>` : ''}
        ${isJapaneseGame ? `<div class="ntsc-j-badge">🇯🇵 <strong>Rygorystyczna Wycena NTSC-J:</strong> Wycena uwzględnia barierę językową (gry w kanji w PL są o 50-70% tańsze niż wersje europejskie).</div>` : ''}
        ${deal.custom_note ? `<p class="card-note">${deal.custom_note}</p>` : ''}
      </div>

      ${closureBanner}
      ${capBanner}

      <div class="market-reality-box">
        <div class="reality-metric">
          <span class="reality-label">Allegro Zakończone:</span>
          <span class="reality-val">${allegroPrice} zł</span>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">OLX (po targu):</span>
          <span class="reality-val text-amber">${olxPrice} zł</span>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">Czysty Zysk:</span>
          <span class="reality-val text-emerald font-bold">+${(deal.est_margin_pln || 0).toFixed(0)} zł</span>
        </div>
      </div>

      <div class="profit-matrix">
        <div class="matrix-item">
          <span class="matrix-label">1. Zakup w Japonii:</span>
          <span class="matrix-val">${(deal.price_jpy || 0).toLocaleString()} JPY</span>
          <span class="matrix-sub">~${(deal.price_pln_raw || 0).toFixed(0)} zł</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">2. Koszt Landed (z VAT):</span>
          <span class="matrix-val">~${(deal.landed_cost_pln || 0).toFixed(0)} zł</span>
          <span class="matrix-sub">cło, prowizje & fracht</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">3. Sprzedaż w PL:</span>
          <span class="matrix-val">${(deal.est_pl_value || 0).toFixed(0)} zł</span>
          <span class="matrix-sub">Rygorystyczna wycena</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">4. Zwrot z Inwestycji:</span>
          <span class="matrix-val highlight-green">+${(deal.roi_percent || 0).toFixed(1)}%</span>
          <span class="matrix-sub text-green">Czysty zysk po kosztach</span>
        </div>
      </div>

      ${inspectionSection}

      <div class="card-actions">
        ${actionButtons}
      </div>
    </article>
  `;
}

// Attach Card Buttons Listeners
function attachCardEvents() {
  // Calculator trigger
  document.querySelectorAll('.btn-calc-trigger').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.dealId;
      const type = btn.dataset.type;
      const deal = findDealById(id, type);
      if (deal) openCalculator(deal);
    });
  });

  // Add to cart trigger
  document.querySelectorAll('.btn-add-cart').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.dealId;
      const type = btn.dataset.type;
      const deal = findDealById(id, type);
      if (deal) addToCart(deal);
    });
  });
}

function findDealById(id, type) {
  if (!state.data) return null;
  const list = type === 'auction' ? state.data.auctions : state.data.mercari_deals;
  return list.find((d) => String(d.id) === String(id));
}

// ==========================================================================
// Interactive Sniping Calculator Modal
// ==========================================================================
function openCalculator(deal = null) {
  state.activeCalcDeal = deal;

  if (deal) {
    elements.calcItemTitle.textContent = deal.model;
    elements.calcItemSub.textContent = `${deal.color || ''} | Kat: ${deal.category_name || deal.category_id}`;
    elements.calcBidInput.value = deal.price_jpy || 12000;
    elements.calcBidRange.value = deal.price_jpy || 12000;
    elements.calcResaleInput.value = deal.est_pl_value || 750;
    if (elements.calcCatSelect.querySelector(`option[value="${deal.category_id}"]`)) {
      elements.calcCatSelect.value = deal.category_id;
    }
  } else {
    elements.calcItemTitle.textContent = 'Własna Kalkulacja Snajpera';
    elements.calcItemSub.textContent = 'Wpisz dowolną ofertę i wycenę w Polsce';
  }

  runCalculator();
  elements.calcModal.style.display = 'flex';
}

function closeCalculator() {
  elements.calcModal.style.display = 'none';
}

function runCalculator() {
  const rateJpy = state.data?.meta?.exchange_rates?.rate_jpy || 0.024802;
  const rateEur = state.data?.meta?.exchange_rates?.rate_eur || 4.3873;

  const bidJpy = parseFloat(elements.calcBidInput.value) || 0;
  const resalePln = parseFloat(elements.calcResaleInput.value) || 0;
  const catId = elements.calcCatSelect.value;

  // Category shipping shares
  const shippingShares = {
    nintendo_3ds_handhelds: 30.0,
    nintendo_ds_handhelds: 30.0,
    gameboy_advance_retro: 25.0,
    ps_vita: 35.0,
    psp_handheld: 30.0,
    retro_games_mix: 20.0,
    high_margin_curated_consoles: 65.0,
    film_cameras_point_shoot: 25.0,
    analog_lenses: 25.0,
    ps5_limited_controllers: 30.0
  };
  const shippingShare = shippingShares[catId] || 30.0;

  // Calculations
  const rawPln = bidJpy * rateJpy;
  const zenDomPln = 800 * rateJpy;
  const zenHandlingPln = 2.0 * rateEur;
  const zenTotalFeePln = zenDomPln + zenHandlingPln;

  const subtotalBeforeDep = rawPln + zenTotalFeePln;
  const depositFeePln = subtotalBeforeDep * 0.035;

  const customsTaxBase = subtotalBeforeDep + depositFeePln + shippingShare;
  const vatPln = customsTaxBase * 0.23;

  const totalLandedPln = customsTaxBase + vatPln;
  const netProfitPln = resalePln - totalLandedPln;
  const roiPct = totalLandedPln > 0 ? (netProfitPln / totalLandedPln) * 100 : 0;

  // Update UI
  elements.calcBidPlnPreview.textContent = `~${rawPln.toFixed(0)} zł`;
  elements.resRawPln.textContent = `${rawPln.toFixed(2)} zł`;
  elements.resZenFee.textContent = `~${zenTotalFeePln.toFixed(2)} zł`;
  elements.resDepositFee.textContent = `${depositFeePln.toFixed(2)} zł`;
  elements.resShippingShare.textContent = `${shippingShare.toFixed(2)} zł`;
  elements.resVatPln.textContent = `${vatPln.toFixed(2)} zł`;
  elements.resTotalLanded.textContent = `${totalLandedPln.toFixed(2)} zł`;

  const profitColor = netProfitPln >= 0 ? '#10b981' : '#ef4444';
  elements.resNetProfit.style.color = profitColor;
  elements.resNetProfit.textContent = `${netProfitPln >= 0 ? '+' : ''}${netProfitPln.toFixed(2)} zł`;

  elements.resRoiPct.style.color = profitColor;
  elements.resRoiPct.textContent = `${roiPct >= 0 ? '+' : ''}${roiPct.toFixed(1)}%`;

  // Verdict Banner
  if (netProfitPln > 200 && roiPct >= 35) {
    elements.calcVerdictBanner.className = 'calc-verdict-banner';
    elements.calcVerdictText.innerHTML = `🌟 <strong>BARDZO WYSOKI ZYSK (+${netProfitPln.toFixed(0)} zł, ROI ${roiPct.toFixed(0)}%)!</strong> Warto licytować z twardym limitem.`;
  } else if (netProfitPln > 0 && roiPct >= 20) {
    elements.calcVerdictBanner.className = 'calc-verdict-banner';
    elements.calcVerdictText.innerHTML = `✅ <strong>OPŁACALNE (+${netProfitPln.toFixed(0)} zł)</strong> – Zysk satysfakcjonujący przy paczce konsolidacyjnej.`;
  } else if (netProfitPln > 0) {
    elements.calcVerdictBanner.className = 'calc-verdict-banner danger';
    elements.calcVerdictText.innerHTML = `⚠️ <strong>NISKA MARŻA (+${netProfitPln.toFixed(0)} zł)</strong> – Ryzyko wahań kursu lub prowizji. Nie przekraczaj tego limitu.`;
  } else {
    elements.calcVerdictBanner.className = 'calc-verdict-banner danger';
    elements.calcVerdictText.innerHTML = `🛑 <strong>STRATA (${netProfitPln.toFixed(0)} zł)!</strong> Nie licytuj za tę kwotę – kupno powyżej progu opłacalności.`;
  }
}

function addCalculationToCart() {
  const bidJpy = parseFloat(elements.calcBidInput.value) || 0;
  const resalePln = parseFloat(elements.calcResaleInput.value) || 0;
  const title = state.activeCalcDeal ? state.activeCalcDeal.model : `Własny Snajper (${bidJpy} JPY)`;
  const hasBattery = state.activeCalcDeal ? state.activeCalcDeal.has_battery : true;

  const item = {
    id: 'calc_' + Date.now(),
    model: title,
    price_jpy: bidJpy,
    landed_cost_pln: parseFloat(elements.resTotalLanded.textContent) || 0,
    est_pl_value: resalePln,
    est_margin_pln: parseFloat(elements.resNetProfit.textContent) || 0,
    has_battery: hasBattery
  };

  addToCart(item);
  closeCalculator();
  openCart();
}

// ==========================================================================
// Parcel Consolidation Basket & IATA Battery Meter
// ==========================================================================
function loadSavedCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (raw) state.cart = JSON.parse(raw);
  } catch (e) {
    state.cart = [];
  }
  updateCartBadge();
}

function saveCart() {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(state.cart));
  } catch (e) {
    console.warn('Could not save cart:', e);
  }
  updateCartBadge();
}

function addToCart(deal) {
  // Prevent duplicate additions
  const exists = state.cart.some((it) => String(it.id) === String(deal.id));
  if (exists) {
    showToast(`"${deal.model}" jest już w koszyku!`);
    return;
  }

  state.cart.push(deal);
  saveCart();
  showToast(`Dodano "${deal.model}" do paczki konsolidacyjnej!`);
}

function removeFromCart(id) {
  state.cart = state.cart.filter((it) => String(it.id) !== String(id));
  saveCart();
  renderCartModal();
}

function clearCart() {
  if (confirm('Czy na pewno chcesz wyczyścić cały koszyk konsolidacyjny?')) {
    state.cart = [];
    saveCart();
    renderCartModal();
  }
}

function updateCartBadge() {
  const count = state.cart.length;
  elements.cartBadgeCount.textContent = count;

  if (count > 0) {
    elements.stickyCartBar.style.display = 'block';
    const totalProfit = state.cart.reduce((sum, it) => sum + (it.est_margin_pln || 0), 0);
    const batteryCount = state.cart.filter((it) => it.has_battery).length;

    elements.barCartCount.textContent = `${count} szt.`;
    elements.barCartProfit.textContent = `+${totalProfit.toFixed(0)} zł`;
    elements.barBatteryText.textContent = `Li-Ion: ${batteryCount}/2`;
    elements.barBatteryText.style.color = batteryCount <= 2 ? '#10b981' : '#ef4444';
  } else {
    elements.stickyCartBar.style.display = 'none';
  }
}

function openCart() {
  renderCartModal();
  elements.cartModal.style.display = 'flex';
}

function closeCart() {
  elements.cartModal.style.display = 'none';
}

function renderCartModal() {
  const count = state.cart.length;
  const batteryCount = state.cart.filter((it) => it.has_battery).length;
  const totalLanded = state.cart.reduce((sum, it) => sum + (it.landed_cost_pln || 0), 0);
  const totalResale = state.cart.reduce((sum, it) => sum + (it.est_pl_value || 0), 0);
  const totalProfit = totalResale - totalLanded;

  // IATA Progress Bar
  elements.iataCountLabel.textContent = `${batteryCount} / 2 baterii`;
  const pct = Math.min((batteryCount / 2) * 100, 100);
  elements.iataProgressFill.style.width = `${pct}%`;

  if (batteryCount <= 1) {
    elements.iataCountLabel.className = 'iata-badge safe';
    elements.iataProgressFill.className = 'iata-fill safe';
    elements.iataHintText.innerHTML = `🟢 <strong>BEZPIECZNIE:</strong> Pozostało wolnych slotów na baterie: <strong>${2 - batteryCount}</strong>. Możesz dobrać kolejnego handhelda.`;
  } else if (batteryCount === 2) {
    elements.iataCountLabel.className = 'iata-badge warning';
    elements.iataProgressFill.className = 'iata-fill warning';
    elements.iataHintText.innerHTML = `🟡 <strong>MAKSYMALNY LIMIT IATA OSIĄGNIĘTY (2/2):</strong> Paczka ma komplet ogniw Li-Ion. Dobieraj tylko gry retro, GameCube, obiektywy lub aparaty (0% Li-Ion)!`;
  } else {
    elements.iataCountLabel.className = 'iata-badge danger';
    elements.iataProgressFill.className = 'iata-fill danger';
    elements.iataHintText.innerHTML = `🔴 <strong>ALARM IATA! (${batteryCount}/2):</strong> Przekroczono dopuszczalny limit linii lotniczych! Usuń urządzenia z baterią lub zgłoś do ZenMarketu usunięcie baterii (Dry Shipping).`;
  }

  // Summary Stats
  elements.cartStatItems.textContent = `${count} szt.`;
  elements.cartStatLanded.textContent = `~${totalLanded.toFixed(0)} zł`;
  elements.cartStatResale.textContent = `${totalResale.toFixed(0)} zł`;
  elements.cartStatProfit.textContent = `+${totalProfit.toFixed(0)} zł`;

  // List Items
  if (count === 0) {
    elements.cartItemsList.innerHTML = `
      <div class="empty-cart-hint">
        <p>Twój koszyk konsolidacyjny jest pusty.</p>
        <small>Dodawaj licytacje i oferty z radaru, aby symulować wspólną paczkę!</small>
      </div>
    `;
    return;
  }

  elements.cartItemsList.innerHTML = state.cart.map((item) => `
    <div class="cart-item-row">
      <div class="cart-item-info">
        <strong class="cart-item-title">${item.model}</strong>
        <span class="cart-item-sub">
          Landed: ~${(item.landed_cost_pln || 0).toFixed(0)} zł | Resale: ${(item.est_pl_value || 0).toFixed(0)} zł | 
          ${item.has_battery ? '<span class="text-amber">🔴 Li-Ion</span>' : '<span class="text-green">🟢 0% Baterii</span>'}
        </span>
      </div>
      <div class="cart-item-right">
        <strong class="text-green">+${(item.est_margin_pln || 0).toFixed(0)} zł</strong>
        <button class="btn-remove-item" onclick="removeFromCart('${item.id}')" title="Usuń z koszyka">✕</button>
      </div>
    </div>
  `).join('');
}

// Global Toast Alert Helper
function showToast(message) {
  let toast = document.getElementById('appToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'appToast';
    toast.style.cssText = `
      position: fixed;
      top: 70px;
      left: 50%;
      transform: translateX(-50%);
      background: #1e293b;
      color: #10b981;
      border: 1px solid rgba(16, 185, 129, 0.4);
      padding: 10px 18px;
      border-radius: 20px;
      font-size: 0.84rem;
      font-weight: 700;
      box-shadow: 0 8px 16px rgba(0,0,0,0.5);
      z-index: 999;
      transition: opacity 0.3s ease;
      pointer-events: none;
    `;
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.style.opacity = '1';
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.opacity = '0';
  }, 2400);
}

// Global scope export for inline onclick
window.removeFromCart = removeFromCart;
