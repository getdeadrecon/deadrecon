/**
 * DeadRecon App Core — Grid Interface Logic
 * SocketIO connection, toast system, and shared utilities
 */

// ── SocketIO Connection ──────────────────────────────────────
let socket = null;
let isConnected = false;

function initSocket() {
  if (socket) return;                          // idempotent
  if (typeof io === 'undefined') return;       // sign-in pages don't load socket.io
  socket = io({ transports: ['websocket', 'polling'], reconnectionAttempts: 10 });

  socket.on('connect', () => {
    isConnected = true;
    setConnectionStatus('online');
  });

  socket.on('disconnect', () => {
    isConnected = false;
    setConnectionStatus('offline');
  });

  socket.on('reconnect_attempt', () => {
    setConnectionStatus('connecting');
  });

  socket.on('server_ready', (data) => {
    appendTerminalLine('live-terminal', 'DEADRECON', data.message, 'system');
  });

  // Global scan event handlers (for any open terminal on page)
  socket.on('terminal_log', (data) => {
    const module = (data.module || 'SYS').toUpperCase().padEnd(12);
    appendTerminalLine('live-terminal', module, data.message, data.level || 'info');
  });

  socket.on('scan_complete', (data) => {
    showToast(
      `Scan complete. Risk Score: ${data.shadow_score?.toFixed(0)}/100 — ${data.result_count} results found.`,
      'success'
    );
  });

  socket.on('scan_failed', (data) => {
    showToast(`Scan failed: ${data.error}`, 'error');
  });

  socket.on('module_start', (data) => {
    appendTerminalLine('live-terminal', data.module.toUpperCase(), `Running...`, 'system');
  });

  socket.on('module_complete', (data) => {
    appendTerminalLine(
      'live-terminal',
      data.module.toUpperCase(),
      `${data.result_count} result(s) found`,
      'success'
    );
    const fill = document.getElementById('progress-fill');
    const pct  = document.getElementById('progress-pct');
    if (fill) fill.style.width = `${data.progress}%`;
    if (pct)  pct.textContent = `${data.progress}%`;
  });
}

function setConnectionStatus(state) {
  const dot  = document.getElementById('connection-dot');
  const text = document.getElementById('connection-status');
  if (!dot || !text) return;
  const states = {
    online:     { cls: 'online',  label: 'ONLINE' },
    offline:    { cls: '',        label: 'OFFLINE' },
    connecting: { cls: '',        label: 'CONNECTING...' },
  };
  const s = states[state] || states.offline;
  dot.className  = 'status-dot ' + s.cls;
  text.textContent = s.label;
  text.style.color = state === 'online' ? 'var(--neon-green)' : 'var(--text-dim)';
}


function appendTerminalLine(termId, module, message, level) {
  const term = document.getElementById(termId);
  if (!term) return;

  const line = document.createElement('div');
  line.className = `term-line term-${level || 'info'}`;

  const ts = new Date().toTimeString().slice(0,8);
  line.innerHTML = `
    <span class="term-prompt">[${ts}][${escapeHtml((module || 'SYS').slice(0,10).padEnd(10))}]</span>
    <span class="term-msg">${escapeHtml(message)}</span>
  `;

  term.appendChild(line);

  // Keep last 150 lines
  while (term.children.length > 150) {
    term.removeChild(term.firstChild);
  }
  term.scrollTop = term.scrollHeight;
}

// ── Toast Notifications ──────────────────────────────────────
function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = { success: '✓', error: '✗', warning: '⚠', info: 'ℹ' };
  toast.innerHTML = `<span style="margin-right:0.5rem">${icons[type] || 'ℹ'}</span>${escapeHtml(message)}`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'none';
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Utility Functions ────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copied to clipboard', 'success', 2000))
    .catch(() => showToast('Copy failed', 'error', 2000));
}

