
const state = {
  data: null,
  currentView: 'opportunities', // 'opportunities' | 'auctions' | 'mercari' | 'search_streams' | 'finished_auctions'
  showAllOpportunities: false,
  hiddenDeals: new Set(),
  expandedDealDetails: new Set(),
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

const CART_STORAGE_KEY = 'agydeal_cart_v2';

const CATEGORY_WEIGHTS = {
  nintendo_switch_lite: 350,
  nintendo_switch: 1000,
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
  mechanical_keyboards: 1150,
  analog_lenses: 280,
  ps5_limited_controllers: 380,
  ps_retro_limited_controllers: 320,
  ps1_consoles: 950,
  retro_consoles_no_battery: 2200,
  nintendo_retro: 400
};
const OUTER_BOX_BUFFER_WEIGHT_G = 300;
const AVIA_MAX_WEIGHT_G = 2000;

const elements = {
  feedContainer: document.getElementById('feedContainer'),
  loadingState: document.getElementById('loadingState'),
  categoryPills: document.getElementById('categoryPills'),
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  batteryZeroOnlyToggle: document.getElementById('batteryZeroOnlyToggle'),
  sureDealsOnlyToggle: document.getElementById('sureDealsOnlyToggle'),
  sortSelect: document.getElementById('sortSelect'),
  
  tickerJpyRate: document.getElementById('tickerJpyRate'),
  tickerStorageDays: document.getElementById('tickerStorageDays'),
  tickerStorageChip: document.getElementById('tickerStorageChip'),
  opportunitiesCountBadge: document.getElementById('opportunitiesCountBadge'),
  auctionsCountBadge: document.getElementById('auctionsCountBadge'),
  mercariCountBadge: document.getElementById('mercariCountBadge'),
  streamsCountBadge: document.getElementById('streamsCountBadge'),
  finishedCountBadge: document.getElementById('finishedCountBadge'),
  totalDealsPill: document.getElementById('totalDealsPill'),
  
  cartBadgeCount: document.getElementById('cartBadgeCount'),
  stickyCartBar: document.getElementById('stickyCartBar'),
  barCartCount: document.getElementById('barCartCount'),
  barWeightText: document.getElementById('barWeightText'),
  barBatteryText: document.getElementById('barBatteryText'),
  barCartProfit: document.getElementById('barCartProfit'),
  openCartBtn: document.getElementById('openCartBtn'),
  cartBarTrigger: document.getElementById('cartBarTrigger'),
  
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

  cartModal: document.getElementById('cartModal'),
  closeCartBtn: document.getElementById('closeCartBtn'),
  closeCartBtnBottom: document.getElementById('closeCartBtnBottom'),
  clearCartBtn: document.getElementById('clearCartBtn'),
  cartItemsList: document.getElementById('cartItemsList'),
  iataCountLabel: document.getElementById('iataCountLabel'),
  iataProgressFill: document.getElementById('iataProgressFill'),
  iataHintText: document.getElementById('iataHintText'),

  packageWeightLabel: document.getElementById('packageWeightLabel'),
  weightProgressFill: document.getElementById('weightProgressFill'),
  weightHintText: document.getElementById('weightHintText'),
  weightNetVal: document.getElementById('weightNetVal'),
  weightBufferVal: document.getElementById('weightBufferVal'),

  shippingRecBadge: document.getElementById('shippingRecBadge'),
  shippingTiersGrid: document.getElementById('shippingTiersGrid'),

  residualProfitVal: document.getElementById('residualProfitVal'),
  residualRoiChip: document.getElementById('residualRoiChip'),
  resSumResale: document.getElementById('resSumResale'),
  resSumPurchase: document.getElementById('resSumPurchase'),
  resMethodName: document.getElementById('resMethodName'),
  resShippingCost: document.getElementById('resShippingCost'),
  resTaxCost: document.getElementById('resTaxCost'),
  resSavingsVal: document.getElementById('resSavingsVal'),

  cartStatItems: document.getElementById('cartStatItems'),
  cartStatLanded: document.getElementById('cartStatLanded'),
  cartStatResale: document.getElementById('cartStatResale'),
  cartStatProfit: document.getElementById('cartStatProfit'),

  installPwaBtn: document.getElementById('installPwaBtn')
};

document.addEventListener('DOMContentLoaded', () => {
  loadSavedCart();
  registerServiceWorker();
  setupPwaInstallPrompt();
  setupEventListeners();
  fetchDealsData();
  handleUrlShortcuts();
  initLiveCountdownTicker();
});

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js')
      .then((reg) => console.log('[PWA] Service Worker registered:', reg.scope))
      .catch((err) => console.warn('[PWA] Service Worker failed:', err));
  }
}

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

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const ALLOWED_URL_DOMAINS = [
  'zenmarket.jp',
  'mercari.com',
  'yahoo.co.jp',
  'allegro.pl',
  'olx.pl',
  'buyee.jp',
  'jauce.com',
  'yimg.jp',
  'mercdn.net'
];

function sanitizeUrl(url) {
  if (!url || typeof url !== 'string') return '#';
  const trimmed = url.trim();
  if (!trimmed || trimmed === '#') return '#';
  if (trimmed.startsWith('./') || trimmed.startsWith('/') || trimmed.startsWith('icons/')) {
    return trimmed;
  }
  try {
    const parsed = new URL(trimmed, window.location.href);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return '#';
    }
    const host = parsed.hostname.toLowerCase();
    const isAllowed = ALLOWED_URL_DOMAINS.some((domain) => host === domain || host.endsWith('.' + domain));
    if (!isAllowed) {
      return '#';
    }
    return parsed.href;
  } catch (e) {
    return '#';
  }
}

function getSafeImageUrl(url) {
  if (!url || typeof url !== 'string') return './assets/images/placeholder.svg';
  const trimmed = url.trim();
  if (!trimmed) return './assets/images/placeholder.svg';
  if (trimmed.startsWith('./') || trimmed.startsWith('/')) return trimmed;

  try {
    let cleanUrl = trimmed;
    if (cleanUrl.startsWith('//')) {
      cleanUrl = 'https:' + cleanUrl;
    } else if (cleanUrl.startsWith('http://')) {
      cleanUrl = 'https://' + cleanUrl.slice(7);
    } else if (!cleanUrl.startsWith('http')) {
      cleanUrl = 'https://' + cleanUrl;
    }

    const parsed = new URL(cleanUrl);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return './assets/images/placeholder.svg';
    }

    if (cleanUrl.startsWith('https://www.jauce.com/read_yafile/')) {
      return cleanUrl;
    }

    if (cleanUrl.includes('auc-pctr.c.yimg.jp')) {
      return 'https://www.jauce.com/read_yafile/' + cleanUrl;
    }

    const host = parsed.hostname.toLowerCase();
    const isAllowed = ALLOWED_URL_DOMAINS.some((domain) => host === domain || host.endsWith('.' + domain));
    if (!isAllowed) return './assets/images/placeholder.svg';
    return cleanUrl;
  } catch (e) {
    return './assets/images/placeholder.svg';
  }
}

function sanitizeColor(col, fallback = '#38bdf8') {
  if (!col || typeof col !== 'string') return fallback;
  const trimmed = col.trim();
  if (/^#[0-9a-fA-F]{3,8}$/.test(trimmed) || /^rgba?\([0-9,.\s]+\)$/.test(trimmed)) {
    return trimmed;
  }
  return fallback;
}

function round2(num) {
  return Math.round((Number(num) + Number.EPSILON) * 100) / 100;
}

