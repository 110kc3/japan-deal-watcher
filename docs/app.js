/**
 * AgyDeal – Japan Deal & Auction Sniping Radar
 * Mobile-First Android PWA & GitHub Pages Application
 */

// Application State
const state = {
  data: null,
  currentView: 'auctions', // 'auctions' | 'mercari' | 'search_streams'
  selectedCategory: 'all',
  batteryZeroOnly: false,
  sureDealsOnly: false,
  searchQuery: '',
  sortOrder: 'time_asc',
  cart: [],
  selectedShippingMethod: null, // null = auto recommended ('avia_small_packet' | 'ems_express' | 'surface_sea')
  activeCalcDeal: null,
  deferredPrompt: null
};

// LocalStorage Cart Key
const CART_STORAGE_KEY = 'agydeal_cart_v2';

// Weight and Logistics Configurations
const CATEGORY_WEIGHTS = {
  nintendo_3ds_handhelds: 320,
  nintendo_ds_handhelds: 280,
  gameboy_advance_retro: 200,
  ps_vita: 290,
  ps_vita_handhelds: 290,
  psp_handheld: 260,
  retro_games_mix: 350,
  danshari_mystery_lots: 1800,
  high_margin_curated_consoles: 2500,
  film_cameras_point_shoot: 260,
  analog_lenses: 280,
  ps5_limited_controllers: 380,
  ps_retro_limited_controllers: 320,
  ps1_consoles: 950,
  retro_consoles_no_battery: 2200,
  nintendo_retro: 400
};
const OUTER_BOX_BUFFER_WEIGHT_G = 300;
const AVIA_MAX_WEIGHT_G = 2000;

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
  streamsCountBadge: document.getElementById('streamsCountBadge'),
  totalDealsPill: document.getElementById('totalDealsPill'),
  
  // Cart
  cartBadgeCount: document.getElementById('cartBadgeCount'),
  stickyCartBar: document.getElementById('stickyCartBar'),
  barCartCount: document.getElementById('barCartCount'),
  barWeightText: document.getElementById('barWeightText'),
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

  // Cart Modal & Battery Meter
  cartModal: document.getElementById('cartModal'),
  closeCartBtn: document.getElementById('closeCartBtn'),
  closeCartBtnBottom: document.getElementById('closeCartBtnBottom'),
  clearCartBtn: document.getElementById('clearCartBtn'),
  cartItemsList: document.getElementById('cartItemsList'),
  iataCountLabel: document.getElementById('iataCountLabel'),
  iataProgressFill: document.getElementById('iataProgressFill'),
  iataHintText: document.getElementById('iataHintText'),

  // Package Weight Meter & Limits
  packageWeightLabel: document.getElementById('packageWeightLabel'),
  weightProgressFill: document.getElementById('weightProgressFill'),
  weightHintText: document.getElementById('weightHintText'),
  weightNetVal: document.getElementById('weightNetVal'),
  weightBufferVal: document.getElementById('weightBufferVal'),

  // Shipping Selector
  shippingRecBadge: document.getElementById('shippingRecBadge'),
  shippingTiersGrid: document.getElementById('shippingTiersGrid'),

  // Residual Profit ("Cena, która zostaje")
  residualProfitVal: document.getElementById('residualProfitVal'),
  residualRoiChip: document.getElementById('residualRoiChip'),
  resSumResale: document.getElementById('resSumResale'),
  resSumPurchase: document.getElementById('resSumPurchase'),
  resMethodName: document.getElementById('resMethodName'),
  resShippingCost: document.getElementById('resShippingCost'),
  resTaxCost: document.getElementById('resTaxCost'),
  resSavingsVal: document.getElementById('resSavingsVal'),

  // Stats Grid
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
  initLiveCountdownTicker();
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

// Get safe CDN image URL (bypasses Yahoo Japan European 403 geoblock via secure proxy)
function getSafeImageUrl(url) {
  if (!url) return './assets/images/placeholder.svg';
  if (url.startsWith('https://auc-pctr.c.yimg.jp')) {
    return 'https://www.jauce.com/read_yafile/' + url;
  }
  return url;
}

