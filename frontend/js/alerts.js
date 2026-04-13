/* ============================================================
   FloodGuard India - Alert & Notification Settings
   ============================================================ */

// -- Risk level ordering --
const RISK_ORDER = { low: 1, moderate: 2, high: 3, critical: 4 };
const SMS_NOTIFICATIONS_ENABLED = false;

/* ============================================================
   🚨 BUZZER / ALARM SYSTEM  (Web Audio API + Vibration API)
   ============================================================ */
const BuzzerAlarm = (() => {
    let _audioCtx = null;
    let _isPlaying = false;
    let _stopTimeout = null;

    /** Lazily create AudioContext (browsers require user gesture first) */
    function _getCtx() {
        if (!_audioCtx) {
            _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (_audioCtx.state === 'suspended') _audioCtx.resume();
        return _audioCtx;
    }

    /**
     * Play a flood-siren sound: alternates between two tones to mimic
     * an emergency alarm. Duration is in milliseconds.
     */
    function play(durationMs = 5000) {
        if (_isPlaying) return;
        _isPlaying = true;

        const ctx = _getCtx();
        const endTime = ctx.currentTime + durationMs / 1000;

        // Build the siren: alternate high (900 Hz) → low (600 Hz) every 0.4s
        const cycleDuration = 0.8; // seconds per full high+low cycle
        const highFreq = 900;
        const lowFreq  = 600;

        let t = ctx.currentTime;
        while (t < endTime) {
            // High tone
            _createBeep(ctx, highFreq, t, Math.min(cycleDuration / 2, endTime - t));
            t += cycleDuration / 2;
            // Low tone
            if (t < endTime) {
                _createBeep(ctx, lowFreq, t, Math.min(cycleDuration / 2, endTime - t));
                t += cycleDuration / 2;
            }
        }

        _stopTimeout = setTimeout(() => { _isPlaying = false; }, durationMs + 200);
    }

    /** Create a single oscillator beep node */
    function _createBeep(ctx, freq, startTime, duration) {
        if (duration <= 0) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth'; // harsh, siren-like
        osc.frequency.setValueAtTime(freq, startTime);
        // Slight ramp for smoother tone transitions
        osc.frequency.linearRampToValueAtTime(freq * 1.05, startTime + duration * 0.5);
        osc.frequency.linearRampToValueAtTime(freq, startTime + duration);

        gain.gain.setValueAtTime(0.0, startTime);
        gain.gain.linearRampToValueAtTime(0.35, startTime + 0.02);  // fade in
        gain.gain.setValueAtTime(0.35, startTime + duration - 0.02);
        gain.gain.linearRampToValueAtTime(0.0, startTime + duration); // fade out

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(startTime);
        osc.stop(startTime + duration);
    }

    /** Stop any ongoing alarm */
    function stop() {
        _isPlaying = false;
        if (_stopTimeout) clearTimeout(_stopTimeout);
        if (_audioCtx) {
            _audioCtx.close();
            _audioCtx = null;
        }
    }

    /**
     * Vibrate the device in an SOS-like pattern (if supported).
     * Pattern: short-short-short / long-long-long / short-short-short
     */
    function vibrate(level = 'high') {
        if (!('vibrate' in navigator)) return;
        const patterns = {
            low:      [100, 100, 100],
            moderate: [200, 100, 200, 100, 200],
            high:     [300, 100, 300, 100, 300, 200, 600, 200, 600, 200, 600],
            critical: [200,80,200,80,200, 150, 500,150,500,150,500, 150, 200,80,200,80,200]
        };
        navigator.vibrate(patterns[level] || patterns.high);
    }

    /** Check if user has buzzer enabled in prefs */
    function isEnabled() {
        const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
        return prefs.buzzerEnabled !== false; // default ON
    }

    return { play, stop, vibrate, isEnabled };
})();

function getCurrentUserId() {
    const user = JSON.parse(sessionStorage.getItem('fg_user') || '{}');
    return user.id || null;
}

async function fetchPrefsFromDb() {
    const userId = getCurrentUserId();
    if (!userId) return null;
    try {
        const res = await fetch(`${API_BASE}/prefs?user_id=${encodeURIComponent(userId)}`);
        if (!res.ok) return null;
        const db = await res.json();
        return {
            emailEnabled: !!db.email_enabled,
            smsEnabled: !!db.sms_enabled,
            browserEnabled: !!db.browser_enabled,
            threshold: ({ low: 1, moderate: 2, high: 3, critical: 4 }[db.threshold_level] || 2),
            alertEmail: db.alert_email || '',
            alertPhone: db.alert_phone || ''
        };
    } catch {
        return null;
    }
}

function pushPrefsToDb(prefs) {
    const userId = getCurrentUserId();
    if (!userId) return;
    const thresholdLevel = ({ 1: 'low', 2: 'moderate', 3: 'high', 4: 'critical' }[parseInt(prefs.threshold || 2, 10)] || 'moderate');
    fetch(`${API_BASE}/prefs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            email_enabled: prefs.emailEnabled !== false ? 1 : 0,
            sms_enabled: prefs.smsEnabled ? 1 : 0,
            browser_enabled: prefs.browserEnabled ? 1 : 0,
            threshold_level: thresholdLevel,
            alert_email: prefs.alertEmail || null,
            alert_phone: prefs.alertPhone || null
        })
    }).catch(() => {});
}

/** Returns saved threshold as a risk string: low/moderate/high/critical */
function getThresholdLevel() {
    const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    const val = parseInt(prefs.threshold || 2);
    const map = { 1: 'low', 2: 'moderate', 3: 'high', 4: 'critical' };
    return map[val] || 'moderate';
}

window.addEventListener('DOMContentLoaded', async () => {
    const toggleEmail = document.getElementById('toggleEmail');
    const toggleSMS = document.getElementById('toggleSMS');
    const toggleBrowser = document.getElementById('toggleBrowser');
    const thresholdRange = document.getElementById('thresholdRange');
    const emailConfig = document.getElementById('emailConfig');
    const smsConfig = document.getElementById('smsConfig');
    const alertEmail = document.getElementById('alertEmail');
    const alertPhone = document.getElementById('alertPhone');
    if (!thresholdRange) return;
    // Load saved prefs
    const localPrefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    const dbPrefs = await fetchPrefsFromDb();
    const prefs = { ...localPrefs, ...(dbPrefs || {}) };
    localStorage.setItem('fg_alert_prefs', JSON.stringify(prefs));
    if (prefs.emailEnabled !== undefined && toggleEmail) toggleEmail.checked = prefs.emailEnabled;
    if (prefs.smsEnabled !== undefined && toggleSMS) toggleSMS.checked = prefs.smsEnabled;
    if (prefs.browserEnabled !== undefined && toggleBrowser) toggleBrowser.checked = prefs.browserEnabled;
    // Sync buzzer toggle (default ON if never saved)
    const toggleBuzzer = document.getElementById('toggleBuzzer');
    if (toggleBuzzer) toggleBuzzer.checked = prefs.buzzerEnabled !== false;
    if (prefs.threshold) {
        thresholdRange.value = prefs.threshold;
        updateThresholdLabel(prefs.threshold);
    } else {
        updateThresholdLabel(thresholdRange.value);
    }

    // Pre-fill from logged-in user; email is account-linked (not manually saved).
    const user = JSON.parse(sessionStorage.getItem('fg_user') || '{}');
    if (alertEmail) {
        alertEmail.value = user.email || '';
        alertEmail.readOnly = true;
        if (prefs.emailEnabled === undefined) {
            prefs.emailEnabled = true;
            localStorage.setItem('fg_alert_prefs', JSON.stringify(prefs));
        }
    }
    if (SMS_NOTIFICATIONS_ENABLED) {
        if (alertPhone && user.phone && !prefs.alertPhone) {
            alertPhone.value = user.phone;
        } else if (alertPhone && prefs.alertPhone) {
            alertPhone.value = prefs.alertPhone;
        }
    }

    // Threshold slider - live label update
    thresholdRange.addEventListener('input', function () {
        updateThresholdLabel(this.value);
    });
    thresholdRange.addEventListener('change', function () {
        updateThresholdLabel(this.value);
    });

    // Toggle email config visibility
    if (toggleEmail) {
        toggleEmail.addEventListener('change', function () {
            saveAlertPref('emailEnabled', this.checked);
            if (emailConfig) emailConfig.style.display = this.checked ? 'flex' : 'none';
        });
        if (emailConfig) emailConfig.style.display = toggleEmail.checked ? 'flex' : 'none';
    }

    // Toggle SMS config visibility
    if (toggleSMS) {
        if (!SMS_NOTIFICATIONS_ENABLED) {
            toggleSMS.checked = false;
            toggleSMS.disabled = true;
            saveAlertPref('smsEnabled', false);
            if (smsConfig) smsConfig.style.display = 'none';
            const smsSetting = toggleSMS.closest('.setting-item');
            if (smsSetting) smsSetting.style.display = 'none';
            const smsTestBtn = document.querySelector('button[onclick="sendTestSMS()"]');
            if (smsTestBtn) smsTestBtn.style.display = 'none';
        } else {
            toggleSMS.addEventListener('change', function () {
                saveAlertPref('smsEnabled', this.checked);
                if (smsConfig) smsConfig.style.display = this.checked ? 'flex' : 'none';
            });
            if (smsConfig) smsConfig.style.display = toggleSMS.checked ? 'flex' : 'none';
        }
    }

    // Browser notification permission
    if (toggleBrowser) {
        toggleBrowser.addEventListener('change', function () {
            if (this.checked && 'Notification' in window) {
                Notification.requestPermission().then(perm => {
                    if (perm !== 'granted') {
                        this.checked = false;
                        showToast('Browser notifications blocked. Please allow in browser settings.', 'error');
                    } else {
                        showToast('Browser notifications enabled!', 'success');
                        saveAlertPref('browserEnabled', true);
                    }
                });
            } else {
                saveAlertPref('browserEnabled', false);
            }
        });
    }
});

function updateThresholdLabel(val) {
    const labels = { 1: 'Low', 2: 'Moderate', 3: 'High', 4: 'Critical' };
    const colors = { 1: '#22c55e', 2: '#f59e0b', 3: '#f97316', 4: '#ef4444' };
    const el = document.getElementById('thresholdLabel');
    el.textContent = labels[val] || 'Moderate';
    el.style.color = colors[val] || '#f59e0b';
    saveAlertPref('threshold', parseInt(val));
}

function saveAlertPref(key, value) {
    const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    prefs[key] = value;
    localStorage.setItem('fg_alert_prefs', JSON.stringify(prefs));
    pushPrefsToDb(prefs);
}

window.saveEmailAlert = function () {
    showToast('Email is linked to your login account automatically.', 'info');
};

window.saveSMSAlert = function () {
    if (!SMS_NOTIFICATIONS_ENABLED) {
        showToast('SMS notifications are temporarily disabled.', 'info');
        return;
    }
    const phone = document.getElementById('alertPhone').value.trim();
    if (!phone || !/^[6-9]\d{9}$/.test(phone)) {
        showToast('Please enter a valid 10-digit Indian mobile number.', 'error'); return;
    }
    saveAlertPref('alertPhone', phone);
    showToast(`[OK] SMS number saved: +91${phone}`, 'success');
};

/** Send a real notification via /api/notify */
async function sendNotification(email, phone, riskData) {
    try {
        const sessionUser = JSON.parse(sessionStorage.getItem('fg_user') || '{}');
        const res = await fetch(`${API_BASE}/notify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email, phone,
                user_id: sessionUser.id || null,
                risk: riskData.risk,
                label: riskData.label,
                message: riskData.message,
                city: riskData.city
            })
        });
        const result = await res.json();
        if (result.email_sent) { showToast('Alert email sent!', 'success'); }
        if (result.sms_sent) { showToast('Alert SMS sent!', 'success'); }
        if (result.errors && result.errors.length) {
            result.errors.forEach(e => console.warn('[FloodGuard Notify]', e));
        }
        return result;
    } catch (e) {
        console.error('Notification API error:', e);
        showToast('Warning: Cannot reach API server. Is api.py running?', 'error');
        return { email_sent: false, sms_sent: false, errors: [e.message] };
    }
}

