'use strict';

// ── App detection ─────────────────────────────────────────────────────────────

const APP = {
  'mail.google.com':     'gmail',
  'calendar.google.com': 'calendar',
  'docs.google.com':     'docs',
  'sheets.google.com':   'sheets',
  'slides.google.com':   'slides',
  'meet.google.com':     'meet',
  'drive.google.com':    'drive',
}[location.hostname] || 'unknown';

// ── Context extractors ────────────────────────────────────────────────────────

function extractCtx() {
  try {
    switch (APP) {
      case 'gmail':    return gmailCtx();
      case 'calendar': return calendarCtx();
      case 'docs':     return docsCtx();
      case 'sheets':   return sheetsCtx();
      case 'meet':     return meetCtx();
      case 'drive':    return driveCtx();
      default:         return { app: APP, title: document.title };
    }
  } catch (e) {
    return { app: APP, title: document.title, extractError: e.message };
  }
}

// ── Gmail ─────────────────────────────────────────────────────────────────────

function gmailCtx() {
  // Compose window open?
  const composeBody = document.querySelector(
    '[aria-label="Message Body"], .Am.Al.editable, [g_editable="true"]'
  );
  if (composeBody) {
    const subject = (
      document.querySelector('[name="subjectbox"]')?.value ||
      document.querySelector('[data-tooltip="Subject"]')?.value || ''
    );
    const toField = document.querySelector('[aria-label="To"]')?.innerText || '';
    const body    = composeBody.innerText || '';
    return {
      app: 'gmail', mode: 'compose',
      subject, to: toField.trim(), body: body.slice(0, 3000),
      wordCount: body.split(/\s+/).filter(Boolean).length,
    };
  }

  // Reading an email?
  const emailBody = document.querySelector('.a3s.aiL, .a3s.aXjCH, [role="main"] .ii');
  if (emailBody) {
    const subject = document.querySelector('h2.hP, [data-thread-perm-id] h2')?.innerText || document.title;
    const from    = document.querySelector('.gD')?.getAttribute('email')
                 || document.querySelector('[email]')?.getAttribute('email') || '';
    return {
      app: 'gmail', mode: 'read',
      subject, from,
      body: emailBody.innerText?.slice(0, 3000) || '',
    };
  }

  return { app: 'gmail', mode: 'inbox', title: document.title };
}

// ── Google Calendar ───────────────────────────────────────────────────────────

function calendarCtx() {
  const viewMode = document.querySelector('[data-view="week"]') ? 'week'
    : document.querySelector('[data-view="day"]')  ? 'day'
    : document.querySelector('[data-view="month"]') ? 'month' : 'unknown';

  // Grab event chips
  const events = [
    ...document.querySelectorAll('[data-eventid], [data-eventchip], [role="gridcell"] [role="button"]')
  ]
    .map(el => (el.getAttribute('aria-label') || el.innerText || '').trim())
    .filter(s => s && s.length > 1 && s.length < 200)
    .slice(0, 20);

  return { app: 'calendar', date: new Date().toLocaleDateString(), viewMode, events };
}

// ── Google Docs ───────────────────────────────────────────────────────────────

function docsCtx() {
  const selection = window.getSelection()?.toString()?.trim()?.slice(0, 1500) || '';

  // Docs renders to a canvas-based editor; innerText on the editor div gives the text
  const editor  = document.querySelector('.kix-appview-editor, .docs-texteventtarget-iframe');
  let content   = '';
  if (editor) {
    content = editor.innerText?.trim().slice(0, 3000) || '';
  }

  return {
    app: 'docs',
    title: document.title.replace(' - Google Docs', '').trim(),
    selection,
    content,
  };
}

// ── Google Sheets ─────────────────────────────────────────────────────────────

function sheetsCtx() {
  const activeCell = document.querySelector('.cell-input, #t-name-box')?.value || '';
  const formulaBar = document.querySelector('#t-formula-bar-input, .cell-input')?.innerText || '';
  return {
    app: 'sheets',
    title: document.title.replace(' - Google Sheets', '').trim(),
    activeCell,
    formulaBar,
  };
}

// ── Google Meet ───────────────────────────────────────────────────────────────

let _meetStart = null;
let _captions  = [];
let _captionObs = null;

