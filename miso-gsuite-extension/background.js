'use strict';

// ── Config ────────────────────────────────────────────────────────────────────

const DEFAULT_HOST = 'https://miso.stemcultivation.com';

async function host() {
  const s = await chrome.storage.local.get('misoHost');
  return s.misoHost || DEFAULT_HOST;
}

async function authHeaders() {
  const s = await chrome.storage.local.get('misoApiKey');
  const h = { 'Content-Type': 'application/json' };
  if (s.misoApiKey) h['X-Miso-Key'] = s.misoApiKey;
  return h;
}

// ── Side panel ────────────────────────────────────────────────────────────────

chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch(() => {});

// ── Consigliere chat ────────────────────────────────────────────────────────────────────────────────

// One persistent conversation_id per stakes level (maps to /chat history)
const _convIds = {};

async function consigliere(content, stakes = 'high') {
  const h    = await host();
  const hdrs = await authHeaders();

  if (!_convIds[stakes]) {
    _convIds[stakes] = 'gsuite_' + stakes + '_' + Date.now();
  }
  const conversation_id = _convIds[stakes];

  const r = await fetch(h + '/apps/consigliere_agent/chat', {
    method: 'POST',
    headers: hdrs,
    body: JSON.stringify({ message: content, conversation_id }),
  });

  if (!r.ok) {
    return { ok: false, content: 'MISO error ' + r.status, conversation_id };
  }
  const d = await r.json();
  if (d.error) {
    return { ok: false, content: d.error, conversation_id };
  }
  return { ok: true, content: d.response || '(no response)', conversation_id };
}

// ── Context store (per tab) ───────────────────────────────────────────────────

const _tabCtx = {};

// ── Message router ────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, respond) => {

  // Content script broadcasting updated context
  if (msg.type === 'CTX_UPDATE') {
    const tabId = sender.tab?.id;
    if (tabId) _tabCtx[tabId] = msg.ctx;
    // Forward to side panel
    chrome.runtime.sendMessage({ type: 'CTX_PUSHED', ctx: msg.ctx }).catch(() => {});
    return;
  }

  // Side panel or popup asking for current context
  if (msg.type === 'GET_CTX') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs[0]?.id;
      if (!tabId) { respond(null); return; }
      // Ask content script directly (freshest data)
      chrome.tabs.sendMessage(tabId, { type: 'PULL_CTX' }, (ctx) => {
        respond(ctx || _tabCtx[tabId] || null);
      });
    });
    return true; // async
  }

  // Analyze current context now
  if (msg.type === 'ANALYZE') {
    const prompt = buildPrompt(msg.ctx, msg.mode || 'general');
    consigliere(prompt, 'high').then(respond).catch(e => respond({ ok: false, content: e.message }));
    return true;
  }

  // Direct chat from side panel
  if (msg.type === 'CHAT') {
    consigliere(msg.content, msg.stakes || 'high')
      .then(respond)
      .catch(e => respond({ ok: false, content: e.message }));
    return true;
  }

  // Config
  if (msg.type === 'SET_HOST') {
    const update = { misoHost: msg.host };
    if (msg.apiKey !== undefined) update.misoApiKey = msg.apiKey || null;
    chrome.storage.local.set(update);
    Object.keys(_sessions).forEach(k => delete _sessions[k]); // reset sessions on host/key change
    respond({ ok: true });
    return;
  }
});

// ── Prompt builder ────────────────────────────────────────────────────────────

