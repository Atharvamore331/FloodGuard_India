/* ============================================================
   FloodGuard India â€“ Dashboard (Live API version)
   All data fetched from http://127.0.0.1:5000/api
   ============================================================ */

// â”€â”€ Session guard â”€â”€
const user = JSON.parse(sessionStorage.getItem('fg_user'));
if (!user) window.location.href = 'index.html';

// Use functions to always read fresh values from sessionStorage
function getCurrentCity() { return sessionStorage.getItem('fg_city') || 'Mumbai'; }
function getCurrentLat() { return sessionStorage.getItem('fg_lat'); }
function getCurrentLng() { return sessionStorage.getItem('fg_lng'); }
const INDIA_COUNTRY_CODE = 'IN';

function formatCountryLabel(country) {
    const code = String(country || INDIA_COUNTRY_CODE).toUpperCase();
    return code === INDIA_COUNTRY_CODE ? 'India' : code;
}

function formatLocationLabel(city, country) {
    const resolvedCity = city || getCurrentCity();
    return `${resolvedCity}, ${formatCountryLabel(country)}`;
}

function getDisplayLocationLabel(city, country) {
    if (getCurrentLat() && getCurrentLng() && city) {
        const gpsLabel = formatLocationLabel(city, country);
        sessionStorage.setItem('fg_city', city);
        sessionStorage.setItem('fg_location', gpsLabel);
        return gpsLabel;
    }
    return sessionStorage.getItem('fg_location') || formatLocationLabel(city, country);
}

function renderLocationLabel(city, country) {
    const label = getDisplayLocationLabel(city, country);
    const locationEl = document.getElementById('locationLabel');
    if (locationEl) locationEl.textContent = label;
    return label;
}

window.getDisplayLocationLabel = getDisplayLocationLabel;

async function loadUserSettingsFromDb() {
    if (!user?.id) return;
    try {
        const res = await fetch(`${API_BASE}/settings?user_id=${encodeURIComponent(user.id)}`, { signal: AbortSignal.timeout(5000) });
        if (!res.ok) return;
        const s = await res.json();
        if (s.theme) localStorage.setItem('fg_theme', s.theme);
        if (s.language) localStorage.setItem('fg_lang', s.language);
        // Only restore saved location if the user hasn't already chosen one this session
        // (avoids skipping the city selection modal on fresh login)
        if (!sessionStorage.getItem('fg_city')) {
            if (s.last_city) sessionStorage.setItem('fg_city', s.last_city);
            if (s.last_location) sessionStorage.setItem('fg_location', s.last_location);
            if (s.last_lat !== null && s.last_lat !== undefined) sessionStorage.setItem('fg_lat', s.last_lat);
            if (s.last_lng !== null && s.last_lng !== undefined) sessionStorage.setItem('fg_lng', s.last_lng);
        }
    } catch { }
}

function persistUserSettingsToDb(partial) {
    if (!user?.id) return;
    fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, ...partial })
    }).catch(() => { });
}
window.persistUserSettingsToDb = persistUserSettingsToDb;

function isIndiaLocation(data) {
    return (data?.country || '').toUpperCase() === INDIA_COUNTRY_CODE;
}

function inferStateFromCity(cityName) {
    if (!cityName || typeof INDIA_STATES_CITIES !== 'object') return '';
    const city = cityName.trim().toLowerCase();
    for (const [state, cities] of Object.entries(INDIA_STATES_CITIES)) {
        if ((cities || []).some(c => c.toLowerCase() === city)) return state;
    }
    return '';
}

