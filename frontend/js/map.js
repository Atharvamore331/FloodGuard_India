/* ============================================================
   FloodGuard India - Flood Risk Map
   Pin colors now follow LIVE model risk; historical index is shown separately.
   ============================================================ */

const OWM_API_KEY = "616bb6e88312cd11c5d068b6f126b54c";
let mapInst = null;
let markerLayer = null;
let precipLayer = null;
let currentMapLayer = 'risk';

const INDIA_BOUNDS = L.latLngBounds(L.latLng(6.0, 68.0), L.latLng(37.5, 97.5));

const RISK_CFG = {
    critical: { color: '#ef4444', outline: '#b91c1c', radius: 16, label: 'CRITICAL' },
    high: { color: '#f97316', outline: '#c2410c', radius: 12, label: 'HIGH' },
    moderate: { color: '#f59e0b', outline: '#b45309', radius: 9, label: 'MODERATE' },
    low: { color: '#22c55e', outline: '#15803d', radius: 7, label: 'LOW' },
    unknown: { color: '#94a3b8', outline: '#64748b', radius: 7, label: 'LIVE N/A' },
};

function normalizeZoneCityName(name) {
    if (!name) return '';
    const raw = String(name).trim();
    const explicit = {
        'Mumbai (Coastal)': 'Mumbai',
        'Cuttack - Mahanadi': 'Cuttack',
        'Cuttack – Mahanadi': 'Cuttack',
        'Imphal Valley': 'Imphal',
        'Brahmaputra Valley': 'Guwahati',
        'Kosi River Basin': 'Patna',
        'Konkan Coast': 'Mumbai',
        'Sundarbans Delta': 'Kolkata',
        'Ganga Plains (Allahabad)': 'Prayagraj',
    };
    if (explicit[raw]) return explicit[raw];
    return raw.replace(/\(.*?\)/g, '').split('–')[0].split('-')[0].trim();
}

async function enrichZonesWithLiveRisk(zones) {
    const out = [...zones];
    const concurrency = 5;
    let idx = 0;

    async function worker() {
        while (idx < out.length) {
            const i = idx++;
            const z = out[i];
            const city = normalizeZoneCityName(z.name);
            if (!city) continue;
            try {
                const p = await apiFetch(`${API_BASE}/predict?city=${encodeURIComponent(city)}`);
                if (p && !p.error) {
                    z.live_city = p.city || city;
                    z.live_risk = p.risk || null;
                    const score = Number(p.score);
                    z.live_score = Number.isFinite(score) ? score : null;
                    z.live_percent = Number.isFinite(score) ? score.toFixed(3) : null;
                }
            } catch {
                // Live risk unavailable for this zone
            }
        }
    }

    const workers = Array.from({ length: Math.min(concurrency, out.length) }, () => worker());
    await Promise.all(workers);
    return out;
}

async function initMap() {
    if (mapInst) { mapInst.invalidateSize(); return; }

    mapInst = L.map('floodMap', {
        zoomControl: true,
        maxBounds: INDIA_BOUNDS,
        maxBoundsViscosity: 0.85,
    }).setView([22.5, 82.5], 5);

    mapInst.setMinZoom(4);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a> | FloodGuard India',
        maxZoom: 18,
    }).addTo(mapInst);

    precipLayer = L.tileLayer(
        `https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${OWM_API_KEY}`,
        { opacity: 0.55, attribution: '&copy; OpenWeatherMap', maxZoom: 18 }
    );

    const lat = parseFloat(sessionStorage.getItem('fg_lat'));
    const lng = parseFloat(sessionStorage.getItem('fg_lng'));
    if (!isNaN(lat) && !isNaN(lng) && INDIA_BOUNDS.contains([lat, lng])) {
        const userIcon = L.divIcon({
            html: `<div style="width:16px;height:16px;border-radius:50%;background:#0ea5e9;border:3px solid white;box-shadow:0 0 0 5px rgba(14,165,233,.3),0 2px 6px rgba(0,0,0,.4);"></div>`,
            iconSize: [16, 16], iconAnchor: [8, 8]
        });
        L.marker([lat, lng], { icon: userIcon }).bindPopup('<strong>Your Location</strong>').addTo(mapInst);
        mapInst.setView([lat, lng], 8);
    }

    await loadFloodZones();
}

