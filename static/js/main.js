// Shared helpers: theme toggle, CSRF-aware fetch, safe DOM building.
(function () {
  const btn = document.getElementById('theme');
  if (btn) btn.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
})();

window.csrf = () => document.querySelector('meta[name=csrf-token]').content;

window.api = async function (url, body, isForm) {
  const opts = { method: 'POST', headers: { 'X-CSRF-Token': csrf() } };
  if (isForm) opts.body = body;
  else { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body || {}); }
  const res = await fetch(url, opts);
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
};

// tiny element builder - uses textContent so API data can never inject HTML
window.h = function (tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'class') el.className = v;
    else if (k === 'style') el.style.cssText = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
};

window.barRow = function (label, pct, risk) {
  const fill = h('i');
  const row = h('div', { class: 'bar' + (risk ? ' risk' : '') }, h('span', {}, label), h('span', { class: 't' }, fill), h('b', {}, pct + '%'));
  requestAnimationFrame(() => setTimeout(() => (fill.style.width = Math.min(100, pct) + '%'), 30));
  return row;
};

window.setBusy = function (btn, busy, label) {
  btn.disabled = busy;
  if (busy) { btn.dataset.old = btn.textContent; btn.textContent = ''; btn.append(h('span', { class: 'spin' }), label || 'Analyzing…'); }
  else btn.textContent = btn.dataset.old || 'Analyze';
};