function inferSubdivisionForCity(cityName) {
    const city = (cityName || '').trim().toLowerCase();
    const state = inferStateFromCity(cityName);

    // City-specific overrides where a state has multiple IMD subdivisions.
    const cityOverrides = {
        // Maharashtra
        'mumbai': 'Konkan & Goa',
        'thane': 'Konkan & Goa',
        'navi mumbai': 'Konkan & Goa',
        'vasai': 'Konkan & Goa',
        'pune': 'Madhya Maharashtra',
        'nashik': 'Madhya Maharashtra',
        'nagpur': 'Vidarbha',
        'aurangabad': 'Matathwada',
        // Karnataka
        'mangaluru': 'Coastal Karnataka',
        'hubballi': 'North Interior Karnataka',
        'belagavi': 'North Interior Karnataka',
        'bengaluru': 'South Interior Karnataka',
        // Andhra Pradesh
        'tirupati': 'Rayalseema',
        'kurnool': 'Rayalseema',
        'visakhapatnam': 'Coastal Andhra Pradesh',
        'vijayawada': 'Coastal Andhra Pradesh',
        // Gujarat
        'rajkot': 'Saurashtra & Kutch',
        'jamnagar': 'Saurashtra & Kutch',
        'bhavnagar': 'Saurashtra & Kutch',
        'surat': 'Gujarat Region',
        'ahmedabad': 'Gujarat Region',
        // Rajasthan
        'jaipur': 'East Rajasthan',
        'kota': 'East Rajasthan',
        'jodhpur': 'West Rajasthan',
        'bikaner': 'West Rajasthan',
        // Uttar Pradesh
        'lucknow': 'East Uttar Pradesh',
        'varanasi': 'East Uttar Pradesh',
        'kanpur': 'East Uttar Pradesh',
        'agra': 'West Uttar Pradesh',
        'meerut': 'West Uttar Pradesh',
        'noida': 'West Uttar Pradesh',
        // West Bengal
        'kolkata': 'Gangetic West Bengal',
        'howrah': 'Gangetic West Bengal',
        'siliguri': 'Sub Himalayan West Bengal & Sikkim',
        // MP
        'bhopal': 'West Madhya Pradesh',
        'indore': 'West Madhya Pradesh',
        'jabalpur': 'East Madhya Pradesh',
    };
    if (cityOverrides[city]) return cityOverrides[city];

    // State-level fallback mapping to IMD subdivisions.
    const stateToSubdivision = {
        'Andhra Pradesh': 'Coastal Andhra Pradesh',
        'Arunachal Pradesh': 'Arunachal Pradesh',
        'Assam': 'Assam & Meghalaya',
        'Bihar': 'Bihar',
        'Chhattisgarh': 'Chhattisgarh',
        'Goa': 'Konkan & Goa',
        'Gujarat': 'Gujarat Region',
        'Haryana': 'Haryana Delhi & Chandigarh',
        'Himachal Pradesh': 'Himachal Pradesh',
        'Jharkhand': 'Jharkhand',
        'Karnataka': 'South Interior Karnataka',
        'Kerala': 'Kerala',
        'Madhya Pradesh': 'West Madhya Pradesh',
        'Maharashtra': 'Madhya Maharashtra',
        'Manipur': 'Naga Mani Mizo Tripura',
        'Meghalaya': 'Assam & Meghalaya',
        'Mizoram': 'Naga Mani Mizo Tripura',
        'Nagaland': 'Naga Mani Mizo Tripura',
        'Odisha': 'Orissa',
        'Punjab': 'Punjab',
        'Rajasthan': 'East Rajasthan',
        'Sikkim': 'Sub Himalayan West Bengal & Sikkim',
        'Tamil Nadu': 'Tamil Nadu',
        'Telangana': 'Telangana',
        'Tripura': 'Naga Mani Mizo Tripura',
        'Uttar Pradesh': 'East Uttar Pradesh',
        'Uttarakhand': 'Uttarakhand',
        'West Bengal': 'Gangetic West Bengal',
        'Delhi': 'Haryana Delhi & Chandigarh',
        'Jammu & Kashmir': 'Jammu & Kashmir',
        'Ladakh': 'Jammu & Kashmir',
        'Chandigarh': 'Haryana Delhi & Chandigarh',
        'Pondicherry': 'Tamil Nadu',
    };

    return stateToSubdivision[state] || '';
}
function hasSavedLocation() {
    const city = (sessionStorage.getItem('fg_city') || '').trim();
    const lat = (sessionStorage.getItem('fg_lat') || '').trim();
    const lng = (sessionStorage.getItem('fg_lng') || '').trim();
    return !!city || (!!lat && !!lng);
}

function getCityOptions() {
    if (typeof INDIA_STATES_CITIES === 'object' && INDIA_STATES_CITIES) {
        const set = new Set();
        Object.values(INDIA_STATES_CITIES).forEach(list => {
            (list || []).forEach(c => set.add(c));
        });
        return Array.from(set).sort((a, b) => a.localeCompare(b));
    }
    return ['Mumbai', 'Pune', 'Delhi', 'Kolkata', 'Chennai', 'Bengaluru', 'Hyderabad'];
}