/** Called from dashboard.js after risk data arrives - sends email alert */
window.checkAndSendThresholdAlert = async function (riskData) {
    if (!riskData) return;
    const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    const threshold = getThresholdLevel();
    const liveRisk = riskData.risk;

    // Send only when live risk meets configured threshold.
    if (RISK_ORDER[liveRisk] < RISK_ORDER[threshold]) return;

    // Debounce: don't repeat the same alert within 2 minutes per city
    const now = Date.now();
    const lastSent = parseInt(localStorage.getItem('fg_last_alert_ts') || '0');
    const lastCity = localStorage.getItem('fg_last_alert_city') || '';
    if (lastCity === riskData.city && now - lastSent < 2 * 60 * 1000) return;

    // Browser notification
    if (prefs.browserEnabled && 'Notification' in window && Notification.permission === 'granted') {
        new Notification(`FloodGuard - ${riskData.label}`, { body: riskData.message });
    }

    // 🚨 Buzzer + Vibration alert
    if (BuzzerAlarm.isEnabled()) {
        BuzzerAlarm.play(6000);          // 6-second siren
        BuzzerAlarm.vibrate(liveRisk);   // Vibration pattern matching risk level
    }

    // Email always comes from current logged-in user.
    const sessionUser = JSON.parse(sessionStorage.getItem('fg_user') || '{}');
    const emailEnabled = prefs.emailEnabled !== false; // treat undefined as enabled
    const email = (emailEnabled && sessionUser.email) ? sessionUser.email : null;
    const phone = (SMS_NOTIFICATIONS_ENABLED && prefs.smsEnabled && prefs.alertPhone) ? prefs.alertPhone : null;

    if (email || phone) {
        await sendNotification(email || '', phone || '', riskData);
        localStorage.setItem('fg_last_alert_ts', now.toString());
        localStorage.setItem('fg_last_alert_city', riskData.city);
    }
};

