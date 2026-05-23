"""
Environment-based configuration.

Operational settings live in the dashboard. Bootstrap signing secrets may be
provided through environment variables, but production installs can also start
plug-and-play: default/blank secrets are replaced with random values persisted
in the app data volume.
"""
import json
import os
import secrets
from datetime import timedelta
from pathlib import Path

# Load .env from the config/ directory when running locally
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / "config" / ".env"
    load_dotenv(dotenv_path=env_file)
except ImportError:
    pass  # python-dotenv optional; rely on real env vars in production


_AUTO_GENERATE_SECRET_VALUES = {
    "",
    "change-me",
    "invisible-key-default-secret-key-change-me",
    "invisible-key-default-jwt-key-change-me",
}
_BOOTSTRAP_SECRETS = None


def _bootstrap_secret_file() -> Path:
    override = os.getenv("BOOTSTRAP_SECRETS_FILE", "").strip()
    if override:
        return Path(override)
    return Path(__file__).parent / "instance" / "data" / "bootstrap_secrets.json"


def _load_or_create_bootstrap_secrets() -> dict:
    global _BOOTSTRAP_SECRETS
    if _BOOTSTRAP_SECRETS is not None:
        return _BOOTSTRAP_SECRETS

    path = _bootstrap_secret_file()
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

    changed = False
    for key in ("secret_key", "jwt_secret_key"):
        if not isinstance(data.get(key), str) or len(data[key]) < 32:
            data[key] = secrets.token_hex(32)
            changed = True

    if changed or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass

    _BOOTSTRAP_SECRETS = data
    return data


def _get_signing_secret(env_name: str, store_key: str) -> str:
    value = os.getenv(env_name, "").strip()
    if value and value not in _AUTO_GENERATE_SECRET_VALUES:
        return value
    return _load_or_create_bootstrap_secrets()[store_key]


class Config:
    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY: str = _get_signing_secret("SECRET_KEY", "secret_key")
    DEBUG: bool = os.getenv("FLASK_ENV", "production") == "development"

    # ── Database ─────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///instance/data/invisible_key.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = _get_signing_secret("JWT_SECRET_KEY", "jwt_secret_key")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(hours=8)

    # ── CORS ─────────────────────────────────────────────────
    # In production limit to your actual origins
    CORS_ORIGINS: list = ["*"]

    # ── Admin bootstrap ──────────────────────────────────────
    # All operational secrets (admin/cleaner credentials, WiFi, SMTP, etc.) are now managed via the dashboard and loaded from the database at runtime.

    # ── Hotspot ──────────────────────────────────────────────
    HOTSPOT_SSID: str = os.getenv("HOTSPOT_SSID", "InvisibleKeySetup")
    HOTSPOT_PASSPHRASE: str = os.getenv("HOTSPOT_PASSPHRASE", "invisiblekey123")
    HOTSPOT_IP: str = os.getenv("HOTSPOT_IP", "192.168.50.1")
    HOTSPOT_DHCP_RANGE: str = os.getenv(
        "HOTSPOT_DHCP_RANGE", "192.168.50.10,192.168.50.50"
    )

    # ── ngrok ────────────────────────────────────────────────
    NGROK_AUTHTOKEN: str = os.getenv("NGROK_AUTHTOKEN", "")
    NGROK_STATIC_DOMAIN: str = os.getenv("NGROK_STATIC_DOMAIN", "")

    # ── iCal Calendar ────────────────────────────────────────
    ICAL_URL: str = os.getenv("ICAL_URL", "")
    ICAL_GUEST_PASSWORD: str = os.getenv("ICAL_GUEST_PASSWORD", "")
    # Guest rotation schedule (HH:MM, 24h)
    CHECKOUT_TIME: str = os.getenv("CHECKOUT_TIME", "12:00")  # guests lose access
    CHECKIN_TIME: str = os.getenv("CHECKIN_TIME", "14:00")    # new guest account created
    # Optional explicit timezone override (IANA name, e.g. Europe/Lisbon).
    # If blank, runtime system timezone detection is used.
    APP_TIMEZONE: str = os.getenv("APP_TIMEZONE", "")
    CALENDAR_GUEST_DEFAULT_PASSWORD: str = os.getenv("CALENDAR_GUEST_DEFAULT_PASSWORD", "guest12345")
    CALENDAR_SYNC_ENABLED: bool = os.getenv("CALENDAR_SYNC_ENABLED", "true").strip().lower() in ("1", "true", "yes", "on")
    CALENDAR_SYNC_INTERVAL: int = int(os.getenv("CALENDAR_SYNC_INTERVAL", "300"))

    # ── GPIO ─────────────────────────────────────────────────
    GPIO_MODE: str = os.getenv("GPIO_MODE", "gpiozero")
    ENABLE_GPIO: bool = os.getenv("ENABLE_GPIO", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # ── Tailscale ────────────────────────────────────────────
    TAILSCALE_SUBNET: str = os.getenv("TAILSCALE_SUBNET", "100.64.0.0/10")
    ADMIN_REQUIRE_TAILSCALE: bool = os.getenv(
        "ADMIN_REQUIRE_TAILSCALE",
        "false",
    ).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # ── Log retention ────────────────────────────────────────
    AUDIT_LOG_RETENTION_DAYS: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "180"))
    DOOR_LOG_RETENTION_DAYS: int = int(os.getenv("DOOR_LOG_RETENTION_DAYS", "90"))

    # ── Application ──────────────────────────────────────────
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "5000"))

    # ── Email/SMTP ────────────────────────────────────────────
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_RECIPIENT: str = os.getenv("EMAIL_RECIPIENT", "")
