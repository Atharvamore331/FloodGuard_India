/* ============================================================
   FloodGuard India - Register Page Logic (MySQL API backend)
   ============================================================ */

function togglePassword(id, btn) {
    const inp = document.getElementById(id);
    if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '??'; }
    else { inp.type = 'password'; btn.textContent = '??'; }
}

const pwEl = document.getElementById('regPassword');
if (pwEl) {
    pwEl.addEventListener('input', function () {
        const pass = this.value;
        const fill = document.getElementById('strengthFill');
        const label = document.getElementById('strengthLabel');
        let score = 0;
        if (pass.length >= 8) score++;
        if (/[A-Z]/.test(pass)) score++;
        if (/[0-9]/.test(pass)) score++;
        if (/[^A-Za-z0-9]/.test(pass)) score++;

        const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
        const colors = ['', '#ef4444', '#f59e0b', '#3b82f6', '#22c55e'];
        const widths = ['0%', '25%', '50%', '75%', '100%'];

        if (fill) {
            fill.style.width = widths[score];
            fill.style.background = colors[score];
        }
        if (label) label.textContent = levels[score] || 'Strength';
    });
}

const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        let valid = true;

        const name = document.getElementById('fullName').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const age = parseInt(document.getElementById('age').value, 10);
        const pass = document.getElementById('regPassword').value;
        const conf = document.getElementById('confirmPass').value;
        const terms = document.getElementById('terms').checked;
        const emailAlert = !!document.getElementById('emailAlert')?.checked;
        const smsAlert = !!document.getElementById('smsAlert')?.checked;

        if (!name || name.length < 2) { document.getElementById('nameError').textContent = 'Please enter your full name.'; valid = false; }
        else { document.getElementById('nameError').textContent = ''; }
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { document.getElementById('regEmailError').textContent = 'Enter a valid email address.'; valid = false; }
        else { document.getElementById('regEmailError').textContent = ''; }
        if (!phone || !/^[6-9]\d{9}$/.test(phone)) { document.getElementById('phoneError').textContent = 'Enter a valid 10-digit Indian mobile number.'; valid = false; }
        else { document.getElementById('phoneError').textContent = ''; }
        if (!age || age < 1 || age > 120) { document.getElementById('ageError').textContent = 'Enter a valid age between 1 and 120.'; valid = false; }
        else { document.getElementById('ageError').textContent = ''; }
        if (!pass || pass.length < 8) { document.getElementById('regPassError').textContent = 'Password must be at least 8 characters.'; valid = false; }
        else { document.getElementById('regPassError').textContent = ''; }
        if (pass !== conf) { document.getElementById('confirmError').textContent = 'Passwords do not match.'; valid = false; }
        else { document.getElementById('confirmError').textContent = ''; }
        if (!terms) { document.getElementById('termsError').textContent = 'You must agree to the terms.'; valid = false; }
        else { document.getElementById('termsError').textContent = ''; }
        if (!valid) return;

        const btn = document.getElementById('registerBtn');
        btn.querySelector('.btn-text').classList.add('hidden');
        btn.querySelector('.btn-loader').classList.remove('hidden');
        btn.disabled = true;

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    email,
                    phone,
                    age,
                    password: pass,
                    emailAlert,
                    smsAlert
                })
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.success || !data.user) {
                throw new Error(data.error || 'Registration failed');
            }

            sessionStorage.setItem('fg_user', JSON.stringify(data.user));
            showToast('Account created! Welcome to FloodGuard.', 'success');
            setTimeout(() => { window.location.href = 'index.html'; }, 1200);
        } catch (err) {
            const msg = err.message || 'Registration failed';
            if (/email/i.test(msg)) {
                document.getElementById('regEmailError').textContent = msg;
            } else {
                showToast(msg, 'error');
            }
        } finally {
            btn.querySelector('.btn-text').classList.remove('hidden');
            btn.querySelector('.btn-loader').classList.add('hidden');
            btn.disabled = false;
        }
    });
}

function showToast(msg, type = 'info') {
    let t = document.getElementById('toast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'toast';
        t.innerHTML = '<span id="toastMsg"></span>';
        document.body.appendChild(t);
    }
    document.getElementById('toastMsg').textContent = msg;
    t.className = `toast ${type}`;
    t.classList.remove('hidden');
    clearTimeout(window._tt);
    window._tt = setTimeout(() => t.classList.add('hidden'), 3500);
}