function isDealEligible(deal) {
  const isAuction = Boolean(deal._isAuction || deal.auction_id || (deal.platform && deal.platform.includes('Yahoo')));
  if (isAuction) {
    if (deal.status === 'closed' || deal.status === 'ended') return false;
    if (deal.time_remaining_formatted === 'Zakończona') return false;
    if (deal.time_remaining_minutes !== undefined && deal.time_remaining_minutes !== null && deal.time_remaining_minutes <= 0) return false;
    if (deal.ends_at_iso) {
      const endsMs = new Date(deal.ends_at_iso).getTime();
      if (!isNaN(endsMs) && endsMs <= Date.now()) return false;
    }
    const timing = getAuctionLiveTiming(deal);
    if (timing.isEnded || timing.diffMs <= 0) return false;
  }

  const rateJpy = state.data?.meta?.exchange_rates?.rate_jpy || 0.024832;
  const pricePln = deal.price_pln_raw || (deal.price_jpy * rateJpy);
  if (deal.category_id === 'film_cameras_point_shoot' || deal.category_id === 'analog_lenses') {
    if (pricePln > 100) return false;
  }

  const margin = deal.expected_margin_pln !== undefined ? deal.expected_margin_pln : deal.est_margin_pln;
  if (margin === undefined || margin === null || margin <= 0) return false;

  if (deal.verdict_code === 'C_TIER_OVERHEATED') return false;

  return true;
}

function getEligibleOpportunitiesCount() {
  if (!state.data) return 0;
  const auctions = (state.data.auctions || []).map((d) => ({ ...d, _isAuction: true }));
  const mercari = (state.data.mercari_deals || []).map((d) => ({ ...d, _isAuction: false }));
  return [...auctions, ...mercari].filter((d) => isDealEligible(d) && !state.hiddenDeals.has(String(d.id))).length;
}

