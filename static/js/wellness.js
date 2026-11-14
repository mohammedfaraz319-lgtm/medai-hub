(function () {
  const data = JSON.parse(document.getElementById('wdata').textContent);

  // highlight today in the weekly plan (JS getDay: Sun=0 -> our Mon=0)
  const idx = (new Date().getDay() + 6) % 7;
  const today = document.querySelector('.day[data-d="' + idx + '"]');
  if (today) today.classList.add('today');

  const gender = document.getElementById('gender'), muscle = document.getElementById('muscle');
  function renderWorkout() {
    document.getElementById('focus').textContent = data.focus[gender.value];
    document.getElementById('exlist').replaceChildren(...data.workouts[muscle.value].map(x => h('li', {}, x)));
  }
  gender.addEventListener('change', renderWorkout); muscle.addEventListener('change', renderWorkout); renderWorkout();

  const goal = document.getElementById('goal');
  function renderDiet() {
    const d = data.diets[goal.value];
    document.getElementById('diettip').textContent = d.tip;
    document.getElementById('meals').replaceChildren(...Object.entries(d.meals).map(([k, v]) => h('div', { class: 'meal' }, h('b', {}, k), h('span', {}, v))));
  }
  goal.addEventListener('change', renderDiet); renderDiet();

  const form = document.getElementById('f-bmi'), out = document.getElementById('r-bmi');
  form.addEventListener('submit', async ev => {
    ev.preventDefault();
    const btn = form.querySelector('button[type=submit]');
    setBusy(btn, true, 'Calculating…');
    try {
      const d = await api('/api/bmi', Object.fromEntries(new FormData(form)));
      const m = (v, l) => h('div', {}, h('b', {}, v), h('span', {}, l));
      out.replaceChildren(
        h('h3', {}, 'Your numbers'),
        h('p', { class: 'kv' }, h('b', {}, 'BMI: '), d.bmi + ' - ' + d.category),
        h('p', { class: 'small' }, 'Healthy weight for your height: ' + d.healthy_range_kg[0] + ' - ' + d.healthy_range_kg[1] + ' kg (WHO Asia-Pacific cut-offs)'),
        h('div', { class: 'metric' }, m(d.bmr, 'BMR kcal'), m(d.maintenance_kcal, 'Maintain kcal'), m(d.loss_kcal, 'Fat-loss kcal'), m(d.gain_kcal, 'Muscle-gain kcal'), m(d.water_litres + ' L', 'Water / day')));
      out.classList.add('on');
    } catch (e) { out.replaceChildren(h('div', { class: 'alert' }, e.message)); out.classList.add('on'); }
    setBusy(btn, false);
  });
})();
