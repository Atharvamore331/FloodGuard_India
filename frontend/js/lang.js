/* ============================================================
   FloodGuard India – Multilingual Support (i18n)
   ============================================================ */

const ALLOWED_LANGS = ['en', 'hi', 'mr'];
let currentLang = localStorage.getItem('fg_lang') || 'en';
if (!ALLOWED_LANGS.includes(currentLang)) currentLang = 'en';

function applyLanguage(lang) {
    currentLang = ALLOWED_LANGS.includes(lang) ? lang : 'en';
    localStorage.setItem('fg_lang', currentLang);
    if (typeof window.persistUserSettingsToDb === 'function') {
        window.persistUserSettingsToDb({ language: currentLang });
    }

    const strings = I18N[currentLang] || I18N['en'];

    // Update all data-i18n elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (strings[key]) el.textContent = strings[key];
    });

    // Update document title direction for RTL languages (none here but future-proof)
    document.documentElement.lang = currentLang;
}

// Language selector
document.addEventListener('DOMContentLoaded', () => {
    const sel = document.getElementById('langSelector');
    if (sel) {
        // Remove any non-allowed options if present in markup.
        Array.from(sel.options).forEach(opt => {
            if (!ALLOWED_LANGS.includes(opt.value)) opt.remove();
        });
        sel.value = currentLang;
        sel.addEventListener('change', () => {
            applyLanguage(sel.value);
            showToast(`Language changed to ${sel.options[sel.selectedIndex].text}`, 'info');
        });
        applyLanguage(currentLang);
    }
});

// Expose globally
window.applyLanguage = applyLanguage;
window.t = function (key) {
    return (I18N[currentLang] || I18N['en'])[key] || key;
};
