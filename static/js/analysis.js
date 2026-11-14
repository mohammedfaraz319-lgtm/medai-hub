(function () {
  const picker = document.getElementById('picker');
  const panels = ['skin', 'symptoms', 'diabetes', 'heart'];

  function show(name) {
    if (!panels.includes(name)) name = 'skin';
    panels.forEach(p => document.getElementById('p-' + p).classList.toggle('on', p === name));
    picker.value = name;
    stopCam();
  }
  picker.addEventListener('change', () => { history.replaceState(null, '', '#' + picker.value); show(picker.value); });

  function showResult(el, ...kids) { el.replaceChildren(...kids); el.classList.add('on'); el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  function showError(el, msg) { showResult(el, h('div', { class: 'alert', role: 'alert' }, '⚠️ ' + msg)); }
  const badge = (txt, cls) => h('span', { class: 'badge b-' + cls }, txt);

  // ------------------------------------------------------------ SKIN
  const file = document.getElementById('skinfile'), preview = document.getElementById('preview'),
        noimg = document.getElementById('noimg'), video = document.getElementById('cam'),
        canvas = document.getElementById('canvas'), snap = document.getElementById('snap');
  let blob = null, stream = null, blobName = 'upload.jpg';

  function setImage(b, name) {
    blob = b; blobName = name;
    preview.src = URL.createObjectURL(b); preview.hidden = false;
    noimg.textContent = name;
  }
  file.addEventListener('change', () => { if (file.files[0]) setImage(file.files[0], file.files[0].name); });

  function stopCam() {
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    video.style.display = 'none'; snap.style.display = 'none';
  }
  document.getElementById('cambtn').addEventListener('click', async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return showError(document.getElementById('r-skin'), 'Camera is not available in this browser (it needs HTTPS or localhost). Use "Choose a File" instead.');
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      video.srcObject = stream; video.style.display = 'block'; snap.style.display = 'inline-block';
    } catch (e) { showError(document.getElementById('r-skin'), 'Could not access the camera. Please allow camera permission or upload a file.'); }
  });
  snap.addEventListener('click', () => {
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    canvas.toBlob(b => { setImage(b, 'capture.jpg'); stopCam(); }, 'image/jpeg', .92);
  });

  const skinBtn = document.getElementById('skinbtn'), rSkin = document.getElementById('r-skin');
  skinBtn.addEventListener('click', async () => {
    if (!blob) return showError(rSkin, 'Please choose or capture an image first.');
    const fd = new FormData(); fd.append('image', blob, blobName);
    setBusy(skinBtn, true);
    try {
      const d = await api('/api/skin', fd, true);
      const abcd = d.abcd;
      showResult(rSkin,
        h('h3', {}, 'Analysis Result'),
        h('p', { class: 'kv' }, h('b', {}, 'Top Prediction: '), d.top_prediction, ' ', badge(d.urgency + ' concern', d.urgency)),
        h('p', { class: 'kv' }, h('b', {}, 'Confidence: '), d.confidence + '%'),
        h('p', { class: 'kv' }, h('b', {}, 'Ranked Results:')),
        d.ranked.map(r => barRow(r.label, r.prob)),
        h('img', { class: 'overlay', src: d.overlay, alt: 'Detected lesion outline' }),
        h('p', { class: 'small', style: 'text-align:center' }, d.segmented ? 'Red outline = detected lesion border' : 'Lesion could not be isolated clearly - retake the photo on plain skin with good lighting.'),
        h('div', { class: 'abcd' },
          [['Asymmetry', abcd.asymmetry], ['Border', abcd.border], ['Colour', abcd.color], ['Diameter', abcd.diameter]]
            .map(([l, v]) => h('div', {}, h('b', {}, v), h('span', {}, l)))),
        h('p', {}, d.note),
        h('p', { class: 'small' }, '⚕️ ' + d.method + '. Not a diagnosis - see a dermatologist for any changing, bleeding or irregular mole.'));
    } catch (e) { showError(rSkin, e.message); }
    setBusy(skinBtn, false);
  });

  // ------------------------------------------------------------ SYMPTOMS
  const chips = [...document.querySelectorAll('#chips .chip')], count = document.getElementById('symcount');
  const updateCount = () => { count.textContent = document.querySelectorAll('#chips input:checked').length + ' selected'; };
  chips.forEach(c => c.querySelector('input').addEventListener('change', updateCount));
  document.getElementById('symsearch').addEventListener('input', e => {
    const q = e.target.value.trim().toLowerCase();
    chips.forEach(c => { c.style.display = !q || c.dataset.name.includes(q) ? '' : 'none'; });
  });
  const symBtn = document.getElementById('symbtn'), rSym = document.getElementById('r-symptoms');
  symBtn.addEventListener('click', async () => {
    const symptoms = [...document.querySelectorAll('#chips input:checked')].map(i => i.value);
    if (!symptoms.length) return showError(rSym, 'Select at least one symptom.');
    setBusy(symBtn, true);
    try {
      const d = await api('/api/symptoms', { symptoms });
      showResult(rSym,
        h('h3', {}, 'Analysis Result'),
        h('p', { class: 'kv' }, h('b', {}, 'Top Prediction: '), d.top_prediction),
        h('p', { class: 'kv' }, h('b', {}, 'Confidence: '), d.confidence + '%'),
        d.warning && h('div', { class: 'alert', role: 'alert' }, '⚠️ ' + d.warning + ' Seek medical care immediately. ' + d.emergency),
        h('p', { class: 'kv' }, h('b', {}, 'Ranked Results:')),
        d.predictions.map(p => h('div', { class: 'disease' },
          h('h4', {}, p.disease, badge(p.severity, p.severity)),
          barRow('Likelihood', p.probability),
          h('p', { class: 'small', style: 'margin:4px 0' }, p.desc),
          h('p', { class: 'small', style: 'margin:4px 0' }, h('b', {}, 'Consult: '), p.specialist),
          h('ul', {}, p.precautions.map(x => h('li', {}, x))))),
        h('p', { class: 'small' }, '⚕️ Naive Bayes model on a synthetic knowledge-base dataset. Not a diagnosis.'));
    } catch (e) { showError(rSym, e.message); }
    setBusy(symBtn, false);
  });

  // ------------------------------------------------------------ RISK FORMS
  function riskForm(name, resultId) {
    const form = document.getElementById('f-' + name), out = document.getElementById(resultId);
    form.addEventListener('submit', async ev => {
      ev.preventDefault();
      const btn = form.querySelector('button[type=submit]');
      setBusy(btn, true);
      try {
        const d = await api('/api/' + name, Object.fromEntries(new FormData(form)));
        showResult(out,
          h('h3', {}, 'Analysis Result'),
          h('p', { class: 'kv' }, h('b', {}, 'Top Prediction: '), d.category + ' risk ', badge(d.category, d.risk_percent < 15 ? 'low' : d.risk_percent < 35 ? 'medium' : 'high')),
          h('p', { class: 'kv' }, h('b', {}, 'Confidence (estimated risk): '), d.risk_percent + '%'),
          barRow('Estimated risk', d.risk_percent, true),
          h('p', { class: 'kv' }, h('b', {}, 'What drives your score:')),
          d.factors.map(f => h('div', { class: 'small', style: 'margin:3px 0' },
            (f.direction === 'raises' ? '🔺 ' : f.direction === 'lowers' ? '🔻 ' : '▫️ ') + f.name + ' - ' + f.direction + ' your risk')),
          h('p', { class: 'kv' }, h('b', {}, 'Advice:')),
          h('ul', { style: 'margin:4px 0 0 18px;font-size:.9rem' }, d.advice.map(a => h('li', {}, a))),
          h('p', { class: 'small' }, '⚕️ Logistic regression on a synthetic population. A screening aid, not a diagnosis.'));
      } catch (e) { showError(out, e.message); }
      setBusy(btn, false, 'Calculating…');
    });
  }
  riskForm('diabetes', 'r-diabetes');
  riskForm('heart', 'r-heart');

  // run last, after every variable above is defined
  show(location.hash.slice(1) || 'skin');
})();
