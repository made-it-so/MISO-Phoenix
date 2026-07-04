(() => {
  const MISO_HOST = 'https://miso.stemcultivation.com';
  let conversationId = 'meet_' + Date.now();
  let busy = false;

  // ── Caption scraping / Listen mode ────────────────────────────────────────
  let listenMode = false;
  let captionBuffer = [];
  let lastFlushedAt = 0;
  let listenInterval = null;
  const LISTEN_FLUSH_MS = 45000;

  // Google Meet caption container selectors
  const CAPTION_SELECTORS = [
    '[jsname="tgaKEb"]',
    '[jsname="C0mSub"]',
    '.a4cQT',
    '[class*="caption-text"]',
    '[data-caption-id]',
  ];

  function scrapeCaptions() {
    const seen = new Set();
    const lines = [];
    for (const sel of CAPTION_SELECTORS) {
      for (const el of document.querySelectorAll(sel)) {
        const t = el.textContent?.trim();
        if (t && t.length > 3 && !seen.has(t)) { seen.add(t); lines.push(t); }
      }
      if (lines.length) break;
    }
    return lines;
  }

  function toggleListen() {
    listenMode = !listenMode;
    const btn = document.getElementById('miso-listen-btn');
    if (!btn) return;

    if (listenMode) {
      btn.textContent = '⏹ Stop';
      btn.style.color = '#ff6b6b';
      appendMsg('system', 'Listening — MISO will auto-analyze meeting speech every 45s.');
      lastFlushedAt = Date.now();
      captionBuffer = [];

      listenInterval = setInterval(() => {
        const lines = scrapeCaptions();
        if (lines.length) captionBuffer.push(...lines);

        const now = Date.now();
        if (captionBuffer.length && (now - lastFlushedAt) >= LISTEN_FLUSH_MS) {
          const block = captionBuffer.splice(0).join(' ').slice(0, 1500);
          lastFlushedAt = now;
          const title = getMeetingTitle();
          appendMsg('system', '[Auto] Analyzing…');
          callConsigliere(
            `Meeting speech just now:\n\n"${block}"\n\nBrief real-time counsel: key points, risks, decisions, actions needed. Be concise.`,
            title ? `Live Google Meet: "${title}"` : 'Live Google Meet',
            true  // fast=true → Ollama only, no cloud spend
          );
        }
      }, 5000);
    } else {
      btn.textContent = '👂 Listen';
      btn.style.color = '#4a9eff';
      clearInterval(listenInterval);
      listenInterval = null;
      captionBuffer = [];
      appendMsg('system', 'Listening off.');
    }
  }

  function getMeetingTitle() {
    return document.querySelector('[data-meeting-title],[jsname="r4nke"]')?.textContent.trim() || '';
  }

  // ── Inject UI ──────────────────────────────────────────────────────────────
  function buildUI() {
    if (document.getElementById('miso-panel')) return;

    const toggle = document.createElement('button');
    toggle.id = 'miso-toggle';
    toggle.title = 'MISO Consigliere';
    toggle.innerHTML = 'M';
    document.body.appendChild(toggle);

    const panel = document.createElement('div');
    panel.id = 'miso-panel';
    panel.className = 'hidden';
    panel.innerHTML = `
      <div id="miso-header">
        <span>MISO</span>
        <span id="miso-meeting-label"></span>
        <button id="miso-listen-btn" title="Auto-analyze meeting speech">👂 Listen</button>
        <span id="miso-close">✕</span>
      </div>
      <div id="miso-jarvis-banner"></div>
      <div id="miso-messages">
        <div class="miso-msg system">Type a question below, or enable Listen for automatic real-time counsel.</div>
      </div>
      <div id="miso-input-row">
        <textarea id="miso-input" placeholder="Ask MISO…" rows="1"></textarea>
        <button id="miso-send">↑</button>
      </div>
    `;
    document.body.appendChild(panel);

    const title = getMeetingTitle();
    if (title) document.getElementById('miso-meeting-label').textContent = title;

    toggle.addEventListener('click', () => panel.classList.toggle('hidden'));
    document.getElementById('miso-close').addEventListener('click', () => panel.classList.add('hidden'));
    document.getElementById('miso-send').addEventListener('click', send);
    document.getElementById('miso-listen-btn').addEventListener('click', toggleListen);
    document.getElementById('miso-input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
  }

  // ── Messaging ──────────────────────────────────────────────────────────────
  function appendMsg(role, text) {
    const msgs = document.getElementById('miso-messages');
    const div = document.createElement('div');
    div.className = `miso-msg ${role}`;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  // fast=true pins to local Ollama (no cloud spend, faster response)
  async function callConsigliere(text, context, fast = false) {
    const btn = document.getElementById('miso-send');
    if (btn) btn.disabled = true;
    busy = true;

    const thinking = document.createElement('div');
    thinking.className = 'miso-thinking';
    thinking.textContent = '▸ thinking…';
    document.getElementById('miso-messages')?.appendChild(thinking);

    try {
      const r = await fetch(`${MISO_HOST}/apps/consigliere_agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          context,
          fast,
        }),
      });
      thinking.remove();
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      if (d.error) throw new Error(d.error);
      appendMsg('assistant', d.response || '(no response)');
    } catch (e) {
      thinking.remove();
      appendMsg('system', `Error: ${e.message}`);
    } finally {
      if (btn) btn.disabled = false;
      busy = false;
    }
  }

  function send() {
    if (busy) return;
    const input = document.getElementById('miso-input');
    const text = input?.value.trim();
    if (!text) return;
    input.value = '';
    appendMsg('user', text);
    const title = getMeetingTitle();
    callConsigliere(text, title ? `Live Google Meet: "${title}"` : 'Live Google Meet');
    document.getElementById('miso-panel')?.classList.remove('hidden');
  }

  // ── Meet chat: detect YOUR OWN messages (no prefix needed) ────────────────
  // Meet labels the current user's messages with sender text "You"
  const seenChatMessages = new Set();

  function scanChat() {
    // Each chat message has a sender element and a text element.
    // Selectors vary by Meet version — try a few combos.
    const messageBlocks = document.querySelectorAll(
      '[jsname="xySENc"], [data-message-id], .GDhqjd'
    );

    for (const block of messageBlocks) {
      // Look for sender label "You" — Meet uses this for the local participant
      const sender = (
        block.querySelector('[jsname="MocGPb"]') ||
        block.querySelector('[class*="sender"]') ||
        block.querySelector('[class*="author"]')
      )?.textContent?.trim();

      const isOwnMessage = sender === 'You' || sender === '';

      // Grab the message text
      const textEl = (
        block.querySelector('[jsname="tgaKEb"]') ||
        block.querySelector('[data-message-text]') ||
        block.querySelector('[class*="message-text"]') ||
        block
      );
      const text = textEl?.textContent?.trim();

      if (!text || seenChatMessages.has(text)) continue;

      if (isOwnMessage && text.length > 2) {
        seenChatMessages.add(text);
        document.getElementById('miso-panel')?.classList.remove('hidden');
        appendMsg('user', text);  // mirror in MISO panel
        const title = getMeetingTitle();
        callConsigliere(text, `Sent in Meet chat. Meeting: "${title}"`);
      }
    }
  }

  // ── JARVIS banner ──────────────────────────────────────────────────────────
  function connectJarvis() {
    setInterval(async () => {
      try {
        const r = await fetch(`${MISO_HOST}/apps/meet_bot/sessions`);
        if (!r.ok) return;
        const sessions = await r.json();
        const live = sessions.find(s => s.status === 'active');
        const banner = document.getElementById('miso-jarvis-banner');
        if (!banner) return;
        if (live && live.jarvis_insights?.length) {
          const last = live.jarvis_insights[live.jarvis_insights.length - 1];
          if (last?.text && !last.text.includes('SILENT')) {
            banner.textContent = `⚡ ${last.text.replace(/^JARVIS:\s*/i, '')}`;
            banner.classList.add('active');
          }
        } else {
          banner.classList.remove('active');
        }
      } catch (_) {}
    }, 10000);
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  function init() {
    buildUI();
    setInterval(scanChat, 2000);
    connectJarvis();
  }

  if (document.readyState === 'complete') {
    setTimeout(init, 2000);
  } else {
    window.addEventListener('load', () => setTimeout(init, 2000));
  }
})();
