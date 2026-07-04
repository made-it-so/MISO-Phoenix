/**
 * MISO Consigliere Widget
 * ──────────────────────
 * Self-contained. Drop one <script> tag on any page.
 * Injects a floating "Ask MISO" button + slide-up panel.
 *
 * Features:
 *  - Omnipresent: fixed bottom-right, survives page navigation (SPA-safe)
 *  - Proactive: polls consigliere_agent's open questions every 60s as a badge
 *  - Context-aware: folds current page context into the first line of each message
 *  - Persistent: keeps last 8 conversations + the active session id in sessionStorage
 *  - Session-based: talks to consigliere_agent's real /sessions API, not a single-shot endpoint
 */
(function MISOConsigliere() {
  'use strict';

  // ── Config ─────────────────────────────────────────────────────────────────
  const API        = '';   // same origin
  const ALERT_POLL = 60 * 1000;       // 1 min — re-polls open questions
  const MAX_HISTORY = 8;
  const WIDGET_ID  = '__miso_cons_widget__';

  // Identity — loaded from /api/identity, falls back to defaults
  let _identity = {
    advisor_name: 'MISO',
    tagline:      'powered by MISO',
    btn_label:    'Ask MISO',
    panel_title:  'MISO',
  };

  // Don't double-inject
  if (document.getElementById(WIDGET_ID)) return;

  // ── State ──────────────────────────────────────────────────────────────────
  let _open       = false;
  let _thinking   = false;
  let _alertCount = 0;
  let _alerts     = [];
  let _history    = JSON.parse(sessionStorage.getItem('miso_cons_history') || '[]');
  let _session    = JSON.parse(sessionStorage.getItem('miso_cons_session') || '[]'); // current session messages
  let _sessionId  = JSON.parse(sessionStorage.getItem('miso_cons_session_id') || 'null'); // consigliere_agent session id

  // ── Styles ─────────────────────────────────────────────────────────────────
  const css = `
  #${WIDGET_ID} {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 99999;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #e4e4e7;
  }

  #__miso_btn__ {
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #0d9488, #6366f1);
    color: #fff;
    border: none;
    border-radius: 100px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 24px rgba(13,148,136,.4);
    transition: transform .15s, box-shadow .15s;
    white-space: nowrap;
    position: relative;
    letter-spacing: -.01em;
  }
  #__miso_btn__:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(13,148,136,.5); }
  #__miso_btn__.has-alerts { animation: __pulse__ 2s ease-in-out infinite; }

  @keyframes __pulse__ {
    0%,100% { box-shadow: 0 4px 24px rgba(239,68,68,.35); }
    50%      { box-shadow: 0 4px 32px rgba(239,68,68,.65); }
  }

  #__miso_badge__ {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #ef4444;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    border-radius: 99px;
    min-width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    border: 2px solid #080810;
  }

  #__miso_panel__ {
    position: fixed;
    bottom: 80px;
    right: 24px;
    width: 480px;
    max-width: calc(100vw - 32px);
    max-height: 75vh;
    background: #111118;
    border: 1px solid #27272a;
    border-radius: 20px;
    box-shadow: 0 24px 80px rgba(0,0,0,.7);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transform: scale(.96) translateY(8px);
    opacity: 0;
    pointer-events: none;
    transition: transform .25s cubic-bezier(.34,1.56,.64,1), opacity .2s;
  }
  #__miso_panel__.open {
    transform: none;
    opacity: 1;
    pointer-events: all;
  }

  .__miso_header__ {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px 12px;
    border-bottom: 1px solid #1c1c26;
    flex-shrink: 0;
  }
  .__miso_header__ .title {
    font-weight: 700;
    font-size: 14px;
    flex: 1;
  }
  .__miso_header__ .close-btn {
    background: none;
    border: none;
    color: #52525b;
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
    padding: 2px 4px;
    border-radius: 4px;
    transition: color .15s;
  }
  .__miso_header__ .close-btn:hover { color: #e4e4e7; }

  #__miso_alerts_bar__ {
    padding: 8px 14px;
    background: rgba(146,64,14,.15);
    border-bottom: 1px solid rgba(146,64,14,.3);
    font-size: 12px;
    color: #fbbf24;
    cursor: pointer;
    flex-shrink: 0;
    display: none;
    align-items: center;
    gap: 6px;
  }

  #__miso_scroll__ {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    scroll-behavior: smooth;
  }
  #__miso_scroll__::-webkit-scrollbar { width: 4px; }
  #__miso_scroll__::-webkit-scrollbar-track { background: transparent; }
  #__miso_scroll__::-webkit-scrollbar-thumb { background: #27272a; border-radius: 2px; }

  .__msg__ {
    margin-bottom: 12px;
    animation: __fadeUp__ .3s ease;
  }
  @keyframes __fadeUp__ { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }

  .__msg__.user .bubble {
    background: #1c1c2e;
    border: 1px solid #27272a;
    border-radius: 14px 14px 4px 14px;
    padding: 10px 14px;
    font-size: 13px;
    color: #e4e4e7;
    margin-left: 40px;
  }
  .__msg__.assistant .bubble {
    background: #0d1117;
    border: 1px solid #1f2937;
    border-radius: 4px 14px 14px 14px;
    padding: 12px 14px;
    font-size: 13px;
    color: #d4d4d8;
    margin-right: 16px;
    word-break: break-word;
    overflow-wrap: break-word;
  }

  .__conf_bar__ {
    height: 4px;
    background: #27272a;
    border-radius: 2px;
    overflow: hidden;
    margin: 6px 0 4px;
  }
  .__conf_fill__ {
    height: 100%;
    border-radius: 2px;
    transition: width 1s ease;
  }
  .__ev_badge__ {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 4px;
    background: #27272a;
    color: #a78bfa;
    font-family: monospace;
    margin-right: 4px;
  }
  .__detail__ {
    font-size: 11px;
    color: #52525b;
    margin-top: 6px;
    cursor: pointer;
    user-select: none;
  }
  .__detail__:hover { color: #71717a; }

  .__typing__ { display: flex; gap: 4px; padding: 4px 2px; }
  .__typing__ span {
    width: 6px; height: 6px;
    background: #14b8a6;
    border-radius: 50%;
    animation: __bounce__ 1.2s infinite;
  }
  .__typing__ span:nth-child(2) { animation-delay: .2s; }
  .__typing__ span:nth-child(3) { animation-delay: .4s; }
  @keyframes __bounce__ {
    0%,80%,100% { transform:scale(.6); opacity:.4; }
    40% { transform:scale(1); opacity:1; }
  }

  .__miso_input_area__ {
    padding: 10px 14px 14px;
    border-top: 1px solid #1c1c26;
    flex-shrink: 0;
  }
  .__miso_textarea__ {
    width: 100%;
    background: #0d0d14;
    border: 1.5px solid #3f3f46;
    border-radius: 12px;
    color: #f4f4f5;
    font-size: 13px;
    padding: 10px 14px;
    resize: none;
    outline: none;
    transition: border-color .2s;
    font-family: inherit;
    box-sizing: border-box;
  }
  .__miso_textarea__:focus { border-color: #14b8a6; }
  .__miso_textarea__::placeholder { color: #3f3f46; }

  .__send_btn__ {
    width: 100%;
    margin-top: 8px;
    background: linear-gradient(135deg,#0d9488,#14b8a6);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 10px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity .15s;
  }
  .__send_btn__:hover:not(:disabled) { opacity: .9; }
  .__send_btn__:disabled { opacity: .45; cursor: not-allowed; }

  .__quick_pills__ {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .__quick_pill__ {
    font-size: 11px;
    padding: 4px 10px;
    background: #1c1c26;
    border: 1px solid #27272a;
    border-radius: 20px;
    cursor: pointer;
    color: #a1a1aa;
    transition: background .15s, color .15s;
    white-space: nowrap;
  }
  .__quick_pill__:hover { background: #27272a; color: #e4e4e7; }

  #__miso_alerts_panel__ {
    padding: 10px 14px;
    border-bottom: 1px solid #1c1c26;
    display: none;
    flex-shrink: 0;
  }
  .__alert_row__ {
    background: rgba(146,64,14,.12);
    border: 1px solid rgba(146,64,14,.25);
    border-radius: 8px;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 12px;
  }
  .__alert_row__ .at { color: #fbbf24; font-weight: 600; }
  .__alert_row__ .adesc { color: #a1a1aa; margin-top: 2px; }
  .__alert_dismiss__ {
    float: right;
    background: none;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    color: #52525b;
    font-size: 11px;
    cursor: pointer;
    padding: 1px 6px;
  }
  .__alert_dismiss__:hover { color: #a1a1aa; }
  `;

  // ── Quick starters ─────────────────────────────────────────────────────────
  const QUICK_PROMPTS = [
    'What should I prioritise today?',
    'What am I missing about this situation?',
    'Is there anything I should be worried about?',
    "What's the strongest argument against what I'm doing?",
    'Summarise what you know about my current work',
  ];

  // ── Brief Me button (separate from quick pills) ─────────────────────────────
  async function triggerBrief() {
    const btn = document.getElementById('__miso_brief_btn__');
    if (btn) { btn.disabled = true; btn.textContent = 'Briefing…'; }
    try {
      const res  = await fetch(`${API}/apps/consigliere_agent/brief`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ focus: buildPageContext() }),
      });
      const data = await res.json();
      if (data.brief) {
        appendBubble('assistant', formatReply({ response: data.brief }), true);
        scrollBottom();
      }
    } catch (e) {
      appendBubble('assistant', '<em>Could not reach Brief endpoint.</em>', true);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = 'Brief Me'; }
      if (!_open) open();
    }
  }

  // ── Identity loading ───────────────────────────────────────────────────────
  async function loadIdentity() {
    try {
      const data = await fetch(`${API}/api/identity`).then(r => r.json());
      if (data.advisor_name) {
        _identity = data;
        applyIdentity();
      }
    } catch {}
  }

  function applyIdentity() {
    const btn   = document.getElementById('__miso_btn__');
    const title = document.getElementById('__miso_panel_title__');
    const sub   = document.getElementById('__miso_panel_sub__');
    const input = document.getElementById('__miso_input__');

    if (btn) {
      // Preserve badge element, just update the text
      const badge = document.getElementById('__miso_badge__');
      btn.innerHTML = `<span style="font-size:16px;">🧠</span>${_esc(_identity.btn_label)}`;
      if (badge) btn.appendChild(badge);
    }
    if (title) title.textContent = _identity.panel_title;
    if (sub)   sub.textContent   = _identity.tagline;
    if (input) input.placeholder = `Ask ${_identity.advisor_name} anything — decisions, priorities, risks…`;
  }

  // ── Build DOM ──────────────────────────────────────────────────────────────
  function build() {
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);

    const root = document.createElement('div');
    root.id = WIDGET_ID;
    root.innerHTML = `
      <div id="__miso_panel__">
        <div class="__miso_header__">
          <span style="font-size:18px;">🧠</span>
          <div style="flex:1;min-width:0;">
            <div class="title" id="__miso_panel_title__">MISO</div>
            <div style="font-size:10px;color:#3f3f46;margin-top:-1px;" id="__miso_panel_sub__">powered by MISO</div>
          </div>
          <span style="font-size:11px;color:#52525b;" id="__miso_ctx_label__"></span>
          <button class="close-btn" onclick="window.__MISO_CONS__.close()">×</button>
        </div>

        <!-- Alert bar (collapsed indicator) -->
        <div id="__miso_alerts_bar__" onclick="window.__MISO_CONS__.toggleAlerts()">
          <span>⚠</span>
          <span id="__miso_alert_count_text__">0 things need your attention</span>
          <span style="margin-left:auto;font-size:10px;color:#92400e;" id="__miso_alert_toggle__">▼ Show</span>
        </div>

        <!-- Alerts expanded panel -->
        <div id="__miso_alerts_panel__"></div>

        <!-- Message scroll area -->
        <div id="__miso_scroll__">
          <div id="__miso_msgs__"></div>
        </div>

        <!-- Input area -->
        <div class="__miso_input_area__">
          <div style="display:flex;gap:6px;margin-bottom:8px;align-items:center;">
            <div class="__quick_pills__" id="__miso_pills__" style="flex:1;"></div>
            <button id="__miso_brief_btn__"
              onclick="window.__MISO_CONS__.triggerBrief()"
              style="flex-shrink:0;font-size:11px;padding:4px 12px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border:none;border-radius:20px;cursor:pointer;color:#fff;font-weight:600;white-space:nowrap;">
              Brief Me
            </button>
          </div>
          <textarea class="__miso_textarea__" id="__miso_input__" rows="2"
            placeholder="Ask MISO anything — decisions, priorities, risks…"
            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();window.__MISO_CONS__.send();}">
          </textarea>
          <button class="__send_btn__" id="__miso_send__" onclick="window.__MISO_CONS__.send()">
            Get advice →
          </button>
        </div>
      </div>

      <button id="__miso_btn__" onclick="window.__MISO_CONS__.toggle()">
        <span style="font-size:16px;">🧠</span>
        Ask MISO
        <span id="__miso_badge__" style="display:none;"></span>
      </button>
    `;
    document.body.appendChild(root);

    // Render quick pills
    const pills = document.getElementById('__miso_pills__');
    QUICK_PROMPTS.forEach(p => {
      const el = document.createElement('button');
      el.className = '__quick_pill__';
      el.textContent = p;
      el.onclick = () => {
        document.getElementById('__miso_input__').value = p;
        document.getElementById('__miso_input__').focus();
      };
      pills.appendChild(el);
    });

    // Restore session messages
    _session.forEach(m => appendBubble(m.role, m.content, false));
    if (_session.length) scrollBottom();
  }

  // ── Panel open/close ───────────────────────────────────────────────────────
  function toggle() {
    _open ? close() : open();
  }
  function open() {
    _open = true;
    document.getElementById('__miso_panel__').classList.add('open');
    document.getElementById('__miso_input__').focus();
    refreshCtxLabel();
    scrollBottom();
  }
  function close() {
    _open = false;
    document.getElementById('__miso_panel__').classList.remove('open');
  }

  function refreshCtxLabel() {
    const hash  = location.hash.replace('#','');
    const title = document.title.replace(' - MISO','').replace('MISO —','').trim();
    const label = hash || title || '';
    const el    = document.getElementById('__miso_ctx_label__');
    if (el) el.textContent = label ? `📍 ${label}` : '';
  }

  // ── Alerts ─────────────────────────────────────────────────────────────────
  let _alertsExpanded = false;

  function toggleAlerts() {
    _alertsExpanded = !_alertsExpanded;
    const panel  = document.getElementById('__miso_alerts_panel__');
    const toggle = document.getElementById('__miso_alert_toggle__');
    if (_alertsExpanded) {
      panel.style.display = 'block';
      toggle.textContent  = '▲ Hide';
      renderAlertRows();
    } else {
      panel.style.display = 'none';
      toggle.textContent  = '▼ Show';
    }
  }

  // "Alerts" = open (unresolved) questions consigliere_agent has surfaced —
  // there's no separate alerts/monitor concept in the current backend, this
  // reuses the /questions resource, which is the real, working equivalent.
  function renderAlertRows() {
    const panel = document.getElementById('__miso_alerts_panel__');
    if (!_alerts.length) {
      panel.innerHTML = '<div style="font-size:12px;color:#52525b;padding:4px 0;">No alerts right now.</div>';
      return;
    }
    panel.innerHTML = _alerts.map((a, idx) => {
      const title = a.title || a.text || 'Alert';
      const body  = a.body  || '';
      const typeLabel = {
        meeting_brief:  'Meeting',
        critical_alert: 'Critical',
        action_email:   'Email',
        manual_brief:   'Briefing',
      }[a.type] || 'Alert';
      return `
      <div class="__alert_row__">
        <button class="__alert_dismiss__" onclick="window.__MISO_CONS__.dismissAlert(${idx})">Dismiss</button>
        <div class="at">${_esc(typeLabel)}: ${_esc(title)}</div>
        ${body ? `<div class="adesc">${_esc(body)}</div>` : ''}
        <button style="margin-top:6px;font-size:11px;padding:2px 8px;background:#1c1c26;border:1px solid #3f3f46;border-radius:6px;cursor:pointer;color:#a1a1aa;"
          onclick="window.__MISO_CONS__.reask(${JSON.stringify(title)})">
          Tell me more →
        </button>
      </div>`;
    }).join('');
  }

  function dismissAlert(idx) {
    _alerts.splice(idx, 1);
    updateBadge(_alerts.length);
    renderAlertRows();
    if (!_alerts.length && _alertsExpanded) toggleAlerts();
  }

  function reask(question) {
    document.getElementById('__miso_input__').value = question;
    if (_alertsExpanded) toggleAlerts();
    open();
    document.getElementById('__miso_input__').focus();
  }

  // ── SSE subscription ───────────────────────────────────────────────────────
  let _sseRetryTimer = null;

  function subscribeSSE() {
    if (typeof EventSource === 'undefined') return;
    const es = new EventSource(`${API}/apps/consigliere_agent/stream`);

    es.onmessage = function(e) {
      let msg;
      try { msg = JSON.parse(e.data); } catch { return; }
      if (!msg || msg.type === 'ping' || msg.type === 'connected') return;

      // Ingest complete: show analysis summary — user decides what to do next
      if (msg.type === 'ingest_complete') {
        const lbl = (msg.label || msg.title || 'upload').replace(/^Analysis complete: /, '').replace(/^"|"$/g, '');
        const summary = msg.body || '';
        const fc = msg.file_count ? ` (${msg.file_count} files)` : '';
        const summaryHtml = `<div style="font-size:12px;color:#a1a1aa;line-height:1.6">
          <strong style="color:#4ade80">Analysis ready: ${_esc(lbl)}${_esc(fc)}</strong><br>${_esc(summary)}
          <br><span style="color:#71717a;font-size:11px">Head to chat to describe what you want to build.</span></div>`;
        appendBubble('assistant', summaryHtml, true);
        open();
        scrollBottom();
        return;
      }

      // Push into alerts list and notify
      _alerts.push(msg);
      updateBadge(_alerts.length);
      if (_alertsExpanded) renderAlertRows();

      // Flash the button label briefly
      const btn = document.getElementById('__miso_btn__');
      if (btn && !_open) {
        const orig = btn.innerHTML;
        btn.innerHTML = `<span style="font-size:16px;">🧠</span>New alert`;
        setTimeout(() => { btn.innerHTML = orig; }, 3000);
      }
    };

    es.onerror = function() {
      es.close();
      clearTimeout(_sseRetryTimer);
      _sseRetryTimer = setTimeout(subscribeSSE, 15000);
    };
  }

  async function pollAlerts() {
    // replaced by SSE subscription in boot()
  }

  function updateBadge(count) {
    _alertCount = count;
    const badge = document.getElementById('__miso_badge__');
    const btn   = document.getElementById('__miso_btn__');
    const bar   = document.getElementById('__miso_alerts_bar__');
    const txt   = document.getElementById('__miso_alert_count_text__');

    if (count > 0) {
      badge.style.display = '';
      badge.textContent   = count;
      btn.classList.add('has-alerts');
      bar.style.display   = 'flex';
      txt.textContent     = `${count} thing${count !== 1 ? 's' : ''} need${count === 1 ? 's' : ''} your attention`;
    } else {
      badge.style.display = 'none';
      btn.classList.remove('has-alerts');
      bar.style.display   = 'none';
    }
  }

  // ── Send message ───────────────────────────────────────────────────────────
  function ensureConvId() {
    if (!_sessionId) {
      _sessionId = 'cons_' + Math.random().toString(36).slice(2,10) + '_' + Date.now();
      sessionStorage.setItem('miso_cons_session_id', JSON.stringify(_sessionId));
    }
    return _sessionId;
  }

  async function send() {
    const input = document.getElementById('__miso_input__');
    const q     = (input.value || '').trim();
    if (!q || _thinking) return;

    input.value = '';
    _thinking   = true;
    setBtn(true);

    const ctx = buildPageContext();

    appendBubble('user', q);
    saveMsg('user', q);

    const thinkId = appendThinking();
    scrollBottom();

    try {
      const res  = await fetch(`${API}/apps/consigliere_agent/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ message: q, context: ctx || null, conversation_id: ensureConvId() }),
      });
      const data = await res.json();

      removeThinking(thinkId);

      if (data.error || data.detail) {
        appendBubble('assistant', `⚠ ${data.error || data.detail}`);
      } else {
        const html = formatReply(data);
        appendBubble('assistant', html, true);
        saveMsg('assistant', data.response || '');
      }
    } catch (err) {
      removeThinking(thinkId);
      appendBubble('assistant', `⚠ Couldn't reach MISO. Is the server running?`);
    } finally {
      _thinking = false;
      setBtn(false);
      scrollBottom();
    }
  }

  function buildPageContext() {
    const parts = [];

    try {
      // Active goal / PRD
      const goal = window._currentGoal;
      if (goal && goal.intent) {
        parts.push(`Active goal: "${goal.intent.slice(0, 150)}" [status=${goal.status || 'active'}, type=${goal.goal_type || 'one_off'}]`);
      }
      if (window._prdData) {
        const bp = window._prdData.bp || window._prdData;
        if (bp && bp.title) parts.push(`PRD open: "${bp.title}"`);
        if (bp && bp.artifact_type) parts.push(`Artifact type: ${bp.artifact_type}`);
      }
      if (window._generating) parts.push('Status: build or spec generation is currently in progress');

      // Active nav tab — look for the highlighted nav button
      const activeNavBtn = document.querySelector('[id$="-nav-btn"][style*="color:var(--accent)"], [id$="-nav-btn"][style*="color: var(--accent)"]');
      if (activeNavBtn) parts.push(`Dashboard tab: ${activeNavBtn.title || activeNavBtn.textContent?.trim()}`);

      // Import modal open
      const importModal = document.getElementById('import-modal');
      if (importModal && importModal.style.display !== 'none') {
        parts.push('User has the Import Code modal open');
        if (window._importContext) parts.push(`Import context: ${String(window._importContext).slice(0, 200)}`);
      }

      // Image gen modal open
      const imgModal = document.getElementById('imggen-modal');
      if (imgModal && imgModal.style.display !== 'none') {
        parts.push('User is in the image generation modal');
        const imgIntent = document.getElementById('imggen-intent');
        if (imgIntent && imgIntent.value.trim()) parts.push(`Image intent: "${imgIntent.value.trim().slice(0, 100)}"`);
      }

      // PRD review panel visible
      const reviewPanel = document.getElementById('prd-review-panel');
      if (reviewPanel && reviewPanel.style.display !== 'none') parts.push('User is reviewing a spec audit');

      // Prompt box has draft text
      const promptInput = document.getElementById('prompt-input');
      const draft = promptInput?.value?.trim();
      if (draft && draft.length > 10) parts.push(`Draft in prompt box: "${draft.slice(0, 120)}"`);
    } catch (_) {}

    // Selected text anywhere on page
    const sel = window.getSelection?.()?.toString?.()?.trim?.();
    if (sel && sel.length > 3 && sel.length < 500) parts.push(`Selected text: "${sel}"`);

    return parts.join('\n') || '';
  }

  // Matches what POST /sessions/{id}/messages actually returns today:
  // {user_message, consigliere_reply, surfaced_context, clarifying_questions}.
  // The old confidence/evidence/adversarial-review rendering was written
  // against an earlier, richer /advise response shape that this backend
  // doesn't produce — showing it would mean displaying fields that are
  // always empty, which is its own kind of fake. This shows only what's real.
  function formatReply(r) {
    // actual /chat response: {response: string, conversation_id: string}
    const text = r.response || r.consigliere_reply?.content || r.content || '';
    // Convert newlines and basic markdown to HTML
    const html = text
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
      .replace(/\*(.+?)\*/g,'<em>$1</em>')
      .replace(/`([^`]+)`/g,'<code style="background:#1c1c26;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>')
      .replace(/\n/g,'<br>');
    return `<div style="font-size:13px;color:#e4e4e7;line-height:1.65;word-break:break-word;overflow-wrap:break-word;">${html}</div>`;
  }

  // ── Feedback ───────────────────────────────────────────────────────────────
  async function feedback(messageId) {
    const correct = confirm('Did this advice turn out to be correct?');
    try {
      await fetch(`${API}/apps/consigliere_agent/messages/${messageId}/outcome`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ outcome: correct ? 'correct' : 'wrong' }),
      });
      const btns = document.querySelectorAll(`[onclick*="feedback(${messageId})"]`);
      btns.forEach(b => { b.textContent = correct ? '✅ Logged' : '❌ Logged'; b.disabled = true; });
    } catch {}
  }

  // ── Message helpers ────────────────────────────────────────────────────────
  function appendBubble(role, content, isHtml = false) {
    const msgs = document.getElementById('__miso_msgs__');
    const div  = document.createElement('div');
    div.className = `__msg__ ${role}`;
    const bubble  = document.createElement('div');
    bubble.className = 'bubble';
    if (isHtml) bubble.innerHTML = content;
    else        bubble.textContent = content;
    div.appendChild(bubble);
    msgs.appendChild(div);
    return div;
  }

  let _thinkCount = 0;
  function appendThinking() {
    const id   = `__think_${++_thinkCount}`;
    const msgs = document.getElementById('__miso_msgs__');
    const div  = document.createElement('div');
    div.className = '__msg__ assistant';
    div.id = id;
    div.innerHTML = `<div class="bubble"><div class="__typing__"><span></span><span></span><span></span></div></div>`;
    msgs.appendChild(div);
    return id;
  }
  function removeThinking(id) {
    document.getElementById(id)?.remove();
  }

  function scrollBottom() {
    const sc = document.getElementById('__miso_scroll__');
    if (sc) sc.scrollTop = sc.scrollHeight;
  }

  function setBtn(loading) {
    const btn = document.getElementById('__miso_send__');
    if (btn) { btn.disabled = loading; btn.textContent = loading ? 'Thinking…' : 'Get advice →'; }
  }

  // ── Session persistence ────────────────────────────────────────────────────
  function saveMsg(role, content) {
    _session.push({ role, content, ts: Date.now() });
    if (_session.length > MAX_HISTORY * 2) _session = _session.slice(-MAX_HISTORY * 2);
    sessionStorage.setItem('miso_cons_session', JSON.stringify(_session));
  }

  // ── Utilities ──────────────────────────────────────────────────────────────
  function _esc(s) {
    return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Public API (exposed so onclick= handlers work) ─────────────────────────
  window.__MISO_CONS__ = { toggle, open, close, send, toggleAlerts, dismissAlert, reask, feedback, loadIdentity, triggerBrief };

  // ── Draggable panel ────────────────────────────────────────────────────────
  function _makeDraggable() {
    const panel  = document.getElementById('__miso_panel__');
    const header = panel.querySelector('.__miso_header__');
    if (!header) return;

    header.style.cursor = 'grab';
    header.title = 'Drag to move';

    // Restore saved position from previous session
    const saved = sessionStorage.getItem('miso_cons_pos');
    if (saved) {
      try {
        const { top, left } = JSON.parse(saved);
        panel.style.top    = top  + 'px';
        panel.style.left   = left + 'px';
        panel.style.bottom = 'auto';
        panel.style.right  = 'auto';
      } catch {}
    }

    let _dragging = false, _ox = 0, _oy = 0;

    header.addEventListener('pointerdown', (e) => {
      if (e.target.closest('.close-btn')) return;
      _dragging = true;
      header.style.cursor = 'grabbing';
      header.setPointerCapture(e.pointerId);

      // Switch from bottom/right to top/left coordinates so we can freely move
      const rect = panel.getBoundingClientRect();
      panel.style.top    = rect.top  + 'px';
      panel.style.left   = rect.left + 'px';
      panel.style.bottom = 'auto';
      panel.style.right  = 'auto';
      _ox = e.clientX - rect.left;
      _oy = e.clientY - rect.top;
      e.preventDefault();
    });

    header.addEventListener('pointermove', (e) => {
      if (!_dragging) return;
      const maxLeft = window.innerWidth  - panel.offsetWidth;
      const maxTop  = window.innerHeight - panel.offsetHeight;
      panel.style.left = Math.max(0, Math.min(maxLeft, e.clientX - _ox)) + 'px';
      panel.style.top  = Math.max(0, Math.min(maxTop,  e.clientY - _oy)) + 'px';
    });

    header.addEventListener('pointerup', () => {
      if (!_dragging) return;
      _dragging = false;
      header.style.cursor = 'grab';
      sessionStorage.setItem('miso_cons_pos', JSON.stringify({
        top:  parseInt(panel.style.top,  10),
        left: parseInt(panel.style.left, 10),
      }));
    });
  }

  // ── Boot ───────────────────────────────────────────────────────────────────
  function boot() {
    build();
    _makeDraggable();
    loadIdentity();   // async — updates names once loaded
    subscribeSSE();   // proactive alerts via SSE
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

})();