function getActiveAuctionsCount() {
  if (!state.data || !Array.isArray(state.data.auctions)) return 0;
  const now = Date.now();
  return state.data.auctions.filter((d) => {
    if (d.time_remaining_formatted === 'Zakończona' || d.status === 'closed' || d.status === 'ended') return false;
    if (d.time_remaining_minutes !== undefined && d.time_remaining_minutes !== null && d.time_remaining_minutes <= 0) return false;
    if (d.ends_at_iso) {
      const endsMs = new Date(d.ends_at_iso).getTime();
      if (isNaN(endsMs) || endsMs <= now) return false;
    }
    const timing = getAuctionLiveTiming(d);
    return !timing.isEnded && timing.diffMs > 0;
  }).length;
}

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
        <small>${escapeHtml(error.message)}. Sprawdź czy plik docs/data/deals.json istnieje.</small>
      </div>
    `;
  }
}

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

  if (elements.tickerStorageChip) {
    const hasItems = state.cart && state.cart.length > 0;
    elements.tickerStorageChip.style.display = hasItems ? 'inline-flex' : 'none';
  }

  const counts = meta.counts || {};
  const liveAuctionsCount = getActiveAuctionsCount() || (counts.yahoo_auctions || 0);
  const eligibleCount = getEligibleOpportunitiesCount();

  if (elements.opportunitiesCountBadge) {
    elements.opportunitiesCountBadge.textContent = eligibleCount;
  }
  elements.auctionsCountBadge.textContent = liveAuctionsCount;
  elements.mercariCountBadge.textContent = counts.mercari_deals || 0;
  if (elements.streamsCountBadge) {
    elements.streamsCountBadge.textContent = counts.search_streams || (state.data && state.data.search_streams ? state.data.search_streams.length : 22);
  }
  if (elements.finishedCountBadge) {
    elements.finishedCountBadge.textContent = counts.finished_auctions || (state.data && state.data.finished_auctions ? state.data.finished_auctions.length : 8);
  }
  elements.totalDealsPill.textContent = counts.total_active || 0;
}

function setupEventListeners() {
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

  elements.categoryPills.querySelectorAll('.pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      elements.categoryPills.querySelectorAll('.pill').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      state.selectedCategory = pill.dataset.cat;
      renderDeals();
    });
  });

  elements.batteryZeroOnlyToggle.addEventListener('change', (e) => {
    state.batteryZeroOnly = e.target.checked;
    renderDeals();
  });

  if (elements.sureDealsOnlyToggle) {
    elements.sureDealsOnlyToggle.addEventListener('change', (e) => {
      state.sureDealsOnly = e.target.checked;
      renderDeals();
    });
  }

  elements.sortSelect.addEventListener('change', (e) => {
    state.sortOrder = e.target.value;
    renderDeals();
  });

  elements.openCartBtn.addEventListener('click', openCart);
  elements.cartBarTrigger.addEventListener('click', openCart);
  elements.closeCartBtn.addEventListener('click', closeCart);
  elements.closeCartBtnBottom.addEventListener('click', closeCart);
  elements.clearCartBtn.addEventListener('click', clearCart);

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
  if (elements.cartItemsList) {
    elements.cartItemsList.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-remove-item');
      if (btn && btn.dataset.cartId) {
        removeFromCart(btn.dataset.cartId);
      }
    });
  }

  if (elements.calcModal) {
    elements.calcModal.addEventListener('click', (e) => {
      if (e.target === elements.calcModal) closeCalculator();
    });
  }
  if (elements.cartModal) {
    elements.cartModal.addEventListener('click', (e) => {
      if (e.target === elements.cartModal) closeCart();
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (elements.calcModal && elements.calcModal.style.display !== 'none') {
        closeCalculator();
      }
      if (elements.cartModal && elements.cartModal.style.display !== 'none') {
        closeCart();
      }
    }
  });
}

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

function handleUrlShortcuts() {
  const urlParams = new URLSearchParams(window.location.search);
  const tab = urlParams.get('tab');
  const action = urlParams.get('action');

  if (tab === 'opportunities' || tab === 'deals') {
    state.currentView = 'opportunities';
    syncTopTabs('opportunities');
    syncBottomNav('opportunities');
  } else if (tab === 'auctions') {
    state.currentView = 'auctions';
    syncTopTabs('auctions');
    syncBottomNav('auctions');
  } else if (tab === 'mercari') {
    state.currentView = 'mercari';
    syncTopTabs('mercari');
    syncBottomNav('mercari');
  } else if (tab === 'search_streams' || tab === 'streams') {
    state.currentView = 'search_streams';
    syncTopTabs('search_streams');
    syncBottomNav('search_streams');
  } else if (tab === 'finished' || tab === 'finished_auctions' || tab === 'closed') {
    state.currentView = 'finished_auctions';
    syncTopTabs('finished_auctions');
    syncBottomNav('finished_auctions');
  }
  if (action === 'calc') {
    setTimeout(openCalculator, 300);
  }
  if (action === 'cart') {
    setTimeout(openCart, 300);
  }
}

function renderDeals() {
  if (!state.data) return;

  renderCategorySearch();

  const sureToggleWrapper = document.getElementById('sureDealsOnlyToggle')?.closest('label');

  if (state.currentView === 'opportunities') {
    if (sureToggleWrapper) sureToggleWrapper.style.display = 'inline-flex';

    const rawAuctions = (state.data.auctions || []).map((d) => ({ ...d, _isAuction: true }));
    const rawMercari = (state.data.mercari_deals || []).map((d) => ({ ...d, _isAuction: false }));
    let deals = [...rawAuctions, ...rawMercari];

    deals = deals.filter((d) => !state.hiddenDeals.has(String(d.id)));

    if (state.selectedCategory !== 'all') {
      deals = deals.filter((d) => d.category_id === state.selectedCategory);
    }

    if (state.batteryZeroOnly) {
      deals = deals.filter((d) => !d.has_battery);
    }

    if (state.sureDealsOnly) {
      deals = deals.filter((d) => d.verdict_code === 'S_TIER_SURE_ARBITRAGE' || d.verdict_code === 'A_TIER_SOLID_DEAL');
    }

    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      deals = deals.filter((d) => {
        const title = (d.model || '').toLowerCase();
        const color = (d.color || '').toLowerCase();
        const note = (d.custom_note || '').toLowerCase();
        const cat = (d.category_name || '').toLowerCase();
        return title.includes(q) || color.includes(q) || note.includes(q) || cat.includes(q);
      });
    }

    deals = deals.filter(isDealEligible);

    deals = sortDealsList(deals, state.sortOrder);

    if (elements.opportunitiesCountBadge) {
      elements.opportunitiesCountBadge.textContent = deals.length;
    }

    if (deals.length === 0) {
      const hiddenCount = state.hiddenDeals.size;
      elements.feedContainer.innerHTML = `
        <div class="empty-cart-hint">
          <p class="text-amber">⚠️ Brak kwalifikujących się okazji spełniających kryteria opłacalności.</p>
          <small>Wszystkie oferty w tej selekcji wygasły, przekraczają limit cenowy (np. aparaty/obiektywy ≤100 zł) lub mają ujemny szacowany zysk.</small>
          ${hiddenCount > 0 ? `<br><button class="btn-compact btn-compact-secondary btn-unhide-all" style="margin-top:10px;">Przywróć ukryte okazje (${hiddenCount})</button>` : ''}
        </div>
      `;
      attachCardEvents();
      return;
    }

    const totalEligible = deals.length;
    const visibleDeals = state.showAllOpportunities ? deals : deals.slice(0, 5);

    const cardsHtml = visibleDeals.map((deal) => renderDealCard(deal, deal._isAuction)).join('');
    const moreBarHtml = totalEligible > 5
      ? `
        <div class="opportunities-more-bar">
          <button class="btn-show-more" id="toggleShowAllBtn">
            ${state.showAllOpportunities ? '▲ Pokaż tylko Top 5 okazji' : `👁️ Pokaż wszystkie okazje (${totalEligible})`}
          </button>
        </div>
      `
      : '';

    elements.feedContainer.innerHTML = cardsHtml + moreBarHtml;
    attachCardEvents();

    if (typeof window.updateLiveCountdowns === 'function') {
      window.updateLiveCountdowns();
    }
    return;
  }

  if (state.currentView === 'search_streams') {
    if (sureToggleWrapper) sureToggleWrapper.style.display = 'none';

    let streams = state.data.search_streams || [];

    if (state.selectedCategory !== 'all') {
      streams = streams.filter((s) => s.category_id === state.selectedCategory);
    }

    if (state.batteryZeroOnly) {
      streams = streams.filter((s) => !s.has_battery);
    }

    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      streams = streams.filter((s) => {
        const title = (s.model || '').toLowerCase();
        const note = (s.sniping_tip || '').toLowerCase();
        const cat = (s.category_name || '').toLowerCase();
        return title.includes(q) || note.includes(q) || cat.includes(q);
      });
    }

    streams = sortStreamsList(streams, state.sortOrder);

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

  if (state.currentView === 'finished_auctions') {
    if (sureToggleWrapper) sureToggleWrapper.style.display = 'none';

    let finished = state.data.finished_auctions || [];

    if (state.selectedCategory !== 'all') {
      finished = finished.filter((f) => f.category_id === state.selectedCategory);
    }

    if (state.batteryZeroOnly) {
      finished = finished.filter((f) => !f.battery_type || f.battery_type === 'none');
    }

    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      finished = finished.filter((f) => {
        const title = (f.model || '').toLowerCase();
        const cat = (f.category_name || '').toLowerCase();
        const col = (f.color || '').toLowerCase();
        return title.includes(q) || cat.includes(q) || col.includes(q);
      });
    }

    if (finished.length === 0) {
      elements.feedContainer.innerHTML = `
        <div class="empty-cart-hint">
          <p>Brak zakończonych aukcji spełniających wybrane kryteria.</p>
          <small>Zmień filtr kategorii lub wyczyść pole wyszukiwania.</small>
        </div>
      `;
      return;
    }

    elements.feedContainer.innerHTML = finished.map((item) => renderFinishedAuctionCard(item)).join('');
    return;
  }

  if (sureToggleWrapper) sureToggleWrapper.style.display = 'inline-flex';

  const isAuctions = state.currentView === 'auctions';
  let deals = isAuctions ? (state.data.auctions || []) : (state.data.mercari_deals || []);

  deals = deals.filter((d) => !state.hiddenDeals.has(String(d.id)));

  if (!deals || deals.length === 0) {
    const hiddenCount = state.hiddenDeals.size;
    elements.feedContainer.innerHTML = `
      <div class="empty-cart-hint">
        <p>Brak ofert w tej sekcji</p>
        ${hiddenCount > 0 ? `<br><button class="btn-compact btn-compact-secondary btn-unhide-all" style="margin-top:10px;">Przywróć ukryte (${hiddenCount})</button>` : ''}
      </div>
    `;
    attachCardEvents();
    return;
  }

  if (isAuctions) {
    const now = Date.now();
    deals = deals.filter((d) => {
      if (d.time_remaining_formatted === 'Zakończona' || d.status === 'closed' || d.status === 'ended') {
        return false;
      }
      if (d.time_remaining_minutes !== undefined && d.time_remaining_minutes !== null && d.time_remaining_minutes <= 0) {
        return false;
      }
      if (d.ends_at_iso) {
        const endsMs = new Date(d.ends_at_iso).getTime();
        if (isNaN(endsMs) || endsMs <= now) {
          return false;
        }
      }
      const timing = getAuctionLiveTiming(d);
      if (timing.isEnded || timing.diffMs <= 0) {
        return false;
      }
      return true;
    });

    if (elements.auctionsCountBadge) {
      elements.auctionsCountBadge.textContent = deals.length;
    }
  }

  if (state.selectedCategory !== 'all') {
    deals = deals.filter((d) => d.category_id === state.selectedCategory);
  }

  if (state.batteryZeroOnly) {
    deals = deals.filter((d) => !d.has_battery);
  }

  if (state.sureDealsOnly) {
    deals = deals.filter((d) => d.verdict_code === 'S_TIER_SURE_ARBITRAGE' || d.verdict_code === 'A_TIER_SOLID_DEAL');
  }

  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    deals = deals.filter((d) => {
      const title = (d.model || '').toLowerCase();
      const color = (d.color || '').toLowerCase();
      const note = (d.custom_note || '').toLowerCase();
      const cat = (d.category_name || '').toLowerCase();
      return title.includes(q) || color.includes(q) || note.includes(q) || cat.includes(q);
    });
  }

  deals = sortDealsList(deals, state.sortOrder);

  if (deals.length === 0) {
    const hiddenCount = state.hiddenDeals.size;
    elements.feedContainer.innerHTML = `
      <div class="empty-cart-hint">
        <p>Brak wyników spełniających wybrane kryteria.</p>
        <small>Spróbuj zmienić filtr kategorii lub wyczyść pole wyszukiwania.</small>
        ${hiddenCount > 0 ? `<br><button class="btn-compact btn-compact-secondary btn-unhide-all" style="margin-top:10px;">Przywróć ukryte (${hiddenCount})</button>` : ''}
      </div>
    `;
    attachCardEvents();
    return;
  }

  elements.feedContainer.innerHTML = deals.map((deal) => renderDealCard(deal, isAuctions)).join('');

  attachCardEvents();

  if (typeof window.updateLiveCountdowns === 'function') {
    window.updateLiveCountdowns();
  }
}

function sortStreamsList(list, order) {
  const items = [...list];
  switch (order) {
    case 'margin_desc':
    case 'pred_margin_desc':
    case 'verdict_desc':
      return items.sort((a, b) => {
        const valA = parseInt((a.est_profit_pln || '').replace(/[^0-9]/g, '')) || 0;
        const valB = parseInt((b.est_profit_pln || '').replace(/[^0-9]/g, '')) || 0;
        return valB - valA;
      });
    case 'roi_desc':
      return items.sort((a, b) => {
        const valA = parseInt((a.roi_pct || '').replace(/[^0-9]/g, '')) || 0;
        const valB = parseInt((b.roi_pct || '').replace(/[^0-9]/g, '')) || 0;
        return valB - valA;
      });
    case 'price_asc':
      return items.sort((a, b) => (a.target_start_jpy || 0) - (b.target_start_jpy || 0));
    case 'cap_desc':
      return items.sort((a, b) => (b.hard_cap_jpy || 0) - (a.hard_cap_jpy || 0));
    default:
      return items;
  }
}

function sortDealsList(list, order) {
  const items = [...list];
  switch (order) {
    case 'time_asc':
      const now = Date.now();
      return items.sort((a, b) => {
        const timeA = a.ends_at_iso ? new Date(a.ends_at_iso).getTime() : ((a.time_remaining_minutes !== undefined && a.time_remaining_minutes !== null) ? (now + a.time_remaining_minutes * 60000) : Infinity);
        const timeB = b.ends_at_iso ? new Date(b.ends_at_iso).getTime() : ((b.time_remaining_minutes !== undefined && b.time_remaining_minutes !== null) ? (now + b.time_remaining_minutes * 60000) : Infinity);
        if (timeA !== timeB) return timeA - timeB;
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

function renderCategorySearch() {
  const panel = document.getElementById('categorySearch');
  const pill = [...elements.categoryPills.querySelectorAll('.pill')]
    .find((item) => item.dataset.cat === state.selectedCategory);
  const query = pill?.dataset.searchQuery;
  const isAuctions = state.currentView === 'auctions';
  const isMercari = state.currentView === 'mercari';
  panel.hidden = !query || !(isAuctions || isMercari);
  panel.replaceChildren();
  if (panel.hidden) return;

  const label = document.createElement('p');
  label.textContent = `${pill.textContent.trim()} — wyszukaj oferty na ${isAuctions ? 'Yahoo! Auctions' : 'Mercari'}:`;
  const link = document.createElement('a');
  link.className = 'btn-compact btn-compact-secondary';
  link.target = '_blank';
  link.rel = 'noopener';
  const encodedQuery = encodeURIComponent(query);
  link.href = isAuctions
    ? `https://zenmarket.jp/pl/yahoo.aspx?q=${encodedQuery}&sort=end&order=asc`
    : `https://zenmarket.jp/pl/mercari.aspx?q=${encodedQuery}`;
  link.textContent = isAuctions ? 'Szukaj aukcji ↗' : 'Szukaj ofert Kup teraz ↗';
  panel.append(label, link);
}

