/* ============================================================
   FloodGuard India – API Config & Shared Data
   Only keeps translation strings, safety data, and city lists.
   All risk/weather data now fetched live from Flask API.
   ============================================================ */

// Auto-detect API host:
// - Local dev: uses current hostname (works on PC and LAN)
// - Production (Vercel): uses the Render backend URL
const _isLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname) ||
                 window.location.hostname.startsWith('192.168.');
const API_BASE = _isLocal
  ? `http://${window.location.hostname}:5000/api`
  : (window.__RENDER_API_URL || 'https://RENDER_BACKEND_URL_HERE') + '/api';

// ── Utility: generic fetch with fallback ──
async function apiFetch(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── India States + Cities (for city dropdown) ──
const INDIA_STATES_CITIES = {
  "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Kurnool", "Rajahmundry", "Kakinada", "Nellore"],
  "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Tawang", "Ziro", "Pasighat"],
  "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tezpur", "Tinsukia"],
  "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Purnia", "Darbhanga"],
  "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Raigarh", "Durg"],
  "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda"],
  "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar", "Gandhinagar"],
  "Haryana": ["Faridabad", "Gurgaon", "Panipat", "Ambala", "Rohtak", "Hisar", "Karnal"],
  "Himachal Pradesh": ["Shimla", "Manali", "Dharamshala", "Kullu", "Mandi", "Solan"],
  "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh"],
  "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Tumakuru"],
  "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Palakkad", "Alappuzha"],
  "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar"],
  "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Thane", "Solapur", "Kolhapur", "Vasai"],
  "Manipur": ["Imphal", "Thoubal", "Bishnupur", "Churachandpur"],
  "Meghalaya": ["Shillong", "Tura", "Nongstoin"],
  "Mizoram": ["Aizawl", "Lunglei", "Champhai"],
  "Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
  "Odisha": ["Bhubaneswar", "Cuttack", "Berhampur", "Sambalpur", "Rourkela", "Puri"],
  "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali"],
  "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer"],
  "Sikkim": ["Gangtok", "Namchi", "Mangan"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Vellore"],
  "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
  "Tripura": ["Agartala", "Udaipur", "Kailashahar"],
  "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Meerut", "Noida", "Bareilly"],
  "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rishikesh"],
  "West Bengal": ["Kolkata", "Asansol", "Siliguri", "Durgapur", "Bardhaman", "Malda", "Howrah"],
  "Delhi": ["New Delhi", "Dwarka", "Rohini", "Shahdara"],
  "Jammu & Kashmir": ["Srinagar", "Jammu", "Baramulla", "Sopore"],
  "Ladakh": ["Leh", "Kargil"],
  "Chandigarh": ["Chandigarh"],
  "Pondicherry": ["Puducherry", "Karaikal"]
};

// ── Alert History (static seed, runtime ones appended) ──
const ALERT_HISTORY_DATA = [
  { level: "critical", msg: "Extreme flood warning – Guwahati", time: "Feb 25, 2026 – 09:32 AM" },
  { level: "high", msg: "Heavy rain alert – Bihar plains", time: "Feb 24, 2026 – 03:14 PM" },
  { level: "moderate", msg: "Rainfall alert – Kolkata", time: "Feb 23, 2026 – 11:50 AM" },
];

// ── Safety precautions per risk level ──
const SAFETY_DATA = {
  low: [
    { icon: "📰", title: "Stay Informed", tips: ["Monitor local weather forecasts daily", "Sign up for government flood alerts", "Follow official social media channels", "Keep a weather app installed"] },
    { icon: "🏠", title: "Home Preparedness", tips: ["Clear drainage gutters and pipes", "Check roof and window seals", "Know your property's flood history", "Prepare a basic emergency kit"] },
    { icon: "📋", title: "Family Planning", tips: ["Discuss flood evacuation plan with family", "Identify local evacuation shelters", "Save emergency contacts", "Keep documents in a waterproof bag"] }
  ],
  moderate: [
    { icon: "📦", title: "Pack Emergency Kit", tips: ["Water (1L/person/day for 3 days)", "Non-perishable food items", "First-aid kit and medications", "Flashlights, batteries, power bank", "Cash and ID documents"] },
    { icon: "🚗", title: "Prepare to Move", tips: ["Fill your vehicle with fuel", "Move valuables to higher floors", "Disconnect electrical appliances", "Trim trees near your home"] },
    { icon: "📡", title: "Communication Plan", tips: ["Inform neighbours about the risk", "Register with local disaster authority", "Identify a family meeting point", "Keep mobile phones fully charged"] }
  ],
  high: [
    { icon: "🚨", title: "Immediate Actions", tips: ["Move to higher ground immediately", "Do NOT walk or drive through floodwater", "Turn off gas, electricity at mains", "Lock your home and leave early", "Carry emergency kit and documents"] },
    { icon: "🏥", title: "Health & Safety", tips: ["Avoid contact with floodwater", "Do not drink tap water — use bottled only", "Wear rubber boots and gloves", "Watch for snakes displaced by floods"] },
    { icon: "📞", title: "Alert Others", tips: ["Call NDRF helpline: 9711077372", "Inform local municipal office", "Alert elderly and disabled neighbours", "Share your location with family"] }
  ],
  critical: [
    { icon: "🆘", title: "EVACUATE NOW", tips: ["Leave immediately — do not wait", "Follow official evacuation routes only", "Do not return until authorities clear", "Leave a note indicating where you went"] },
    { icon: "⚡", title: "Avoid Hazards", tips: ["Stay away from power lines", "Never drive through flooded roads", "Avoid bridges over fast-flowing water", "Beware of storm drains and manholes"] },
    { icon: "🏕", title: "At Emergency Shelter", tips: ["Register with shelter staff", "Keep family together", "Conserve phone battery", "Follow all shelter rules", "Report injuries to staff"] }
  ]
};