window.sendTestEmail = async function () {
    const sessionUser = JSON.parse(sessionStorage.getItem('fg_user') || '{}');
    const email = (sessionUser.email || '').trim();
    if (!email) { showToast('No login email found. Please log in again.', 'error'); return; }

    const currentCity = (sessionStorage.getItem('fg_city') || '').trim() || 'Mumbai';
    let payload = {
        risk: 'moderate',
        label: 'MODERATE FLOOD RISK',
        message: `Moderate flood risk detected in ${currentCity}. Stay alert and monitor weather.`,
        city: currentCity
    };

    showToast('Sending test email...', 'info');
    try {
        const res = await fetch(`${API_BASE}/predict?city=${encodeURIComponent(currentCity)}`, {
            signal: AbortSignal.timeout(7000)
        });
        if (res.ok) {
            const p = await res.json();
            payload = {
                risk: p.risk || payload.risk,
                label: p.label || payload.label,
                message: p.message || payload.message,
                city: p.city || payload.city
            };
        }
    } catch (_) { }

    const result = await sendNotification(email, '', payload);
    if (!result.email_sent) {
        const err = result.errors?.[0] || 'Unknown error';
        if (err.includes('not configured') || err.includes('credentials missing')) {
            showToast('Email credentials not configured. Set SMTP_* environment variables.', 'error');
        } else {
            showToast(`Email failed: ${err}`, 'error');
        }
    }
};

