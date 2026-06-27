/* ============================================================
   Cache Manager – UI Enhancements (Vanilla JS)
   ============================================================ */
(function () {
  'use strict';

  // ── Constants ──────────────────────────────────────────────
  const REFRESH_INTERVAL_MS = 15_000;
  const TOAST_DURATION_MS   = 4_000;
  const TAB_SELECTOR        = '#cache-manager-tab';
  const BAR_FILL_SELECTOR   = '.cm-bar-fill';
  const LOG_SELECTOR        = '.cm-log';

  // ── State ──────────────────────────────────────────────────
  let refreshTimer   = null;
  let tabIsVisible   = true;
  let toastContainer = null;

  // ── Utility ────────────────────────────────────────────────
  /**
   * Safely query inside the cache-manager tab.
   * @param {string} sel  CSS selector
   * @param {boolean} all  Return all matches
   * @returns {Element|NodeList|null}
   */
  function q(sel, all = false) {
    const root = document.querySelector(TAB_SELECTOR);
    if (!root) return all ? [] : null;
    return all ? root.querySelectorAll(sel) : root.querySelector(sel);
  }

  // ── Toast Notification System ──────────────────────────────
  function ensureToastContainer() {
    if (toastContainer && document.body.contains(toastContainer)) return;
    toastContainer = document.createElement('div');
    toastContainer.className = 'cm-toast-container';
    document.body.appendChild(toastContainer);
  }

  /**
   * Show a toast notification.
   * @param {string} message  Text to display
   * @param {'success'|'warning'|'error'|'info'} type  Visual variant
   * @param {number} duration  Auto-dismiss time (ms)
   */
  function showToast(message, type = 'info', duration = TOAST_DURATION_MS) {
    ensureToastContainer();

    const icons = {
      success: '✓',
      warning: '⚠',
      error:   '✕',
      info:    'ℹ',
    };

    const toast = document.createElement('div');
    toast.className = `cm-toast cm-toast-${type}`;

    const icon = document.createElement('span');
    icon.textContent = icons[type] || 'ℹ';
    icon.setAttribute('aria-hidden', 'true');
    icon.style.fontSize = '1.1em';

    const text = document.createElement('span');
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);
    toastContainer.appendChild(toast);

    const dismiss = () => {
      toast.classList.add('removing');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    };

    toast.addEventListener('click', dismiss);
    setTimeout(dismiss, duration);
  }

  // Expose globally so Python callbacks can trigger toasts
  window.cmToast = showToast;

  // ── Progress Bar Animations ────────────────────────────────
  /**
   * Set a progress bar's width and apply the correct usage class.
   * @param {Element} barEl  The .cm-bar-fill element
   * @param {number} percent  0-100
   */
  function setBarProgress(barEl, percent) {
    const clamped = Math.max(0, Math.min(100, percent));
    barEl.style.width = `${clamped}%`;

    // Remove old usage classes
    barEl.classList.remove('usage-low', 'usage-mid', 'usage-high', 'usage-critical');

    if (clamped < 50) {
      barEl.classList.add('usage-low');
    } else if (clamped < 75) {
      barEl.classList.add('usage-mid');
    } else if (clamped < 90) {
      barEl.classList.add('usage-high');
    } else {
      barEl.classList.add('usage-critical');
    }
  }

  // Expose globally for Gradio Python callbacks
  window.cmSetBar = setBarProgress;

  /**
   * Update all progress bars that carry a `data-cm-percent` attribute.
   * Useful after Gradio re-renders the component.
   */
  function refreshAllBars() {
    const bars = q(BAR_FILL_SELECTOR, true);
    bars.forEach((bar) => {
      const pct = parseFloat(bar.dataset.cmPercent);
      if (!isNaN(pct)) setBarProgress(bar, pct);
    });
  }

  // ── Tab Visibility Detection ───────────────────────────────
  function handleVisibilityChange() {
    tabIsVisible = !document.hidden;

    if (tabIsVisible) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }

  // ── Auto-Refresh Logic ─────────────────────────────────────
  function triggerResourceRefresh() {
    // Click Gradio's hidden refresh button if it exists
    const refreshBtn = q('#cm-refresh-btn');
    if (refreshBtn) {
      refreshBtn.click();
    }
    refreshAllBars();
  }

  function startAutoRefresh() {
    if (refreshTimer) return;
    refreshTimer = setInterval(() => {
      if (tabIsVisible) triggerResourceRefresh();
    }, REFRESH_INTERVAL_MS);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  // ── Button Tooltips ────────────────────────────────────────
  /**
   * Scan buttons inside the tab and attach tooltip attributes
   * based on their `data-cm-tooltip` or title attributes.
   */
  function initTooltips() {
    const buttons = q('.cm-btn', true);
    buttons.forEach((btn) => {
      // Prefer explicit data attribute; fall back to title
      if (!btn.hasAttribute('data-cm-tooltip') && btn.title) {
        btn.setAttribute('data-cm-tooltip', btn.title);
        btn.removeAttribute('title'); // avoid native tooltip overlap
      }
    });
  }

  // ── Log Area Helpers ───────────────────────────────────────
  /**
   * Append a styled line to the log area.
   * @param {string} message
   * @param {'success'|'warning'|'error'|'info'} level
   */
  function appendLog(message, level = 'info') {
    const log = q(LOG_SELECTOR);
    if (!log) return;

    const line = document.createElement('div');
    line.className = `log-${level}`;
    const ts = new Date().toLocaleTimeString();
    line.textContent = `[${ts}] ${message}`;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
  }

  window.cmLog = appendLog;

  // ── Mutation Observer (handle Gradio re-renders) ───────────
  function watchForReRenders() {
    const tab = document.querySelector(TAB_SELECTOR);
    if (!tab) return;

    const observer = new MutationObserver(() => {
      refreshAllBars();
      initTooltips();
    });

    observer.observe(tab, { childList: true, subtree: true });
  }

  // ── Initialisation ────────────────────────────────────────
  function init() {
    const tab = document.querySelector(TAB_SELECTOR);
    if (!tab) {
      // Tab not yet in the DOM — retry shortly
      setTimeout(init, 500);
      return;
    }

    ensureToastContainer();
    initTooltips();
    refreshAllBars();
    watchForReRenders();

    document.addEventListener('visibilitychange', handleVisibilityChange);
    startAutoRefresh();

    // Initial refresh
    triggerResourceRefresh();

    console.info('[Cache Manager] UI enhancements loaded.');
  }

  // Hook into Gradio's lifecycle
  if (typeof onUiLoaded === 'function') {
    onUiLoaded(init);
  } else {
    // Fallback: wait for DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }
})();
