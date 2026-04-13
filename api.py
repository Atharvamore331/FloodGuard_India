"""
FloodGuard India - Flask REST API
Connects ml.py, weather.py, visualization.py, sm.py, flood_risk_graphs.py
to the HTML/JS frontend via JSON endpoints.

Run:  python3 api.py
API:  http://127.0.0.1:5000/api/...
"""
import sys
import io
# Force UTF-8 output so Windows cmd doesn't crash on special chars
try:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

import os
import sys
import json
import time
import threading
import traceback
import unicodedata
import smtplib
import ssl
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache

import pandas as pd
import numpy as np
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

# â”€â”€ Import your existing modules â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_local_ps1_env(filename="local.env.ps1"):
    """
    Load environment variables from local.env.ps1 when running api.py directly.
    Expected format per line: $env:KEY = "value"
    """
    env_path = Path(__file__).resolve().parent / filename
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.lower().startswith("$env:") or "=" not in line:
            continue

        key_part, value_part = line.split("=", 1)
        key = key_part.replace("$env:", "", 1).strip()
        value = value_part.strip().strip('"').strip("'")
        os.environ[key] = value

load_local_ps1_env()

app = Flask(__name__)
CORS(app)  # Allow browser calls from file:// or any origin

# ============================================================
#  CONSTANTS
# ============================================================
OWM_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OWM_CURRENT = "https://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"
OWM_REVERSE_GEOCODE = "https://api.openweathermap.org/geo/1.0/reverse"

# Optional fixed risk override for selected cities (disabled by default).
# Set env var like: FLOOD_CITY_OVERRIDES=pune:0.80,mumbai:0.65
FORCED_CITY_PROBABILITY = {}
_forced_overrides = (os.getenv("FLOOD_CITY_OVERRIDES", "") or "").strip()
if _forced_overrides:
    for item in _forced_overrides.split(","):
        part = item.strip()
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        try:
            FORCED_CITY_PROBABILITY[name.strip().lower()] = max(0.0, min(1.0, float(value.strip())))
        except Exception:
            pass
FLOOD_PRONE_LOGIN_RISKS = {
    level.strip().lower()
    for level in os.getenv("FLOOD_PRONE_LOGIN_RISKS", "moderate,high,critical").split(",")
    if level.strip()
}

# â”€â”€ Email (SMTP) Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Use a Gmail App Password (not your regular password).
# Steps: Google Account â†’ Security â†’ 2-Step Verification â†’ App Passwords
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))                               # SSL port
SMTP_USER = os.getenv("SMTP_USER", "").strip()            # â† FILL IN your Gmail address
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()          # â† FILL IN your Gmail App Password
SMTP_FROM = os.getenv("SMTP_FROM", f"FloodGuard <{SMTP_USER}>").strip()  # â† same Gmail address here
SMTP_SECURITY = os.getenv("SMTP_SECURITY", "auto").strip().lower()  # auto | ssl | starttls

# â”€â”€ Twilio SMS Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Sign up at https://www.twilio.com/ (free trial available)
# pip install twilio
TWILIO_SID = os.getenv("TWILIO_SID", "").strip()   # â† FILL IN Account SID
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "").strip()                 # â† FILL IN Auth Token
TWILIO_FROM = os.getenv("TWILIO_FROM", "").strip()                         # â† FILL IN Twilio phone number

# SMS delivery toggle (set SMS_NOTIFICATIONS_ENABLED=true in local.env.ps1)
SMS_NOTIFICATIONS_ENABLED = os.getenv("SMS_NOTIFICATIONS_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")

# â”€â”€ Flood Admin Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# When flood risk is HIGH or CRITICAL, the system automatically alerts
# the Flood Admin via SMS (when Twilio is configured) and email.
FLOOD_ADMIN_NAME  = os.getenv("FLOOD_ADMIN_NAME", "Flood Admin").strip() or "Flood Admin"
FLOOD_ADMIN_PHONE = os.getenv("FLOOD_ADMIN_PHONE", "9819348071").strip() or "9819348071"
FLOOD_ADMIN_EMAIL = os.getenv("FLOOD_ADMIN_EMAIL", SMTP_USER).strip() or SMTP_USER

# Debounce: track last admin alert per city to avoid spam
_admin_alert_cache = {}  # city_lower -> timestamp
_ADMIN_ALERT_COOLDOWN = 600  # seconds (10 minutes)

# â”€â”€ MySQL Database Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def smtp_configured():
    return bool(SMTP_USER and SMTP_PASS and SMTP_HOST and SMTP_PORT)


def email_safe_text(value):
    """
    Normalize text to plain ASCII-safe content for email subject/body.
    Prevents mojibake like 'â€“' / 'ðŸ' in clients with mixed encodings.
    """
    text = str(value or "")
    text = text.replace("–", "-").replace("—", "-")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text


def send_email_smtp(to_email, msg):
    """
    Send email using SMTP SSL (465) or STARTTLS (587).
    Selection rules:
    - SMTP_SECURITY=ssl/starttls forces that mode.
    - SMTP_SECURITY=auto chooses by SMTP_PORT (465->ssl, 587->starttls, else ssl then starttls fallback).
    """
    mode = SMTP_SECURITY
    ctx = ssl.create_default_context()

    if mode == "ssl" or (mode == "auto" and SMTP_PORT == 465):
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as srv:
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_USER, to_email, msg.as_string())
        return "ssl"

    if mode == "starttls" or (mode == "auto" and SMTP_PORT == 587):
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as srv:
            srv.ehlo()
            srv.starttls(context=ctx)
            srv.ehlo()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_USER, to_email, msg.as_string())
        return "starttls"

    # Fallback for uncommon ports when mode is auto
    last_err = None
    for candidate in ("ssl", "starttls"):
        try:
            if candidate == "ssl":
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as srv:
                    srv.login(SMTP_USER, SMTP_PASS)
                    srv.sendmail(SMTP_USER, to_email, msg.as_string())
                return "ssl"
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as srv:
                srv.ehlo()
                srv.starttls(context=ctx)
                srv.ehlo()
                srv.login(SMTP_USER, SMTP_PASS)
                srv.sendmail(SMTP_USER, to_email, msg.as_string())
            return "starttls"
        except Exception as e:
            last_err = e
    raise last_err if last_err else RuntimeError("SMTP send failed")


def twilio_configured():
    return bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and TWILIO_SID.startswith("AC"))


DB_HOST = os.getenv("DB_HOST", os.getenv("MYSQL_HOST", "localhost")).strip()
DB_PORT = int(os.getenv("DB_PORT", os.getenv("MYSQL_PORT", "3306")))
DB_USER = os.getenv("DB_USER", os.getenv("MYSQL_USER", "root")).strip()
DB_PASS = os.getenv("DB_PASS", os.getenv("MYSQL_PASSWORD", "")).strip()
DB_NAME = os.getenv("DB_NAME", os.getenv("MYSQL_DB", "floodguard_db")).strip()

mysql_available = False
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    mysql_available = True
except ImportError:
    print("[DB] mysql-connector-python not installed. Run: pip install mysql-connector-python")

bcrypt_available = False
try:
    import bcrypt
    bcrypt_available = True
except ImportError:
    print("[DB] bcrypt not installed. Run: pip install bcrypt")

def get_db():
    """Return a fresh MySQL connection (caller must close it)."""
    if not mysql_available:
        raise RuntimeError("mysql-connector-python not installed")
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset='utf8mb4',
        autocommit=False
    )