function meetCtx() {
  if (!_meetStart) _meetStart = Date.now();
  const duration = Math.round((Date.now() - _meetStart) / 1000);

  // Title
  const title = (
    document.querySelector('[data-meeting-title]')?.getAttribute('data-meeting-title') ||
    document.querySelector('c-wiz[data-meeting-code]')?.getAttribute('data-meeting-code') ||
    document.querySelector('[jsname="r4nke"]')?.innerText ||
    document.title.replace('Meet - ', '').trim()
  );

  // Participants
  const participantEls = document.querySelectorAll('[data-participant-id], [data-ssrc]');
  const participantCount = participantEls.length;

  // Live captions (if enabled)
  const capEls = document.querySelectorAll('[jsname="tgaKEf"], .a4cQT, [class*="caption"]');
  capEls.forEach(el => {
    const text = el.innerText?.trim();
    if (text && !_captions.includes(text)) _captions.push(text);
  });
  // Keep last 40 caption lines
  if (_captions.length > 40) _captions = _captions.slice(-40);

  return {
    app: 'meet', title, duration, participantCount,
    recentCaptions: _captions.slice(-15),
  };
}

// Watch for captions appearing in Meet
function startCaptionObserver() {
  if (_captionObs || APP !== 'meet') return;
  _captionObs = new MutationObserver(() => {
    document.querySelectorAll('[jsname="tgaKEf"], .a4cQT').forEach(el => {
      const text = el.innerText?.trim();
      if (text && !_captions.includes(text)) {
        _captions.push(text);
        if (_captions.length > 60) _captions = _captions.slice(-60);
      }
    });
  });
  _captionObs.observe(document.body, { childList: true, subtree: true });
}

// ── Google Drive ──────────────────────────────────────────────────────────────

function driveCtx() {
  const selected = [...document.querySelectorAll('[aria-selected="true"] [data-tooltip]')]
    .map(el => el.getAttribute('data-tooltip'))
    .filter(Boolean)
    .slice(0, 10);
  return {
    app: 'drive',
    title: document.title.replace(' - Google Drive', '').trim(),
    selected,
  };
}

// ── Broadcast loop ────────────────────────────────────────────────────────────

let _lastBroadcast = '';
let _debounceTimer = null;

function broadcast() {
  const ctx = extractCtx();
  const key = JSON.stringify(ctx);
  if (key === _lastBroadcast) return;
  _lastBroadcast = key;
  try { chrome.runtime.sendMessage({ type: 'CTX_UPDATE', ctx }).catch(() => {}); } catch (_) {}
}

function scheduleBroadcast() {
  clearTimeout(_debounceTimer);
  _debounceTimer = setTimeout(broadcast, 1200);
}

// Observe DOM changes
new MutationObserver(scheduleBroadcast)
  .observe(document.body, { childList: true, subtree: true, characterData: true });

// Initial broadcast after page settles
setTimeout(broadcast, 2500);

// Start Meet caption watcher
if (APP === 'meet') {
  setTimeout(startCaptionObserver, 3000);
  setInterval(broadcast, 15000); // Meet: push every 15s even without DOM changes
}

// ── Message listener ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, respond) => {
  if (msg.type === 'PULL_CTX') {
    respond(extractCtx());
    return;
  }
});

// ── Floating analyze button ───────────────────────────────────────────────────

function injectBtn() {
  if (document.getElementById('__miso_gsuite_btn__')) return;

  const btn = document.createElement('button');
  btn.id = '__miso_gsuite_btn__';
  btn.innerHTML = '&#129504; Analyze';
  Object.assign(btn.style, {
    position:   'fixed',
    bottom:     '72px',
    right:      '16px',
    zIndex:     '2147483646',
    background: '#7c3aed',
    color:      '#fff',
    border:     'none',
    borderRadius: '24px',
    padding:    '8px 16px',
    fontSize:   '13px',
    fontWeight: '700',
    fontFamily: '-apple-system,BlinkMacSystemFont,sans-serif',
    cursor:     'pointer',
    boxShadow:  '0 4px 20px rgba(124,58,237,.5)',
    transition: 'opacity .15s',
  });

  btn.addEventListener('click', () => {
    const ctx = extractCtx();
    btn.innerHTML = '&#9203; Analyzing…';
    btn.style.opacity = '0.7';
    try { chrome.runtime.sendMessage({ type: 'ANALYZE', ctx }, () => {
      btn.innerHTML = '&#10003; Done — see panel';
      btn.style.opacity = '1';
      setTimeout(() => { btn.innerHTML = '&#129504; Analyze'; }, 3000);
    }); } catch (_) { btn.innerHTML = '&#129504; Analyze'; btn.style.opacity = '1'; }
  });

  document.body.appendChild(btn);
}

// Inject after page fully loads
window.addEventListener('load', () => setTimeout(injectBtn, 2000));
if (document.readyState === 'complete') setTimeout(injectBtn, 2000);