async function ensureLocationSelected() {
    // Only show the location picker right after a fresh login.
    // auth.js sets 'fg_location_pending' on successful login.
    // On page refresh / nav within session this flag is absent → skip.
    if (!sessionStorage.getItem('fg_location_pending')) return;

    const modal = document.getElementById('locModal');
    const allowBtn = document.getElementById('locAllowBtn');
    const chooseCityBtn = document.getElementById('locChooseCityBtn');
    const cityPanel = document.getElementById('locCityPanel');
    const citySelect = document.getElementById('locCitySelect');
    const cityContinueBtn = document.getElementById('locCityContinueBtn');
    const msg = document.getElementById('locModalMsg');

    if (!modal || !allowBtn || !chooseCityBtn || !cityPanel || !citySelect || !cityContinueBtn || !msg) return;

    const cities = getCityOptions();
    citySelect.innerHTML = cities.map(c => `<option value="${c}">${c}</option>`).join('');

    // Pre-select previously saved city (from DB) so user can just confirm
    const savedCity = sessionStorage.getItem('fg_city');
    if (savedCity && cities.includes(savedCity)) {
        citySelect.value = savedCity;
        // Show city panel pre-filled so user can confirm quickly
        cityPanel.classList.remove('hidden');
        msg.textContent = `Previously: ${savedCity}. Confirm or choose a different city.`;
    }

    modal.classList.remove('hidden');

    await new Promise((resolve) => {
        let finished = false;
        const done = () => {
            if (finished) return;
            finished = true;
            // Clear the pending flag — modal won't show again until next login
            sessionStorage.removeItem('fg_location_pending');
            modal.classList.add('hidden');
            resolve();
        };

        const onChooseCity = () => {
            cityPanel.classList.remove('hidden');
            msg.textContent = 'Select your city to continue.';
        };

        const onAllow = () => {
            allowBtn.disabled = true;
            msg.textContent = 'Requesting location access...';

            if (!navigator.geolocation) {
                msg.textContent = 'Location is not supported. Please choose city.';
                cityPanel.classList.remove('hidden');
                allowBtn.disabled = false;
                return;
            }

            navigator.geolocation.getCurrentPosition(async (pos) => {
                const { latitude, longitude } = pos.coords;
                sessionStorage.setItem('fg_lat', latitude);
                sessionStorage.setItem('fg_lng', longitude);
                sessionStorage.setItem('fg_city', 'Current Location');
                // Keep user-facing label readable until reverse lookup resolves city.
                sessionStorage.setItem('fg_location', 'Current Location, India');

                try {
                    const res = await fetch(`${API_BASE}/weather?lat=${latitude}&lng=${longitude}`, { signal: AbortSignal.timeout(7000) });
                    const data = await res.json();
                    if (res.ok && !data.error) {
                        if (!isIndiaLocation(data)) {
                            msg.textContent = 'FloodGuard is currently limited to India locations only. Please choose an Indian city.';
                            sessionStorage.removeItem('fg_lat');
                            sessionStorage.removeItem('fg_lng');
                            sessionStorage.removeItem('fg_city');
                            sessionStorage.removeItem('fg_location');
                            cityPanel.classList.remove('hidden');
                            allowBtn.disabled = false;
                            return;
                        }
                        const resolvedCity = data.city || 'Current Location';
                        sessionStorage.setItem('fg_city', resolvedCity);
                        sessionStorage.setItem('fg_location', `${resolvedCity}, ${data.country || 'IN'}`);
                        persistUserSettingsToDb({
                            last_city: resolvedCity,
                            last_location: `${resolvedCity}, ${data.country || 'IN'}`,
                            last_lat: latitude,
                            last_lng: longitude
                        });
                    }
                } catch { }

                done();
            }, () => {
                msg.textContent = 'Location permission denied. Please choose your city.';
                cityPanel.classList.remove('hidden');
                allowBtn.disabled = false;
            }, { timeout: 10000, maximumAge: 60000 });
        };

        const onCityContinue = async () => {
            const selectedCity = citySelect.value;
            if (!selectedCity) {
                msg.textContent = 'Please select a city.';
                return;
            }

            cityContinueBtn.disabled = true;
            msg.textContent = 'Loading city details...';
            try {
                const res = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(selectedCity)}`, { signal: AbortSignal.timeout(12000) });
                const data = await res.json();
                if (!res.ok || data.error) throw new Error(data.error || 'City not found');
                if (!isIndiaLocation(data)) {
                    msg.textContent = 'FloodGuard is currently limited to India locations only.';
                    cityContinueBtn.disabled = false;
                    return;
                }

                const resolvedCity = data.city || selectedCity;
                sessionStorage.setItem('fg_city', resolvedCity);
                sessionStorage.setItem('fg_location', `${resolvedCity}, ${data.country || 'IN'}`);
                sessionStorage.removeItem('fg_lat');
                sessionStorage.removeItem('fg_lng');
                persistUserSettingsToDb({
                    last_city: resolvedCity,
                    last_location: `${resolvedCity}, ${data.country || 'IN'}`,
                    last_lat: null,
                    last_lng: null
                });
                done();
            } catch {
                // Fallback: let user proceed with selected Indian city even if weather lookup is temporarily unavailable.
                const resolvedCity = selectedCity;
                sessionStorage.setItem('fg_city', resolvedCity);
                sessionStorage.setItem('fg_location', `${resolvedCity}, IN`);
                sessionStorage.removeItem('fg_lat');
                sessionStorage.removeItem('fg_lng');
                persistUserSettingsToDb({
                    last_city: resolvedCity,
                    last_location: `${resolvedCity}, IN`,
                    last_lat: null,
                    last_lng: null
                });
                msg.textContent = 'Using selected city. Live weather will load shortly.';
                done();
            }
        };

        chooseCityBtn.addEventListener('click', onChooseCity);
        allowBtn.addEventListener('click', onAllow);
        cityContinueBtn.addEventListener('click', onCityContinue);
    });
}

// Live data cache
let liveRisk = null;
let liveWeather = null;

// â”€â”€ Init â”€â”€
window.addEventListener('DOMContentLoaded', async () => {
    // Load theme/language from DB first (before rendering)
    // but NOT location — that's handled by ensureLocationSelected below
    setupSidebar();
    setupTheme();
    setupNavigation();
    applyLanguage(localStorage.getItem('fg_lang') || 'en');
    // Show city selection modal FIRST (before DB prefs restore location)
    await ensureLocationSelected();
    // Now load remaining DB settings (won't overwrite user's fresh city choice)
    await loadUserSettingsFromDb();
    setupUser();

    // Clear debounce so the first alert on login always sends
    localStorage.removeItem('fg_last_alert_ts');
    localStorage.removeItem('fg_last_alert_city');

    // Check API health first
    await checkAPIStatus();
    // Load overview (fetch predict + weather in parallel)
    await loadOverview();
    // Setup breadcrumb and notifications AFTER data is loaded
    setupBreadcrumb();

    // â”€â”€ Auto-request browser notification permission â”€â”€
    // Only ask if not already decided and browserEnabled pref is on (or first visit)
    const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    if ('Notification' in window && Notification.permission === 'default') {
        // Small delay so the dashboard is visually ready
        setTimeout(() => {
            Notification.requestPermission().then(perm => {
                if (perm === 'granted') {
                    // Save preference & send welcome notification
                    prefs.browserEnabled = true;
                    localStorage.setItem('fg_alert_prefs', JSON.stringify(prefs));
                    // Update the toggle in alerts panel if visible
                    const tog = document.getElementById('toggleBrowser');
                    if (tog) tog.checked = true;
                    new Notification('FloodGuard India', {
                        body: `Welcome, ${user?.name || 'User'}! Browser flood alerts are now active.`,
                        icon: ''
                    });
                }
            });
        }, 2000);
    }
});


// â”€â”€ Check if API is running â”€â”€
async function checkAPIStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            document.getElementById('apiStatusBadge') && (document.getElementById('apiStatusBadge').textContent = 'API Live');
        }
    } catch {
        showToast('API server not running. Start api.py first.', 'error');
    }
}

// â”€â”€ Load Overview Section â”€â”€ (always reads fresh sessionStorage)
async function loadOverview() {
    setStatsLoading(true);
    try {
        // IMPORTANT: read fresh each time so city switching works
        const city = getCurrentCity();
        const gpsLat = getCurrentLat();
        const gpsLng = getCurrentLng();

        const cityParam = (gpsLat && gpsLng)
            ? `lat=${gpsLat}&lng=${gpsLng}&city=Current Location`
            : `city=${encodeURIComponent(city)}`;

        const [riskData, forecastData] = await Promise.all([
            apiFetch(`${API_BASE}/predict?${cityParam}`).catch(e => null),
            apiFetch(`${API_BASE}/forecast?${cityParam}`).catch(e => null),
        ]);

        const weatherData = riskData?.weather || null;
        if (weatherData && !isIndiaLocation(weatherData)) {
            sessionStorage.setItem('fg_city', 'Mumbai');
            sessionStorage.setItem('fg_location', 'Mumbai, India');
            sessionStorage.removeItem('fg_lat');
            sessionStorage.removeItem('fg_lng');
            showToast('FloodGuard is limited to India locations only. Switched to Mumbai.', 'error');
            const mumbai = await apiFetch(`${API_BASE}/predict?city=Mumbai`);
            const mumbaiForecast = await apiFetch(`${API_BASE}/forecast?city=Mumbai`);
            liveRisk = mumbai;
            liveWeather = mumbai?.weather || null;
            if (mumbai) updateRiskBanner(mumbai);
            if (mumbai?.weather) updateStats(mumbai.weather, mumbai);
            if (mumbaiForecast) populateForecast(mumbaiForecast.forecast || []);
            setupLastUpdated();
            return;
        }

        liveRisk = riskData;
        liveWeather = weatherData;

        if (riskData) updateRiskBanner(riskData);
        if (weatherData) updateStats(weatherData, riskData);
        if (forecastData) populateForecast(forecastData.forecast || []);

        setupLastUpdated();

    } catch (err) {
        showToast('Error loading data: ' + err.message, 'error');
    } finally {
        setStatsLoading(false);
    }
}

function setStatsLoading(on) {
    const vals = document.querySelectorAll('.stat-value');
    if (on) vals.forEach(v => { if (v.textContent === '--') v.textContent = '...'; });
}

// â”€â”€ Risk Banner â”€â”€
function updateRiskBanner(data) {
    const risk = data.risk || 'moderate';
    const banner = document.getElementById('riskBanner');
    const badge = document.getElementById('riskBadge');
    banner.className = `risk-banner ${risk}`;

    const icons = { low: 'OK', moderate: 'ALERT', high: 'HIGH', critical: 'CRITICAL' };
    document.getElementById('riskIcon').textContent = icons[risk] || 'RISK';
    document.getElementById('riskLevel').textContent = data.label || risk.toUpperCase();
    document.getElementById('riskDesc').textContent = data.message || '';

    const score = (data.score !== undefined && data.score !== null)
        ? parseFloat(data.score).toFixed(3)
        : (data.probability ? (data.probability * 100).toFixed(3) : 'N/A');
    badge.textContent = `${score}%`;
    badge.className = `risk-badge ${risk}`;

    // Update location chip with real city name
    if (data.city) {
        renderLocationLabel(data.city, data.weather?.country || INDIA_COUNTRY_CODE);
    }

    // Trigger threshold-based notification (email/SMS/browser)
    if (typeof window.checkAndSendThresholdAlert === 'function') {
        window.checkAndSendThresholdAlert(data);
    }
}

// â”€â”€ Stats Cards â”€â”€
function updateStats(weather, risk) {
    document.getElementById('statTemp').textContent = `${weather.temperature ?? '--'} C`;
    document.getElementById('statHumidity').textContent = `${weather.humidity ?? '--'}%`;
    document.getElementById('statWind').textContent = `${weather.wind_speed ?? '--'} km/h`;
    document.getElementById('statRainfall').textContent = `${((weather.rain_1h || 0) * 24).toFixed(1)} mm`;
    document.getElementById('statRisk').textContent = risk ? `${parseFloat(risk.score).toFixed(3)}/100` : '--/100';

    // Trends
    const hum = weather.humidity || 60;
    const humTrend = document.getElementById('humidTrend');
    humTrend.textContent = hum > 85 ? 'Very High' : hum > 70 ? 'High' : 'Normal';
    humTrend.className = `stat-trend ${hum > 80 ? 'up' : ''}`;

    const rain = (weather.rain_1h || 0) * 24;
    const rainfallTrend = document.getElementById('rainfallTrend');
    rainfallTrend.textContent = rain > 50 ? 'Heavy' : rain > 10 ? 'Moderate' : 'Light';
    rainfallTrend.className = `stat-trend ${rain > 20 ? 'up' : ''}`;

    if (risk) {
        const riskTrend = document.getElementById('riskTrend');
        riskTrend.textContent = `${parseFloat(risk.score).toFixed(3)}/100`;
        riskTrend.className = `stat-trend ${risk.score > 60 ? 'up' : ''}`;
    }
}

// â”€â”€ 7-Day Forecast â”€â”€
function populateForecast(forecast) {
    const container = document.getElementById('forecastCards');
    container.innerHTML = '';

    if (!forecast.length) {
        container.innerHTML = '<p style="color:var(--text2);font-size:.85rem;">Forecast unavailable. Start api.py for live data.</p>';
        return;
    }

    const riskClass = { low: 'risk-l', moderate: 'risk-m', high: 'risk-h', critical: 'risk-c' };

    forecast.forEach(day => {
        const dateObj = new Date(day.date);
        const dayName = dateObj.toLocaleDateString('en-IN', { weekday: 'short' });
        container.innerHTML += `
      <div class="forecast-card">
        <div class="forecast-day">${dayName}</div>
        <img src="${day.icon_url}" alt="${day.description}" style="width:40px;height:40px;margin:.2rem auto;display:block;" onerror="this.style.display='none'">
        <div class="forecast-temp">${day.temp} C</div>
        <div class="forecast-rain">Rain ${day.rain_mm}mm</div>
        <div class="forecast-risk ${riskClass[day.risk] || 'risk-l'}">${day.risk.toUpperCase()}</div>
      </div>`;
    });
}

// â”€â”€ Rainfall Chart (from CSV via API) â”€â”€
async function buildRainfallChart() {
    const ctx = document.getElementById('rainfallChart').getContext('2d');
    const cityForChart = getCurrentCity();
    const inferredSubdivision = inferSubdivisionForCity(cityForChart);

    // Load available subdivisions
    let subdivisions = [];
    try {
        const subData = await apiFetch(`${API_BASE}/rainfall?action=subdivisions`);
        subdivisions = subData.subdivisions || [];
    } catch { }

    // Populate year selector with a placeholder; will be updated from API response
    const yearSel = document.getElementById('chartYearSelect');
    yearSel.innerHTML = '<option value="">Loading...</option>';

    // Subdivision selector (add dynamically)
    let subSel = document.getElementById('subdivisionSelect');
    if (!subSel && subdivisions.length) {
        const chartHeader = document.querySelector('#section-overview .chart-header');
        subSel = document.createElement('select');
        subSel.id = 'subdivisionSelect';
        subSel.className = 'select-sm';
        subdivisions.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; subSel.appendChild(o); });
        if (chartHeader) chartHeader.appendChild(subSel);
    }

    // Auto-pick subdivision from selected city so chart is city-aware.
    if (subSel && inferredSubdivision && subdivisions.includes(inferredSubdivision)) {
        subSel.value = inferredSubdivision;
    }

    async function loadChart() {
        const year = yearSel.value;  // may be empty on first call; API picks latest available
        let subdivision = subSel
            ? (subSel.value || inferredSubdivision || subdivisions[0] || 'Konkan & Goa')
            : (inferredSubdivision || subdivisions[0] || 'Konkan & Goa');
        let monthlyData, annualData;

        // Try requested subdivision first, fall back to a safe default silently
        const tryFetch = async (sub) => {
            monthlyData = await apiFetch(`${API_BASE}/rainfall?action=monthly&subdivision=${encodeURIComponent(sub)}&year=${year}`);
            annualData = await apiFetch(`${API_BASE}/rainfall?action=annual&subdivision=${encodeURIComponent(sub)}`);
        };

        try {
            await tryFetch(subdivision);
        } catch (e) {
            // Try a known-good default subdivision silently
            try {
                subdivision = subdivisions[0] || 'KONKAN & GOA';
                await tryFetch(subdivision);
            } catch (e2) {
                // Final fallback: render a static placeholder chart
                monthlyData = {
                    months: ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
                    values: [8, 10, 12, 18, 45, 220, 310, 290, 180, 60, 25, 10]
                };
                annualData = { moving_avg_5yr: [] };
            }
        }

        // Populate year dropdown from API's actual available years (first time only)
        if (monthlyData.years_available && yearSel.options.length <= 1) {
            const avail = [...monthlyData.years_available].sort((a, b) => b - a);
            yearSel.innerHTML = '';
            avail.forEach(y => {
                const o = document.createElement('option');
                o.value = y; o.textContent = y;
                yearSel.appendChild(o);
            });
            // Select the year actually returned by the API
            if (monthlyData.year) yearSel.value = monthlyData.year;
        }

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const tc = isDark ? '#94a3b8' : '#64748b';
        const gc = isDark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.06)';

        if (window.rainfallChartInst) window.rainfallChartInst.destroy();

        window.rainfallChartInst = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthlyData.months,
                datasets: [{
                    label: `${monthlyData.year || yearSel.value} Rainfall (mm)`,
                    data: monthlyData.values,
                    backgroundColor: monthlyData.values.map(v =>
                        v > 300 ? 'rgba(239,68,68,.75)' : v > 150 ? 'rgba(249,115,22,.75)' : 'rgba(14,165,233,.65)'
                    ),
                    borderRadius: 6,
                }, {
                    label: '5-yr Moving Avg',
                    data: annualData.moving_avg_5yr?.slice(-12) || [],
                    type: 'line',
                    borderColor: '#6366f1', borderWidth: 2, pointRadius: 3,
                    fill: false, tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: tc } } },
                scales: {
                    x: { grid: { color: gc }, ticks: { color: tc } },
                    y: {
                        grid: { color: gc }, ticks: { color: tc }, beginAtZero: true,
                        title: { display: true, text: 'mm', color: tc }
                    }
                }
            }
        });
    }

    yearSel.onchange = loadChart;
    if (subSel) subSel.onchange = loadChart;
    await loadChart();
}

// ── Sidebar ──
function setupUser() {
    document.getElementById('userName').textContent = user.name || 'User';
    document.getElementById('userAvatar').textContent = (user.name || 'U')[0].toUpperCase();
    renderLocationLabel();
    if (document.getElementById('alertEmail')) document.getElementById('alertEmail').value = user.email || '';
    if (document.getElementById('alertPhone')) document.getElementById('alertPhone').value = user.phone || '';

    // Keep email notifications enabled by default for logged-in users.
    if (user.email) {
        const alertPrefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
        if (alertPrefs.emailEnabled === undefined) {
            alertPrefs.emailEnabled = true;
            localStorage.setItem('fg_alert_prefs', JSON.stringify(alertPrefs));
        }
    }
}

function setupSidebar() {
    const sidebar = document.getElementById('sidebar');
    document.getElementById('sidebarToggle').addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    document.getElementById('menuBtn').addEventListener('click', () => sidebar.classList.toggle('mobile-open'));
    document.addEventListener('click', e => {
        if (window.innerWidth <= 768 && !sidebar.contains(e.target) && !document.getElementById('menuBtn').contains(e.target)) {
            sidebar.classList.remove('mobile-open');
        }
    });
    document.getElementById('logoutBtn').addEventListener('click', () => { sessionStorage.clear(); window.location.href = 'index.html'; });

    // ── Location Search Bar ──
    setupLocationSearch();
}

// â”€â”€ India city list for autocomplete â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const INDIA_CITIES_AC = [
    "Agra", "Ahmedabad", "Ajmer", "Akola", "Alappuzha", "Aligarh", "Allahabad", "Alwar",
    "Amravati", "Amritsar", "Anand", "Aurangabad", "Bangalore", "Bareilly", "Belgaum",
    "Bengaluru", "Bhavnagar", "Bhilai", "Bhopal", "Bhubaneswar", "Bikaner", "Chandigarh",
    "Chennai", "Coimbatore", "Cuttack", "Darbhanga", "Dehradun", "Delhi", "Dhanbad",
    "Durgapur", "Erode", "Faridabad", "Gandhinagar", "Ghaziabad", "Gorakhpur", "Guntur",
    "Gurgaon", "Guwahati", "Gwalior", "Haridwar", "Hubli", "Hyderabad", "Imphal",
    "Indore", "Jabalpur", "Jaipur", "Jalandhar", "Jamshedpur", "Jodhpur", "Kakinada",
    "Kalyan", "Kanpur", "Kochi", "Kolhapur", "Kolkata", "Kota", "Kozhikode", "Lucknow",
    "Ludhiana", "Madurai", "Mangalore", "Meerut", "Moradabad", "Mumbai", "Mysore", "Nagpur",
    "Nashik", "Navi Mumbai", "Nellore", "Noida", "Patna", "Pune", "Raipur", "Rajkot",
    "Ranchi", "Salem", "Shillong", "Shimla", "Siliguri", "Solapur", "Srinagar", "Surat",
    "Thane", "Thiruvananthapuram", "Tiruchirappalli", "Tiruppati", "Udaipur", "Ujjain",
    "Vadodara", "Varanasi", "Vijayawada", "Visakhapatnam", "Warangal", "Mumbai", "Agartala",
    "Aizawl", "Dharamsala", "Dibrugarh", "Goa", "Itanagar", "Jammu", "Jorhat", "Kavaratti",
    "Kohima", "Leh", "Panaji", "Pasighat", "Port Blair", "Shillong", "Silvassa", "Tadepalligudem",
    "Bhagalpur", "Muzaffarpur", "Gaya", "Purnia", "Bihar Sharif", "Dhubri", "Lakhimpur",
    "Silchar", "Tezpur", "Dimapur", "Ukhrul", "Daman", "Palghar", "Sangli", "Nanded"
];

function setupLocationSearch() {
    const input = document.getElementById('locSearchInput');
    const btn = document.getElementById('locSearchBtn');
    const wrap = document.getElementById('locSearchWrap');
    if (!input || !btn) return;

    // â”€â”€ Create suggestion dropdown â”€â”€
    const dropdown = document.createElement('ul');
    dropdown.id = 'cityDropdown';
    dropdown.style.cssText = `
        position:absolute; top:100%; left:0; right:0; z-index:9999;
        background:var(--surface); border:1px solid var(--border);
        border-top:none; border-radius:0 0 8px 8px;
        box-shadow:0 8px 24px rgba(0,0,0,.15);
        list-style:none; margin:0; padding:0;
        max-height:220px; overflow-y:auto; display:none;`;
    wrap.style.position = 'relative';
    wrap.appendChild(dropdown);

    let activeIdx = -1;

    function showSuggestions(query) {
        const q = query.trim().toLowerCase();
        if (!q || q.length < 1) { dropdown.style.display = 'none'; activeIdx = -1; return; }
        const matches = INDIA_CITIES_AC.filter(c => c.toLowerCase().startsWith(q)).slice(0, 8);
        if (!matches.length) { dropdown.style.display = 'none'; return; }

        dropdown.innerHTML = matches.map((city, i) => {
            const hi = `<strong>${city.slice(0, query.length)}</strong>${city.slice(query.length)}`;
            return `<li data-city="${city}" style="
                padding:.55rem 1rem; font-size:.85rem; cursor:pointer;
                border-bottom:1px solid var(--border); color:var(--text);
                transition:background .15s;">
                ${hi}
            </li>`;
        }).join('');
        dropdown.style.display = 'block';
        activeIdx = -1;

        // Hover highlight
        dropdown.querySelectorAll('li').forEach(li => {
            li.addEventListener('mouseenter', () => li.style.background = 'rgba(14,165,233,.1)');
            li.addEventListener('mouseleave', () => li.style.background = '');
            li.addEventListener('mousedown', e => {
                e.preventDefault(); // prevent blur before click
                input.value = li.dataset.city;
                dropdown.style.display = 'none';
                doSearch();
            });
        });
    }

    const doSearch = async () => {
        const query = input.value.trim();
        if (!query) return;
        dropdown.style.display = 'none';

        btn.textContent = '...';
        btn.classList.add('loading');
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/weather?city=${encodeURIComponent(query)}`, {
                signal: AbortSignal.timeout(7000)
            });
            const data = await res.json();
            if (!res.ok || data.error) throw new Error(data.error || 'Not found');
            if (!isIndiaLocation(data)) throw new Error('OUTSIDE_INDIA');

            const resolvedCity = data.city || query;
            sessionStorage.setItem('fg_city', resolvedCity);
            sessionStorage.setItem('fg_location', `${resolvedCity}, ${data.country || 'IN'}`);
            sessionStorage.removeItem('fg_lat');
            sessionStorage.removeItem('fg_lng');
            persistUserSettingsToDb({
                last_city: resolvedCity,
                last_location: `${resolvedCity}, ${data.country || 'IN'}`,
                last_lat: null,
                last_lng: null
            });

            renderLocationLabel(resolvedCity, data.country || INDIA_COUNTRY_CODE);
            input.value = '';
            showToast(`Location updated to ${resolvedCity}`, 'success');
            // Clear stale weather cache so next section switch re-fetches
            liveWeather = null;
            await loadOverview();
            // If weather section is currently visible, reload it too
            const weatherSec = document.getElementById('section-weather');
            if (weatherSec && weatherSec.classList.contains('active')) {
                setTimeout(() => loadWeatherSection(), 200);
            }
        } catch (e) {
            if (e.message === 'OUTSIDE_INDIA') {
                showToast('⚠ FloodGuard is currently limited to India locations only.', 'error');
            } else {
                showToast('Location not found. Try a different spelling.', 'error');
            }
        } finally {
            btn.textContent = 'Search';
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    };

    // â”€â”€ Input events â”€â”€
    input.addEventListener('input', () => showSuggestions(input.value));
    input.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 150));
    input.addEventListener('keydown', e => {
        const items = dropdown.querySelectorAll('li');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIdx = Math.min(activeIdx + 1, items.length - 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIdx = Math.max(activeIdx - 1, -1);
        } else if (e.key === 'Enter') {
            if (activeIdx >= 0 && items[activeIdx]) {
                input.value = items[activeIdx].dataset.city;
                dropdown.style.display = 'none';
            }
            doSearch();
            return;
        } else if (e.key === 'Escape') {
            dropdown.style.display = 'none'; return;
        }
        // Highlight active item
        items.forEach((li, i) => {
            li.style.background = i === activeIdx ? 'rgba(14,165,233,.15)' : '';
        });
        if (items[activeIdx]) input.value = items[activeIdx].dataset.city;
    });

    btn.addEventListener('click', doSearch);
}



