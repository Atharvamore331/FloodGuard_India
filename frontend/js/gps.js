/* ============================================================
   FloodGuard India – GPS & Location Search Logic
   ============================================================ */

const API_BASE_GPS = `http://${window.location.hostname}:5000/api`;
const INDIA_COUNTRY_CODE = 'IN';

function isIndiaLocation(data) {
    return (data?.country || '').toUpperCase() === INDIA_COUNTRY_CODE;
}

// ── Enable Continue button when user types something ──
window.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('locationSearch');
    const btn = document.getElementById('confirmCityBtn');
    if (!input || !btn) return;

    input.addEventListener('input', () => {
        btn.disabled = input.value.trim().length < 2;
        document.getElementById('locationSearchError').textContent = '';
    });

    // Allow pressing Enter to submit
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !btn.disabled) btn.click();
    });
});

// GPS ALLOW
const allowGpsBtn = document.getElementById('allowGpsBtn');
if (allowGpsBtn) {
    allowGpsBtn.addEventListener('click', () => {
        const btn = document.getElementById('allowGpsBtn');
        btn.textContent = '📡 Locating...'; btn.disabled = true;

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const { latitude, longitude } = pos.coords;
                sessionStorage.setItem('fg_lat', latitude);
                sessionStorage.setItem('fg_lng', longitude);
                // Use readable fallback label; API lookup will replace this with city name.
                sessionStorage.setItem('fg_location', 'Current Location, India');
                sessionStorage.setItem('fg_city', 'Detected Location');
                sessionStorage.setItem('fg_location_mode', 'gps');
                window.location.href = 'dashboard.html';
            },
            (err) => {
                btn.textContent = '📍 Allow Location'; btn.disabled = false;
                document.getElementById('gpsOverlay').classList.add('hidden');
                document.getElementById('cityOverlay').classList.remove('hidden');
                // Focus input for quick typing
                setTimeout(() => document.getElementById('locationSearch')?.focus(), 200);
            },
            { timeout: 10000, maximumAge: 60000 }
        );
    });
}

// GPS DENY
const denyGpsBtn = document.getElementById('denyGpsBtn');
if (denyGpsBtn) {
    denyGpsBtn.addEventListener('click', () => {
        document.getElementById('gpsOverlay').classList.add('hidden');
        document.getElementById('cityOverlay').classList.remove('hidden');
        setTimeout(() => document.getElementById('locationSearch')?.focus(), 200);
    });
}

// Back to GPS
const backToGpsBtn = document.getElementById('backToGpsBtn');
if (backToGpsBtn) {
    backToGpsBtn.addEventListener('click', () => {
        document.getElementById('cityOverlay').classList.add('hidden');
        document.getElementById('gpsOverlay').classList.remove('hidden');
    });
}

// ── Confirm location by validating against OWM via our API ──
const confirmCityBtn = document.getElementById('confirmCityBtn');
if (confirmCityBtn) {
    confirmCityBtn.addEventListener('click', async () => {
        const input = document.getElementById('locationSearch');
        const query = input.value.trim();
        if (!query) return;

        const btn = document.getElementById('confirmCityBtn');
        const errEl = document.getElementById('locationSearchError');

        // Show loading state
        btn.querySelector('.btn-text').classList.add('hidden');
        btn.querySelector('.btn-loader').classList.remove('hidden');
        btn.disabled = true;
        errEl.textContent = '';

        try {
            const res = await fetch(`${API_BASE_GPS}/weather?city=${encodeURIComponent(query)}`, {
                signal: AbortSignal.timeout(8000)
            });
            const data = await res.json();

            if (!res.ok || data.error) {
                throw new Error(data.error || 'Location not found');
            }

            // OWM resolved the city — use the official name it returned
            if (!isIndiaLocation(data)) {
                errEl.textContent = '⚠ FloodGuard is currently limited to India locations only.';
                btn.querySelector('.btn-text').classList.remove('hidden');
                btn.querySelector('.btn-loader').classList.add('hidden');
                btn.disabled = false;
                input.select();
                return;
            }

            const resolvedCity = data.city || query;
            sessionStorage.setItem('fg_city', resolvedCity);
            sessionStorage.setItem('fg_location', `${resolvedCity}, ${data.country || 'IN'}`);
            sessionStorage.setItem('fg_location_mode', 'city');
            // Clear any GPS coords so API uses city name
            sessionStorage.removeItem('fg_lat');
            sessionStorage.removeItem('fg_lng');
            window.location.href = 'dashboard.html';

        } catch (e) {
            errEl.textContent = `❌ "${query}" not found. Try a different spelling or nearby city.`;
            btn.querySelector('.btn-text').classList.remove('hidden');
            btn.querySelector('.btn-loader').classList.add('hidden');
            btn.disabled = false;
            input.select();
        }
    });
}