function renderSearchStreamCard(stream) {
  const safeId = escapeHtml(stream.id);
  const safeModel = escapeHtml(stream.model || '');
  const safeCatName = escapeHtml(stream.category_name || '');
  const safeIcon = escapeHtml(stream.icon || '🔍');
  const safeTargetStart = escapeHtml(stream.target_start_label || 'od 1 JPY');
  const safeExpectedClosedJpy = escapeHtml(stream.expected_closed_range_jpy || '');
  const safeExpectedClosedPln = escapeHtml(stream.expected_closed_range_pln || '');
  const safeHardCap = escapeHtml(stream.hard_cap_label || '');
  const safePolandResale = escapeHtml(stream.poland_resale_range || '');
  const safeEstProfit = escapeHtml(stream.est_profit_pln || '');
  const safeRoi = escapeHtml(stream.roi_pct || '');
  const safeSnipingTip = escapeHtml(stream.sniping_tip || '');

  const isZeroBattery = !stream.has_battery;
  const batteryBadge = isZeroBattery
    ? `<span class="pill-badge battery-zero" title="Brak baterii litowej – dozwolona nielimitowana wysyłka lotnicza">🟢 0% Baterii (Brak limitu IATA)</span>`
    : `<span class="pill-badge battery-liion" title="Zawiera akumulator Li-Ion – limit maks. 2 sztuki na paczkę lotniczą">⚡ Bateria Li-Ion (Maks 2/paczka)</span>`;

  const zenEarliest = (stream.links && stream.links.zenmarket_ending_earliest) || (stream.links && stream.links.primary_url) || '#';
  const zenLowest = (stream.links && stream.links.zenmarket_lowest_bid) || zenEarliest;
  const buyeeEarliest = (stream.links && stream.links.buyee_ending_earliest) || '';
  const yahooArchive = (stream.links && stream.links.yahoo_closed_archive) || '';
  const allegroLink = (stream.links && stream.links.allegro_search) || '';
  const olxLink = (stream.links && stream.links.olx_search) || '';

  const safeZenEarliest = escapeHtml(sanitizeUrl(zenEarliest));
  const safeZenLowest = escapeHtml(sanitizeUrl(zenLowest));
  const safeBuyeeEarliest = buyeeEarliest ? escapeHtml(sanitizeUrl(buyeeEarliest)) : '';
  const safeYahooArchive = yahooArchive ? escapeHtml(sanitizeUrl(yahooArchive)) : '';
  const safeAllegroLink = allegroLink ? escapeHtml(sanitizeUrl(allegroLink)) : '';
  const safeOlxLink = olxLink ? escapeHtml(sanitizeUrl(olxLink)) : '';

  return `
    <article class="deal-card stream-card" id="stream-${safeId}">
      <div class="stream-card-top">
        <div class="stream-icon-badge">${safeIcon}</div>
        <div class="stream-header-text">
          <div class="stream-meta-row">
            <span class="platform-tag" style="background:#0284c7; color:#fff;">🔍 Strumień Snajpera</span>
            <span class="pill-badge stream-cat-tag">${safeCatName}</span>
            ${batteryBadge}
          </div>
          <h3 class="stream-title">${safeModel}</h3>
        </div>
      </div>

      <!-- Proper Short Price Guide (4-Grid) -->
      <div class="price-guide-grid">
        <div class="guide-stat-box">
          <span class="guide-stat-label">🎯 Okazja wywoławcza:</span>
          <strong class="guide-stat-val text-amber">${safeTargetStart}</strong>
          <small class="guide-stat-sub">Próg rozpoczęcia licytacji</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">📊 Ceny zamknięcia (落札相場):</span>
          <strong class="guide-stat-val text-sky">${safeExpectedClosedJpy}</strong>
          <small class="guide-stat-sub">${safeExpectedClosedPln}</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">🛑 Twardy limit opłacalności:</span>
          <strong class="guide-stat-val text-emerald">${safeHardCap}</strong>
          <small class="guide-stat-sub">Maksymalna oferta snajpera</small>
        </div>
        <div class="guide-stat-box">
          <span class="guide-stat-label">🇵🇱 Realna wycena w Polsce:</span>
          <strong class="guide-stat-val text-purple">${safePolandResale}</strong>
          <small class="guide-stat-sub">Allegro / OLX po targu</small>
        </div>
      </div>

      <!-- Reality Summary Row -->
      <div class="stream-reality-row">
        <div class="reality-metric">
          <span class="reality-label">Szacowany Zysk Netto w PL:</span>
          <strong class="reality-val text-green font-bold">${safeEstProfit}</strong>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">Średni Zwrot z Inwestycji:</span>
          <strong class="reality-val text-green font-bold">${safeRoi}</strong>
        </div>
      </div>

      <!-- Sniping Tip Box -->
      <div class="stream-tip-box">
        <span class="tip-icon">💡</span>
        <div class="tip-body">
          <strong>Wskazówki Snajpera & Stan Techniczny:</strong>
          <p>${safeSnipingTip}</p>
        </div>
      </div>

      <!-- Direct 1-Click Action Buttons to Earliest Ending Auctions -->
      <div class="card-action-tiers stream-actions-wrap">
        <!-- Tier 1: Main High-Contrast CTAs -->
        <div class="card-main-ctas">
          <a href="${safeZenEarliest}" target="_blank" rel="noopener" class="btn-action primary-cta" title="Zobacz trwające aukcje posortowane od najmniej czasu do końca (ZenMarket działa w PL bez VPN)">
            <span class="cta-text">⏰ Najszybciej Kończące się (ZenMarket)</span>
            <span class="cta-vpn-badge">Prawdziwe Ceny</span>
          </a>
          <a href="${safeZenLowest}" target="_blank" rel="noopener" class="btn-action secondary-cta" title="Najtańsze oferty od 1 JPY">
            <span class="cta-text">🪙 Od 1 JPY / Najtańsze</span>
          </a>
        </div>

        <!-- Tier 2: Auxiliary Research & Direct Archives -->
        <div class="card-pills-row">
          ${safeBuyeeEarliest ? `
            <a href="${safeBuyeeEarliest}" target="_blank" rel="noopener" class="pill-btn" title="Aukcje tego modelu kończące się na Buyee">
              🌐 Buyee Kończące się
            </a>
          ` : ''}
          ${safeYahooArchive ? `
            <a href="${safeYahooArchive}" target="_blank" rel="noopener" class="pill-btn" title="Archiwum zakończonych licytacji na Yahoo (落札相場)">
              📊 Archiwum Zamkniętych (落札相場)
            </a>
          ` : ''}
          ${safeAllegroLink ? `
            <a href="${safeAllegroLink}" target="_blank" rel="noopener" class="pill-btn allegro-pill" title="Sprawdź ceny sprzedaży na Allegro w PL">
              🇵🇱 Allegro
            </a>
          ` : ''}
          ${safeOlxLink ? `
            <a href="${safeOlxLink}" target="_blank" rel="noopener" class="pill-btn olx-pill" title="Sprawdź ogłoszenia na OLX w PL">
              🇵🇱 OLX
            </a>
          ` : ''}
        </div>
      </div>
    </article>
  `;
}