// ── Translations ──
const I18N = {
  en: {
    brand: "FloodGuard", nav_overview: "Overview", nav_map: "Flood Risk Map",
    nav_weather: "Weather Analysis", nav_safety: "Safety Precautions", nav_alerts: "Alert Settings",
    notifications: "Notifications", overview_title: "Flood Risk Overview",
    risk_loading: "Fetching live data...", rainfall: "Rainfall", temperature: "Temperature",
    humidity: "Humidity", wind_speed: "Wind Speed", river_level: "River Level", risk_score: "Risk Score",
    forecast_title: "7-Day Forecast", monthly_rainfall_chart: "Monthly Rainfall Pattern",
    map_sub: "Live ML flood risk across India",
    low_risk: "Low Risk", moderate_risk: "Moderate Risk", high_risk: "High Risk", critical_risk: "Critical / Flood Alert",
    flood_risk_layer: "Flood Risk", rainfall_layer: "Rainfall", river_layer: "River Levels",
    high_risk_zones: "⚠ Live High-Risk Zones", weather_sub: "Live meteorological data from OpenWeatherMap",
    feels_like: "Feels Like", pressure: "Pressure", visibility: "Visibility",
    uv_index: "UV Index", dew_point: "Dew Point",
    hourly_rainfall: "24h Rainfall Intensity", wind_rose: "Wind & Humidity Trend",
    seasonal_analysis: "Seasonal Monsoon Analysis",
    safety_sub: "Guidelines to stay safe during flood events",
    emergency_contacts: "Emergency Contacts",
    alerts_sub: "Manage how you receive flood warnings",
    active_alerts: "Active Alerts", notification_pref: "Notification Preferences",
    email_alerts: "Email Alerts", email_desc: "Receive flood warnings via email",
    sms_alerts: "SMS Alerts", sms_desc: "Get instant SMS during critical floods",
    browser_alerts: "Browser Notifications", browser_desc: "Real-time alerts in your browser",
    alert_threshold: "Alert Threshold", threshold_desc: "Send alerts when risk is at or above:",
    test_alert: "Send Test Alert", alert_history: "Alert History"
  },
  hi: {
    brand: "फलडगारड", nav_overview: "अवलोकन", nav_map: "बाढ़ जोखिम मानचितर",
    nav_weather: "मौसम विशलेषण", nav_safety: "सरकषा सावधानिया", nav_alerts: "अलरट सेटिंग",
    notifications: "सूचनां", overview_title: "बाढ़ जोखिम अवलोकन", risk_loading: "लाइव डेटा लोड हो रहा है...",
    rainfall: "वरषा", temperature: "तापमान", humidity: "आरदरता",
    wind_speed: "हवा की गति", river_level: "नदी सतर", risk_score: "जोखिम सकोर",
    forecast_title: "7-दिन का पूरवानमान", low_risk: "कम जोखिम", moderate_risk: "मधयम जोखिम",
    high_risk: "उचच जोखिम", critical_risk: "गंभीर अलरट",
    emergency_contacts: "आपातकालीन संपरक", active_alerts: "सकरिय अलरट", alert_history: "अलरट इतिहास"
  },
  mr: {
    brand: "फलडगारड", nav_overview: "आढावा", nav_map: "पूर जोखीम नकाशा",
    nav_weather: "हवामान विशलेषण", nav_safety: "सरकषा सावधानी", nav_alerts: "सूचना सेटिंग",
    rainfall: "पाऊस", temperature: "तापमान", humidity: "आरदरता",
    low_risk: "कमी जोखीम", moderate_risk: "मधयम जोखीम", high_risk: "उचच जोखीम", critical_risk: "गंभीर सूचना",
    emergency_contacts: "आपतकालीन संपरक"
  },
  ta: {
    brand: "FloodGuard", nav_overview: "கணணோடடம", nav_map: "வெளள ஆபதத வரைபடம",
    rainfall: "மழைபபொழிவ", temperature: "வெபபநிலை", humidity: "ஈரபபதம",
    low_risk: "கறைநத ஆபதத", moderate_risk: "மிதமான ஆபதத", high_risk: "அதிக ஆபதத", critical_risk: "மிகவம ஆபததான"
  },
  te: {
    brand: "FloodGuard", nav_overview: "అవలోకనం", nav_map: "వరద పరమాద మయాప",
    rainfall: "వరషపాతం", temperature: "ఉషణోగరత",
    low_risk: "తకకవ పరమాదం", moderate_risk: "మధయమ పరమాదం", high_risk: "అధిక పరమాదం"
  },
  bn: {
    brand: "FloodGuard", nav_overview: "সংকষিপত বিবরণ",
    rainfall: "বৃষটিপাত", temperature: "তাপমাতরা",
    low_risk: "কম কি", moderate_risk: "মাারি কি", high_risk: "উচচ কি"
  },
  gu: {
    brand: "FloodGuard", nav_overview: "ાંખી",
    rainfall: "વરસাદ", temperature: "તાપમান",
    low_risk: "ઓછં જોખ", moderate_risk: "મधयम जोखम", high_risk: "ઉचच जोखम"
  }
};

function getRiskColor(level) {
  const colors = { low: "#22c55e", moderate: "#f59e0b", high: "#f97316", critical: "#ef4444" };
  return colors[level] || colors.moderate;
}

function getRiskLabel(level) {
  const labels = { low: "LOW RISK", moderate: "MODERATE RISK", high: "HIGH RISK", critical: "CRITICAL" };
  return labels[level] || level.toUpperCase();
}