function buildPrompt(ctx, mode) {
  if (!ctx) return 'G Suite is open but no context could be extracted. What should I watch for?';

  const header = `[MISO G Suite Monitor — App: ${ctx.app?.toUpperCase()} — Stakes: HIGH — Mode: hypercritical]`;

  switch (ctx.app) {

    case 'gmail': {
      if (ctx.mode === 'compose') {
        return `${header}

GMAIL — DRAFT EMAIL

Subject: ${ctx.subject || '(none)'}
To: ${ctx.to || '(unknown)'}
Word count: ${ctx.wordCount || 0}

---
${ctx.body || '(empty)'}
---

Be hypercritical. Evaluate:
1. Subject line — does it get to the point? Is it too vague, too long?
2. Opening — does it waste words?
3. Body — clarity, logic, tone. What's confusing or missing?
4. Call to action — is there one? Is it clear?
5. Length — should this be shorter? Should it be a call instead?
6. Anything that makes the sender look bad.

Don't soften the feedback.`;
      }

      if (ctx.mode === 'read') {
        return `${header}

GMAIL — INCOMING EMAIL

Subject: ${ctx.subject || '(none)'}
From: ${ctx.from || '(unknown)'}

---
${ctx.body || '(empty)'}
---

Analyze:
1. What does this person actually want (vs. what they said)?
2. What's the subtext, tension, or unstated expectation?
3. What's the best response strategy?
4. What should NOT be said in reply?
5. Any red flags — legal, interpersonal, scope creep, etc.?`;
      }

      return `${header}\n\nGmail inbox open. No specific email context available. What patterns should I watch for?`;
    }

    case 'calendar': {
      const evts = ctx.events?.slice(0, 15).join('\n  ') || '(none detected)';
      return `${header}

GOOGLE CALENDAR — SCHEDULE ANALYSIS

Date: ${ctx.date || new Date().toLocaleDateString()}
View: ${ctx.viewMode || 'unknown'}

Visible events:
  ${evts}

Be hypercritical. Evaluate:
1. Which of these meetings should have been an email?
2. Back-to-back meetings with no buffer — risk?
3. Missing deep work / focus blocks.
4. Meetings that lack a clear owner or outcome.
5. Calendar hygiene issues (vague titles, missing descriptions).
6. What is this person's week actually optimized for — and is that right?`;
    }

    case 'docs': {
      const content = ctx.selection
        ? `SELECTED TEXT:\n${ctx.selection}`
        : `DOCUMENT CONTENT (truncated):\n${ctx.content?.slice(0, 2500) || '(empty)'}`;

      return `${header}

GOOGLE DOCS — CONTENT ANALYSIS

Document: ${ctx.title || '(untitled)'}

${content}

Be hypercritical. Evaluate:
1. Clarity — what will a reader misunderstand?
2. Structure — is the flow logical?
3. Vague language — list every hedge, weasel word, or non-commitment.
4. What's missing that a reader needs to act on this?
5. What can be cut without losing meaning?
6. If this is a decision doc: is the decision actually stated? Are trade-offs listed?`;
    }

    case 'sheets': {
      return `${header}

GOOGLE SHEETS — ANALYSIS

Sheet: ${ctx.title || '(untitled)'}

Context: ${ctx.activeCell ? `Active cell: ${ctx.activeCell}` : 'No cell selected.'}
${ctx.selection ? `Selection: ${ctx.selection}` : ''}

Analyze for: formula correctness, naming conventions, data structure issues,
hardcoded values that should be references, missing validation, unclear column headers.`;
    }

    case 'meet': {
      const captions = ctx.recentCaptions?.length
        ? `Recent transcript:\n${ctx.recentCaptions.slice(-10).join('\n')}`
        : '(no transcript captured — enable captions for analysis)';

      return `${header}

GOOGLE MEET — LIVE MEETING ANALYSIS

Meeting: ${ctx.title || '(untitled)'}
Participants: ${ctx.participantCount || '?'}
Duration: ${ctx.duration ? Math.round(ctx.duration / 60) + ' min' : 'unknown'}

${captions}

Analyze:
1. Is this meeting necessary? Could it be async?
2. Is there a clear agenda and owner?
3. Based on transcript: is the conversation productive or circular?
4. What decisions have been made vs. deferred?
5. What action items have been mentioned?
6. When should this meeting end?`;
    }

    case 'drive': {
      return `${header}

GOOGLE DRIVE — ORGANIZATION ANALYSIS

Folder/file: ${ctx.title || document?.title || 'unknown'}

Analyze file naming, folder structure, sharing hygiene,
stale files, and what's missing from an information architecture standpoint.`;
    }

    default:
      return `${header}\n\nContext: ${JSON.stringify(ctx, null, 2)}\n\nWhat should I pay attention to here?`;
  }
}