function renderFinishedAuctionCard(item) {
  const safeId = escapeHtml(item.id);
  const safeModel = escapeHtml(item.model || '');
  const safeColor = item.color ? escapeHtml(item.color) : '';
  const safeCondition = escapeHtml(item.condition_short_label || item.condition_label || 'Box CIB');
  const safeBadgeColor = sanitizeColor(item.condition_badge_color, '#8b5cf6');

  const isZeroBattery = !item.battery_type || item.battery_type === 'none';
  const batteryBadge = isZeroBattery
    ? `<span class="pill-badge battery-zero">🟢 0% Li-Ion</span>`
    : `<span class="pill-badge battery-liion">🔴 1 Li-Ion</span>`;

  const weightFormatted = item.package_weight_g
    ? `~${item.package_weight_g} g`
    : (item.weight_kg ? `~${(item.weight_kg * 1000).toFixed(0)} g` : '~300 g');

  const closedDate = item.closed_at ? escapeHtml(item.closed_at.replace('T', ' ').replace('Z', ' UTC')) : 'Zakończona';
  const zenUrl = item.zenmarket_url || `https://zenmarket.jp/pl/auction.aspx?itemCode=${item.auction_id || item.id}`;
  const safeZenUrl = escapeHtml(sanitizeUrl(zenUrl));
  const safeAllegroUrl = item.allegro_url ? escapeHtml(sanitizeUrl(item.allegro_url)) : '';
  const safeOlxUrl = item.olx_url ? escapeHtml(sanitizeUrl(item.olx_url)) : '';

  const finalJpy = (item.final_price_jpy || 0).toLocaleString();
  const finalPln = (item.final_price_pln || 0).toFixed(0);
  const estVal = (item.est_pl_value || 0).toFixed(0);
  const realizedMargin = (item.potential_arbitrage_pln || item.hypothetical_margin_pln || item.realized_margin_pln || 0).toFixed(0);
  const landedCost = (item.landed_cost_pln || 0).toFixed(0);
  const roiPct = (item.roi_percent || 0).toFixed(1);

  return `
    <article class="deal-card finished-card" data-deal-id="${safeId}">
      <div class="card-header">
        <div class="card-meta-top">
          <span class="platform-tag" style="background:#475569; color:#f8fafc;">🏁 Zakończona Aukcja</span>
          <span class="pill-badge" style="background:rgba(255,255,255,0.06); color:${safeBadgeColor}; font-weight:700; border:1px solid ${safeBadgeColor}40;">
            ${safeCondition}
          </span>
          ${batteryBadge}
          <span class="pill-badge weight-badge">⚖️ ${escapeHtml(weightFormatted)}</span>
        </div>
      </div>

      <div class="time-ribbon time-ribbon-finished" style="background:rgba(30, 41, 59, 0.8); border-left:3px solid #10b981;">
        <div class="time-ribbon-left">
          <span class="time-ribbon-icon">🏁</span>
          <span class="time-ribbon-val"><strong>Wylicytowano: ${closedDate}</strong></span>
        </div>
        <div class="time-ribbon-right">
          <span class="time-ribbon-stage" style="color:#10b981; font-weight:700;">Zrealizowany Arbitraż</span>
        </div>
      </div>

      <div class="card-main">
        <h4 class="card-title">
          <a href="${safeZenUrl}" target="_blank" rel="noopener" class="card-title-link" title="Sprawdź historię tej licytacji w ZenMarket">
            <span class="title-text">${safeModel}</span>
            <span class="title-icon">↗</span>
          </a>
        </h4>
        ${safeColor ? `<div class="card-color">${safeColor}</div>` : ''}
      </div>

      <div class="market-reality-box">
        <div class="reality-metric">
          <span class="reality-label">Cena Wylicytowana:</span>
          <span class="reality-val">${finalJpy} JPY</span>
          <span class="reality-sub">~${finalPln} zł</span>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">Wycena w Polsce:</span>
          <span class="reality-val text-amber">${estVal} zł</span>
        </div>
        <div class="reality-divider">·</div>
        <div class="reality-metric">
          <span class="reality-label">Potencjalny Arbitraż:</span>
          <span class="reality-val text-emerald font-bold">+${realizedMargin} zł</span>
        </div>
      </div>

      <div class="profit-matrix">
        <div class="matrix-item">
          <span class="matrix-label">1. Zakup (落札価格):</span>
          <span class="matrix-val">${finalJpy} JPY</span>
          <span class="matrix-sub">~${finalPln} zł</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">2. Koszt Landed (z VAT):</span>
          <span class="matrix-val">~${landedCost} zł</span>
          <span class="matrix-sub">cło, prowizje & fracht</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">3. Sprzedaż w PL:</span>
          <span class="matrix-val">${estVal} zł</span>
          <span class="matrix-sub">realna wartość</span>
        </div>
        <div class="matrix-item">
          <span class="matrix-label">4. Stopa Zwrotu:</span>
          <span class="matrix-val highlight-green">+${roiPct}%</span>
          <span class="matrix-sub text-green">Czysty ROI</span>
        </div>
      </div>

      <div class="card-actions">
        <div class="card-main-ctas">
          <a href="${safeZenUrl}" target="_blank" rel="noopener" class="btn-action primary-cta" title="Otwórz zakończoną aukcję w ZenMarket">
            <span class="cta-text">🔍 Podgląd w ZenMarket</span>
            <span class="cta-vpn-badge">Archiwum</span>
          </a>
          ${safeAllegroUrl ? `
            <a href="${safeAllegroUrl}" target="_blank" rel="noopener" class="pill-btn allegro-pill" title="Sprawdź aktualne ceny w Polsce">🇵🇱 Allegro</a>
          ` : ''}
          ${safeOlxUrl ? `
            <a href="${safeOlxUrl}" target="_blank" rel="noopener" class="pill-btn olx-pill" title="Sprawdź ogłoszenia na OLX">🇵🇱 OLX</a>
          ` : ''}
        </div>
      </div>
    </article>
  `;
}

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