function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => {
            e.preventDefault();
            const section = item.dataset.section;
            switchSection(section);
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            const lbl = item.querySelector('.nav-label');
            if (lbl) document.getElementById('currentSection').textContent = lbl.textContent;
            if (window.innerWidth <= 768) document.getElementById('sidebar').classList.remove('mobile-open');
        });
    });
}

function switchSection(id) {
    document.querySelectorAll('.dash-section').forEach(s => s.classList.remove('active'));
    const t = document.getElementById(`section-${id}`);
    if (t) t.classList.add('active');

    if (id === 'map') setTimeout(initMap, 100);
    if (id === 'weather') {
        // Always re-fetch for the current city (don't use stale cache)
        liveWeather = null;
        setTimeout(loadWeatherSection, 100);
    }
    if (id === 'safety') showSafety('low', document.querySelector('.alt-tab'));
    if (id === 'alerts') { buildActiveAlerts(); }
}

function setupBreadcrumb() {
    document.getElementById('notifBtn').addEventListener('click', e => {
        e.stopPropagation();
        const drawer = document.getElementById('notifDrawer');
        // Refresh notifications each time drawer opens
        const list = document.getElementById('notifList');
        const risk = liveRisk;
        if (risk) {
            list.innerHTML = `<div class="notif-item ${risk.risk}"><div>${risk.label} - ${risk.message}</div><div class="notif-time">Just now</div></div>`;
        } else {
            list.innerHTML = '<div class="notif-item info"><div>Monitoring flood conditions...</div><div class="notif-time">Starting up</div></div>';
        }
        drawer.classList.toggle('hidden');
    });
    document.addEventListener('click', () => document.getElementById('notifDrawer').classList.add('hidden'));
}