async function loadFloodZones() {
    let zones = [];
    try {
        const data = await apiFetch(`${API_BASE}/flood-risk-zones`);
        const raw = data.zones || [];
        const INDIA_LAT = [6.0, 37.5], INDIA_LNG = [68.0, 97.5];
        const valid = raw.filter(z =>
            z.lat >= INDIA_LAT[0] && z.lat <= INDIA_LAT[1] &&
            z.lng >= INDIA_LNG[0] && z.lng <= INDIA_LNG[1] &&
            z.name
        );
        zones = valid.length >= 5 ? valid : FALLBACK_ZONES;
    } catch {
        zones = FALLBACK_ZONES;
    }

    zones = await enrichZonesWithLiveRisk(zones);

    if (markerLayer) mapInst.removeLayer(markerLayer);
    markerLayer = L.layerGroup();

    const ORDER = { unknown: -1, low: 0, moderate: 1, high: 2, critical: 3 };
    zones.sort((a, b) => (ORDER[a.live_risk || 'unknown'] ?? -1) - (ORDER[b.live_risk || 'unknown'] ?? -1));

    zones.forEach(zone => {
        const level = zone.live_risk || 'unknown';
        const cfg = RISK_CFG[level] || RISK_CFG.unknown;
        const liveProb = zone.live_percent !== null && zone.live_percent !== undefined ? `${zone.live_percent}%` : 'N/A';
        const name = zone.name || `${zone.lat.toFixed(2)}N ${zone.lng.toFixed(2)}E`;
        const state = zone.state ? `, ${zone.state}` : '';

        if (level === 'critical' || level === 'high') {
            L.circleMarker([zone.lat, zone.lng], {
                radius: cfg.radius + 9,
                fillColor: cfg.color,
                color: cfg.color,
                weight: 1,
                opacity: 0.3,
                fillOpacity: 0.12,
            }).addTo(markerLayer);
        }

        const circle = L.circleMarker([zone.lat, zone.lng], {
            radius: cfg.radius,
            fillColor: cfg.color,
            color: cfg.outline,
            weight: 2,
            opacity: 1,
            fillOpacity: 0.85,
        });

        circle.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:230px;padding:.3rem 0;">
          <div style="font-weight:700;font-size:.95rem;margin-bottom:.25rem;color:#1e293b;">
            ${name}${state ? `<span style="font-size:.78rem;color:#64748b;">${state}</span>` : ''}
          </div>
          <div style="display:flex;align-items:center;gap:.5rem;margin:.4rem 0;">
            <span style="background:${cfg.color}22;color:${cfg.color};font-weight:700;font-size:.78rem;padding:.2rem .6rem;border-radius:1rem;border:1.5px solid ${cfg.color}55;">⬤ ${cfg.label}</span>
            <span style="color:#64748b;font-size:.8rem;">Live ML: <strong>${liveProb}</strong></span>
          </div>
          <div style="color:#94a3b8;font-size:.72rem;margin-top:.4rem;padding-top:.3rem;border-top:1px solid #f1f5f9;">
            Decision basis: Live ML risk only
          </div>
        </div>`);

        circle.on('click', () => {
            mapInst.flyTo([zone.lat, zone.lng], Math.max(mapInst.getZoom(), 9), { duration: 0.7 });
        });

        markerLayer.addLayer(circle);
    });

    markerLayer.addTo(mapInst);
    addLegend();
    buildZonesList(zones);
}

function addLegend() {
    const old = document.getElementById('mapLegend');
    if (old) old.remove();

    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = () => {
        const div = L.DomUtil.create('div');
        div.id = 'mapLegend';
        div.style.cssText = 'background:rgba(255,255,255,.95);padding:.6rem .9rem;border-radius:8px;font-family:Inter,sans-serif;font-size:.78rem;box-shadow:0 2px 12px rgba(0,0,0,.18);line-height:1.8;';
        div.innerHTML = `
            <div style="font-weight:700;margin-bottom:.3rem;color:#1e293b;">Live ML Flood Risk (Pin Colors)</div>
            <div><span style="color:#ef4444;font-size:1rem;">⬤</span> Critical (&gt;80%)</div>
            <div><span style="color:#f97316;font-size:1rem;">⬤</span> High (60-80%)</div>
            <div><span style="color:#f59e0b;font-size:1rem;">⬤</span> Moderate (40-60%)</div>
            <div><span style="color:#22c55e;font-size:1rem;">⬤</span> Low (&lt;40%)</div>
            <div><span style="color:#94a3b8;font-size:1rem;">⬤</span> Live N/A</div>`;
        return div;
    };
    legend.addTo(mapInst);
}

function buildZonesList(zones) {
    const list = document.getElementById('zonesList');
    if (!list) return;

    const highRisk = zones.filter(z => z.live_risk === 'critical' || z.live_risk === 'high');

    const emojiMap = { critical: '🔴', high: '🟠', moderate: '🟡', low: '🟢', unknown: '⚪' };
    const colorMap = { critical: '#ef4444', high: '#f97316', moderate: '#f59e0b', low: '#22c55e', unknown: '#94a3b8' };

    list.innerHTML = highRisk.slice(0, 12).map(z => {
        const level = z.live_risk || 'unknown';
        const color = colorMap[level];
        const liveProb = z.live_percent !== null && z.live_percent !== undefined ? `${z.live_percent}%` : '';
        const name = z.name || `${z.lat.toFixed(2)}°, ${z.lng.toFixed(2)}°`;
        const state = z.state ? `, ${z.state}` : '';

        return `<div class="zone-item" style="cursor:pointer;transition:background .15s;"
          onmouseenter="this.style.background='rgba(14,165,233,.07)'"
          onmouseleave="this.style.background=''"
          onclick="mapInst.flyTo([${z.lat},${z.lng}],10,{duration:0.8})">
          <span class="zone-name">${emojiMap[level]} <b>${name}</b><small style="color:var(--text3);font-weight:400;">${state}</small></span>
          <div style="display:flex;align-items:center;gap:.45rem;flex-shrink:0;">
            ${liveProb ? `<span style="font-size:.79rem;color:#64748b;">Live: ${liveProb}</span>` : ''}
            <span class="zone-level" style="background:${color}20;color:${color};border:1px solid ${color}40;">${level.toUpperCase()}</span>
          </div>
        </div>`;
    }).join('') || '<p style="color:var(--text2);font-size:.85rem;">No high-risk zones found.</p>';
}

const FALLBACK_ZONES = [
    { name: 'Brahmaputra Valley', state: 'Assam', lat: 26.14, lng: 91.74, risk: 'critical', flood_occurred: 0.94 },
    { name: 'Kosi River Basin', state: 'Bihar', lat: 25.60, lng: 86.90, risk: 'critical', flood_occurred: 0.91 },
    { name: 'Patna', state: 'Bihar', lat: 25.59, lng: 85.14, risk: 'critical', flood_occurred: 0.85 },
    { name: 'Imphal Valley', state: 'Manipur', lat: 24.82, lng: 93.94, risk: 'critical', flood_occurred: 0.82 },
    { name: 'Shillong', state: 'Meghalaya', lat: 25.58, lng: 91.89, risk: 'critical', flood_occurred: 0.81 },
    { name: 'Kolkata', state: 'West Bengal', lat: 22.57, lng: 88.36, risk: 'high', flood_occurred: 0.76 },
    { name: 'Bhubaneswar', state: 'Odisha', lat: 20.30, lng: 85.82, risk: 'high', flood_occurred: 0.74 },
    { name: 'Visakhapatnam', state: 'Andhra Pradesh', lat: 17.69, lng: 83.22, risk: 'high', flood_occurred: 0.71 },
    { name: 'Mumbai (Coastal)', state: 'Maharashtra', lat: 19.08, lng: 72.88, risk: 'high', flood_occurred: 0.70 },
    { name: 'Kochi', state: 'Kerala', lat: 9.96, lng: 76.28, risk: 'high', flood_occurred: 0.68 },
    { name: 'Chennai', state: 'Tamil Nadu', lat: 13.08, lng: 80.27, risk: 'moderate', flood_occurred: 0.55 },
    { name: 'Hyderabad', state: 'Telangana', lat: 17.39, lng: 78.49, risk: 'moderate', flood_occurred: 0.52 },
    { name: 'Pune', state: 'Maharashtra', lat: 18.52, lng: 73.86, risk: 'moderate', flood_occurred: 0.50 },
    { name: 'Surat', state: 'Gujarat', lat: 21.17, lng: 72.83, risk: 'moderate', flood_occurred: 0.46 },
    { name: 'Delhi', state: 'Delhi', lat: 28.61, lng: 77.21, risk: 'low', flood_occurred: 0.30 },
    { name: 'Ahmedabad', state: 'Gujarat', lat: 23.02, lng: 72.57, risk: 'low', flood_occurred: 0.28 },
    { name: 'Jaipur', state: 'Rajasthan', lat: 26.91, lng: 75.79, risk: 'low', flood_occurred: 0.18 },
];

window.setMapLayer = function (layer, btn) {
    currentMapLayer = layer;
    document.querySelectorAll('.map-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (!mapInst) return;

    if (layer === 'rainfall') {
        if (!mapInst.hasLayer(precipLayer)) precipLayer.addTo(mapInst);
        precipLayer.setUrl(`https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${OWM_API_KEY}`);
        precipLayer.setOpacity(0.6);
        showToast('Showing live precipitation overlay', 'info');
    } else if (layer === 'rivers') {
        if (!mapInst.hasLayer(precipLayer)) precipLayer.addTo(mapInst);
        precipLayer.setUrl(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${OWM_API_KEY}`);
        precipLayer.setOpacity(0.45);
        showToast('Showing wind/river overlay', 'info');
    } else {
        if (mapInst.hasLayer(precipLayer)) mapInst.removeLayer(precipLayer);
        showToast('Showing live model risk markers', 'info');
    }
};
