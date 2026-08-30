(() => {
  'use strict';
  if (window.__cindrelaDesktopAgentLoaded) return;
  window.__cindrelaDesktopAgentLoaded = true;

  const api = window.cindrelaDesktop;
  if (!api || !api.isDesktop) return;

  const KEY = 'cindrela_sales_leads_v3';
  const AGENT_KEY = 'cindrela_desktop_agent_v1';

  const state = {
    leads: [],
    selected: null,
    panel: 'home',
    settings: {},
    followUps: []
  };

  const esc = (value) => String(value ?? '').replace(/[&<>\"']/g, (c) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
  const today = () => new Date().toISOString().slice(0, 10);

  async function saveAgent() {
    state.followUps = state.followUps.slice(0, 500);
    await api.writeDatabase({
      version: 2,
      storage: Object.fromEntries(Object.keys(localStorage).map((k) => [k, localStorage.getItem(k)])),
      leads: state.leads,
      deals: state.leads.filter((x) => x.status === 'Won'),
      notes: [],
      settings: state.settings,
      followUps: state.followUps
    });
  }

  function loadLeads() {
    try { state.leads = JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch { state.leads = []; }
    if (!Array.isArray(state.leads)) state.leads = [];
  }

  function rankLead(lead) {
    let score = 0;
    const reasons = [];
    if (lead.contactPerson) { score += 35; reasons.push('Named decision-maker found'); }
    if (lead.contactRole) {
      score += /ceo|founder|owner|director|manager|operations|admin|travel|procurement|hr|business development/i.test(lead.contactRole) ? 25 : 10;
      reasons.push('Role available');
    }
    if (lead.businessEmail) { score += 20; reasons.push('Business email available'); }
    if (lead.businessPhone) { score += 10; reasons.push('Business phone/WhatsApp available'); }
    if (lead.linkedin) { score += 10; reasons.push('Professional profile available'); }
    if (lead.contactSource || lead.source) { score += 5; reasons.push('Source available'); }
    return { score: Math.min(score, 100), reasons };
  }

  function searchUrl(company, kind) {
    const q = encodeURIComponent(`"${company}" ${kind} official business contact`);
    return `https://www.google.com/search?q=${q}`;
  }

  function openExternal(url) {
    if (api.openExternal) api.openExternal(url);
    else window.open(url, '_blank', 'noopener');
  }

  function dueFollowUps() {
    const now = today();
    return state.followUps.filter((x) => x && x.date && x.date <= now && !x.completed);
  }

  function panelHtml() {
    const followDue = dueFollowUps();
    const selected = state.selected ? state.leads.find((x) => String(x.id) === String(state.selected)) : null;
    if (state.panel === 'contact' && selected) {
      const rank = rankLead(selected);
      return `<div class="csa-head"><b>Contact Intelligence</b><button data-csa="close">×</button></div>
        <div class="csa-company"><strong>${esc(selected.company)}</strong><span>${esc(selected.event || '')}</span></div>
        <div class="csa-score">Best-contact strength <b>${rank.score}/100</b></div>
        <div class="csa-list">${rank.reasons.map((r) => `<div>✓ ${esc(r)}</div>`).join('') || '<div>No verified contact data yet.</div>'}</div>
        <div class="csa-fields">
          <div><label>Person</label><b>${esc(selected.contactPerson || 'Not found')}</b></div>
          <div><label>Role</label><b>${esc(selected.contactRole || selected.role || 'Not found')}</b></div>
          <div><label>Business email</label><b>${esc(selected.businessEmail || 'Not found')}</b></div>
          <div><label>Business phone</label><b>${esc(selected.businessPhone || 'Not found')}</b></div>
          <div><label>LinkedIn</label><b>${selected.linkedin ? `<a href="${esc(selected.linkedin)}" target="_blank" rel="noopener">Open profile</a>` : 'Not found'}</b></div>
        </div>
        <div class="csa-actions">
          <button data-csa="search" data-kind="decision maker">🔎 Find decision maker</button>
          <button data-csa="search" data-kind="business email">✉ Find business email</button>
          <button data-csa="search" data-kind="business phone OR WhatsApp">☎ Find business phone</button>
          <button data-csa="email">📧 Draft Email</button>
          <button data-csa="follow">📅 Add Follow-up</button>
        </div>`;
    }

    if (state.panel === 'followups') {
      const items = state.followUps.slice().sort((a,b) => String(a.date).localeCompare(String(b.date))).slice(0, 50);
      return `<div class="csa-head"><b>Follow-up Agent</b><button data-csa="close">×</button></div>
        <div class="csa-summary"><b>${followDue.length}</b> due now • <b>${items.filter(x => !x.completed).length}</b> open</div>
        <div class="csa-list">${items.length ? items.map((x) => `<div class="csa-follow ${x.completed?'done':''}"><b>${esc(x.company)}</b><span>${esc(x.date)} • ${esc(x.action || 'Follow up')}</span><button data-csa="complete-follow" data-id="${esc(x.id)}">${x.completed ? 'Done' : 'Complete'}</button></div>`).join('') : '<div>No follow-ups yet.</div>'}</div>`;
    }

    if (state.panel === 'email' && selected) {
      const subject = `Travel support for ${selected.event || 'your upcoming business travel'}`;
      const body = `Hi ${selected.contactPerson || '[Name]'},\n\nI’m Devanshu from Cindrela Travel. We support companies and teams with flights, hotels, airport transfers and business travel coordination.\n\nIf you have upcoming travel requirements, I’d be happy to prepare a quick option based on your dates and team size.\n\nRegards,\nDevanshu\nCindrela Travel`;
      const href = `mailto:${encodeURIComponent(selected.businessEmail || '')}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      return `<div class="csa-head"><b>Email Outreach</b><button data-csa="close">×</button></div>
        <div class="csa-email"><label>To</label><input id="csa-to" value="${esc(selected.businessEmail || '')}" placeholder="Business email">
        <label>Subject</label><input id="csa-subject" value="${esc(subject)}">
        <label>Message</label><textarea id="csa-body">${esc(body)}</textarea>
        <div class="csa-actions"><a data-csa-mail href="${href}">📧 Open in email app</a><button data-csa="log-email">✓ Log as prepared</button></div></div>`;
    }

    return `<div class="csa-head"><div><b>Cindrela Desktop Sales Agent</b><span>${state.leads.length} leads loaded</span></div><button data-csa="close">×</button></div>
      <div class="csa-summary"><b>${followDue.length}</b> follow-up(s) due • <b>${state.leads.filter((x)=>x.status==='Won').length}</b> won</div>
      <div class="csa-actions">
        <button data-csa="pick-contact">👤 Contact Intelligence</button>
        <button data-csa="followups">📅 Follow-up Agent</button>
        <button data-csa="pick-email">📧 Email Outreach</button>
      </div>
      <div class="csa-note">Public professional contact data only. No guessed private details.</div>`;
  }

  function selectedLeadOrFirst() {
    if (state.selected) return state.leads.find((x) => String(x.id) === String(state.selected));
    return state.leads[0];
  }

  function renderPanel() {
    let root = document.getElementById('csa-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'csa-root';
      document.body.appendChild(root);
    }
    root.innerHTML = panelHtml();
    root.classList.add('show');
  }

  function closePanel() {
    const root = document.getElementById('csa-root');
    if (root) root.classList.remove('show');
  }

  function addStyles() {
    const style = document.createElement('style');
    style.textContent = `.csa-launch{position:fixed;right:18px;bottom:18px;z-index:99990;border:0;border-radius:999px;padding:11px 14px;background:#101828;color:#fff;font-weight:900;box-shadow:0 8px 25px #10182833;cursor:pointer}.csa-launch .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#12b76a;margin-right:7px}.csa-root{display:none;position:fixed;right:18px;bottom:68px;width:min(420px,calc(100vw - 36px));max-height:78vh;overflow:auto;z-index:99999;background:#fff;border:1px solid #e4e7ec;border-radius:16px;box-shadow:0 20px 55px #10182833;padding:16px;color:#172033;font-family:Inter,Arial,sans-serif}.csa-root.show{display:block}.csa-head{display:flex;justify-content:space-between;gap:8px;align-items:start;margin-bottom:12px}.csa-head b{font-size:15px}.csa-head span,.csa-company span{display:block;color:#667085;font-size:11px;margin-top:3px}.csa-head button{border:0;background:#eef2f6;border-radius:8px;padding:5px 8px;cursor:pointer}.csa-company{padding:10px;background:#f8fafc;border-radius:10px}.csa-score{margin-top:10px;padding:10px;border-radius:10px;background:#eef4ff;color:#175cd3}.csa-score b{float:right}.csa-list{margin-top:10px;display:grid;gap:6px;font-size:12px}.csa-fields{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}.csa-fields>div{background:#f8fafc;padding:9px;border-radius:9px}.csa-fields label,.csa-email label{display:block;color:#667085;font-size:10px;margin-bottom:3px}.csa-fields b{font-size:11px;word-break:break-word}.csa-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.csa-actions button,.csa-actions a{border:0;border-radius:9px;padding:9px 10px;background:#eef2f6;color:#172033;text-decoration:none;font-size:11px;font-weight:800;cursor:pointer}.csa-note{margin-top:12px;padding:9px;border:1px solid #f2dfad;background:#fffbeb;color:#7a5b00;border-radius:9px;font-size:10px}.csa-summary{padding:10px;background:#f8fafc;border-radius:10px;font-size:12px}.csa-follow{position:relative;padding:10px;background:#f8fafc;border-radius:9px}.csa-follow.done{opacity:.6}.csa-follow span{display:block;color:#667085;font-size:10px;margin-top:3px}.csa-follow button{position:absolute;right:8px;top:8px;border:0;border-radius:7px;padding:6px;background:#fff;cursor:pointer;font-size:10px}.csa-email{display:grid;gap:7px}.csa-email input,.csa-email textarea{width:100%;box-sizing:border-box;padding:9px;border:1px solid #e4e7ec;border-radius:8px;font:inherit}.csa-email textarea{min-height:170px;resize:vertical}@media(max-width:560px){.csa-fields{grid-template-columns:1fr}}`;
    document.head.appendChild(style);
  }

  function launch() {
    let button = document.getElementById('csa-launch');
    if (!button) {
      button = document.createElement('button');
      button.id = 'csa-launch';
      button.className = 'csa-launch';
      button.innerHTML = '<span class="dot"></span>Sales Agent';
      button.addEventListener('click', () => { state.panel='home'; renderPanel(); });
      document.body.appendChild(button);
    }
  }

  document.addEventListener('click', async (event) => {
    const target = event.target.closest('[data-csa]');
    if (!target) return;
    const action = target.dataset.csa;
    if (action === 'close') return closePanel();
    if (action === 'pick-contact') { state.selected = selectedLeadOrFirst()?.id; state.panel='contact'; return renderPanel(); }
    if (action === 'pick-email') { state.selected = selectedLeadOrFirst()?.id; state.panel='email'; return renderPanel(); }
    if (action === 'followups') { state.panel='followups'; return renderPanel(); }
    if (action === 'search') {
      const lead = selectedLeadOrFirst();
      if (lead) openExternal(searchUrl(lead.company, target.dataset.kind));
      return;
    }
    if (action === 'email') { state.panel='email'; return renderPanel(); }
    if (action === 'follow') {
      const lead = selectedLeadOrFirst();
      if (!lead) return;
      const date = window.prompt('Follow-up date (YYYY-MM-DD):', today());
      if (!date) return;
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return window.alert('Use YYYY-MM-DD.');
      const actionText = window.prompt('Next action:', 'Send follow-up / call / quote') || 'Follow up with lead';
      state.followUps.push({ id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, leadId: lead.id, company: lead.company, email: lead.businessEmail || '', date, action: actionText, completed: false, createdAt: new Date().toISOString() });
      await saveAgent();
      renderPanel();
      return;
    }
    if (action === 'complete-follow') {
      state.followUps = state.followUps.map((x) => String(x.id) === String(target.dataset.id) ? { ...x, completed: true, completedAt: new Date().toISOString() } : x);
      await saveAgent();
      renderPanel();
      return;
    }
    if (action === 'log-email') {
      const lead = selectedLeadOrFirst();
      if (lead) {
        lead.lastEmailPreparedAt = new Date().toISOString();
        lead.emailStatus = 'Prepared';
        localStorage.setItem(KEY, JSON.stringify(state.leads));
      }
      await saveAgent();
      window.alert('Email activity logged ✓');
      return;
    }
  });

  async function init() {
    addStyles();
    loadLeads();
    try {
      const db = await api.readDatabase();
      if (db && typeof db === 'object') {
        state.settings = db.settings || {};
        state.followUps = Array.isArray(db.followUps) ? db.followUps : [];
        if ((!state.leads || !state.leads.length) && Array.isArray(db.leads) && db.leads.length) {
          state.leads = db.leads;
          localStorage.setItem(KEY, JSON.stringify(state.leads));
        }
      }
      await saveAgent();
    } catch {}
    launch();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
