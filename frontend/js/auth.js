/* ============================================================
   FloodGuard India - Auth Logic / Login (MySQL API backend)
   ============================================================ */

function togglePassword(id, btn) {
    const inp = document.getElementById(id);
    if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '??'; }
    else { inp.type = 'password'; btn.textContent = '??'; }
}

function showToast(msg, type = 'info') {
    const t = document.getElementById('toast') || createToast();
    document.getElementById('toastMsg').textContent = msg;
    t.className = `toast ${type}`;
    t.classList.remove('hidden');
    clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => t.classList.add('hidden'), 3500);
}

function createToast() {
    const t = document.createElement('div');
    t.className = 'toast hidden';
    t.id = 'toast';
    t.innerHTML = '<span id="toastMsg"></span>';
    document.body.appendChild(t);
    return t;
}

function getLoginCityForAlert() {
    const raw = (
        sessionStorage.getItem('fg_city')
        || sessionStorage.getItem('fg_location')
        || localStorage.getItem('fg_last_alert_city')
        || ''
    ).trim();
    if (!raw) return '';
    const firstPart = raw.split(',')[0].trim();
    if (!firstPart) return '';
    const lower = firstPart.toLowerCase();
    if (lower === 'current location' || lower === 'detected location') return '';
    return firstPart;
}

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value.trim();
        const pass = document.getElementById('loginPassword').value;
        let valid = true;

        if (!email) {
            document.getElementById('emailError').textContent = 'Email is required.';
            document.getElementById('loginEmail').classList.add('error');
            valid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            document.getElementById('emailError').textContent = 'Please enter a valid email address.';
            document.getElementById('loginEmail').classList.add('error');
            valid = false;
        } else {
            document.getElementById('emailError').textContent = '';
            document.getElementById('loginEmail').classList.remove('error');
        }

        if (!pass || pass.length < 6) {
            document.getElementById('passError').textContent = 'Password must be at least 6 characters.';
            document.getElementById('loginPassword').classList.add('error');
            valid = false;
        } else {
            document.getElementById('passError').textContent = '';
            document.getElementById('loginPassword').classList.remove('error');
        }

        if (!valid) return;

        const btn = document.getElementById('loginBtn');
        btn.querySelector('.btn-text').classList.add('hidden');
        btn.querySelector('.btn-loader').classList.remove('hidden');
        btn.disabled = true;

        try {
            const city = getLoginCityForAlert();
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password: pass, city })
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success || !data.user) {
                throw new Error(data.error || 'Invalid email or password');
            }

            sessionStorage.setItem('fg_user', JSON.stringify(data.user));
            // Signal dashboard to show the location picker after login
            sessionStorage.setItem('fg_location_pending', '1');
            // Clear any stale location so the picker always shows fresh
            sessionStorage.removeItem('fg_loc_chosen');
            sessionStorage.removeItem('fg_city');
            sessionStorage.removeItem('fg_lat');
            sessionStorage.removeItem('fg_lng');
            if (data.admin_alert && data.admin_alert.reason === 'delivery_failed') {
                const err = (data.admin_alert.delivery && data.admin_alert.delivery.errors && data.admin_alert.delivery.errors[0]) || 'Admin alert delivery failed.';
                showToast(`Login ok, admin alert failed: ${err}`, 'error');
            } else if (data.admin_alert && data.admin_alert.triggered) {
                showToast('Login ok. Admin alert sent.', 'success');
            }
            showToast(`Welcome back, ${data.user.name}!`, 'success');
            setTimeout(() => { window.location.href = 'dashboard.html'; }, 1200);
        } catch (err) {
            document.getElementById('passError').textContent = err.message || 'Login failed.';
            document.getElementById('loginPassword').classList.add('error');
        } finally {
            btn.querySelector('.btn-text').classList.remove('hidden');
            btn.querySelector('.btn-loader').classList.add('hidden');
            btn.disabled = false;
        }
    });
}