function renderDealCard(deal, isAuction) {
  const safeId = escapeHtml(deal.id);
  const safeModel = escapeHtml(deal.model || 'Przedmiot bez nazwy');
  const safeSellerTitle = deal.seller_title ? escapeHtml(deal.seller_title) : '';
  const safeCustomNote = deal.custom_note ? escapeHtml(deal.custom_note) : '';
  const safeColor = deal.color ? escapeHtml(deal.color) : '';
  const safeCategoryName = escapeHtml(deal.category_name || deal.category_id || '');

  const rateJpy = state.data?.meta?.exchange_rates?.rate_jpy || 0.024832;
  const rateEur = state.data?.meta?.exchange_rates?.rate_eur || 4.35;

  const primaryUrl = (deal.links && (deal.links.primary_url || deal.links.zenmarket_sniper || deal.links.zenmarket_buy || deal.links.zenmarket_url)) || '#';
  const endingSoonUrl = (deal.links && deal.links.zenmarket_ending_soon) || primaryUrl;
  const safePrimaryUrl = escapeHtml(sanitizeUrl(primaryUrl));
  const safeEndingSoonUrl = escapeHtml(sanitizeUrl(endingSoonUrl));
  const safeImgUrl = escapeHtml(getSafeImageUrl(deal.image_url));

  const safeCondition = escapeHtml(deal.condition_short_label || deal.condition_badge || 'Sprawny');
  const safeBadgeColor = sanitizeColor(deal.condition_badge_color, '#38bdf8');

  let liveTiming = null;
  let timingBadge = '';
  if (isAuction) {
    liveTiming = getAuctionLiveTiming(deal);
    timingBadge = `<span class="compact-time-badge ${liveTiming.timeClass}" data-ends-at="${escapeHtml(deal.ends_at_iso || '')}">⏳ <strong class="auction-countdown-text">${escapeHtml(liveTiming.formattedCountdown)}</strong></span>`;
  } else {
    timingBadge = `<span class="compact-time-badge compact-time-bin">🛍️ Kup Teraz</span>`;
  }

  const isAuctionEnded = Boolean(isAuction && liveTiming && liveTiming.isEnded);
  const platformLabel = isAuction ? 'Yahoo!' : 'Mercari';
  const platformBadgeClass = isAuction ? 'platform-yahoo' : 'platform-mercari';

  const auctionTargetUrl = (isAuctionEnded && deal.links?.zenmarket_ending_soon)
    ? deal.links.zenmarket_ending_soon
    : ((deal.links && (deal.links.zenmarket_auction || deal.links.zenmarket_sniper || deal.links.primary_url)) || primaryUrl);
  const mercariBuyUrl = (deal.links && deal.links.zenmarket_buy) || primaryUrl;
  const ctaUrl = isAuction ? auctionTargetUrl : mercariBuyUrl;
  const safeCtaUrl = escapeHtml(sanitizeUrl(ctaUrl));
  const ctaText = isAuctionEnded
    ? '⏰ Szukaj w ZenMarket'
    : (isAuction ? '🎯 Licytuj' : '🛒 Kup Teraz');

  const priceJpy = Number(deal.price_jpy) || 0;
  const pricePlnRaw = deal.price_pln_raw !== undefined ? Number(deal.price_pln_raw) : round2(priceJpy * rateJpy);
  const landedPln = deal.landed_cost_pln !== undefined ? Number(deal.landed_cost_pln) : 0;
  const resalePln = Number(deal.est_pl_value) || 0;
  const estMargin = deal.est_margin_pln !== undefined ? Number(deal.est_margin_pln) : (deal.expected_margin_pln !== undefined ? Number(deal.expected_margin_pln) : 0);
  const roiPct = deal.roi_percent !== undefined ? Number(deal.roi_percent) : (deal.expected_roi_pct !== undefined ? Number(deal.expected_roi_pct) : 0);
  const profitSign = estMargin >= 0 ? '+' : '';
  const profitClass = estMargin >= 80 ? 'text-green' : (estMargin > 0 ? 'text-amber' : 'text-red');

  const domesticShippingPln = round2(800 * rateJpy);
  const zenHandlingPln = round2(2.0 * rateEur);
  const shippingSharePln = Number(deal.shipping_share_pln) || 30.0;
  const basePurchasePln = round2(pricePlnRaw + domesticShippingPln + zenHandlingPln);
  const subtotalGoodsFreight = round2(basePurchasePln + shippingSharePln);
  const depositFeePln = round2(subtotalGoodsFreight * 0.035);
  const vatPln = round2(subtotalGoodsFreight * 0.23);

  const allegroPrice = deal.allegro_archive_pln ? deal.allegro_archive_pln.toFixed(0) : Math.round(resalePln * 1.08);
  const olxPrice = deal.olx_haggled_pln ? deal.olx_haggled_pln.toFixed(0) : Math.round(resalePln * 0.90);

  const isExpanded = state.expandedDealDetails.has(String(deal.id));

  const allegroSearchUrl = deal.links?.allegro_search ? escapeHtml(sanitizeUrl(deal.links.allegro_search)) : '';
  const olxSearchUrl = deal.links?.olx_search ? escapeHtml(sanitizeUrl(deal.links.olx_search)) : '';
  const buyeeUrl = deal.links?.buyee_url ? escapeHtml(sanitizeUrl(deal.links.buyee_url)) : '';
  const yahooArchiveUrl = deal.links?.yahoo_closed_archive ? escapeHtml(sanitizeUrl(deal.links.yahoo_closed_archive)) : '';

  let inspectionHtml = '';
  if (deal.photo_inspection && deal.photo_inspection.inspected) {
    const pi = deal.photo_inspection;
    const gems = Array.isArray(pi.top_gems) ? pi.top_gems : [];
    const gemsListHtml = gems.map((g) => {
      const gTitle = escapeHtml(g.title || 'Gra');
      const gPlatform = escapeHtml(g.platform || '');
      const gEstVal = Number(g.est_pl_value) || 0;
      const gNote = g.language_note ? escapeHtml(g.language_note) : '';
      const alUrl = g.allegro_search_url ? escapeHtml(sanitizeUrl(g.allegro_search_url)) : '';
      const olUrl = g.olx_search_url ? escapeHtml(sanitizeUrl(g.olx_search_url)) : '';
      return `
        <div class="gem-badge-row">
          <div class="gem-info-col">
            <span class="gem-title">💎 ${gTitle} (${gPlatform})</span>
            ${gNote ? `<small class="gem-note">${gNote}</small>` : ''}
          </div>
          <div class="gem-price-col">
            <span class="gem-val">~${gEstVal} zł</span>
            <div class="gem-links">
              ${alUrl ? `<a href="${alUrl}" target="_blank" rel="noopener" class="gem-link-badge">Allegro ↗</a>` : ''}
              ${olUrl ? `<a href="${olUrl}" target="_blank" rel="noopener" class="gem-link-badge">OLX ↗</a>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');

    inspectionHtml = `
      <div class="inspection-box">
        <div class="inspection-title">
          <span class="inspection-icon">🔍</span>
          <strong>Inspekcja Foto:</strong> ${escapeHtml(pi.lot_type_name || 'Pakiet')} (${escapeHtml(pi.total_items_spotted || 0)} szt.)
        </div>
        ${pi.battery_notes ? `<div class="inspection-battery">${escapeHtml(pi.battery_notes)}</div>` : ''}
        ${pi.break_even_gem ? `<div class="inspection-breakeven">💡 ${escapeHtml(pi.break_even_gem)}</div>` : ''}
        ${gemsListHtml ? `<div class="inspection-gems-list">${gemsListHtml}</div>` : ''}
      </div>
    `;
  }

  return `
    <article class="deal-card compact-deal-card ${isExpanded ? 'is-expanded' : ''} ${isAuctionEnded ? 'deal-card-ended' : ''}" id="card-${safeId}" data-deal-id="${safeId}" data-ends-at="${escapeHtml(deal.ends_at_iso || '')}" data-is-auction="${isAuction ? '1' : '0'}" data-is-ended="${isAuctionEnded ? '1' : '0'}">
      <div class="compact-card-summary">
        <a href="${safeCtaUrl}" target="_blank" rel="noopener" class="compact-card-media" title="Otwórz ofertę w ZenMarket">
          <img src="${safeImgUrl}" alt="${safeModel}" class="compact-card-img" loading="lazy" onerror="this.src='./assets/images/placeholder.svg'" />
          <span class="compact-media-tag ${platformBadgeClass}">${platformLabel}</span>
        </a>

        <div class="compact-card-info">
          <div class="compact-meta-row">
            <span class="compact-badge-cond" style="border-color:${safeBadgeColor}66; color:${safeBadgeColor};">${safeCondition}</span>
            ${timingBadge}
            ${deal.has_battery ? '<span class="compact-badge-bat">🔋 Li-Ion</span>' : '<span class="compact-badge-nobat">🟢 0% Bat</span>'}
          </div>

          <h4 class="compact-card-title">
            <a href="${safeCtaUrl}" target="_blank" rel="noopener" class="compact-title-link" title="${safeModel}">
              ${safeModel}
            </a>
          </h4>

          <div class="compact-metrics-row">
            <div class="metric-item">
              <span class="metric-lbl">Koszt w PL:</span>
              <strong class="metric-val">~${landedPln.toFixed(0)} zł</strong>
            </div>
            <div class="metric-item">
              <span class="metric-lbl">Wkład / Zysk:</span>
              <strong class="metric-val ${profitClass}">${profitSign}${Math.round(estMargin)} zł <small>(${roiPct >= 0 ? '+' : ''}${Math.round(roiPct)}%)</small></strong>
            </div>
          </div>

          <div class="compact-sub-row">
            <span>Cena JP: <strong>${priceJpy.toLocaleString()} JPY</strong> (~${pricePlnRaw.toFixed(0)} zł)</span>
            ${isAuction && deal.max_bid_jpy ? `<span class="compact-cap">Limit: <strong>${Number(deal.max_bid_jpy).toLocaleString()} JPY</strong></span>` : ''}
          </div>
        </div>
      </div>

      <div class="compact-actions-bar">
        <a href="${safeCtaUrl}" target="_blank" rel="noopener" class="btn-compact primary-cta" title="Otwórz bezpośrednio w ZenMarket">
          ${ctaText}
        </a>
        <button class="btn-compact btn-details-toggle" data-deal-id="${safeId}" aria-expanded="${isExpanded ? 'true' : 'false'}" aria-controls="details-${safeId}" title="Pokaż pełną kalkulację, opłaty i tytuł japoński">
          ${isExpanded ? '▲ Ukryj' : '🔍 Szczegóły'}
        </button>
        <button class="btn-compact btn-compact-secondary btn-add-cart" data-deal-id="${safeId}" data-type="${isAuction ? 'auction' : 'mercari'}" title="Dodaj do wspólnej paczki">
          ➕ Paczka
        </button>
        <button class="btn-compact btn-compact-ghost btn-hide-deal" data-deal-id="${safeId}" title="Ukryj tę ofertę z listy">
          ✕ Ukryj
        </button>
      </div>

      <div class="compact-details-panel ${isExpanded ? 'expanded' : ''}" id="details-${safeId}" style="display: ${isExpanded ? 'flex' : 'none'};">
        ${safeSellerTitle ? `
          <div class="details-item">
            <span class="details-lbl">🇯🇵 Tytuł sprzedawcy:</span>
            <div class="details-val font-jp">${safeSellerTitle}</div>
          </div>
        ` : ''}

        ${safeCustomNote ? `
          <div class="details-item">
            <span class="details-lbl">📝 Notatka analityka:</span>
            <div class="details-val">${safeCustomNote}</div>
          </div>
        ` : ''}

        ${safeColor ? `
          <div class="details-item">
            <span class="details-lbl">🎨 Kolor / Wariant:</span>
            <span class="details-val">${safeColor}</span>
          </div>
        ` : ''}

        <div class="details-section-title">📊 Rozbicie Kosztów Landed w Polsce:</div>
        <div class="details-breakdown-grid">
          <div class="details-breakdown-row"><span>Cena zakupu w JP:</span><strong>${priceJpy.toLocaleString()} JPY (~${pricePlnRaw.toFixed(2)} zł)</strong></div>
          <div class="details-breakdown-row"><span>Wysyłka w JP (800 JPY):</span><strong>~${domesticShippingPln.toFixed(2)} zł</strong></div>
          <div class="details-breakdown-row"><span>Prowizja ZenMarket (2 EUR):</span><strong>~${zenHandlingPln.toFixed(2)} zł</strong></div>
          <div class="details-breakdown-row"><span>Udział w frachcie PL:</span><strong>${shippingSharePln.toFixed(2)} zł</strong></div>
          <div class="details-breakdown-row"><span>Opłata depozytowa (3.5%):</span><strong>~${depositFeePln.toFixed(2)} zł</strong></div>
          <div class="details-breakdown-row"><span>Podatek VAT (23%):</span><strong>~${vatPln.toFixed(2)} zł</strong></div>
          <div class="details-breakdown-row highlight"><span>Łączny Koszt Landed:</span><strong class="text-amber">~${landedPln.toFixed(2)} zł</strong></div>
        </div>

        <div class="details-section-title">🇵🇱 Scenariusze Rynkowe & Wycena:</div>
        <div class="details-breakdown-grid">
          <div class="details-breakdown-row"><span>Wycena w Polsce:</span><strong>~${resalePln.toFixed(0)} zł</strong></div>
          <div class="details-breakdown-row"><span>Allegro zakończone:</span><strong>~${allegroPrice} zł</strong></div>
          <div class="details-breakdown-row"><span>OLX (po targu):</span><strong>~${olxPrice} zł</strong></div>
          <div class="details-breakdown-row"><span>Czysty Zysk Netto:</span><strong class="${profitClass}">${profitSign}${estMargin.toFixed(0)} zł</strong></div>
          <div class="details-breakdown-row"><span>Zwrot z Inwestycji:</span><strong class="${profitClass}">${roiPct >= 0 ? '+' : ''}${roiPct.toFixed(1)}%</strong></div>
          ${isAuction && deal.predicted_closure_jpy ? `<div class="details-breakdown-row"><span>Prognoza końcowa:</span><strong>${Number(deal.predicted_closure_jpy).toLocaleString()} JPY</strong></div>` : ''}
          ${isAuction && deal.max_bid_jpy ? `<div class="details-breakdown-row highlight"><span>Twardy Limit Snajpera:</span><strong class="text-amber">${Number(deal.max_bid_jpy).toLocaleString()} JPY</strong></div>` : ''}
        </div>

        ${inspectionHtml}

        <div class="details-links-row">
          ${allegroSearchUrl ? `<a href="${allegroSearchUrl}" target="_blank" rel="noopener" class="pill-btn allegro-pill" title="Sprawdź ceny na Allegro">🇵🇱 Allegro ↗</a>` : ''}
          ${olxSearchUrl ? `<a href="${olxSearchUrl}" target="_blank" rel="noopener" class="pill-btn olx-pill" title="Sprawdź oferty na OLX">🇵🇱 OLX ↗</a>` : ''}
          ${buyeeUrl ? `<a href="${buyeeUrl}" target="_blank" rel="noopener" class="pill-btn" title="Otwórz w Buyee">🌐 Buyee ↗</a>` : ''}
          ${yahooArchiveUrl ? `<a href="${yahooArchiveUrl}" target="_blank" rel="noopener" class="pill-btn" title="Archiwum zakończonych na Yahoo">📊 落札相場 ↗</a>` : ''}
          <button class="pill-btn calc-pill btn-calc-trigger" data-deal-id="${safeId}" data-type="${isAuction ? 'auction' : 'mercari'}" title="Przelicz koszty w kalkulatorze">
            🧮 Snajper / Kalkulator
          </button>
        </div>

        <button class="btn-collapse-details" data-deal-id="${safeId}">▲ Zwiń szczegóły</button>
      </div>
    </article>
  `;
}

function attachCardEvents() {
  document.querySelectorAll('.btn-calc-trigger').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.dealId;
      const type = btn.dataset.type;
      const deal = findDealById(id, type);
      if (deal) openCalculator(deal);
    });
  });

  document.querySelectorAll('.btn-add-cart').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = btn.dataset.dealId;
      const type = btn.dataset.type;
      const deal = findDealById(id, type);
      if (deal) addToCart(deal);
    });
  });

  document.querySelectorAll('.btn-details-toggle, .btn-collapse-details').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = String(btn.dataset.dealId);
      const isExp = !state.expandedDealDetails.has(id);
      if (isExp) {
        state.expandedDealDetails.add(id);
      } else {
        state.expandedDealDetails.delete(id);
      }
      const card = document.getElementById(`card-${id}`);
      if (card) {
        const panel = card.querySelector('.compact-details-panel');
        const toggleBtn = card.querySelector('.btn-details-toggle');
        card.classList.toggle('is-expanded', isExp);
        if (panel) {
          panel.style.display = isExp ? 'flex' : 'none';
          panel.classList.toggle('expanded', isExp);
        }
        if (toggleBtn) {
          toggleBtn.textContent = isExp ? '▲ Ukryj' : '🔍 Szczegóły';
          toggleBtn.setAttribute('aria-expanded', isExp ? 'true' : 'false');
        }
      }
    });
  });

  document.querySelectorAll('.btn-hide-deal').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = String(btn.dataset.dealId);
      state.hiddenDeals.add(id);
      const card = document.getElementById(`card-${id}`);
      if (card) {
        card.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
        card.style.opacity = '0';
        card.style.transform = 'translateY(-10px)';
        setTimeout(() => {
          renderDeals();
        }, 200);
      } else {
        renderDeals();
      }
    });
  });

  document.querySelectorAll('.btn-unhide-all').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.hiddenDeals.clear();
      renderDeals();
    });
  });

  const showMoreBtn = document.getElementById('toggleShowAllBtn');
  if (showMoreBtn) {
    showMoreBtn.addEventListener('click', () => {
      state.showAllOpportunities = !state.showAllOpportunities;
      renderDeals();
    });
  }
}