function setupTheme() {
    const saved = localStorage.getItem('fg_theme') || 'light';
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    updateThemeBtn(saved);
    document.getElementById('themeToggle').addEventListener('click', () => {
        const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        if (next === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
        else document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('fg_theme', next);
        persistUserSettingsToDb({ theme: next });
        updateThemeBtn(next);
    });
}
function updateThemeBtn(t) { const b = document.getElementById('themeToggle'); if (b) b.textContent = t === 'dark' ? '\u2600' : '\uD83C\uDF19'; }

function setupLastUpdated() {
    const now = new Date();
    document.getElementById('lastUpdated').textContent = `Last updated: ${now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST`;
}

// â”€â”€ Season chart (for Weather section) â”€â”€
window.showSeason = function (season, el) {
    document.querySelectorAll('.stab').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    buildSeasonChartFromAPI(season);
};

window.buildSeasonChartFromAPI = async function (season) {
    const ctx = document.getElementById('seasonChart').getContext('2d');
    if (window.seasonChartInst) window.seasonChartInst.destroy();

    const seasonMonths = { kharif: ['Jun', 'Jul', 'Aug', 'Sep'], rabi: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb'], summer: ['Mar', 'Apr', 'May'] };
    const labels = seasonMonths[season];

    let vals = labels.map(() => 0);
    try {
        const sub = document.getElementById('subdivisionSelect')?.value || '';
        const year = document.getElementById('chartYearSelect')?.value || '2020';
        if (sub) {
            const data = await apiFetch(`${API_BASE}/rainfall?action=monthly&subdivision=${encodeURIComponent(sub)}&year=${year}`);
            const monthMap = { Jan: 0, Feb: 1, Mar: 2, Apr: 3, May: 4, Jun: 5, Jul: 6, Aug: 7, Sep: 8, Oct: 9, Nov: 10, Dec: 11 };
            vals = labels.map(m => data.values[monthMap[m]] || 0);
        }
    } catch { }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const tc = isDark ? '#94a3b8' : '#64748b';
    const gc = isDark ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.06)';

    window.seasonChartInst = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: `${season.charAt(0).toUpperCase() + season.slice(1)} Rainfall (mm)`, data: vals, backgroundColor: 'rgba(14,165,233,.65)', borderRadius: 6 }] },
        options: {
            responsive: true, plugins: { legend: { labels: { color: tc } } },
            scales: { x: { grid: { color: gc }, ticks: { color: tc } }, y: { grid: { color: gc }, ticks: { color: tc }, beginAtZero: true } }
        }
    });
};

// â”€â”€ Toast (global) â”€â”€
window.showToast = function (msg, type = 'info') {
    const t = document.getElementById('toast');
    document.getElementById('toastMsg').textContent = msg;
    t.className = `toast ${type}`;
    t.classList.remove('hidden');
    clearTimeout(window._tt);
    window._tt = setTimeout(() => t.classList.add('hidden'), 4000);
};

// Expose liveWeather for weather.js
window.getLiveWeather = () => liveWeather;
window.getLiveRisk = () => liveRisk;
window.getCityParam = () => {
    const city = getCurrentCity();
    const gpsLat = getCurrentLat();
    const gpsLng = getCurrentLng();
    return (gpsLat && gpsLng)
        ? `lat=${gpsLat}&lng=${gpsLng}&city=Current Location`
        : `city=${encodeURIComponent(city)}`;
};