def ensure_db_schema():
    """Create database/tables if missing so auth APIs work immediately."""
    if not mysql_available:
        raise RuntimeError("mysql-connector-python not installed")

    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        charset="utf8mb4",
        autocommit=True,
    )
    cur = conn.cursor()
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{DB_NAME}`")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(180) NOT NULL UNIQUE,
                phone VARCHAR(15) NOT NULL,
                age TINYINT UNSIGNED,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(30) NOT NULL DEFAULT 'user',
                email_alert TINYINT(1) NOT NULL DEFAULT 1,
                sms_alert TINYINT(1) NOT NULL DEFAULT 1,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                INDEX idx_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Backward-compatible migrations for existing databases.
        for ddl in (
            "ALTER TABLE users ADD COLUMN role VARCHAR(30) NOT NULL DEFAULT 'user'",
            "ALTER TABLE users ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        ):
            try:
                cur.execute(ddl)
            except Exception:
                pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_preferences (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NOT NULL,
                email_enabled TINYINT(1) NOT NULL DEFAULT 1,
                sms_enabled TINYINT(1) NOT NULL DEFAULT 1,
                browser_enabled TINYINT(1) NOT NULL DEFAULT 0,
                threshold_level ENUM('low','moderate','high','critical') NOT NULL DEFAULT 'moderate',
                alert_email VARCHAR(180),
                alert_phone VARCHAR(15),
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user (user_id),
                CONSTRAINT fk_alert_prefs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NOT NULL,
                risk_level ENUM('low','moderate','high','critical','info') NOT NULL DEFAULT 'info',
                city VARCHAR(100),
                message TEXT,
                sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_sent (user_id, sent_at),
                CONSTRAINT fk_alert_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notification_log (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NULL,
                channel ENUM('email','sms','browser') NOT NULL,
                recipient VARCHAR(200) NOT NULL,
                subject VARCHAR(255),
                body TEXT,
                status ENUM('sent','failed','pending') NOT NULL DEFAULT 'pending',
                error_msg TEXT,
                risk_level VARCHAR(20),
                city VARCHAR(100),
                sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_ch (user_id, channel),
                CONSTRAINT fk_notify_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Requested flood intelligence schema (without model_registry table).
        cur.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                district VARCHAR(120),
                state VARCHAR(120),
                lat DECIMAL(9,6),
                lon DECIMAL(9,6),
                river_basin VARCHAR(120),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_location_name_state_district (name, state, district),
                INDEX idx_location_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_observations (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                location_id INT UNSIGNED NOT NULL,
                timestamp DATETIME NOT NULL,
                rainfall_mm DECIMAL(10,2),
                temperature_c DECIMAL(6,2),
                humidity DECIMAL(6,2),
                river_level DECIMAL(10,2),
                soil_moisture DECIMAL(6,2),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_weather_location_ts (location_id, timestamp),
                CONSTRAINT fk_weather_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                location_id INT UNSIGNED NOT NULL,
                model_version VARCHAR(60) NOT NULL,
                prediction_time DATETIME NOT NULL,
                flood_risk_score DECIMAL(8,3) NOT NULL,
                risk_level ENUM('low','moderate','high','critical') NOT NULL,
                confidence DECIMAL(6,4),
                input_snapshot JSON,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_predictions_location_ts (location_id, prediction_time),
                INDEX idx_predictions_level (risk_level),
                CONSTRAINT fk_predictions_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS flood_events (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                location_id INT UNSIGNED NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                severity ENUM('low','moderate','high','critical') NOT NULL,
                damage_notes TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_flood_events_location_start (location_id, start_time),
                CONSTRAINT fk_flood_events_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                location_id INT UNSIGNED NOT NULL,
                prediction_id BIGINT UNSIGNED NULL,
                alert_type ENUM('email','sms','browser','system') NOT NULL DEFAULT 'system',
                message TEXT NOT NULL,
                sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status ENUM('sent','failed','pending','partial') NOT NULL DEFAULT 'pending',
                INDEX idx_alerts_location_sent (location_id, sent_at),
                CONSTRAINT fk_alerts_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
                CONSTRAINT fk_alerts_prediction FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NULL,
                action VARCHAR(80) NOT NULL,
                entity VARCHAR(80) NOT NULL,
                entity_id VARCHAR(80),
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(64),
                INDEX idx_audit_user_time (user_id, timestamp),
                CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NOT NULL,
                theme VARCHAR(20) DEFAULT 'light',
                language VARCHAR(10) DEFAULT 'en',
                last_city VARCHAR(120),
                last_location VARCHAR(180),
                last_lat DECIMAL(10,6) NULL,
                last_lng DECIMAL(10,6) NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user_settings_user (user_id),
                CONSTRAINT fk_user_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    finally:
        cur.close()
        conn.close()


def _utc_now_str():
    """UTC timestamp string for DB writes."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def upsert_location(conn, city_name, lat=None, lon=None):
    """Find or create a location row and return its id."""
    state = CITY_STATE_MAP.get((city_name or "").strip().lower())
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM locations WHERE name=%s AND COALESCE(state,'')=COALESCE(%s,'') LIMIT 1",
            (city_name, state),
        )
        row = cur.fetchone()
        if row:
            location_id = int(row[0])
            # Keep latest coordinates when available.
            if lat is not None and lon is not None:
                cur.execute(
                    "UPDATE locations SET lat=%s, lon=%s WHERE id=%s",
                    (float(lat), float(lon), location_id),
                )
            return location_id

        cur.execute(
            """
            INSERT INTO locations (name, district, state, lat, lon, river_basin)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (city_name, None, state, lat, lon, None),
        )
        return int(cur.lastrowid)
    finally:
        cur.close()


def persist_prediction_snapshot(city, weather, score, risk, prob):
    """
    Best-effort DB persistence for weather + prediction traceability.
    Returns (location_id, prediction_id) or (None, None) on failure.
    """
    if not mysql_available:
        return None, None
    try:
        conn = get_db()
        location_id = upsert_location(conn, city, weather.get("lat"), weather.get("lng"))
        ts = _utc_now_str()
        cur = conn.cursor()
        try:
            rainfall_mm = float(weather.get("rain_1h", 0.0) or 0.0)
            temperature_c = float(weather.get("temperature", 0.0) or 0.0)
            humidity = float(weather.get("humidity", 0.0) or 0.0)
            cur.execute(
                """
                INSERT INTO weather_observations
                (location_id, timestamp, rainfall_mm, temperature_c, humidity, river_level, soil_moisture)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (location_id, ts, rainfall_mm, temperature_c, humidity, None, humidity),
            )

            model_version = "hybrid_xgboost_v1" if ml_ready else "hybrid_rule_v1"
            confidence = round(abs(float(prob) - 0.5) * 2.0, 4)
            input_snapshot = json.dumps(
                {
                    "weather": {
                        "temperature": weather.get("temperature"),
                        "humidity": weather.get("humidity"),
                        "rain_1h": weather.get("rain_1h"),
                        "rain_3h": weather.get("rain_3h"),
                        "pressure": weather.get("pressure"),
                        "wind_speed": weather.get("wind_speed"),
                    },
                    "city": city,
                    "risk": risk,
                    "score": score,
                }
            )
            cur.execute(
                """
                INSERT INTO predictions
                (location_id, model_version, prediction_time, flood_risk_score, risk_level, confidence, input_snapshot)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (location_id, model_version, ts, float(score), risk, confidence, input_snapshot),
            )
            prediction_id = int(cur.lastrowid)
            conn.commit()
            return location_id, prediction_id
        finally:
            cur.close()
            conn.close()
    except Exception:
        return None, None


def persist_alert_record(city, message, alert_type, status, prediction_id=None):
    """Best-effort insert into alerts table without impacting API response."""
    if not mysql_available:
        return
    try:
        conn = get_db()
        location_id = upsert_location(conn, city, None, None)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO alerts (location_id, prediction_id, alert_type, message, sent_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (location_id, prediction_id, alert_type, message, _utc_now_str(), status),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception:
        return

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CITY_STATE_MAP = {
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "nashik": "Maharashtra", "thane": "Maharashtra", "kolkata": "West Bengal",
    "siliguri": "West Bengal", "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu", "hyderabad": "Telangana",
    "delhi": "Delhi", "new delhi": "Delhi", "ahmedabad": "Gujarat", "surat": "Gujarat",
    "jaipur": "Rajasthan", "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh",
    "patna": "Bihar", "kochi": "Kerala", "thiruvananthapuram": "Kerala",
    "guwahati": "Assam", "bhubaneswar": "Odisha",
}

# ============================================================
#  ML MODEL  (XGBoost â€“ loaded once at startup)
# ============================================================
ml_model = None
ml_imputer = None
ml_scaler = None
ml_feature_columns = None
ml_feature_defaults = None
ml_ready = False
ml_error = ""

# â”€â”€ Weather response cache (city -> (data, timestamp)) â”€â”€
_weather_cache = {}
_CACHE_TTL = 600  # seconds (10 minutes) â€“ reduces repeated OWM hits

def load_ml_model():
    global ml_model, ml_imputer, ml_scaler, ml_feature_columns, ml_feature_defaults, ml_ready, ml_error
    try:
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier

        csv_path = os.path.join(BASE_DIR, "India_Flood_Dataset.csv")
        df = pd.read_csv(csv_path)
        df = pd.get_dummies(df, columns=["State"], drop_first=True)

        X_df = df.drop("Flood_Occurred", axis=1)
        y = df["Flood_Occurred"]

        ml_imputer = SimpleImputer(strategy="median")
        ml_scaler = StandardScaler()

        X_imputed = ml_imputer.fit_transform(X_df)
        X_scaled = ml_scaler.fit_transform(X_imputed)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        ml_model = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, gamma=0.1,
            reg_alpha=0.5, reg_lambda=1, scale_pos_weight=1,
            random_state=42, eval_metric="logloss",
        )
        ml_model.fit(X_train, y_train)

        ml_feature_defaults = X_df.median(numeric_only=True).to_dict()
        ml_feature_columns = X_df.columns.tolist()
        ml_ready = True
        print("[OK] ML Model (XGBoost) loaded successfully.")
    except Exception as e:
        ml_error = str(e)
        print(f"[WARN] ML model failed to load: {e}")


def _start_ml_background():
    """Load ML model in a background thread so API starts instantly."""
    t = threading.Thread(target=load_ml_model, daemon=True)
    t.start()

# ============================================================
#  HELPER: Get weather from OpenWeatherMap
# ============================================================
def fetch_weather(city_name):
    # Check cache first
    cache_key = city_name.strip().lower()
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if time.time() - cached_time < _CACHE_TTL:
            return cached_data

    try:
        params = {"q": city_name, "appid": OWM_API_KEY, "units": "metric"}
        r = requests.get(OWM_CURRENT, params=params, timeout=4)
        r.raise_for_status()
        data = r.json()
        rain = data.get("rain", {})
        result = {
            "success": True,
            "city": data.get("name", city_name),
            "country": data.get("sys", {}).get("country", "IN"),
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "icon_url": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "visibility": round(data.get("visibility", 10000) / 1000, 1),
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
            "wind_deg": data["wind"].get("deg", 0),
            "rain_1h": rain.get("1h", 0.0),
            "rain_3h": rain.get("3h", 0.0),
            "lat": data["coord"]["lat"],
            "lng": data["coord"]["lon"],
        }
        _weather_cache[cache_key] = (result, time.time())
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
#  Historical average monthly rainfall per state (from training data)
#  Used so predictions are realistic even on dry days (when live rain = 0)
# ============================================================
STATE_MONTHLY_RAINFALL = {
    "Andhra Pradesh":    {1:65.2,2:76.7,3:85.4,4:89.8,5:86.9,6:323.8,7:304.3,8:310.4,9:297.3,10:103.8,11:80.3,12:81.9},
    "Arunachal Pradesh": {1:80.5,2:67.9,3:81.0,4:76.9,5:87.7,6:305.3,7:318.4,8:279.6,9:307.2,10:81.1,11:90.3,12:83.8},
    "Assam":             {1:88.1,2:73.5,3:78.5,4:94.3,5:88.1,6:283.5,7:281.0,8:337.6,9:285.3,10:88.5,11:91.0,12:83.6},
    "Bihar":             {1:85.7,2:77.2,3:85.6,4:62.7,5:82.2,6:312.7,7:321.4,8:287.2,9:297.9,10:90.2,11:83.2,12:74.2},
    "Chhattisgarh":      {1:69.5,2:85.1,3:89.9,4:75.8,5:71.2,6:320.3,7:287.4,8:292.0,9:304.5,10:72.8,11:80.6,12:88.8},
    "Goa":               {1:72.2,2:65.8,3:78.5,4:94.4,5:91.2,6:296.6,7:294.0,8:311.0,9:300.0,10:75.9,11:81.2,12:95.6},
    "Gujarat":           {1:94.3,2:85.5,3:87.6,4:69.1,5:54.2,6:314.1,7:291.4,8:322.5,9:292.7,10:91.1,11:89.9,12:78.3},
    "Haryana":           {1:82.9,2:83.0,3:82.3,4:88.9,5:87.7,6:297.3,7:316.3,8:287.8,9:297.9,10:82.2,11:94.6,12:76.0},
    "Himachal Pradesh":  {1:80.5,2:77.4,3:81.8,4:77.8,5:79.6,6:272.2,7:277.6,8:283.1,9:285.3,10:80.9,11:83.1,12:75.6},
    "Jharkhand":         {1:71.6,2:76.3,3:90.6,4:85.5,5:78.2,6:307.9,7:319.2,8:308.9,9:287.1,10:65.7,11:77.7,12:84.3},
    "Karnataka":         {1:83.9,2:88.4,3:89.3,4:89.7,5:82.4,6:306.0,7:312.2,8:296.4,9:301.4,10:83.1,11:75.0,12:95.2},
    "Kerala":            {1:79.4,2:82.0,3:83.7,4:61.8,5:93.8,6:296.4,7:309.8,8:288.2,9:239.8,10:73.5,11:91.2,12:79.4},
    "Madhya Pradesh":    {1:55.5,2:82.7,3:89.7,4:90.5,5:79.0,6:293.7,7:279.1,8:310.8,9:320.6,10:77.4,11:72.8,12:72.9},
    "Maharashtra":       {1:80.2,2:101.2,3:91.4,4:77.1,5:75.3,6:321.2,7:321.3,8:302.9,9:282.6,10:88.3,11:87.7,12:87.1},
    "Manipur":           {1:65.8,2:77.7,3:74.5,4:69.3,5:91.5,6:282.6,7:277.6,8:292.1,9:318.3,10:80.7,11:71.1,12:81.4},
    "Meghalaya":         {1:78.0,2:84.4,3:91.0,4:73.5,5:76.4,6:263.7,7:352.8,8:316.8,9:318.5,10:65.2,11:86.5,12:81.1},
    "Mizoram":           {1:71.5,2:75.6,3:77.9,4:74.2,5:91.4,6:317.4,7:290.8,8:314.8,9:311.4,10:99.2,11:70.9,12:76.2},
    "Nagaland":          {1:70.1,2:75.5,3:85.6,4:91.2,5:86.0,6:292.0,7:284.2,8:328.5,9:289.9,10:74.2,11:92.1,12:76.9},
    "Odisha":            {1:77.3,2:69.3,3:79.8,4:73.0,5:81.4,6:345.5,7:284.5,8:320.3,9:289.8,10:88.1,11:63.8,12:88.5},
    "Punjab":            {1:69.3,2:81.1,3:96.2,4:74.4,5:71.9,6:301.1,7:309.5,8:292.3,9:316.7,10:81.6,11:86.5,12:88.2},
    "Rajasthan":         {1:100.3,2:78.7,3:78.7,4:79.2,5:96.7,6:251.6,7:290.4,8:311.6,9:295.5,10:75.9,11:94.2,12:72.4},
    "Sikkim":            {1:79.4,2:88.5,3:89.3,4:84.8,5:82.0,6:276.1,7:308.5,8:284.7,9:296.8,10:71.3,11:81.4,12:93.4},
    "Tamil Nadu":        {1:70.0,2:70.7,3:100.4,4:82.5,5:79.9,6:295.3,7:301.4,8:309.5,9:308.4,10:76.4,11:74.0,12:58.0},
    "Telangana":         {1:80.6,2:76.6,3:88.7,4:89.8,5:86.6,6:315.5,7:286.4,8:293.4,9:330.4,10:84.0,11:85.9,12:71.0},
    "Tripura":           {1:85.4,2:89.1,3:72.3,4:83.9,5:71.7,6:296.1,7:271.8,8:302.6,9:293.7,10:72.1,11:80.1,12:85.8},
    "Uttar Pradesh":     {1:81.7,2:93.7,3:79.2,4:93.4,5:70.1,6:297.9,7:283.3,8:325.5,9:298.1,10:75.2,11:85.6,12:75.7},
    "Uttarakhand":       {1:77.0,2:72.4,3:82.2,4:72.8,5:90.2,6:316.8,7:304.9,8:303.9,9:302.0,10:75.3,11:84.4,12:75.1},
    "West Bengal":       {1:69.5,2:83.1,3:76.8,4:88.6,5:85.1,6:310.4,7:278.4,8:287.2,9:276.2,10:80.5,11:83.2,12:61.7},
    # Delhi mapped separately
    "Delhi":             {1:24.2,2:20.5,3:16.2,4:7.0,5:20.9,6:65.2,7:215.0,8:206.3,9:108.4,10:9.7,11:3.1,12:11.5},
}

# ============================================================
#  HELPER: Build sample for XGBoost prediction
# ============================================================
def build_prediction_sample(city_name, weather_data):
    import datetime
    sample = ml_feature_defaults.copy()

    # â”€â”€ Current year/month (important temporal features) â”€â”€
    now = datetime.datetime.utcnow()
    current_month = now.month
    current_year  = now.year
    sample["Year"]  = current_year
    sample["Month"] = current_month

    # â”€â”€ Rainfall: use historical state average for this month as base,
    #    then boost by the live rain signal (so dry days aren't always 0) â”€â”€
    city_key = city_name.strip().lower()
    mapped_state = CITY_STATE_MAP.get(city_key)

    historical_avg = 107.0  # global median fallback
    if mapped_state and mapped_state in STATE_MONTHLY_RAINFALL:
        historical_avg = STATE_MONTHLY_RAINFALL[mapped_state].get(current_month, 107.0)

    rain_1h = float(weather_data.get("rain_1h", 0.0))
    rain_3h = float(weather_data.get("rain_3h", 0.0))
    live_hourly_mm = max(rain_1h, rain_3h / 3.0)
    # Live rain adds on top of the historical base (scaled conservatively)
    live_contribution = live_hourly_mm * 24.0 * 0.5  # half-day equivalent

    monthly_rainfall = historical_avg + live_contribution
    sample["Monthly_Rainfall_mm"] = monthly_rainfall

    # â”€â”€ Humidity-based features â”€â”€
    hum = float(weather_data.get("humidity", 70))
    sample["Soil_Moisture_%"]   = hum
    sample["Reservoir_Level_%"] = hum

    # â”€â”€ Derived features â”€â”€
    sample["Previous_Month_Rainfall"] = max(0.0, monthly_rainfall * 0.8)
    sample["River_Discharge_Cumecs"]  = max(
        0.0, monthly_rainfall * 2.5 * (ml_feature_defaults.get("River_Discharge_Cumecs", 200) / 200.0)
    )

    # â”€â”€ State one-hot encoding â”€â”€
    if mapped_state:
        col_name = f"State_{mapped_state}"
        if col_name in ml_feature_columns:
            for col in ml_feature_columns:
                if col.startswith("State_"):
                    sample[col] = 0.0
            sample[col_name] = 1.0

    sample_df      = pd.DataFrame([sample], columns=ml_feature_columns)
    sample_imputed = ml_imputer.transform(sample_df)
    return ml_scaler.transform(sample_imputed)


# ============================================================
#  FLOOD ADMIN AUTO-NOTIFICATION
#  Sends email + SMS to Flood Admin when risk is HIGH or CRITICAL
# ============================================================

def _send_admin_alert_delivery(city, risk, label, message, score, respect_cooldown=True):
    city = email_safe_text(city)
    risk = email_safe_text(risk)
    label = email_safe_text(label)
    message = email_safe_text(message)
    city_key = (city or "").strip().lower()
    now = time.time()
    results = {"email_sent": False, "sms_sent": False, "errors": [], "debounced": False}

    if respect_cooldown:
        last_sent = _admin_alert_cache.get(city_key, 0)
        if city_key and (now - last_sent < _ADMIN_ALERT_COOLDOWN):
            results["debounced"] = True
            return results
        if city_key:
            _admin_alert_cache[city_key] = now

    if smtp_configured() and FLOOD_ADMIN_EMAIL:
        try:
            risk_colors = {"low": "#22c55e", "moderate": "#f59e0b", "high": "#f97316", "critical": "#ef4444"}
            color = risk_colors.get(risk, "#ef4444")
            html_body = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:30px auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <tr><td style="background:linear-gradient(135deg,#7f1d1d,#dc2626);padding:28px 32px;text-align:center;">
      <div style="font-size:28px;margin-bottom:6px;">ALERT</div>
      <div style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1px;">FLOOD ADMIN ALERT</div>
      <div style="color:rgba(255,255,255,0.7);font-size:13px;margin-top:4px;">FloodGuard India - Automated System</div>
    </td></tr>
    <tr><td style="padding:24px 32px 0;">
      <div style="display:inline-block;background:{color}1a;border:2px solid {color};border-radius:50px;padding:8px 22px;">
        <span style="color:{color};font-weight:700;font-size:15px;">{label}</span>
      </div>
    </td></tr>
    <tr><td style="padding:20px 32px;">
      <p style="font-size:16px;color:#1e293b;line-height:1.6;margin:0 0 12px;">
        <strong>City:</strong> {city}<br>
        <strong>Risk Score:</strong> {score}%<br>
        <strong>Risk Level:</strong> {risk.upper()}
      </p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 20px;">{message}</p>
    </td></tr>
  </table>
</body>
</html>"""

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"ADMIN ALERT - {label} in {city} ({score}%)"
            msg["From"] = SMTP_FROM
            msg["To"] = FLOOD_ADMIN_EMAIL
            msg.attach(MIMEText(
                f"FLOOD ADMIN ALERT\n\n{label}\nCity: {city}\nRisk Score: {score}%\n\n{message}",
                "plain",
            ))
            msg.attach(MIMEText(html_body, "html"))
            send_email_smtp(FLOOD_ADMIN_EMAIL, msg)
            results["email_sent"] = True
        except Exception as e:
            results["errors"].append(f"Email failed: {e}")
    else:
        results["errors"].append("Email skipped: SMTP or admin email not configured.")

    if SMS_NOTIFICATIONS_ENABLED and twilio_configured():
        try:
            from twilio.rest import Client as TwilioClient
            sms_body = f"[FloodGuard ADMIN] {label} - {city}\nRisk Score: {score}%\n{message}"
            client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
            to_phone = FLOOD_ADMIN_PHONE if FLOOD_ADMIN_PHONE.startswith("+") else f"+91{FLOOD_ADMIN_PHONE}"
            client.messages.create(body=sms_body, from_=TWILIO_FROM, to=to_phone)
            results["sms_sent"] = True
        except Exception as e:
            results["errors"].append(f"SMS failed: {e}")
    else:
        results["errors"].append("SMS skipped: disabled or Twilio not configured.")

    return results


def notify_flood_admin(city, risk, label, message, score):
    """
    Background task: alert the Flood Admin via email and SMS.
    Called from /api/predict when risk is high or critical.
    """
    print(f"[ADMIN ALERT] {label} in {city} (score={score}%) -> Notifying {FLOOD_ADMIN_NAME}")
    results = _send_admin_alert_delivery(city, risk, label, message, score, respect_cooldown=True)
    if results.get("debounced"):
        print(f"[ADMIN ALERT] Debounced for {city}")
    for err in results.get("errors", []):
        print(f"[ADMIN ALERT] {err}")

def _normalize_city_text(value):
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in str(value or "").lower())
    return " ".join(text.split())


def _extract_city_candidates(raw_city):
    text = str(raw_city or "").strip()
    if not text:
        return []

    # Common frontend values: "Mumbai, IN", "Pune, Maharashtra", etc.
    parts = [p.strip() for p in text.split(",") if p.strip()]
    candidates = []
    if parts:
        candidates.append(parts[0])
    candidates.append(text)

    seen = set()
    out = []
    for c in candidates:
        key = _normalize_city_text(c)
        if key and key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _find_zone_for_city(city):
    for candidate in _extract_city_candidates(city):
        city_key = _normalize_city_text(candidate)
        if not city_key:
            continue

        for zone in INDIA_FLOOD_ZONES:
            zone_name = str(zone.get("name", ""))
            zone_key = _normalize_city_text(zone_name)
            zone_base = _normalize_city_text(zone_name.split("(")[0])

            if city_key in (zone_key, zone_base):
                return zone
            if zone_key.startswith(city_key + " ") or zone_base.startswith(city_key + " "):
                return zone
            if city_key and city_key in zone_key:
                return zone
    return None


def maybe_notify_admin_login(user_id, user_name, city):
    """
    Trigger admin alert when a user logs in from a known flood-prone city.
    Non-blocking and best-effort only.
    """
    if not city:
        return {"triggered": False, "reason": "city_missing"}

    zone = _find_zone_for_city(city)
    if not zone:
        return {"triggered": False, "reason": "city_not_in_flood_zone_list"}

    # Check FORCED_CITY_PROBABILITY override first (e.g. pune:0.80 from env var).
    # This ensures the login alert uses the same value as /api/predict.
    city_key_lower = (city or "").strip().lower()
    # Also try the first part before comma (e.g. "Pune, Maharashtra" -> "pune")
    city_first_part = city_key_lower.split(",")[0].strip()
    forced_prob = FORCED_CITY_PROBABILITY.get(city_first_part) or FORCED_CITY_PROBABILITY.get(city_key_lower)

    if forced_prob is not None:
        prob = max(0.0, min(1.0, float(forced_prob)))
        score = int(round(prob * 100))
        # Derive risk level from the forced probability (same thresholds as /api/predict)
        if prob >= 0.8:
            risk = "critical"
        elif prob >= 0.6:
            risk = "high"
        elif prob >= 0.4:
            risk = "moderate"
        else:
            risk = "low"
    else:
        risk = str(zone.get("risk", "moderate")).lower()
        try:
            score = int(round(float(zone.get("flood_occurred", 0.0)) * 100))
        except Exception:
            score = 0

    if risk not in FLOOD_PRONE_LOGIN_RISKS:
        return {
            "triggered": False,
            "reason": f"risk_{risk}_not_enabled",
            "risk": risk,
            "zone": zone.get("name"),
        }

    safe_name = (user_name or "Unknown User").strip()[:80]
    safe_city = (city or zone.get("name") or "Unknown City").strip()[:120]
    label = "FLOOD-PRONE CITY LOGIN ALERT"
    message = (
        f"User login detected from a flood-prone city.\n"
        f"User: {safe_name} (ID: {user_id})\n"
        f"City: {safe_city}\n"
        f"Zone Risk: {risk.upper()}"
    )

    delivery = _send_admin_alert_delivery(
        safe_city,
        risk,
        label,
        message,
        score,
        respect_cooldown=False,
    )

    # Persist admin notification attempt for traceability in DB.
    email_error = "; ".join([e for e in delivery.get("errors", []) if str(e).startswith("Email")]) or None
    sms_error = "; ".join([e for e in delivery.get("errors", []) if str(e).startswith("SMS")]) or None
    if FLOOD_ADMIN_EMAIL:
        log_notification_event(
            user_id=user_id,
            channel="email",
            recipient=FLOOD_ADMIN_EMAIL,
            subject=f"Admin Login Alert - {label} in {safe_city}",
            body=message,
            status="sent" if delivery.get("email_sent") else "failed",
            error_msg=email_error,
            risk_level=risk,
            city=safe_city,
        )
    if SMS_NOTIFICATIONS_ENABLED and FLOOD_ADMIN_PHONE:
        log_notification_event(
            user_id=user_id,
            channel="sms",
            recipient=FLOOD_ADMIN_PHONE,
            subject=f"Admin Login SMS Alert - {label} in {safe_city}",
            body=message,
            status="sent" if delivery.get("sms_sent") else "failed",
            error_msg=sms_error,
            risk_level=risk,
            city=safe_city,
        )

    return {
        "triggered": bool(delivery.get("email_sent") or delivery.get("sms_sent")),
        "reason": "sent" if (delivery.get("email_sent") or delivery.get("sms_sent")) else "delivery_failed",
        "risk": risk,
        "zone": zone.get("name"),
        "city": safe_city,
        "delivery": delivery,
    }


# ============================================================
#  ENDPOINTS
# ============================================================

# ============================================================
#  HYBRID FLOOD RISK SCORING ENGINE
#  Components:
#    A) Live Weather Physics (60%) â€“ based directly on OWM values
#    B) Historical Seasonal Baseline (15%) â€“ state monthly rainfall ratio
#    C) ML Model Probability (25%) â€“ XGBoost trained on India Flood Dataset
#
#  Result is always meaningful. Never exactly 0 unless perfect conditions.
# ============================================================

def live_weather_score(weather, mapped_state=None):
    """
    Physics-based flood probability from live OWM data.
    Returns a probability in [0, 1].
    """
    import datetime
    score = 0.0

    # 1. Rainfall contribution (dominant signal, 0â€“0.55)
    rain_1h = float(weather.get("rain_1h", 0.0))
    rain_3h = float(weather.get("rain_3h", 0.0))
    rain_mm_h = max(rain_1h, rain_3h / 3.0)   # mm per hour

    # Thresholds: IMD classification
    # Light: <2.5  Moderate: 2.5-7.5  Heavy: 7.5-35.5  Very Heavy: 35.5-64.5  Extreme: >64.5 mm/hr
    if rain_mm_h >= 64.5:
        rain_score = 0.55
    elif rain_mm_h >= 35.5:
        rain_score = 0.45
    elif rain_mm_h >= 15.0:
        rain_score = 0.35
    elif rain_mm_h >= 7.5:
        rain_score = 0.25
    elif rain_mm_h >= 2.5:
        rain_score = 0.15
    elif rain_mm_h >= 0.5:
        rain_score = 0.07
    else:
        rain_score = 0.0
    score += rain_score

    # 2. Humidity contribution (0â€“0.20)
    hum = float(weather.get("humidity", 60))
    # Every city has baseline humidity; score rises steeply above 80%
    hum_score = max(0.0, (hum - 55) / 45.0) * 0.20   # 55% = 0, 100% = 0.20
    score += hum_score

    # 3. Pressure contribution (low pressure = cyclone/storm, 0â€“0.10)
    pressure = float(weather.get("pressure", 1013))
    # < 980 hPa = deep depression / cyclone
    if pressure < 960:
        score += 0.10
    elif pressure < 975:
        score += 0.07
    elif pressure < 990:
        score += 0.04
    elif pressure < 1005:
        score += 0.02
    # else: normal, 0

    # 4. Wind speed contribution (0â€“0.10)
    wind = float(weather.get("wind_speed", 0))
    if wind >= 90:     score += 0.10   # severe cyclone
    elif wind >= 60:   score += 0.07
    elif wind >= 40:   score += 0.04
    elif wind >= 25:   score += 0.02

    # 5. Seasonal baseline for the state (0â€“0.05)
    # High months (JUN-SEP) get a small bonus even on dry days
    now = datetime.datetime.utcnow()
    month = now.month
    if mapped_state and mapped_state in STATE_MONTHLY_RAINFALL:
        monthly_normal = STATE_MONTHLY_RAINFALL[mapped_state].get(month, 80)
    else:
        monthly_normal = 80
    # Monsoon season states naturally have higher base risk
    if month in (6, 7, 8, 9) and monthly_normal > 200:
        score += 0.05
    elif month in (5, 10) and monthly_normal > 150:
        score += 0.02

    return min(1.0, max(0.0, score))


def seasonal_baseline_score(city_name, weather):
    """
    Historical seasonal probability:
    how often does this state see floods in this calendar month?
    Returns [0, 1].
    """
    import datetime
    month = datetime.datetime.utcnow().month
    city_key = city_name.strip().lower()
    state = CITY_STATE_MAP.get(city_key)
    if not state or state not in STATE_MONTHLY_RAINFALL:
        return 0.08  # generic baseline

    monthly_mm = STATE_MONTHLY_RAINFALL[state].get(month, 80)
    # Normalise: monsoon months (>250mm) â†’ up to 0.4 baseline probability
    # Dry months (<30mm) â†’ ~0.03
    baseline = min(0.40, max(0.03, (monthly_mm - 20) / 600.0))
    return baseline


def hybrid_flood_probability(city_name, weather):
    """
    Final hybrid score.
    Returns probability in [0, 1] with a min floor so it is never exactly 0.
    Weights:  Live weather 60% + Seasonal baseline 15% + ML model 25%
    """
    city_key = city_name.strip().lower()
    mapped_state = CITY_STATE_MAP.get(city_key)

    # A) Live weather physics (always run â€” no model needed)
    w_score = live_weather_score(weather, mapped_state)

    # B) Seasonal historical baseline
    s_score = seasonal_baseline_score(city_name, weather)

    # C) ML model probability (if available)
    m_score = s_score  # same as seasonal if ML unavailable
    if ml_ready:
        try:
            sample  = build_prediction_sample(city_name, weather)
            m_score = float(ml_model.predict_proba(sample)[0][1])
        except Exception:
            m_score = s_score

    # Weighted combination
    prob = 0.60 * w_score + 0.15 * s_score + 0.25 * m_score

    # Minimum floor: every inhabited city has some baseline risk
    FLOOR = 0.015   # 1.5%
    prob  = max(FLOOR, min(1.0, prob))
    return prob


def resolve_city_from_coords(lat, lng):
    """
    Prefer reverse geocoding for GPS labels so smaller towns are not replaced
    by the nearest large-city weather station name.
    """
    try:
        params = {"lat": lat, "lon": lng, "limit": 5, "appid": OWM_API_KEY}
        r = requests.get(OWM_REVERSE_GEOCODE, params=params, timeout=5)
        r.raise_for_status()
        results = r.json() or []
        for item in results:
            if (item.get("country") or "").upper() == "IN" and item.get("name"):
                return item.get("name")
        for item in results:
            if item.get("name"):
                return item.get("name")
    except Exception:
        pass

    params = {"lat": lat, "lon": lng, "appid": OWM_API_KEY, "units": "metric"}
    r = requests.get(OWM_CURRENT, params=params, timeout=5)
    r.raise_for_status()
    return r.json().get("name", "Mumbai")


# â”€â”€ 1. Flood Risk Prediction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/predict", methods=["GET"])
def predict():
    city = request.args.get("city", "").strip()
    lat  = request.args.get("lat")
    lng  = request.args.get("lng")

    # When GPS coords provided, resolve city name from OWM
    if lat and lng and (not city or city.lower() == "current location"):
        try:
            city = resolve_city_from_coords(lat, lng)
        except Exception as e:
            return jsonify({"error": f"GPS weather lookup failed: {e}"}), 503

    if not city:
        return jsonify({"error": "city or lat/lng required"}), 400

    weather = fetch_weather(city)
    if not weather["success"]:
        return jsonify({"error": f"Weather unavailable: {weather['error']}"}), 503

    # Run hybrid probability engine unless a demo city override is configured.
    forced_prob = FORCED_CITY_PROBABILITY.get(city.strip().lower())
    if forced_prob is not None:
        prob = max(0.0, min(1.0, float(forced_prob)))
    else:
        prob = hybrid_flood_probability(city, weather)
    score = round(prob * 100, 3)

    if prob >= 0.8:
        risk = "critical"
        label = "CRITICAL FLOOD ALERT"
        color = "#ef4444"
        message = f"Severe flooding imminent in {city}. Evacuate immediately!"
    elif prob >= 0.6:
        risk = "high"
        label = "HIGH FLOOD RISK"
        color = "#f97316"
        message = f"High flood risk detected in {city}. Take precautions now."
    elif prob >= 0.4:
        risk = "moderate"
        label = "MODERATE FLOOD RISK"
        color = "#f59e0b"
        message = f"Moderate risk in {city}. Stay alert and monitor weather."
    else:
        risk = "low"
        label = "LOW FLOOD RISK"
        color = "#22c55e"
        message = f"Low flood risk currently in {city}. Normal conditions."

    # Persist weather + prediction history (best-effort, no API failure on DB issues).
    try:
        persist_prediction_snapshot(city, weather, score, risk, prob)
    except Exception:
        pass

    # â”€â”€ Auto-alert Flood Admin for HIGH / CRITICAL risk â”€â”€
    if risk in ("high", "critical"):
        threading.Thread(
            target=notify_flood_admin,
            args=(city, risk, label, message, score),
            daemon=True
        ).start()

    return jsonify({
        "city": city,
        "probability": prob,
        "score": score,
        "risk": risk,
        "label": label,
        "color": color,
        "message": message,
        "ml_model_used": ml_ready,
        "weather_summary": weather.get("description", ""),
        # Embed full weather so the frontend doesn't need a separate /weather call
        "weather": weather,
    })


# â”€â”€ 2. Live Weather â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/weather", methods=["GET"])
def weather_endpoint():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if lat and lng:
        # GPS coordinates
        try:
            city = resolve_city_from_coords(lat, lng)
        except Exception as e:
            return jsonify({"error": str(e)}), 503

    if not city:
        return jsonify({"error": "city or lat/lng required"}), 400

    weather = fetch_weather(city)
    if not weather["success"]:
        return jsonify({"error": weather["error"]}), 503
    return jsonify(weather)


# â”€â”€ 3. 5-Day Forecast â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/forecast", methods=["GET"])
def forecast_endpoint():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    try:
        if lat and lng:
            params = {"lat": lat, "lon": lng, "appid": OWM_API_KEY, "units": "metric", "cnt": 16}
        else:
            params = {"q": city, "appid": OWM_API_KEY, "units": "metric", "cnt": 16}

        r = requests.get(OWM_FORECAST, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()

        # Group by day, pick noon reading
        days = {}
        for item in data["list"]:
            date = item["dt_txt"].split(" ")[0]
            hour = item["dt_txt"].split(" ")[1]
            if date not in days or hour == "12:00:00":
                rain = item.get("rain", {}).get("3h", 0.0)
                temp = round(item["main"]["temp"])
                hum = item["main"]["humidity"]
                desc = item["weather"][0]["description"].title()
                icon = item["weather"][0]["icon"]

                # Simple risk calc
                prob_est = min(1.0, rain * 0.12 + hum * 0.005)
                if prob_est >= 0.8: risk = "critical"
                elif prob_est >= 0.6: risk = "high"
                elif prob_est >= 0.4: risk = "moderate"
                else: risk = "low"

                days[date] = {
                    "date": date,
                    "temp": temp,
                    "humidity": hum,
                    "description": desc,
                    "icon": icon,
                    "icon_url": f"https://openweathermap.org/img/wn/{icon}@2x.png",
                    "rain_mm": round(rain, 1),
                    "risk": risk,
                }

        return jsonify({"forecast": list(days.values())[:7]})
    except Exception as e:
        return jsonify({"error": str(e)}), 503


# â”€â”€ 4. Monthly Rainfall (from CSV) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/rainfall", methods=["GET"])
def rainfall_endpoint():
    try:
        csv_path = os.path.join(BASE_DIR, "monthly_rainfall.csv")
        df = pd.read_csv(csv_path).dropna(subset=["YEAR"])
        df["YEAR"] = df["YEAR"].astype(int)

        subdivision = request.args.get("subdivision", "")
        year = request.args.get("year", "")
        action = request.args.get("action", "monthly")  # monthly|annual|seasonal|heatmap|subdivisions

        # List all subdivisions
        if action == "subdivisions":
            return jsonify({"subdivisions": sorted(df["SUBDIVISION"].unique().tolist())})

        if not subdivision:
            subdivision = df["SUBDIVISION"].iloc[0]

        sub_df = df[df["SUBDIVISION"] == subdivision]
        years_available = sorted(sub_df["YEAR"].unique().tolist())

        if not year and years_available:
            year = str(years_available[-1])

        months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

        if action == "monthly":
            year_df = sub_df[sub_df["YEAR"] == int(year)]
            # Auto-fall back to the latest available year if requested year has no data
            if year_df.empty and years_available:
                year = str(years_available[-1])
                year_df = sub_df[sub_df["YEAR"] == int(year)]
            if year_df.empty:
                return jsonify({"error": "No data for selected year"}), 404
            values = year_df[months].values.flatten().tolist()
            return jsonify({
                "subdivision": subdivision, "year": int(year),
                "months": months, "values": [round(float(v), 1) for v in values],
                "annual": round(float(year_df["ANNUAL"].values[0]), 1),
                "years_available": years_available
            })

        if action == "annual":
            trend = sub_df.sort_values("YEAR")
            ma = trend["ANNUAL"].rolling(window=5).mean().round(1).tolist()
            return jsonify({
                "subdivision": subdivision,
                "years": trend["YEAR"].tolist(),
                "annual": [round(float(v), 1) for v in trend["ANNUAL"].tolist()],
                "moving_avg_5yr": ma
            })

        if action == "seasonal":
            year_df = sub_df[sub_df["YEAR"] == int(year)]
            if year_df.empty:
                return jsonify({"error": "No data"}), 404
            seasons = {"JF": "Jan-Feb", "MAM": "Mar-May", "JJAS": "Jun-Sep", "OND": "Oct-Dec"}
            return jsonify({
                "subdivision": subdivision, "year": int(year),
                "seasons": list(seasons.values()),
                "values": [round(float(year_df[k].values[0]), 1) for k in seasons]
            })

        if action == "heatmap":
            pivot = sub_df.pivot_table(index="YEAR", values=months, aggfunc="mean")
            return jsonify({
                "subdivision": subdivision,
                "years": pivot.index.tolist(),
                "months": months,
                "data": [[round(float(v), 1) if not np.isnan(v) else 0 for v in row]
                         for row in pivot.values.tolist()]
            })

        return jsonify({"error": "Unknown action"}), 400
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# â”€â”€ 5. Soil Moisture (from merged.csv) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/soil", methods=["GET"])
def soil_endpoint():
    try:
        csv_path = os.path.join(BASE_DIR, "merged.csv")
        df = pd.read_csv(csv_path)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["Date"])

        STATE_COL = "State Name"
        DIST_COL = "DistrictName"
        SM_COL = "Volume Soilmoisture percentage (at 15cm)"

        action = request.args.get("action", "states")
        state = request.args.get("state", "")
        district = request.args.get("district", "")

        if action == "states":
            return jsonify({"states": sorted(df[STATE_COL].dropna().unique().tolist())})

        if action == "districts":
            if not state:
                return jsonify({"error": "state required"}), 400
            sub = df[df[STATE_COL] == state]
            return jsonify({"districts": sorted(sub[DIST_COL].dropna().unique().tolist())})

        # Trend for district
        if not state or not district:
            return jsonify({"error": "state and district required"}), 400

        filt = df[(df[STATE_COL] == state) & (df[DIST_COL] == district)].copy()
        filt = filt.sort_values("Date")

        if action == "trend":
            return jsonify({
                "dates": filt["Date"].dt.strftime("%Y-%m-%d").tolist(),
                "values": [round(float(v), 2) for v in filt[SM_COL].fillna(0).tolist()]
            })

        if action == "monthly_avg":
            filt["month"] = filt["Date"].dt.month
            avg = filt.groupby("month")[SM_COL].mean().round(2)
            return jsonify({
                "months": avg.index.tolist(),
                "values": avg.tolist()
            })

        return jsonify({"error": "Unknown action"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# â”€â”€ 6. Flood Risk Zones (India â€“ Named Locations) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Comprehensive curated list of historically flood-prone zones in India
INDIA_FLOOD_ZONES = [
    # Critical â€“ historically most flood-prone
    {"name": "Brahmaputra Valley", "state": "Assam",        "lat": 26.14, "lng": 91.74, "risk": "critical", "flood_occurred": 0.94},
    {"name": "Kosi River Basin",   "state": "Bihar",        "lat": 25.60, "lng": 86.90, "risk": "critical", "flood_occurred": 0.91},
    {"name": "Guwahati",           "state": "Assam",        "lat": 26.14, "lng": 91.74, "risk": "critical", "flood_occurred": 0.90},
    {"name": "Dhubri",             "state": "Assam",        "lat": 26.02, "lng": 89.97, "risk": "critical", "flood_occurred": 0.88},
    {"name": "Lakhimpur",          "state": "Assam",        "lat": 27.23, "lng": 94.10, "risk": "critical", "flood_occurred": 0.87},
    {"name": "Patna",              "state": "Bihar",        "lat": 25.59, "lng": 85.14, "risk": "critical", "flood_occurred": 0.85},
    {"name": "Muzaffarpur",        "state": "Bihar",        "lat": 26.12, "lng": 85.38, "risk": "critical", "flood_occurred": 0.84},
    {"name": "Darbhanga",          "state": "Bihar",        "lat": 26.15, "lng": 85.89, "risk": "critical", "flood_occurred": 0.83},
    {"name": "Imphal Valley",      "state": "Manipur",      "lat": 24.82, "lng": 93.94, "risk": "critical", "flood_occurred": 0.82},
    {"name": "Shillong",           "state": "Meghalaya",    "lat": 25.58, "lng": 91.89, "risk": "critical", "flood_occurred": 0.81},
    {"name": "Agartala",           "state": "Tripura",      "lat": 23.83, "lng": 91.28, "risk": "critical", "flood_occurred": 0.80},
    # High risk
    {"name": "Kolkata",            "state": "West Bengal",  "lat": 22.57, "lng": 88.36, "risk": "high", "flood_occurred": 0.76},
    {"name": "Bhubaneswar",        "state": "Odisha",       "lat": 20.30, "lng": 85.82, "risk": "high", "flood_occurred": 0.74},
    {"name": "Puri",               "state": "Odisha",       "lat": 19.80, "lng": 85.85, "risk": "high", "flood_occurred": 0.73},
    {"name": "Cuttack â€“ Mahanadi", "state": "Odisha",       "lat": 20.46, "lng": 85.88, "risk": "high", "flood_occurred": 0.72},
    {"name": "Visakhapatnam",      "state": "Andhra Pradesh","lat": 17.69, "lng": 83.22, "risk": "high", "flood_occurred": 0.71},
    {"name": "Mumbai (Coastal)",   "state": "Maharashtra",  "lat": 19.08, "lng": 72.88, "risk": "high", "flood_occurred": 0.70},
    {"name": "Alappuzha",          "state": "Kerala",       "lat":  9.50, "lng": 76.34, "risk": "high", "flood_occurred": 0.70},
    {"name": "Kochi",              "state": "Kerala",       "lat":  9.96, "lng": 76.28, "risk": "high", "flood_occurred": 0.68},
    {"name": "Siliguri",           "state": "West Bengal",  "lat": 26.72, "lng": 88.43, "risk": "high", "flood_occurred": 0.67},
    {"name": "Gorakhpur",          "state": "Uttar Pradesh","lat": 26.76, "lng": 83.37, "risk": "high", "flood_occurred": 0.67},
    {"name": "Varanasi",           "state": "Uttar Pradesh","lat": 25.32, "lng": 83.01, "risk": "high", "flood_occurred": 0.65},
    {"name": "Ganga Plains (Allahabad)","state": "Uttar Pradesh","lat": 25.43, "lng": 81.85, "risk": "high", "flood_occurred": 0.64},
    {"name": "Srinagar",           "state": "J&K",          "lat": 34.08, "lng": 74.80, "risk": "high", "flood_occurred": 0.63},
    {"name": "Rajahmundry",        "state": "Andhra Pradesh","lat": 17.00, "lng": 81.78, "risk": "high", "flood_occurred": 0.62},
    {"name": "Sundarbans Delta",   "state": "West Bengal",  "lat": 21.94, "lng": 88.90, "risk": "high", "flood_occurred": 0.62},
    # Moderate risk
    {"name": "Chennai",            "state": "Tamil Nadu",   "lat": 13.08, "lng": 80.27, "risk": "moderate", "flood_occurred": 0.55},
    {"name": "Hyderabad",          "state": "Telangana",    "lat": 17.39, "lng": 78.49, "risk": "moderate", "flood_occurred": 0.52},
    {"name": "Thiruvananthapuram", "state": "Kerala",       "lat":  8.52, "lng": 76.94, "risk": "moderate", "flood_occurred": 0.51},
    {"name": "Pune",               "state": "Maharashtra",  "lat": 18.52, "lng": 73.86, "risk": "moderate", "flood_occurred": 0.50},
    {"name": "Nagpur",             "state": "Maharashtra",  "lat": 21.15, "lng": 79.09, "risk": "moderate", "flood_occurred": 0.49},
    {"name": "Konkan Coast",       "state": "Maharashtra",  "lat": 16.80, "lng": 73.50, "risk": "moderate", "flood_occurred": 0.48},
    {"name": "Surat",              "state": "Gujarat",      "lat": 21.17, "lng": 72.83, "risk": "moderate", "flood_occurred": 0.46},
    {"name": "Bengaluru",          "state": "Karnataka",    "lat": 12.97, "lng": 77.59, "risk": "moderate", "flood_occurred": 0.44},
    {"name": "Dehradun",           "state": "Uttarakhand",  "lat": 30.32, "lng": 78.03, "risk": "moderate", "flood_occurred": 0.43},
    {"name": "Haridwar",           "state": "Uttarakhand",  "lat": 29.94, "lng": 78.16, "risk": "moderate", "flood_occurred": 0.42},
    # Low risk
    {"name": "Ahmedabad",          "state": "Gujarat",      "lat": 23.02, "lng": 72.57, "risk": "low", "flood_occurred": 0.28},
    {"name": "Jaipur",             "state": "Rajasthan",    "lat": 26.91, "lng": 75.79, "risk": "low", "flood_occurred": 0.18},
    {"name": "Delhi",              "state": "Delhi",        "lat": 28.61, "lng": 77.21, "risk": "low", "flood_occurred": 0.30},
    {"name": "Lucknow",            "state": "Uttar Pradesh","lat": 26.85, "lng": 80.95, "risk": "low", "flood_occurred": 0.32},
]

@app.route("/api/flood-risk-zones", methods=["GET"])
def flood_zones():
    # India bounding box: lat 6â€“37, lng 68â€“97
    INDIA_LAT = (6.0, 37.5)
    INDIA_LNG = (68.0, 97.5)

    # Filter strictly to India and return named zones
    zones = [
        z for z in INDIA_FLOOD_ZONES
        if INDIA_LAT[0] <= z["lat"] <= INDIA_LAT[1]
        and INDIA_LNG[0] <= z["lng"] <= INDIA_LNG[1]
    ]
    return jsonify({"zones": zones, "total": len(zones)})



# â”€â”€ 7. Health check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/status", methods=["GET"])
def status():
    db_ok = False
    db_error = None
    if mysql_available:
        try:
            ensure_db_schema()
            db_ok = True
        except Exception as e:
            db_error = str(e)
    return jsonify({
        "status": "running",
        "ml_model": "ready" if ml_ready else f"unavailable ({ml_error})",
        "db": {"mysql_driver": mysql_available, "connected": db_ok, "error": db_error},
        "endpoints": ["/api/predict", "/api/weather", "/api/forecast",
                      "/api/rainfall", "/api/soil", "/api/flood-risk-zones",
                      "/api/auth/register", "/api/auth/login", "/api/prefs", "/api/settings", "/api/db/status"]
    })

# â”€â”€ 8. Send Notification (Email + SMS) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/notify", methods=["POST"])
def notify():
    """Send real email (SMTP) and/or SMS (Twilio) flood alert."""
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    email   = body.get("email", "").strip()
    phone   = body.get("phone", "").strip()
    user_id = body.get("user_id")
    risk    = email_safe_text(body.get("risk", "moderate"))
    label   = email_safe_text(body.get("label", "FLOOD ALERT"))
    message = email_safe_text(body.get("message", "A flood warning has been issued for your area."))
    city    = email_safe_text(body.get("city", "your area"))

    results = {"email_sent": False, "sms_sent": False, "errors": []}

    # â”€â”€ Email via SMTP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if email:
        if not smtp_configured():
            results["errors"].append("Email credentials missing. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM.")
        else:
            try:
                risk_colors = {
                    "low": "#22c55e", "moderate": "#f59e0b",
                    "high": "#f97316", "critical": "#ef4444"
                }
                color = risk_colors.get(risk, "#0ea5e9")

                html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="max-width:600px;margin:30px auto;background:#ffffff;
                border-radius:12px;overflow:hidden;
                box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <!-- Header -->
    <tr><td style="background:linear-gradient(135deg,#0c1a2e,#0a3a5c);padding:28px 32px;text-align:center;">
      <div style="font-size:28px;margin-bottom:6px;">Flood</div>
      <div style="color:#ffffff;font-size:22px;font-weight:700;letter-spacing:1px;">FloodGuard India</div>
      <div style="color:rgba(255,255,255,0.6);font-size:13px;margin-top:4px;">Early Flood Warning System</div>
    </td></tr>
    <!-- Risk Badge -->
    <tr><td style="padding:24px 32px 0;">
      <div style="display:inline-block;background:{color}1a;border:2px solid {color};
                  border-radius:50px;padding:8px 22px;">
        <span style="color:{color};font-weight:700;font-size:15px;">ALERT: {label}</span>
      </div>
    </td></tr>
    <!-- Body -->
    <tr><td style="padding:20px 32px;">
      <p style="font-size:16px;color:#1e293b;line-height:1.6;margin:0 0 12px;">
        A flood risk alert has been detected for <strong>{city}</strong>.
      </p>
      <p style="font-size:15px;color:#334155;line-height:1.6;margin:0 0 10px;">
        <strong>Flood Risk:</strong> {risk.upper()}
      </p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 20px;">{message}</p>
      <div style="background:#f8fafc;border-left:4px solid {color};border-radius:4px;
                  padding:14px 18px;margin:20px 0;">
        <p style="margin:0;font-size:13px;color:#64748b;">Stay safe and follow official instructions.
        Call NDRF helpline: <strong>9711077372</strong> | Disaster Management: <strong>1078</strong></p>
      </div>
    </td></tr>
    <!-- Footer -->
    <tr><td style="background:#f8fafc;padding:16px 32px;text-align:center;
                   border-top:1px solid #e2e8f0;">
      <p style="margin:0;font-size:12px;color:#94a3b8;">
        This is an automated alert from FloodGuard India Early Warning System.<br>
        Do not reply to this email.
      </p>
    </td></tr>
  </table>
</body>
</html>"""

                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"FloodGuard Alert - {label} in {city}"
                msg["From"]    = SMTP_FROM
                msg["To"]      = email
                msg.attach(MIMEText(
                    f"FloodGuard Alert\n\nCity: {city}\nFlood Risk: {risk.upper()}\n{label}\n\n{message}\n\n"
                    f"Stay safe. NDRF: 9711077372 | Disaster Mgmt: 1078", "plain"))
                msg.attach(MIMEText(html_body, "html"))

                used_mode = send_email_smtp(email, msg)
                results["email_sent"] = True
                results["email_mode"] = used_mode
            except Exception as e:
                results["errors"].append(f"Email error: {e}")

    # â”€â”€ SMS via Twilio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if phone:
        if not SMS_NOTIFICATIONS_ENABLED:
            results["errors"].append("SMS notifications are temporarily disabled.")
        elif not twilio_configured():
            results["errors"].append("Twilio credentials missing. Set TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM.")
        else:
            try:
                from twilio.rest import Client as TwilioClient
                sms_body = (
                    f"[FloodGuard India] {label} - {city}\n"
                    f"{message}\n"
                    f"NDRF: 9711077372 | Disaster Mgmt: 1078"
                )
                client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
                # Ensure phone has country code
                to_phone = phone if phone.startswith("+") else f"+91{phone}"
                client.messages.create(body=sms_body, from_=TWILIO_FROM, to=to_phone)
                results["sms_sent"] = True
            except ImportError:
                results["errors"].append("Twilio not installed. Run: pip install twilio")
            except Exception as e:
                results["errors"].append(f"SMS error: {e}")

    if not email and not phone:
        return jsonify({"error": "Provide email and/or phone"}), 400

    if email:
        log_notification_event(
            user_id=user_id,
            channel="email",
            recipient=email,
            subject=f"FloodGuard Alert - {label} in {city}",
            body=message,
            status="sent" if results["email_sent"] else "failed",
            error_msg="; ".join([e for e in results["errors"] if e.startswith("Email")]) or None,
            risk_level=risk,
            city=city,
        )
    if phone and SMS_NOTIFICATIONS_ENABLED:
        log_notification_event(
            user_id=user_id,
            channel="sms",
            recipient=phone if phone.startswith("+") else f"+91{phone}",
            subject=f"FloodGuard SMS Alert - {label} in {city}",
            body=message,
            status="sent" if results["sms_sent"] else "failed",
            error_msg="; ".join([e for e in results["errors"] if e.startswith("SMS") or e.startswith("Twilio")]) or None,
            risk_level=risk,
            city=city,
        )

    # Track consolidated alert outcome in requested alerts table.
    try:
        overall_status = "sent" if (results["email_sent"] or results["sms_sent"]) else "failed"
        if results["email_sent"] and results["sms_sent"]:
            overall_status = "sent"
        elif results["email_sent"] or results["sms_sent"]:
            overall_status = "partial" if results["errors"] else "sent"
        persist_alert_record(city=city, message=message, alert_type="system", status=overall_status, prediction_id=body.get("prediction_id"))
    except Exception:
        pass

    status_code = 200 if (results["email_sent"] or results["sms_sent"]) else 207
    return jsonify(results), status_code




# ============================================================
#  DATABASE ENDPOINTS
# ============================================================

def db_error_response(e):
    """Consistent error response for DB failures."""
    msg = str(e)
    if "mysql-connector-python" in msg or "not installed" in msg:
        return jsonify({"error": "DB driver missing. Run: pip install mysql-connector-python"}), 503
    if "Access denied" in msg or "Unknown database" in msg:
        return jsonify({"error": f"DB connection failed: {msg}. Check DB_*/MYSQL_* environment variables"}), 503
    return jsonify({"error": f"Database error: {msg}"}), 500


# â”€â”€ 9. Register â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def log_notification_event(user_id, channel, recipient, subject, body, status, error_msg, risk_level, city):
    """Best-effort audit logging for notification attempts."""
    if not mysql_available:
        return
    try:
        ensure_db_schema()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notification_log "
            "(user_id, channel, recipient, subject, body, status, error_msg, risk_level, city) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                int(user_id) if user_id else None,
                channel,
                recipient,
                subject,
                body,
                status,
                error_msg,
                risk_level,
                city,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


def log_auth_event(user_id, action, entity_id, ip_address):
    """Best-effort auth audit logging."""
    if not mysql_available:
        return
    try:
        ensure_db_schema()
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (user_id, action, entity, entity_id, timestamp, ip_address) "
            "VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), %s)",
            (
                int(user_id) if user_id else None,
                action,
                "users",
                str(entity_id) if entity_id is not None else None,
                ip_address,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


@app.route("/api/auth/register", methods=["POST"])
def register():
    data  = request.get_json() or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    age   = data.get("age")
    password = data.get("password") or ""

    if not all([name, email, phone, password]):
        return jsonify({"error": "name, email, phone, password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not bcrypt_available:
        return jsonify({"error": "bcrypt not installed. Run: pip install bcrypt"}), 503

    try:
        ensure_db_schema()
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
        conn = get_db(); cur = conn.cursor()
        # Check duplicate email
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"error": "Email already registered"}), 409

        cur.execute(
            "INSERT INTO users (name, email, phone, age, password_hash, email_alert, sms_alert) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, email, phone, age, pw_hash,
             int(data.get("emailAlert", True)), int(data.get("smsAlert", True)))
        )
        user_id = cur.lastrowid
        # Create default alert preferences
        cur.execute(
            "INSERT INTO alert_preferences (user_id, email_enabled, sms_enabled, threshold_level, alert_email, alert_phone) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, int(data.get("emailAlert", True)), int(data.get("smsAlert", True)),
             "moderate", email, phone)
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success": True, "user": {"id": user_id, "name": name, "email": email, "phone": phone}}), 201
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 10. Login â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/auth/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    city     = (data.get("city") or "").strip()
    ip_addr  = request.headers.get("X-Forwarded-For", request.remote_addr)

    # Demo bypass (no DB needed)
    if email == "demo@floodguard.in" and password in ("demo1234", "demo123"):
        log_auth_event(user_id=0, action="login_success_demo", entity_id=email, ip_address=ip_addr)
        return jsonify({"success": True, "user": {
            "id": 0, "name": "Demo User", "email": email, "phone": "9000000000"
        }}), 200

    if not bcrypt_available:
        return jsonify({"error": "bcrypt not installed. Run: pip install bcrypt"}), 503

    try:
        ensure_db_schema()
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND is_active=1", (email,))
        user = cur.fetchone()
        if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            found_user_id = user["id"] if user else None
            cur.close(); conn.close()
            log_auth_event(user_id=found_user_id, action="login_failed", entity_id=email, ip_address=ip_addr)
            return jsonify({"error": "Invalid email or password"}), 401

        # Ensure user_settings row exists for every logged-in user.
        cur.execute(
            """
            INSERT INTO user_settings (user_id, theme, language)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE updated_at=updated_at
            """,
            (user["id"], "light", "en"),
        )

        # Fallback to user's saved city if city not provided in login payload.
        if not city:
            cur.execute(
                "SELECT last_city FROM user_settings WHERE user_id=%s LIMIT 1",
                (user["id"],),
            )
            row = cur.fetchone() or {}
            city = (row.get("last_city") or "").strip()

        # Update last_login
        cur.execute("UPDATE users SET last_login=UTC_TIMESTAMP() WHERE id=%s", (user["id"],))
        conn.commit(); cur.close(); conn.close()
        log_auth_event(user_id=user["id"], action="login_success", entity_id=email, ip_address=ip_addr)

        admin_alert = maybe_notify_admin_login(user_id=user["id"], user_name=user.get("name"), city=city)

        return jsonify({"success": True, "user": {
            "id": user["id"], "name": user["name"],
            "email": user["email"], "phone": user["phone"]
        }, "admin_alert": admin_alert}), 200
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 11. Alert Preferences: GET + POST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/prefs", methods=["GET", "POST"])
def alert_prefs():
    user_id = request.args.get("user_id") or (request.get_json() or {}).get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    try:
        ensure_db_schema()
        conn = get_db(); cur = conn.cursor(dictionary=True)

        if request.method == "GET":
            cur.execute("SELECT * FROM alert_preferences WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            cur.close(); conn.close()
            if not row:
                return jsonify({"error": "No preferences found"}), 404
            # Remove internal id/user_id from response
            row.pop("id", None); row.pop("user_id", None)
            return jsonify(row), 200

        # POST â€“ upsert preferences
        data = request.get_json() or {}
        cur.execute(
            "INSERT INTO alert_preferences "
            "(user_id, email_enabled, sms_enabled, browser_enabled, threshold_level, alert_email, alert_phone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "email_enabled=VALUES(email_enabled), sms_enabled=VALUES(sms_enabled), "
            "browser_enabled=VALUES(browser_enabled), threshold_level=VALUES(threshold_level), "
            "alert_email=VALUES(alert_email), alert_phone=VALUES(alert_phone)",
            (user_id,
             int(data.get("email_enabled", 1)), int(data.get("sms_enabled", 1)),
             int(data.get("browser_enabled", 0)),
             data.get("threshold_level", "moderate"),
             data.get("alert_email"), data.get("alert_phone"))
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 12. User Settings: GET + POST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/settings", methods=["GET", "POST"])
def user_settings():
    user_id = request.args.get("user_id") or (request.get_json() or {}).get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    try:
        ensure_db_schema()
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        if request.method == "GET":
            cur.execute("SELECT * FROM user_settings WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            if not row:
                return jsonify({"error": "No settings found"}), 404
            row.pop("id", None)
            row.pop("user_id", None)
            return jsonify(row), 200

        data = request.get_json() or {}
        last_city = (data.get("last_city") or "").strip()
        cur.execute(
            """
            INSERT INTO user_settings
            (user_id, theme, language, last_city, last_location, last_lat, last_lng)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            theme=COALESCE(VALUES(theme), theme),
            language=COALESCE(VALUES(language), language),
            last_city=COALESCE(VALUES(last_city), last_city),
            last_location=COALESCE(VALUES(last_location), last_location),
            last_lat=COALESCE(VALUES(last_lat), last_lat),
            last_lng=COALESCE(VALUES(last_lng), last_lng)
            """,
            (
                user_id,
                data.get("theme"),
                data.get("language"),
                last_city,
                data.get("last_location"),
                data.get("last_lat"),
                data.get("last_lng"),
            ),
        )
        admin_alert = None
        if last_city:
            try:
                cur.execute("SELECT name FROM users WHERE id=%s LIMIT 1", (user_id,))
                urow = cur.fetchone() or {}
                admin_alert = maybe_notify_admin_login(
                    user_id=int(user_id),
                    user_name=urow.get("name"),
                    city=last_city,
                )
            except Exception as _e:
                admin_alert = {"triggered": False, "reason": f"settings_alert_error: {_e}"}
        conn.commit()
        cur.close()
        conn.close()
        resp = {"success": True}
        if admin_alert is not None:
            resp["admin_alert"] = admin_alert
        return jsonify(resp), 200
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 12. Log an Alert History Entry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/alerts/log", methods=["POST"])
def log_alert():
    data    = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    try:
        ensure_db_schema()
        conn = get_db(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO alert_history (user_id, risk_level, city, message) VALUES (%s, %s, %s, %s)",
            (user_id, data.get("risk_level", "info"), data.get("city", ""), data.get("message", ""))
        )
        conn.commit(); cur.close(); conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 13. Get Alert History â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/alerts/history", methods=["GET"])
def get_alert_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    try:
        ensure_db_schema()
        conn = get_db(); cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT risk_level AS level, city, message AS msg, "
            "DATE_FORMAT(sent_at, '%d %b %Y, %H:%i') AS time "
            "FROM alert_history WHERE user_id=%s "
            "ORDER BY sent_at DESC LIMIT 30",
            (user_id,)
        )
        rows = cur.fetchall(); cur.close(); conn.close()
        return jsonify({"history": rows}), 200
    except Exception as e:
        return db_error_response(e)


# â”€â”€ 14. DB Status Check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@app.route("/api/db/status", methods=["GET"])
def db_status():
    if not mysql_available:
        return jsonify({"connected": False, "error": "mysql-connector-python not installed"}), 503
    try:
        ensure_db_schema()
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        cur.close(); conn.close()
        return jsonify({"connected": True, "users": count, "database": DB_NAME}), 200
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 503


if __name__ == "__main__":
    print("=" * 50)
    print("  FloodGuard India - API Server")
    print("=" * 50)
    print(f"[Notify] SMTP configured: {smtp_configured()}")
    print("Starting ML model in background thread...")
    _start_ml_background()  # Non-blocking â€“ API starts immediately
    if mysql_available:
        try:
            ensure_db_schema()
            print(f"[DB] MySQL connected and schema ready: {DB_NAME}")
        except Exception as e:
            print(f"[DB] MySQL not ready: {e}")
    else:
        print("[DB] mysql-connector-python missing. Run: pip install mysql-connector-python")
    print("\nAPI running at: http://127.0.0.1:5000  (local)")
    print("API running at: http://192.168.1.16:5000  (phone/LAN)")
    print("Open frontend/index.html in your browser.\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)