function findDealById(id, type) {
  if (!state.data) return null;
  const list = type === 'auction' ? state.data.auctions : state.data.mercari_deals;
  return list.find((d) => String(d.id) === String(id));
}

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

  const shippingShares = {
    nintendo_switch_lite: 30.0,
    nintendo_switch: 45.0,
    nintendo_3ds_handhelds: 30.0,
    nintendo_ds_handhelds: 30.0,
    gameboy_advance_retro: 25.0,
    ps_vita: 35.0,
    ps_vita_handhelds: 35.0,
    psp_handheld: 30.0,
    retro_games_mix: 20.0,
    danshari_mystery_lots: 35.0,
    high_margin_curated_consoles: 65.0,
    film_cameras_point_shoot: 25.0,
    analog_lenses: 25.0,
    ps5_limited_controllers: 30.0
  };
  const shippingShare = shippingShares[catId] !== undefined ? shippingShares[catId] : 30.0;

  const pricePlnRaw = round2(bidJpy * rateJpy);
  const domesticShippingPln = round2(800 * rateJpy);
  const zenHandlingPln = round2(2.0 * rateEur);
  const zenTotalFeePln = round2(domesticShippingPln + zenHandlingPln);

  const basePurchasePln = round2(pricePlnRaw + domesticShippingPln + zenHandlingPln);
  const subtotalGoodsAndFreight = round2(basePurchasePln + shippingShare);
  const depositFeePln = round2(subtotalGoodsAndFreight * 0.035);
  const vatPln = round2(subtotalGoodsAndFreight * 0.23);
  const totalLandedPln = round2(basePurchasePln + shippingShare + depositFeePln + vatPln);

  const netProfitPln = round2(resalePln - totalLandedPln);
  const roiPct = totalLandedPln > 0 ? (netProfitPln / totalLandedPln) * 100 : 0;

  elements.calcBidPlnPreview.textContent = `~${pricePlnRaw.toFixed(0)} zł`;
  elements.resRawPln.textContent = `${pricePlnRaw.toFixed(2)} zł`;
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

  let aviaAvailable = weightG <= 2000 && weightG > 0;
  let aviaJpy = 0;
  if (aviaAvailable) {
    if (weightG <= 100) aviaJpy = 1200;
    else aviaJpy = 1200 + Math.ceil((weightG - 100) / 100) * 150;
  }
  const aviaPln = aviaAvailable ? Math.round(aviaJpy * rateJpy * 100) / 100 : null;

  let emsJpy = 0;
  if (weightG > 0) {
    if (weightG <= 500) emsJpy = 3900;
    else if (weightG <= 2000) emsJpy = 3900 + Math.ceil((weightG - 500) / 250) * 350;
    else emsJpy = 6000 + Math.ceil((weightG - 2000) / 500) * 700;
  }
  const emsPln = weightG > 0 ? Math.round(emsJpy * rateJpy * 100) / 100 : 0;

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
  const exists = state.cart.some((it) => String(it.id) === String(deal.id));
  if (exists) {
    showToast(`"${deal.model}" jest już w koszyku!`);
    return;
  }

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

  if (elements.cartStatItems) elements.cartStatItems.textContent = `${count} szt.`;
  if (elements.cartStatLanded) elements.cartStatLanded.textContent = `~${details.totalLandedPln.toFixed(0)} zł`;
  if (elements.cartStatResale) elements.cartStatResale.textContent = `${details.totalResalePln.toFixed(0)} zł`;
  if (elements.cartStatProfit) {
    elements.cartStatProfit.textContent = `${details.residualProfitPln >= 0 ? '+' : ''}${details.residualProfitPln.toFixed(0)} zł`;
    elements.cartStatProfit.className = details.residualProfitPln >= 0 ? 'text-green' : 'text-red';
  }

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
    const safeModel = escapeHtml(item.model || 'Przedmiot');
    const safeId = escapeHtml(item.id);
    const landed = (Number(item.landed_cost_pln) || 0).toFixed(0);
    const resale = (Number(item.est_pl_value) || 0).toFixed(0);
    const margin = (Number(item.est_margin_pln) || 0).toFixed(0);
    return `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <strong class="cart-item-title">${safeModel}</strong>
          <span class="cart-item-sub">
            Landed: ~${landed} zł | Resale: ${resale} zł | 
            <span class="text-sky font-semibold">⚖️ ~${itemWeight}g</span> | 
            ${item.has_battery ? '<span class="text-amber">🔴 Li-Ion</span>' : '<span class="text-green">🟢 0% Baterii</span>'}
          </span>
        </div>
        <div class="cart-item-right">
          <strong class="text-green">+${margin} zł</strong>
          <button class="btn-remove-item" data-cart-id="${safeId}" title="Usuń z koszyka">✕</button>
        </div>
      </div>
    `;
  }).join('');
}

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