window.sendTestSMS = async function () {
    if (!SMS_NOTIFICATIONS_ENABLED) {
        showToast('SMS notifications are temporarily disabled.', 'info');
        return;
    }
    const prefs = JSON.parse(localStorage.getItem('fg_alert_prefs') || '{}');
    const phone = prefs.alertPhone || document.getElementById('alertPhone').value.trim();
    if (!phone) { showToast('Enter and save a phone number first.', 'error'); return; }

    const currentCity = (sessionStorage.getItem('fg_city') || '').trim() || 'Mumbai';
    showToast('Sending test SMS...', 'info');
    let payload = {
        risk: 'moderate',
        label: 'MODERATE FLOOD RISK',
        message: `Moderate flood risk detected in ${currentCity}. Stay alert and monitor weather.`,
        city: currentCity
    };
    try {
        const res = await fetch(`${API_BASE}/predict?city=${encodeURIComponent(currentCity)}`, {
            signal: AbortSignal.timeout(7000)
        });
        if (res.ok) {
            const p = await res.json();
            payload = {
                risk: p.risk || payload.risk,
                label: p.label || payload.label,
                message: p.message || payload.message,
                city: p.city || payload.city
            };
        }
    } catch (_) { }

    const result = await sendNotification('', phone, payload);
    if (!result.sms_sent) {
        const err = result.errors?.[0] || 'Unknown error';
        if (err.includes('not configured') || err.includes('credentials missing')) {
            showToast('Twilio credentials not configured. Set TWILIO_* environment variables.', 'error');
        } else if (err.includes('not installed')) {
            showToast('Run: pip install twilio then restart api.py', 'error');
        } else {
            showToast(`SMS failed: ${err}`, 'error');
        }
    }
};