// Fetch compiled data feed from ./data/deals.json
async function fetchDealsData() {
  try {
    const response = await fetch('./data/deals.json?v=' + Date.now(), { cache: 'no-store' });
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
  const now = Date.now();
  const liveAuctionsCount = (state.data && state.data.auctions)
    ? state.data.auctions.filter((d) => {
        if (!d.ends_at_iso) return (d.time_remaining_minutes !== undefined && d.time_remaining_minutes !== null) ? d.time_remaining_minutes > 0 : true;
        const endsMs = new Date(d.ends_at_iso).getTime();
        return !isNaN(endsMs) && (endsMs > now);
      }).length
    : (counts.yahoo_auctions || 0);

  elements.auctionsCountBadge.textContent = liveAuctionsCount;
  elements.mercariCountBadge.textContent = counts.mercari_deals || 0;
  if (elements.streamsCountBadge) {
    elements.streamsCountBadge.textContent = counts.search_streams || (state.data && state.data.search_streams ? state.data.search_streams.length : 22);
  }
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

  // View 1: Search Streams & Tactical Price Guides
  if (state.currentView === 'search_streams') {
    let streams = state.data.search_streams || [];

    // Filter by Category
    if (state.selectedCategory !== 'all') {
      streams = streams.filter((s) => s.category_id === state.selectedCategory);
    }

    // Filter by Battery (Zero only)
    if (state.batteryZeroOnly) {
      streams = streams.filter((s) => !s.has_battery);
    }

    // Filter by Search Query
    if (state.searchQuery) {
      const q = state.searchQuery;
      streams = streams.filter((s) => {
        const title = (s.model || '').toLowerCase();
        const note = (s.sniping_tip || '').toLowerCase();
        const cat = (s.category_name || '').toLowerCase();
        return title.includes(q) || note.includes(q) || cat.includes(q);
      });
    }

    if (streams.length === 0) {
      elements.feedContainer.innerHTML = `
        <div class="empty-cart-hint">
          <p>Brak strumieni snajpera spełniających wybrane kryteria.</p>
          <small>Zmień filtr kategorii lub wyczyść pole wyszukiwania.</small>
        </div>
      `;
      return;
    }

    elements.feedContainer.innerHTML = streams.map((stream) => renderSearchStreamCard(stream)).join('');
    return;
  }

  // View 2 & 3: Specific Auction Listings (Yahoo) & Specific BIN Listings (Mercari)
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

  // 0. Auto-remove ended/expired auctions (User requirement: no old auctions on the app)
  if (isAuctions) {
    const now = Date.now();
    deals = deals.filter((d) => {
      if (d.time_remaining_minutes !== undefined && d.time_remaining_minutes !== null && d.time_remaining_minutes <= 0) {
        return false;
      }
      if (d.time_remaining_formatted === 'Zakończona') {
        return false;
      }
      if (!d.ends_at_iso) {
        return true;
      }
      const endsMs = new Date(d.ends_at_iso).getTime();
      return !isNaN(endsMs) && (endsMs > now);
    });
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

  // Instantly sync live countdowns to newly rendered DOM nodes
  if (typeof window.updateLiveCountdowns === 'function') {
    window.updateLiveCountdowns();
  }
}

// Sort deals list helper
function sortDealsList(list, order) {
  const items = [...list];
  switch (order) {
    case 'time_asc':
      const now = Date.now();
      return items.sort((a, b) => {
        const timeA = a.ends_at_iso ? new Date(a.ends_at_iso).getTime() : ((a.time_remaining_minutes !== undefined && a.time_remaining_minutes !== null) ? (now + a.time_remaining_minutes * 60000) : Infinity);
        const timeB = b.ends_at_iso ? new Date(b.ends_at_iso).getTime() : ((b.time_remaining_minutes !== undefined && b.time_remaining_minutes !== null) ? (now + b.time_remaining_minutes * 60000) : Infinity);
        const isEndedA = timeA <= now;
        const isEndedB = timeB <= now;

        // Active auctions ALWAYS come first before ended ones!
        if (isEndedA !== isEndedB) {
          return isEndedA ? 1 : -1;
        }

        // Both active: ending soonest comes first
        if (!isEndedA) {
          if (timeA !== timeB) return timeA - timeB;
        } else {
          // Both ended: most recently ended comes first
          if (timeA !== timeB) return timeB - timeA;
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

// ==========================================================================
// Search Stream Card Generator (Category: Search Streams & Short Price Guides)
// ==========================================================================
function renderSearchStreamCard(stream) {
  const isZeroBattery = !stream.has_battery;
  const batteryBadge = isZeroBattery
    ? `<span class="pill-badge battery-zero" title="Brak baterii litowej – dozwolona nielimitowana wysyłka lotnicza">🟢 0% Baterii (Brak limitu IATA)</span>`
    : `<span class="pill-badge battery-liion" title="Zawiera akumulator Li-Ion – limit maks. 2 sztuki na paczkę lotniczą">⚡ Bateria Li-Ion (Maks 2/paczka)</span>`;

  return `
    <article class="deal-card stream-card" id="stream-${stream.id}">
      <div class="stream-card-top">
        <div class="stream-icon-badge">${stream.icon || '🔍'}</div>
        <div class="stream-header-text">
          <div class="stream-meta-row">
            <span class="platform-tag" style="background:#0284c7; color:#fff;">🔍 Strumień Snajpera</span>
            <span class="pill-badge stream-cat-tag">${stream.category_name}</span>
            ${batteryBadge}
          </div>
          <h3 class="stream-title">${stream.model}</h3>
        </div>
      </div>

      <!-- Proper Short Price Guide (4-Grid) -->
      <div class="price-guide-grid">
        <div class="guide-stat-box">
          <span class="guide-stat-label">🎯 Okazja wywoławcza:</span>
          <strong class="guide-stat-val text-amber">${stream.target_start_label || 'od 1 JPY'}</strong>
          <small class="guide-stat-sub">Próg rozpoczęcia licytacji</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">📊 Ceny zamknięcia (落札相場):</span>
          <strong class="guide-stat-val text-sky">${stream.expected_closed_range_jpy}</strong>
          <small class="guide-stat-sub">${stream.expected_closed_range_pln}</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">🛑 Twardy limit opłacalności:</span>
          <strong class="guide-stat-val text-emerald">${stream.hard_cap_label}</strong>
          <small class="guide-stat-sub">Maksymalna oferta snajpera</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">🇵🇱 Realna wycena w Polsce:</span>
          <strong class="guide-stat-val text-purple">${stream.poland_resale_range}</strong>
          <small class="guide-stat-sub">Allegro / OLX po targu</small>
        </div>
      </div>

      <!-- Reality Summary Row -->
      <div class="stream-reality-row">
        <div class="reality-metric">
          <span class="reality-label">Szacowany Zysk Netto w PL:</span>
          <strong class="reality-val text-green font-bold">${stream.est_profit_pln}</strong>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">Średni Zwrot z Inwestycji:</span>
          <strong class="reality-val text-green font-bold">${stream.roi_pct}</strong>
        </div>
      </div>

      <!-- Sniping Tip Box -->
      <div class="stream-tip-box">
        <span class="tip-icon">💡</span>
        <div class="tip-body">
          <strong>Wskazówki Snajpera & Stan Techniczny:</strong>
          <p>${stream.sniping_tip}</p>
        </div>
      </div>

      <!-- Direct 1-Click Action Buttons to Earliest Ending Auctions -->
      <div class="card-action-tiers stream-actions-wrap">
        <!-- Tier 1: Main High-Contrast CTAs -->
        <div class="card-main-ctas">
          <a href="${stream.links.zenmarket_ending_earliest}" target="_blank" rel="noopener" class="btn-action primary-cta" title="Zobacz trwające aukcje posortowane od najmniej czasu do końca (ZenMarket działa w PL bez VPN)">
            <span class="cta-text">⏰ Najszybciej Kończące się (ZenMarket)</span>
            <span class="cta-vpn-badge">Prawdziwe Ceny</span>
          </a>
          <a href="${stream.links.zenmarket_lowest_bid}" target="_blank" rel="noopener" class="btn-action secondary-cta" title="Najtańsze oferty od 1 JPY">
            <span class="cta-text">🪙 Od 1 JPY / Najtańsze</span>
          </a>
        </div>

        <!-- Tier 2: Auxiliary Research & Direct Archives -->
        <div class="card-pills-row">
          <a href="${stream.links.buyee_ending_earliest}" target="_blank" rel="noopener" class="pill-btn" title="Aukcje tego modelu kończące się na Buyee">
            🌐 Buyee Kończące się
          </a>
          <a href="${stream.links.yahoo_closed_archive}" target="_blank" rel="noopener" class="pill-btn" title="Archiwum zakończonych licytacji na Yahoo (落札相場)">
            📊 Archiwum Zamkniętych (落札相場)
          </a>
          <a href="${stream.links.allegro_search}" target="_blank" rel="noopener" class="pill-btn allegro-pill" title="Sprawdź ceny sprzedaży na Allegro w PL">
            🇵🇱 Allegro
          </a>
          <a href="${stream.links.olx_search}" target="_blank" rel="noopener" class="pill-btn olx-pill" title="Sprawdź ogłoszenia na OLX w PL">
            🇵🇱 OLX
          </a>
        </div>
      </div>
    </article>
  `;
}

// Dynamic Auction Timing & Timezone Localization Engine
function getAuctionLiveTiming(deal) {
  const now = Date.now();
  let endsAtMs = null;
  if (deal.ends_at_iso) {
    const parsed = new Date(deal.ends_at_iso).getTime();
    if (!isNaN(parsed)) endsAtMs = parsed;
  }

  if (endsAtMs === null) {
    const mins = (deal.time_remaining_minutes !== undefined && deal.time_remaining_minutes !== null) ? deal.time_remaining_minutes : 9999;
    return {
      isEnded: mins <= 0,
      diffMs: mins * 60000,
      minsRemaining: mins,
      formattedCountdown: deal.time_remaining_formatted || `${mins} min`,
      badgeFormatted: deal.time_remaining_formatted || `${mins} min`,
      timeClass: mins <= 60 ? 'time-ribbon-urgent' : (mins <= 360 ? 'time-ribbon-soon' : 'time-ribbon-normal'),
      icon: mins <= 60 ? '🔥' : (mins <= 360 ? '⚡' : '⏳'),
      stageTitle: deal.price_stage_note || (mins <= 60 ? 'Faza Końcowa – Prawdziwa cena rynkowa!' : 'W toku'),
      clockFormatted: deal.ends_at_formatted ? `⏰ ${deal.ends_at_formatted}` : ''
    };
  }

  const diffMs = endsAtMs - now;
  const isEnded = diffMs <= 0;
  const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
  const minsRemaining = Math.max(0, Math.floor(diffMs / 60000));

  let formattedCountdown = '';
  let badgeFormatted = '';
  let timeClass = 'time-ribbon-normal';
  let icon = '⏳';
  let stageTitle = deal.price_stage_note || 'Średnia faza – Wzrost przed końcem';

  if (isEnded) {
    formattedCountdown = 'Zakończona';
    badgeFormatted = 'Zakończona';
    timeClass = 'time-ribbon-ended';
    icon = '🏁';
    stageTitle = 'Aukcja zakończona (落札終了)';
  } else if (diffMs < 300000) { // < 5 minutes: show dynamic minutes and seconds
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    formattedCountdown = `${m}m ${s < 10 ? '0' : ''}${s}s`;
    badgeFormatted = formattedCountdown;
    timeClass = 'time-ribbon-urgent live-pulse';
    icon = '🔥';
    stageTitle = 'Ostatnie sekundy – Snajper na żywo!';
  } else if (minsRemaining <= 60) {
    formattedCountdown = `${minsRemaining} min`;
    badgeFormatted = `${minsRemaining} min`;
    timeClass = 'time-ribbon-urgent';
    icon = '🔥';
    stageTitle = 'Faza Końcowa – Prawdziwa cena rynkowa!';
  } else if (minsRemaining <= 360) {
    const h = Math.floor(minsRemaining / 60);
    const m = minsRemaining % 60;
    formattedCountdown = m > 0 ? `${h}h ${m}m` : `${h}h`;
    badgeFormatted = formattedCountdown;
    timeClass = 'time-ribbon-soon';
    icon = '⚡';
    stageTitle = 'Ostatnie godziny – Walka snajperów';
  } else if (minsRemaining <= 1440) {
    const h = Math.floor(minsRemaining / 60);
    const m = minsRemaining % 60;
    formattedCountdown = m > 0 ? `${h}h ${m}m` : `${h}h`;
    badgeFormatted = formattedCountdown;
    timeClass = 'time-ribbon-medium';
    icon = '⏰';
    stageTitle = 'Średnia faza – Wzrost przed końcem';
  } else {
    const d = Math.floor(minsRemaining / 1440);
    const remH = Math.floor((minsRemaining % 1440) / 60);
    formattedCountdown = remH > 0 ? `${d}d ${remH}h` : `${d}d`;
    badgeFormatted = formattedCountdown;
    timeClass = 'time-ribbon-normal';
    icon = '🕒';
    stageTitle = 'Wczesna faza – Startowa oferta';
  }

  const clockFormatted = deal.ends_at_formatted ? `⏰ ${deal.ends_at_formatted}` : (deal.ends_at_pl ? `⏰ Dziś o ${deal.ends_at_pl} PL` : '');

  return {
    isEnded,
    diffMs,
    minsRemaining,
    formattedCountdown,
    badgeFormatted,
    timeClass,
    icon,
    stageTitle,
    clockFormatted
  };
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

  // Dynamic Remaining Time & Price Authenticity Ribbon
  let timeRibbon = '';
  let liveTiming = null;
  if (isAuction) {
    liveTiming = getAuctionLiveTiming(deal);
    timeRibbon = `
      <div class="time-ribbon ${liveTiming.timeClass}" data-ends-at="${deal.ends_at_iso || ''}">
        <div class="time-ribbon-left">
          <span class="time-ribbon-icon">${liveTiming.icon}</span>
          <div class="time-ribbon-col">
            <span class="time-ribbon-val">Koniec za: <strong class="auction-countdown-text">${liveTiming.formattedCountdown}</strong></span>
            ${liveTiming.clockFormatted ? `<span class="time-ribbon-clock">${liveTiming.clockFormatted}</span>` : ''}
          </div>
        </div>
        <div class="time-ribbon-right">
          <span class="time-ribbon-stage">${liveTiming.stageTitle}</span>
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

  // Primary Direct URL (ZenMarket works in PL/EEA without VPN)
  const primaryUrl = (deal.links && (deal.links.primary_url || deal.links.zenmarket_sniper || deal.links.zenmarket_buy || deal.links.zenmarket_url)) || '#';
  const endingSoonUrl = (deal.links && deal.links.zenmarket_ending_soon) || primaryUrl;

  // Action Buttons with Clean 3-Tier Mobile Hierarchy (Solves button clutter & geoblocks)
  let actionButtons = '';
  const allegroBtn = deal.links && deal.links.allegro_search
    ? `<a href="${deal.links.allegro_search}" target="_blank" rel="noopener" class="pill-btn allegro-pill" title="Sprawdź archiwalne ceny sprzedaży na Allegro w PL">🇵🇱 Allegro</a>`
    : '';
  const olxBtn = deal.links && deal.links.olx_search
    ? `<a href="${deal.links.olx_search}" target="_blank" rel="noopener" class="pill-btn olx-pill" title="Sprawdź ogłoszenia na OLX w Polsce po targu">🇵🇱 OLX</a>`
    : '';
  const streamPill = (deal.links && deal.links.zenmarket_ending_soon)
    ? `<a href="${deal.links.zenmarket_ending_soon}" target="_blank" rel="noopener" class="pill-btn stream-pill" title="Live stream kończących się licytacji ${deal.model} w ZenMarket (natychmiastowy dostęp w 1-klik)">⚡ Live Stream</a>`
    : '';

  const isAuctionEnded = isAuction && liveTiming && liveTiming.isEnded;
  const auctionTargetUrl = (isAuctionEnded && deal.links && deal.links.zenmarket_ending_soon)
    ? deal.links.zenmarket_ending_soon
    : primaryUrl;
  const cardMainUrl = isAuction
    ? (isAuctionEnded ? endingSoonUrl : primaryUrl)
    : primaryUrl;
  const auctionBuyNowUrl = (isAuctionEnded && deal.links && deal.links.zenmarket_ending_soon)
    ? deal.links.zenmarket_ending_soon
    : ((deal.links && (deal.links.zenmarket_buy_now || deal.links.zenmarket_buy)) || primaryUrl);
  const mercariBuyUrl = (deal.links && (deal.links.zenmarket_buy || deal.links.primary_url)) || primaryUrl;

  const ctaText = isAuctionEnded
    ? '⏰ Szukaj trwających w ZenMarket'
    : (isAuction ? '🎯 Licytuj w ZenMarket' : '🛒 Kup w ZenMarket');

  if (isAuction) {
    actionButtons = `
      <div class="card-action-tiers">
        <!-- Tier 1: Main High-Contrast CTAs (Direct Auction Bidding & Buy Now) -->
        <div class="card-main-ctas">
          <a href="${auctionTargetUrl}" target="_blank" rel="noopener" class="btn-action primary-cta ${isAuctionEnded ? 'cta-ended' : ''}" title="${isAuctionEnded ? 'Aukcja zakończona – otwórz trwające licytacje tego modelu w ZenMarket' : 'Licytuj na tej aukcji bezpośrednio przez ZenMarket (Działa w Polsce i UE bez VPN)'}">
            <span class="cta-text">${ctaText}</span>
            <span class="cta-vpn-badge">${isAuctionEnded ? 'Nowe oferty' : 'Licytacja'}</span>
          </a>
          ${deal.buy_now_price_jpy ? `
            <a href="${auctionBuyNowUrl}" target="_blank" rel="noopener" class="btn-action buy-now-cta" title="${isAuctionEnded ? 'Aukcja zakończona – szukaj ofert Kup Teraz tego modelu w ZenMarket' : 'Kup natychmiast bez licytacji w ZenMarket (Cena 即決: ' + deal.buy_now_price_jpy.toLocaleString() + ' JPY' + (deal.buy_now_price_pln ? ' ~' + deal.buy_now_price_pln.toFixed(2) + ' zł' : '') + ')'}">
              <span class="cta-text">⚡ Kup Teraz (${deal.buy_now_price_jpy.toLocaleString()} JPY)</span>
              <span class="cta-vpn-badge">即決</span>
            </a>
          ` : ''}
          <button class="btn-action secondary-cta btn-add-cart" data-deal-id="${deal.id}" data-type="auction" title="Dodaj do wspólnej paczki morskiej/lotniczej">
            ➕ Do paczki
          </button>
        </div>

        <!-- Prominent Direct Active Auctions Stream Link (Never leads to a dead page) -->
        ${deal.links && deal.links.zenmarket_ending_soon ? `
          <div class="card-active-stream-banner">
            <a href="${deal.links.zenmarket_ending_soon}" target="_blank" rel="noopener" class="active-auctions-search-link" title="Szukaj wszystkich trwających licytacji ${deal.model} w ZenMarket (posortowane od kończących się najszybciej)">
              <span class="active-pulse-dot">🔴</span>
              <span class="active-link-title">Aktywne licytacje: <strong>${deal.model}</strong></span>
              <span class="active-link-badge">ZenMarket ↗</span>
            </a>
          </div>
        ` : ''}

        <!-- Tier 2: Polish Market Verification & Sniping Calculator -->
        <div class="card-pills-row">
          ${allegroBtn}
          ${olxBtn}
          <button class="pill-btn calc-pill btn-calc-trigger" data-deal-id="${deal.id}" data-type="auction" title="Przelicz koszty landed, cło i twardy limit snajpera">
            🧮 Snajper
          </button>
          ${streamPill}
        </div>

        <!-- Tier 3: Collapsible Advanced Research & Proxy Links -->
        <details class="extra-tools-drawer">
          <summary class="extra-tools-summary">
            <span class="summary-label">⚙️ Bezpośrednie linki, archiwa i wyszukiwarki</span>
            <span class="summary-chevron">▾</span>
          </summary>
          <div class="extra-tools-grid">
            <a href="${deal.links.yahoo_direct}" target="_blank" rel="noopener" class="tool-sublink vpn-warn-link" title="Bezpośredni link do tej aukcji na Yahoo Japan – blokowany w UE bez japońskiego VPN">
              🇯🇵 Yahoo Direct (Aukcja) <span class="tag-vpn-alert">⚠️ VPN</span>
            </a>
            ${deal.links.buyee_url ? `
              <a href="${deal.links.buyee_url}" target="_blank" rel="noopener" class="tool-sublink" title="Otwórz tę aukcję na platformie Buyee">
                🌐 Buyee Proxy (Aukcja)
              </a>
            ` : ''}
            <a href="${deal.links.zenmarket_ending_soon}" target="_blank" rel="noopener" class="tool-sublink" title="Inne kończące się aukcje tego modelu w ZenMarket">
              ⏰ Inne kończące się (ZenMarket)
            </a>
            <a href="${deal.links.zenmarket_lowest_bid}" target="_blank" rel="noopener" class="tool-sublink" title="Inne oferty od 1 JPY">
              🪙 Inne od 1 JPY (ZenMarket)
            </a>
            <a href="${deal.links.yahoo_closed_archive}" target="_blank" rel="noopener" class="tool-sublink" title="Archiwum zakończonych licytacji tego przedmiotu na Yahoo (落札相場)">
              📊 Archiwum Yahoo (落札相場)
            </a>
          </div>
        </details>
      </div>
    `;
  } else {
    actionButtons = `
      <div class="card-action-tiers">
        <!-- Tier 1: Main High-Contrast CTAs (Direct Buy Now) -->
        <div class="card-main-ctas">
          <a href="${mercariBuyUrl}" target="_blank" rel="noopener" class="btn-action primary-cta mercari-primary buy-now-cta" title="Kup teraz bezpośrednio przez ZenMarket (Działa w Polsce i UE bez VPN)">
            <span class="cta-text">🛒 Kup Teraz w ZenMarket</span>
            <span class="cta-vpn-badge">Kup Teraz</span>
          </a>
          <button class="btn-action secondary-cta btn-add-cart" data-deal-id="${deal.id}" data-type="mercari" title="Dodaj do wspólnej paczki morskiej/lotniczej">
            ➕ Do paczki
          </button>
        </div>

        <!-- Tier 2: Polish Market Verification & Calculator -->
        <div class="card-pills-row">
          ${allegroBtn}
          ${olxBtn}
          <button class="pill-btn calc-pill btn-calc-trigger" data-deal-id="${deal.id}" data-type="mercari" title="Przelicz koszty landed, cło i marżę">
            🧮 Koszty
          </button>
        </div>

        <!-- Tier 3: Collapsible Advanced Research & Proxy Links -->
        <details class="extra-tools-drawer">
          <summary class="extra-tools-summary">
            <span class="summary-label">⚙️ Więcej linków i wyszukiwarki</span>
            <span class="summary-chevron">▾</span>
          </summary>
          <div class="extra-tools-grid">
            ${deal.links && deal.links.mercari_direct ? `
              <a href="${deal.links.mercari_direct}" target="_blank" rel="noopener" class="tool-sublink" title="Bezpośrednia oferta na japońskim Mercari">
                🏷️ Mercari Direct (Oferta)
              </a>
            ` : ''}
            ${deal.links && deal.links.buyee_url ? `
              <a href="${deal.links.buyee_url}" target="_blank" rel="noopener" class="tool-sublink" title="Otwórz tę ofertę na platformie Buyee">
                🌐 Buyee Proxy (Oferta)
              </a>
            ` : ''}
            ${deal.links && deal.links.zenmarket_search_mercari ? `
              <a href="${deal.links.zenmarket_search_mercari}" target="_blank" rel="noopener" class="tool-sublink" title="Szukaj innych egzemplarzy na Mercari przez ZenMarket">
                🔍 Szukaj na Mercari (ZenMarket)
              </a>
            ` : ''}
            ${deal.links && deal.links.zenmarket_yahoo_search ? `
              <a href="${deal.links.zenmarket_yahoo_search}" target="_blank" rel="noopener" class="tool-sublink" title="Zobacz licytacje tego przedmiotu na Yahoo Aukcjach">
                🔨 Szukaj na Yahoo Aukcjach
              </a>
            ` : ''}
          </div>
        </details>
      </div>
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
    <article class="deal-card ${isAuction && liveTiming && liveTiming.isEnded ? 'deal-card-ended' : ''}" id="card-${deal.id}" data-ends-at="${deal.ends_at_iso || ''}" data-is-auction="${isAuction ? '1' : '0'}" data-is-ended="${isAuction && liveTiming && liveTiming.isEnded ? '1' : '0'}" data-ending-soon-url="${endingSoonUrl}">
      <a href="${cardMainUrl}" target="_blank" rel="noopener" class="deal-card-media deal-card-media-link" title="${isAuctionEnded ? 'Aukcja zakończona – szukaj aktywnych ofert tego modelu w ZenMarket' : 'Otwórz ofertę w ZenMarket (Działa w PL bez VPN)'}">
        <img src="${getSafeImageUrl(deal.image_url)}" alt="${deal.model}" class="deal-card-img" loading="lazy" onerror="this.src='./assets/images/placeholder.svg'" />
        <span class="media-platform-badge ${isAuction ? 'badge-yahoo' : 'badge-mercari'}">
          ${isAuction ? '🔨 Yahoo! Aukcja' : '🛍️ Mercari'}
        </span>
        ${deal.arbitrage_discount_pct ? `<span class="media-discount-badge">-${deal.arbitrage_discount_pct}% vs BIN</span>` : ''}
        ${isAuction && liveTiming ? `<span class="media-time-badge ${liveTiming.minsRemaining <= 60 && !liveTiming.isEnded ? 'urgent' : ''} ${liveTiming.isEnded ? 'badge-ended' : ''}" data-ends-at="${deal.ends_at_iso || ''}">⏳ <span class="badge-countdown-text">${liveTiming.badgeFormatted}</span>${deal.ends_at_pl ? ' (' + deal.ends_at_pl + ')' : ''}</span>` : ''}
        <span class="media-hover-hint">↗ Otwórz w ZenMarket</span>
      </a>

      <div class="card-header">
        ${platformTag}
        <div class="badge-row">
          ${batteryBadge}
          <span class="pill-badge pill-weight" title="Szacowana waga przedmiotu">⚖️ ${deal.weight_formatted || (deal.est_weight_g ? deal.est_weight_g + ' g' : '~300 g')}</span>
          <span class="pill-badge" style="background:#1e293b; color:#94a3b8;">${deal.condition_badge || 'Sprawny'}</span>
          ${deal.condition_short_label ? `<span class="pill-badge" style="background:rgba(255,255,255,0.06); color:${deal.condition_badge_color || '#38bdf8'}; font-weight:700; border:1px solid ${deal.condition_badge_color || '#38bdf8'}40;">${deal.condition_short_label}</span>` : ''}
          ${isAuction && liveTiming && liveTiming.isEnded ? `<span class="pill-badge" style="background:rgba(239,68,68,0.2); color:#fca5a5; border:1px solid rgba(239,68,68,0.4); font-weight:700;">🏁 Zakończona</span>` : ''}
        </div>
      </div>

      ${timeRibbon}
      ${predictionBox}

      <div class="card-main">
        <h4 class="card-title">
          <a href="${cardMainUrl}" target="_blank" rel="noopener" class="card-title-link" title="${isAuctionEnded ? 'Aukcja zakończona – szukaj aktywnych ofert tego modelu w ZenMarket' : 'Otwórz ofertę w ZenMarket'}">
            <span class="title-text">${deal.model}</span>
            <span class="title-icon">↗</span>
          </a>
        </h4>
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
  const catId = elements.calcCatSelect ? elements.calcCatSelect.value : (state.activeCalcDeal ? state.activeCalcDeal.category_id : 'nintendo_3ds_handhelds');
  const weightG = state.activeCalcDeal && state.activeCalcDeal.est_weight_g ? state.activeCalcDeal.est_weight_g : (CATEGORY_WEIGHTS[catId] || 300);

  const item = {
    id: 'calc_' + Date.now(),
    model: title,
    category_id: catId,
    price_jpy: bidJpy,
    est_weight_g: weightG,
    weight_formatted: weightG < 1000 ? `~${weightG} g` : `~${(weightG / 1000).toFixed(1)} kg`,
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
// Parcel Consolidation Basket, Package Weight Analysis & Residual Profit
// ==========================================================================
function getItemWeight(item) {
  if (item && item.est_weight_g && Number(item.est_weight_g) > 0) {
    return Number(item.est_weight_g);
  }
  const cat = (item && item.category_id) || '';
  if (cat && CATEGORY_WEIGHTS[cat]) {
    return CATEGORY_WEIGHTS[cat];
  }
  const name = (item && (item.model || item.name || '')).toLowerCase();
  if (name.includes('3ds ll') || name.includes('new 3ds')) return 320;
  if (name.includes('ds lite')) return 220;
  if (name.includes('dsi ll')) return 315;
  if (name.includes('vita')) return 290;
  if (name.includes('psp')) return 260;
  if (name.includes('danshari') || name.includes('mystery') || name.includes('karton')) return 1800;
  if (name.includes('ps4') || name.includes('ps1')) return 1500;
  return 300;
}

function calculateCartPackageWeight(cartItems) {
  if (!cartItems || cartItems.length === 0) {
    return {
      itemCount: 0,
      netWeightG: 0,
      boxBufferG: 0,
      totalWeightG: 0,
      totalWeightKg: '0.00',
      isAviaEligible: true,
      aviaRemainingG: AVIA_MAX_WEIGHT_G,
      aviaOverweightG: 0,
      weightPct: 0
    };
  }
  const netWeightG = cartItems.reduce((sum, it) => sum + getItemWeight(it), 0);
  const boxBufferG = OUTER_BOX_BUFFER_WEIGHT_G;
  const totalWeightG = netWeightG + boxBufferG;
  const isAviaEligible = totalWeightG <= AVIA_MAX_WEIGHT_G;
  const aviaRemainingG = isAviaEligible ? Math.max(0, AVIA_MAX_WEIGHT_G - totalWeightG) : 0;
  const aviaOverweightG = isAviaEligible ? 0 : totalWeightG - AVIA_MAX_WEIGHT_G;
  const weightPct = Math.min(100, Math.round((totalWeightG / AVIA_MAX_WEIGHT_G) * 100));

  return {
    itemCount: cartItems.length,
    netWeightG,
    boxBufferG,
    totalWeightG,
    totalWeightKg: (totalWeightG / 1000).toFixed(2),
    isAviaEligible,
    aviaRemainingG,
    aviaOverweightG,
    weightPct
  };
}

function calculateShippingOptions(weightG, rateJpy) {
  rateJpy = rateJpy || (state.data && state.data.meta && state.data.meta.exchange_rates ? state.data.meta.exchange_rates.rate_jpy : 0.024832);

  // AVIA Small Packet (Air Economy, max 2000g)
  let aviaAvailable = weightG <= 2000 && weightG > 0;
  let aviaJpy = 0;
  if (aviaAvailable) {
    if (weightG <= 100) aviaJpy = 1200;
    else aviaJpy = 1200 + Math.ceil((weightG - 100) / 100) * 150;
  }
  const aviaPln = aviaAvailable ? Math.round(aviaJpy * rateJpy * 100) / 100 : null;

  // EMS Express Air (up to 30kg)
  let emsJpy = 0;
  if (weightG > 0) {
    if (weightG <= 500) emsJpy = 3900;
    else if (weightG <= 2000) emsJpy = 3900 + Math.ceil((weightG - 500) / 250) * 350;
    else emsJpy = 6000 + Math.ceil((weightG - 2000) / 500) * 700;
  }
  const emsPln = weightG > 0 ? Math.round(emsJpy * rateJpy * 100) / 100 : 0;

  // Surface Sea Mail (up to 30kg)
  let surfJpy = 0;
  if (weightG > 0) {
    if (weightG <= 1000) surfJpy = 3300;
    else surfJpy = 3300 + Math.ceil((weightG - 1000) / 1000) * 450;
  }
  const surfPln = weightG > 0 ? Math.round(surfJpy * rateJpy * 100) / 100 : 0;

  let recId = 'avia_small_packet';
  if (!aviaAvailable) {
    recId = weightG <= 4000 ? 'ems_express' : 'surface_sea';
  }

  return {
    avia_small_packet: {
      id: 'avia_small_packet',
      name: '✈️ AVIA Small Packet',
      badge: 'Ekonomiczna lotnicza (7-14 dni)',
      isAvailable: aviaAvailable,
      costJpy: aviaJpy,
      costPln: aviaPln,
      unavailText: 'Niedostępna (>2,000 g)'
    },
    ems_express: {
      id: 'ems_express',
      name: '🚀 EMS Express Air',
      badge: 'Ekspres (3-6 dni, pełne ubezpieczenie)',
      isAvailable: true,
      costJpy: emsJpy,
      costPln: emsPln
    },
    surface_sea: {
      id: 'surface_sea',
      name: '🚢 Surface Mail (Morska)',
      badge: 'Ekonomiczna (>3 kg, 60-90 dni)',
      isAvailable: true,
      costJpy: surfJpy,
      costPln: surfPln
    },
    recommendedId: recId
  };
}

function computeResidualProfitDetails(cartItems) {
  const count = cartItems ? cartItems.length : 0;
  const rateJpy = state.data && state.data.meta && state.data.meta.exchange_rates ? state.data.meta.exchange_rates.rate_jpy : 0.024832;
  const rateEur = state.data && state.data.meta && state.data.meta.exchange_rates ? state.data.meta.exchange_rates.rate_eur : 4.35;

  const weightInfo = calculateCartPackageWeight(cartItems);
  const shippingInfo = calculateShippingOptions(weightInfo.totalWeightG, rateJpy);

  let chosenMethodKey = state.selectedShippingMethod || shippingInfo.recommendedId;
  let chosenOpt = shippingInfo[chosenMethodKey];
  if (!chosenOpt || !chosenOpt.isAvailable) {
    chosenMethodKey = shippingInfo.recommendedId;
    chosenOpt = shippingInfo[chosenMethodKey];
  }
  const chosenShippingPln = chosenOpt && chosenOpt.costPln ? chosenOpt.costPln : 0;

  const totalPurchaseJpy = cartItems.reduce((sum, it) => sum + (Number(it.price_jpy) || 0), 0);
  const totalPurchasePln = totalPurchaseJpy * rateJpy;
  const domesticZenPln = count * 800 * rateJpy;
  const handlingZenPln = count * 2.0 * rateEur;
  const totalZenFeesPln = domesticZenPln + handlingZenPln;
  const totalBasePurchasePln = totalPurchasePln + totalZenFeesPln;

  const totalResalePln = cartItems.reduce((sum, it) => sum + (Number(it.est_pl_value) || 0), 0);

  const subtotalGoodsFreight = count > 0 ? (totalBasePurchasePln + chosenShippingPln) : 0;
  const depositFeePln = subtotalGoodsFreight * 0.035;
  const vatPln = subtotalGoodsFreight * 0.23;

  const totalLandedPln = count > 0 ? (subtotalGoodsFreight + depositFeePln + vatPln) : 0;
  const residualProfitPln = count > 0 ? (totalResalePln - totalLandedPln) : 0;
  const residualRoiPct = totalLandedPln > 0 ? (residualProfitPln / totalLandedPln * 100) : 0;

  // Individual shipping comparison (~110 PLN per item in separate packages)
  const individualShippingPln = count * 110;
  const consolidationSavingsPln = Math.max(0, individualShippingPln - chosenShippingPln);

  return {
    count,
    rateJpy,
    rateEur,
    weightInfo,
    shippingInfo,
    chosenMethodKey,
    chosenOpt,
    chosenShippingPln,
    totalPurchaseJpy,
    totalPurchasePln,
    totalZenFeesPln,
    totalBasePurchasePln,
    totalResalePln,
    depositFeePln,
    vatPln,
    totalLandedPln,
    residualProfitPln,
    residualRoiPct,
    individualShippingPln,
    consolidationSavingsPln
  };
}

function selectShippingMethod(methodId) {
  state.selectedShippingMethod = methodId;
  renderCartModal();
  updateCartBadge();
}

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

  // Ensure weight fields are preserved
  const w = getItemWeight(deal);
  const cartDeal = {
    ...deal,
    est_weight_g: w,
    weight_formatted: w < 1000 ? `~${w} g` : `~${(w / 1000).toFixed(1)} kg`
  };

  state.cart.push(cartDeal);
  saveCart();
  showToast(`Dodano "${deal.model}" (⚖️ ~${w}g) do paczki konsolidacyjnej!`);
}

function removeFromCart(id) {
  state.cart = state.cart.filter((it) => String(it.id) !== String(id));
  saveCart();
  renderCartModal();
}

function clearCart() {
  if (confirm('Czy na pewno chcesz wyczyścić cały koszyk konsolidacyjny?')) {
    state.cart = [];
    state.selectedShippingMethod = null;
    saveCart();
    renderCartModal();
  }
}

function updateCartBadge() {
  const count = state.cart.length;
  if (elements.cartBadgeCount) elements.cartBadgeCount.textContent = count;

  if (count > 0) {
    elements.stickyCartBar.style.display = 'block';
    const details = computeResidualProfitDetails(state.cart);
    const batteryCount = state.cart.filter((it) => it.has_battery).length;

    if (elements.barCartCount) elements.barCartCount.textContent = `${count} szt.`;
    if (elements.barWeightText) elements.barWeightText.textContent = `⚖️ ${details.weightInfo.totalWeightKg} kg`;
    if (elements.barCartProfit) {
      elements.barCartProfit.textContent = `${details.residualProfitPln >= 0 ? '+' : ''}${details.residualProfitPln.toFixed(0)} zł`;
      elements.barCartProfit.style.color = details.residualProfitPln >= 0 ? '#10b981' : '#ef4444';
    }
    if (elements.barBatteryText) {
      elements.barBatteryText.textContent = `Li-Ion: ${batteryCount}/2`;
      elements.barBatteryText.style.color = batteryCount <= 2 ? '#10b981' : '#ef4444';
    }
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
  const details = computeResidualProfitDetails(state.cart);
  const w = details.weightInfo;

  // IATA Progress Bar
  if (elements.iataCountLabel) elements.iataCountLabel.textContent = `${batteryCount} / 2 baterii`;
  const iataPct = Math.min((batteryCount / 2) * 100, 100);
  if (elements.iataProgressFill) elements.iataProgressFill.style.width = `${iataPct}%`;

  if (batteryCount <= 1) {
    if (elements.iataCountLabel) elements.iataCountLabel.className = 'iata-badge safe';
    if (elements.iataProgressFill) elements.iataProgressFill.className = 'iata-fill safe';
    if (elements.iataHintText) elements.iataHintText.innerHTML = `🟢 <strong>BEZPIECZNIE:</strong> Pozostało wolnych slotów na baterie: <strong>${2 - batteryCount}</strong>. Możesz dobrać kolejnego handhelda.`;
  } else if (batteryCount === 2) {
    if (elements.iataCountLabel) elements.iataCountLabel.className = 'iata-badge warning';
    if (elements.iataProgressFill) elements.iataProgressFill.className = 'iata-fill warning';
    if (elements.iataHintText) elements.iataHintText.innerHTML = `🟡 <strong>MAKSYMALNY LIMIT IATA OSIĄGNIĘTY (2/2):</strong> Paczka ma komplet ogniw Li-Ion. Dobieraj tylko gry retro, GameCube, obiektywy lub aparaty (0% Li-Ion)!`;
  } else {
    if (elements.iataCountLabel) elements.iataCountLabel.className = 'iata-badge danger';
    if (elements.iataProgressFill) elements.iataProgressFill.className = 'iata-fill danger';
    if (elements.iataHintText) elements.iataHintText.innerHTML = `🔴 <strong>ALARM IATA! (${batteryCount}/2):</strong> Przekroczono dopuszczalny limit linii lotniczych! Usuń urządzenia z baterią lub zgłoś do ZenMarketu usunięcie baterii (Dry Shipping).`;
  }

  // Package Weight Meter Widget
  if (elements.weightNetVal) elements.weightNetVal.textContent = w.netWeightG;
  if (elements.weightBufferVal) elements.weightBufferVal.textContent = w.boxBufferG;
  if (elements.packageWeightLabel) {
    elements.packageWeightLabel.textContent = `${w.totalWeightG} g / 2,000 g (${w.totalWeightKg} kg)`;
  }
  if (elements.weightProgressFill) {
    elements.weightProgressFill.style.width = `${w.weightPct}%`;
  }

  if (w.totalWeightG <= 1600) {
    if (elements.packageWeightLabel) elements.packageWeightLabel.className = 'weight-badge safe';
    if (elements.weightProgressFill) elements.weightProgressFill.className = 'weight-fill safe';
    if (elements.weightHintText) {
      elements.weightHintText.innerHTML = count === 0
        ? `🟢 <strong>WAGA W NORMIE AVIA:</strong> Możesz nadać tanią paczkę lotniczą AVIA Small Packet do 2,000 g.`
        : `🟢 <strong>WAGA W NORMIE AVIA (${w.totalWeightG} g):</strong> Zostało jeszcze <strong>${w.aviaRemainingG} g wolnego miejsca</strong> do limitu taniej paczki lotniczej AVIA (2 kg). Możesz śmiało dobrać handhelda lub gry!`;
    }
  } else if (w.totalWeightG <= 2000) {
    if (elements.packageWeightLabel) elements.packageWeightLabel.className = 'weight-badge warning';
    if (elements.weightProgressFill) elements.weightProgressFill.className = 'weight-fill warning';
    if (elements.weightHintText) {
      elements.weightHintText.innerHTML = `🟡 <strong>BLISKO LIMITU AVIA (${w.totalWeightG} g):</strong> Pozostało tylko <strong>${w.aviaRemainingG} g</strong>. Dodanie przedmiotu powyżej ${w.aviaRemainingG} g przeniesie paczkę na wyższą taryfę (EMS Air lub Morską)!`;
    }
  } else {
    if (elements.packageWeightLabel) elements.packageWeightLabel.className = 'weight-badge danger';
    if (elements.weightProgressFill) elements.weightProgressFill.className = 'weight-fill danger';
    if (elements.weightHintText) {
      elements.weightHintText.innerHTML = `⚠️ <strong>PRZEKROCZONO LIMIT AVIA (${w.totalWeightG} g / +${w.aviaOverweightG} g):</strong> Paczka waży ponad 2 kg – taryfa AVIA Small Packet jest niedostępna. Rekomendujemy ekspresowy <strong>EMS Air</strong> lub tanią <strong>Morską Surface</strong>!`;
    }
  }

  // Shipping Selector Grid
  if (elements.shippingRecBadge) {
    const recOpt = details.shippingInfo[details.shippingInfo.recommendedId];
    elements.shippingRecBadge.textContent = `Zalecana: ${recOpt ? recOpt.name : 'AVIA'}`;
  }
  if (elements.shippingTiersGrid) {
    const tiers = ['avia_small_packet', 'ems_express', 'surface_sea'];
    elements.shippingTiersGrid.innerHTML = tiers.map((tierKey) => {
      const opt = details.shippingInfo[tierKey];
      if (!opt) return '';
      const isSelected = tierKey === details.chosenMethodKey;
      const isAvail = opt.isAvailable;
      const priceTxt = isAvail && opt.costPln !== null ? `~${opt.costPln.toFixed(0)} zł` : 'Niedostępna';

      return `
        <div class="shipping-tier-card ${isSelected ? 'selected' : ''} ${!isAvail ? 'disabled' : ''}" 
             onclick="${isAvail ? `selectShippingMethod('${opt.id}')` : ''}"
             title="${isAvail ? `Wybierz ${opt.name}` : opt.unavailText || ''}">
          <div class="tier-top">
            <strong class="tier-name">${opt.name}</strong>
            <span class="tier-price">${priceTxt}</span>
          </div>
          <div class="tier-sub">${opt.badge}</div>
          ${!isAvail && opt.unavailText ? `<div class="tier-warn">⚠️ ${opt.unavailText}</div>` : ''}
        </div>
      `;
    }).join('');
  }

  // Residual Net Profit Card ("Cena, która Ci zostaje")
  if (elements.residualProfitVal) {
    elements.residualProfitVal.textContent = `${details.residualProfitPln >= 0 ? '+' : ''}${details.residualProfitPln.toFixed(0)} zł`;
    elements.residualProfitVal.style.color = details.residualProfitPln >= 0 ? '#34d399' : '#ef4444';
  }
  if (elements.residualRoiChip) {
    elements.residualRoiChip.textContent = `ROI: ${details.residualRoiPct >= 0 ? '+' : ''}${details.residualRoiPct.toFixed(1)}%`;
    elements.residualRoiChip.style.color = details.residualRoiPct >= 0 ? '#10b981' : '#ef4444';
  }
  if (elements.resSumResale) elements.resSumResale.textContent = `+${details.totalResalePln.toFixed(0)} zł`;
  if (elements.resSumPurchase) elements.resSumPurchase.textContent = `-${details.totalBasePurchasePln.toFixed(0)} zł`;
  if (elements.resMethodName) elements.resMethodName.textContent = details.chosenOpt.name;
  if (elements.resShippingCost) elements.resShippingCost.textContent = `-${details.chosenShippingPln.toFixed(0)} zł`;
  if (elements.resTaxCost) elements.resTaxCost.textContent = `-${(details.vatPln + details.depositFeePln).toFixed(0)} zł`;
  if (elements.resSavingsVal) {
    elements.resSavingsVal.textContent = count > 1 ? `+${details.consolidationSavingsPln.toFixed(0)} zł` : '0 zł (1 sztuka)';
  }

  // Summary Stats Grid
  if (elements.cartStatItems) elements.cartStatItems.textContent = `${count} szt.`;
  if (elements.cartStatLanded) elements.cartStatLanded.textContent = `~${details.totalLandedPln.toFixed(0)} zł`;
  if (elements.cartStatResale) elements.cartStatResale.textContent = `${details.totalResalePln.toFixed(0)} zł`;
  if (elements.cartStatProfit) {
    elements.cartStatProfit.textContent = `${details.residualProfitPln >= 0 ? '+' : ''}${details.residualProfitPln.toFixed(0)} zł`;
    elements.cartStatProfit.className = details.residualProfitPln >= 0 ? 'text-green' : 'text-red';
  }

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

  elements.cartItemsList.innerHTML = state.cart.map((item) => {
    const itemWeight = getItemWeight(item);
    return `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <strong class="cart-item-title">${item.model}</strong>
          <span class="cart-item-sub">
            Landed: ~${(item.landed_cost_pln || 0).toFixed(0)} zł | Resale: ${(item.est_pl_value || 0).toFixed(0)} zł | 
            <span class="text-sky font-semibold">⚖️ ~${itemWeight}g</span> | 
            ${item.has_battery ? '<span class="text-amber">🔴 Li-Ion</span>' : '<span class="text-green">🟢 0% Baterii</span>'}
          </span>
        </div>
        <div class="cart-item-right">
          <strong class="text-green">+${(item.est_margin_pln || 0).toFixed(0)} zł</strong>
          <button class="btn-remove-item" onclick="removeFromCart('${item.id}')" title="Usuń z koszyka">✕</button>
        </div>
      </div>
    `;
  }).join('');
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

// Live Real-Time Countdown Ticker for Yahoo Auctions (1-second high-precision ticker)
function initLiveCountdownTicker() {
  function updateCountdowns() {
    const cards = document.querySelectorAll('.deal-card[data-is-auction="1"][data-ends-at]');
    if (!cards || cards.length === 0) return;
    const now = Date.now();

    cards.forEach((card) => {
      const endsAtStr = card.getAttribute('data-ends-at');
      if (!endsAtStr) return;
      const endsAt = new Date(endsAtStr).getTime();
      if (isNaN(endsAt)) return;

      const diffMs = endsAt - now;
      const totalSecs = Math.max(0, Math.floor(diffMs / 1000));
      const minsRemaining = Math.max(0, Math.floor(diffMs / 60000));

      const ribbon = card.querySelector('.time-ribbon');
      const ribbonText = card.querySelector('.auction-countdown-text');
      const badgeText = card.querySelector('.badge-countdown-text');
      const mediaBadge = card.querySelector('.media-time-badge');
      const stageEl = ribbon ? ribbon.querySelector('.time-ribbon-stage') : null;
      const iconEl = ribbon ? ribbon.querySelector('.time-ribbon-icon') : null;

      if (diffMs <= 0) {
        // Auction finished: swap all links immediately to active search so clicking never leads to a dead page
        card.setAttribute('data-is-ended', '1');
        card.classList.add('deal-card-ended');
        const endingSoonUrl = card.getAttribute('data-ending-soon-url');
        if (endingSoonUrl) {
          const mediaLink = card.querySelector('.deal-card-media-link');
          if (mediaLink) {
            mediaLink.href = endingSoonUrl;
            mediaLink.title = 'Aukcja zakończona – szukaj aktywnych ofert tego modelu w ZenMarket';
          }
          const titleLink = card.querySelector('.card-title-link');
          if (titleLink) {
            titleLink.href = endingSoonUrl;
            titleLink.title = 'Aukcja zakończona – szukaj aktywnych ofert tego modelu w ZenMarket';
          }
          const primaryCta = card.querySelector('.primary-cta');
          if (primaryCta) {
            primaryCta.href = endingSoonUrl;
            primaryCta.classList.add('cta-ended');
            primaryCta.title = 'Aukcja zakończona – otwórz trwające licytacje tego modelu w ZenMarket';
            const ctaTextEl = primaryCta.querySelector('.cta-text');
            if (ctaTextEl) ctaTextEl.textContent = '⏰ Szukaj trwających w ZenMarket';
            const vpnBadge = primaryCta.querySelector('.cta-vpn-badge');
            if (vpnBadge) vpnBadge.textContent = 'Nowe oferty';
          }
          const buyNowCta = card.querySelector('.buy-now-cta');
          if (buyNowCta) {
            buyNowCta.href = endingSoonUrl;
            buyNowCta.title = 'Aukcja zakończona – szukaj ofert tego modelu w ZenMarket';
          }
        }

        // Auction finished: remove it completely from the app (User requested: no old auctions on the app)
        if (!card._removing) {
          card._removing = true;
          card.style.transition = 'opacity 0.4s ease, transform 0.4s ease, max-height 0.4s ease, margin 0.4s ease, padding 0.4s ease';
          card.style.opacity = '0';
          card.style.transform = 'scale(0.92)';
          card.style.maxHeight = card.offsetHeight + 'px';
          setTimeout(() => {
            card.style.maxHeight = '0px';
            card.style.margin = '0px';
            card.style.padding = '0px';
            card.style.overflow = 'hidden';
            setTimeout(() => {
              card.remove();
              // Update live counter badge
              if (elements.auctionsCountBadge) {
                const remaining = document.querySelectorAll('.deal-card[data-is-auction="1"]').length;
                elements.auctionsCountBadge.textContent = remaining;
              }
              if (document.querySelectorAll('.deal-card').length === 0) {
                renderDeals();
              }
            }, 300);
          }, 100);
        }
        return;
      }

      // Format remaining time (seconds precision under 5m)
      let formatted = '';
      if (diffMs < 300000) {
        const m = Math.floor(totalSecs / 60);
        const s = totalSecs % 60;
        formatted = `${m}m ${s < 10 ? '0' : ''}${s}s`;
      } else if (minsRemaining <= 60) {
        formatted = `${minsRemaining} min`;
      } else if (minsRemaining <= 1440) {
        const h = Math.floor(minsRemaining / 60);
        const m = minsRemaining % 60;
        formatted = m > 0 ? `${h}h ${m}m` : `${h}h`;
      } else {
        const d = Math.floor(minsRemaining / 1440);
        const remH = Math.floor((minsRemaining % 1440) / 60);
        formatted = remH > 0 ? `${d}d ${remH}h` : `${d}d`;
      }

      if (ribbonText) ribbonText.textContent = formatted;
      if (badgeText) badgeText.textContent = formatted;

      // Update urgency classes dynamically
      if (ribbon) {
        if (minsRemaining <= 60) {
          const targetClass = diffMs < 300000 ? 'time-ribbon time-ribbon-urgent live-pulse' : 'time-ribbon time-ribbon-urgent';
          if (ribbon.className !== targetClass) {
            ribbon.className = targetClass;
          }
          if (iconEl && iconEl.textContent !== '🔥') iconEl.textContent = '🔥';
          if (stageEl) {
            stageEl.textContent = diffMs < 300000 ? 'Ostatnie sekundy – Snajper na żywo!' : 'Faza Końcowa – Prawdziwa cena rynkowa!';
          }
          if (mediaBadge && !mediaBadge.classList.contains('urgent')) {
            mediaBadge.classList.add('urgent');
            mediaBadge.classList.remove('badge-ended');
          }
        } else if (minsRemaining <= 360) {
          if (!ribbon.classList.contains('time-ribbon-soon')) {
            ribbon.className = 'time-ribbon time-ribbon-soon';
            if (iconEl) iconEl.textContent = '⚡';
            if (stageEl) stageEl.textContent = 'Ostatnie godziny – Walka snajperów';
          }
        }
      }
    });
  }

  // Run immediately and every 1 second
  updateCountdowns();
  if (window._countdownInterval) clearInterval(window._countdownInterval);
  window._countdownInterval = setInterval(updateCountdowns, 1000);
  window.updateLiveCountdowns = updateCountdowns;
}

// Global scope export for inline onclick
window.removeFromCart = removeFromCart;
window.selectShippingMethod = selectShippingMethod;
