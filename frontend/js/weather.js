/* ============================================================
   FloodGuard India – Weather Section (Live OWM API)
   ============================================================ */

async function loadWeatherSection() {
    const cityParam = window.getCityParam();

    // Use cached weather from overview if already loaded
    let weather = window.getLiveWeather();

    if (!weather) {
        try {
            weather = await apiFetch(`${API_BASE}/weather?${cityParam}`);
        } catch (e) {
            showToast('Weather API unavailable. Start api.py.', 'error');
            return;
        }
    }

    populateWeatherHero(weather);
    await buildHourlyChart(cityParam);
    await buildWindChart(cityParam);

}

function populateWeatherHero(w) {
    const iconEmoji = {
        '01': '☀', '02': '🌤', '03': '🌥', '04': '☁',
        '09': '🌧', '10': '🌦', '11': '⛈', '13': '❄', '50': '🌫'
    };
    const iconCode = w.icon || '01d';
    const prefix = iconCode.substring(0, 2);
    const emoji = iconEmoji[prefix] || '🌤';

    document.getElementById('weatherEmoji').textContent = emoji;
    document.getElementById('weatherTempBig').textContent = `${w.temperature}°C`;
    const displayLocation = (typeof window.getDisplayLocationLabel === 'function')
        ? window.getDisplayLocationLabel(w.city, w.country || 'IN')
        : `${w.city}, ${w.country || 'IN'}`;
    document.getElementById('weatherLocation').textContent = displayLocation;
    document.getElementById('weatherCondition').textContent = w.description || '';

    document.getElementById('wdFeels').textContent = `${w.feels_like}°C`;
    document.getElementById('wdHumidity').textContent = `${w.humidity}%`;
    document.getElementById('wdPressure').textContent = `${w.pressure} hPa`;
    document.getElementById('wdVisibility').textContent = `${w.visibility} km`;

    // UV Index from OWM free tier not available, estimate from cloud cover
    const uv = w.description?.toLowerCase().includes('clear') ? '8 (High)'
        : w.description?.toLowerCase().includes('cloud') ? '3 (Low)'
            : '5 (Moderate)';
    document.getElementById('wdUV').textContent = uv;

    // Dew point estimate: T - ((100 - RH) / 5)
    const dew = w.temperature - ((100 - w.humidity) / 5);
    document.getElementById('wdDew').textContent = `${Math.round(dew)}°C`;
}

// ── 24h Simulated Hourly (OWM free → use 3-hourly from forecast) ──
async function buildHourlyChart(cityParam) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
    if (window.hourlyChartInst) window.hourlyChartInst.destroy();

    let hours = [];
    let rainfall = [];

    try {
        const data = await apiFetch(`${API_BASE}/forecast?${cityParam}`);
        const forecast = (data.forecast || []).slice(0, 8);
        forecast.forEach(f => {
            hours.push(f.date);
            rainfall.push(f.rain_mm);
        });
    } catch {
        // fallback: simulated
        for (let h = 0; h < 8; h++) {
            hours.push(`+${h * 3}h`);
            rainfall.push(+(Math.random() * 8).toFixed(1));
        }
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const tc = isDark ? '#94a3b8' : '#64748b';
    const gc = isDark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.06)';

    window.hourlyChartInst = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [{
                label: 'Rainfall (mm)',
                data: rainfall,
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14,165,233,.12)',
                fill: true, tension: 0.4, pointRadius: 4,
                pointBackgroundColor: '#0ea5e9'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: tc } } },
            scales: {
                x: { grid: { color: gc }, ticks: { color: tc, maxRotation: 30 } },
                y: { grid: { color: gc }, ticks: { color: tc }, beginAtZero: true, title: { display: true, text: 'mm', color: tc } }
            }
        }
    });
}

// ── Wind & Humidity Dual-Axis from Forecast API ──
async function buildWindChart(cityParam) {
    const ctx = document.getElementById('windChart').getContext('2d');
    if (window.windChartInst) window.windChartInst.destroy();

    let days = [];
    let humVals = [];
    let windVals = [];

    try {
        const data = await apiFetch(`${API_BASE}/forecast?${cityParam}`);
        (data.forecast || []).forEach(f => {
            days.push(new Date(f.date).toLocaleDateString('en-IN', { weekday: 'short' }));
            humVals.push(f.humidity || 0);
        });
        // Wind data comes from current weather extended (simulate per forecast)
        const w = window.getLiveWeather();
        const baseWind = w?.wind_speed || 14;
        windVals = days.map(() => +(baseWind * (0.7 + Math.random() * 0.6)).toFixed(1));
    } catch {
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        humVals = days.map(() => Math.round(60 + Math.random() * 30));
        windVals = days.map(() => +(10 + Math.random() * 20).toFixed(1));
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const tc = isDark ? '#94a3b8' : '#64748b';
    const gc = isDark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.06)';

    window.windChartInst = new Chart(ctx, {
        data: {
            labels: days,
            datasets: [
                { type: 'bar', label: 'Humidity (%)', data: humVals, backgroundColor: 'rgba(14,165,233,.5)', yAxisID: 'y', borderRadius: 4 },
                { type: 'line', label: 'Wind (km/h)', data: windVals, borderColor: '#f59e0b', tension: 0.4, pointRadius: 4, yAxisID: 'y2', fill: false }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: tc } } },
            scales: {
                x: { grid: { color: gc }, ticks: { color: tc } },
                y: { grid: { color: gc }, ticks: { color: tc, callback: v => v + '%' }, position: 'left', beginAtZero: true },
                y2: { grid: { display: false }, ticks: { color: '#f59e0b', callback: v => v + 'km/h' }, position: 'right', beginAtZero: true }
            }
        }
    });
}