window.sendTestBrowser = function () {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
        showToast('Browser notifications not enabled. Toggle the switch first.', 'error'); return;
    }
    new Notification('FloodGuard Test Alert', {
        body: 'This is a test notification from FloodGuard India.',
    });
    showToast('Browser notification sent!', 'success');
};

/** Test the buzzer alarm (3 seconds) + vibration */
window.sendTestBuzzer = function () {
    showToast('🚨 Testing alarm buzzer...', 'info');
    BuzzerAlarm.play(3000);
    BuzzerAlarm.vibrate('critical');
};

/** Stop the buzzer manually */
window.stopBuzzer = function () {
    BuzzerAlarm.stop();
    showToast('Buzzer stopped.', 'info');
};

function buildActiveAlerts() {
    const list = document.getElementById('activeAlertsList');
    if (!list) return;
    const risk = window.getLiveRisk ? window.getLiveRisk() : null;
    if (risk) {
        const colors = { low: '#22c55e', moderate: '#f59e0b', high: '#f97316', critical: '#ef4444' };
        const color = colors[risk.risk] || '#0ea5e9';
        list.innerHTML = `
        <div class="active-alert-item">
          <div class="alert-item-dot" style="background:${color};box-shadow:0 0 6px ${color}55;"></div>
          <div class="alert-item-text">
            <div class="alert-item-title">${risk.label} - ${risk.city || ''}</div>
            <div class="alert-item-sub">${risk.message}</div>
          </div>
          <div class="alert-item-time">Just now</div>
        </div>`;
    } else {
        list.innerHTML = '<div style="color:var(--text2);font-size:.85rem;padding:.5rem 0;">Monitoring flood conditions...</div>';
    }
}

// Expose for dashboard.js
window.buildActiveAlerts = buildActiveAlerts;
window.getThresholdLevel = getThresholdLevel;
window.BuzzerAlarm = BuzzerAlarm;