function initLiveCountdownTicker() {
  function updateCountdowns() {
    const cards = document.querySelectorAll('.deal-card[data-is-auction="1"]');
    if (!cards || cards.length === 0) return;
    const now = Date.now();

    cards.forEach((card) => {
      if (card._removing) return;

      const endsAtStr = card.getAttribute('data-ends-at');
      const endsAt = endsAtStr ? new Date(endsAtStr).getTime() : NaN;
      const diffMs = !isNaN(endsAt) ? endsAt - now : -1;

      if (diffMs <= 0) {
        card.setAttribute('data-is-ended', '1');

        const dealId = card.id ? card.id.replace('card-', '') : null;
        if (dealId && state.data && Array.isArray(state.data.auctions)) {
          state.data.auctions = state.data.auctions.filter(a => String(a.id) !== String(dealId));
        }

        if (elements.auctionsCountBadge) {
          const liveRemaining = document.querySelectorAll('.deal-card[data-is-auction="1"]:not([data-is-ended="1"])').length;
          elements.auctionsCountBadge.textContent = liveRemaining;
        }

        card._removing = true;
        card.classList.add('deal-card-fade-out');

        setTimeout(() => {
          card.remove();

          if (elements.auctionsCountBadge) {
            const remaining = document.querySelectorAll('.deal-card[data-is-auction="1"]').length;
            elements.auctionsCountBadge.textContent = remaining;
          }

          if (state.currentView === 'auctions' && document.querySelectorAll('.deal-card[data-is-auction="1"]').length === 0) {
            elements.feedContainer.innerHTML = `
              <div class="empty-cart-hint">
                <p>Brak aktywnych licytacji w tym momencie.</p>
                <small>Wszystkie bieżące licytacje zostały zakończone. Sprawdź sekcję Kup Teraz (Mercari) lub przejdź do Strumieni Snajpera!</small>
              </div>
            `;
          }
        }, 450);

        return;
      }

      const totalSecs = Math.max(0, Math.floor(diffMs / 1000));
      const minsRemaining = Math.max(0, Math.floor(diffMs / 60000));
      const ribbon = card.querySelector('.time-ribbon');
      const ribbonText = card.querySelector('.auction-countdown-text');
      const badgeText = card.querySelector('.badge-countdown-text');
      const mediaBadge = card.querySelector('.media-time-badge');
      const stageEl = ribbon ? ribbon.querySelector('.time-ribbon-stage') : null;
      const iconEl = ribbon ? ribbon.querySelector('.time-ribbon-icon') : null;

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

  updateCountdowns();
  if (window._countdownInterval) clearInterval(window._countdownInterval);
  window._countdownInterval = setInterval(updateCountdowns, 1000);
  window.updateLiveCountdowns = updateCountdowns;
}

window.removeFromCart = removeFromCart;
window.selectShippingMethod = selectShippingMethod;
