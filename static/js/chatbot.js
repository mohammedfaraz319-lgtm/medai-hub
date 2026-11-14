(function () {
  const box = document.getElementById('msgs'), form = document.getElementById('cform'),
        input = document.getElementById('cinput'), quick = document.getElementById('quick');

  // render **bold** and *italic* without ever using innerHTML
  function rich(text) {
    const frag = document.createDocumentFragment();
    text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).forEach(part => {
      if (part.startsWith('**')) frag.append(h('b', {}, part.slice(2, -2)));
      else if (part.startsWith('*') && part.length > 2) frag.append(h('i', {}, part.slice(1, -1)));
      else frag.append(part);
    });
    return frag;
  }
  function add(text, who) {
    const el = h('div', { class: 'm ' + who });
    el.append(who === 'bot' ? rich(text) : document.createTextNode(text));
    box.append(el); box.scrollTop = box.scrollHeight;
  }
  const delay = ms => new Promise(r => setTimeout(r, ms));
  async function say(messages) {
    for (const m of messages) {
      const t = h('div', { class: 'm bot typing' }, h('i'), h('i'), h('i'));
      box.append(t); box.scrollTop = box.scrollHeight;
      await delay(350 + Math.min(m.length * 4, 700));
      t.remove(); add(m, 'bot');
    }
  }
  async function start() {
    box.replaceChildren(); quick.style.display = 'flex';
    try { const d = await api('/api/chat/start', {}); await say(d.messages); }
    catch (e) { add('Could not start the chat: ' + e.message, 'bot'); }
  }
  async function send(text) {
    text = text.trim(); if (!text) return;
    add(text, 'me'); input.value = ''; quick.style.display = 'none'; input.disabled = true;
    try { const d = await api('/api/chat', { message: text }); await say(d.messages); }
    catch (e) { add('⚠️ ' + e.message, 'bot'); }
    input.disabled = false; input.focus();
  }
  form.addEventListener('submit', e => { e.preventDefault(); send(input.value); });
  quick.querySelectorAll('button').forEach(b => b.addEventListener('click', () => send(b.textContent)));
  document.getElementById('resetbtn').addEventListener('click', start);
  start();
})();
