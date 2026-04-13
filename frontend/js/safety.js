/* ============================================================
   FloodGuard India – Safety Precautions Section
   ============================================================ */

window.showSafety = function (level, el) {
    document.querySelectorAll('.alt-tab').forEach(b => b.classList.remove('active'));
    if (el) el.classList.add('active');

    const grid = document.getElementById('safetyGrid');
    grid.innerHTML = '';
    const cards = SAFETY_DATA[level] || SAFETY_DATA.low;

    cards.forEach(card => {
        const li = card.tips.map(t => `<li>${t}</li>`).join('');
        grid.innerHTML += `
      <div class="safety-card">
        <div class="safety-card-icon">${card.icon}</div>
        <div class="safety-card-title">${card.title}</div>
        <ul class="safety-card-list">${li}</ul>
      </div>`;
    });
};