function formatBytes(bytes) {
  const units = ['B','KB','MB','GB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

function timeAgo(dateStr) {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr);
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h/24)}d ago`;
}

// ── Boot Sequence ─────────────────────────────────────────────
// Initialise the socket immediately — scripts on the results page need it
// before DOMContentLoaded fires (socket.io is already loaded by this point).
initSocket();

document.addEventListener('DOMContentLoaded', () => {
  // initSocket() already called above; this is a no-op guard

  // Auto-dismiss flashes after 6s
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 6000);
  });

  // Animate stat values counting up
  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (!isNaN(target) && target > 0) {
      let current = 0;
      const step = Math.ceil(target / 30);
      const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current.toLocaleString();
        if (current >= target) clearInterval(timer);
      }, 30);
    }
  });

  // Animate risk score bars (.shadow-score-fill = legacy class name for the risk score)
  document.querySelectorAll('.shadow-score-fill').forEach(el => {
    const width = el.style.width;
    el.style.width = '0%';
    setTimeout(() => { el.style.width = width; }, 200);
  });

  document.querySelectorAll('.score-fill').forEach(el => {
    const width = el.style.width;
    el.style.width = '0%';
    setTimeout(() => { el.style.width = width; }, 300);
  });
});

// ── Markup behaviours ────────────────────────────────────────
// The content security policy blocks inline handlers, so these are wired here.
document.addEventListener('submit', (event) => {
  const message = event.target.dataset && event.target.dataset.confirm;
  if (message && !window.confirm(message)) event.preventDefault();
});

document.addEventListener('click', (event) => {
  const close = event.target.closest('.flash-close');
  if (close) close.parentElement.remove();
  const raw = event.target.closest('[data-toggle-raw]');
  if (raw) raw.closest('.card').querySelector('.raw-body').classList.toggle('hidden');
});

document.addEventListener('input', (event) => {
  const output = event.target.dataset && event.target.dataset.output;
  if (output) document.getElementById(output).textContent = event.target.value;
});

// ── One-click Tor ────────────────────────────────────────────
(function torButton() {
  const button = document.getElementById('tor-toggle');
  if (!button) return;
  const label = document.getElementById('tor-label');
  let timer = null;
  let lastState = null;

  function show(status) {
    const state = status.enabled ? status.state : 'off';
    button.dataset.state = state;
    button.setAttribute('aria-pressed', status.enabled ? 'true' : 'false');
    button.title = status.message + (status.source ? ` (${status.source})` : '');
    label.textContent = {
      off: 'Tor',
      starting: status.percent ? `Tor ${status.percent}%` : 'Tor…',
      ready: 'Tor on',
      failed: 'Tor failed',
    }[state];
    if (lastState && state !== lastState) {
      if (state === 'ready') showToast('Tor is on. Scan traffic is confirmed to be using it.', 'success');
      if (state === 'failed') showToast(status.message, 'error', 12000);
    }
    lastState = state;
    const chip = document.querySelector('a.stealth-chip');
    if (chip && status.posture) {
      chip.className = `stealth-chip stealth-${status.posture.level}`;
      chip.querySelector('.stealth-label').textContent = status.posture.label;
    }
    clearTimeout(timer);
    if (status.enabled) timer = setTimeout(refresh, state === 'starting' ? 1000 : 15000);
  }

  async function refresh() {
    try {
      show(await (await fetch(button.dataset.url)).json());
    } catch (error) {
      timer = setTimeout(refresh, 5000);
    }
  }

  button.addEventListener('click', async () => {
    // Clicking a failed button tries again rather than turning Tor off.
    const enabled = button.getAttribute('aria-pressed') !== 'true' || button.dataset.state === 'failed';
    button.disabled = true;
    try {
      const reply = await fetch(button.dataset.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': button.dataset.csrf },
        body: JSON.stringify({ enabled }),
      });
      show(await reply.json());
    } catch (error) {
      showToast('Tor could not be changed. Please try again.', 'error');
    } finally {
      button.disabled = false;
    }
  });

  refresh();
})();
