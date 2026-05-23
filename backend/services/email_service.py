"""
Email sending utility for notifications.
"""
import smtplib
from email.mime.text import MIMEText
from flask import current_app

def send_notification_email(subject: str, body: str):
    smtp_host = current_app.config.get("SMTP_HOST")
    smtp_port = int(current_app.config.get("SMTP_PORT", 587))
    smtp_user = current_app.config.get("SMTP_USER")
    smtp_pass = current_app.config.get("SMTP_PASS")
    sender = current_app.config.get("EMAIL_SENDER")
    recipient = current_app.config.get("EMAIL_RECIPIENT")
    print(f"[Email Debug] SMTP_HOST={smtp_host}")
    print(f"[Email Debug] SMTP_PORT={smtp_port}")
    print(f"[Email Debug] SMTP_USER={smtp_user}")
    print(f"[Email Debug] SMTP_PASS={'***' if smtp_pass else None}")
    print(f"[Email Debug] EMAIL_SENDER={sender}")
    print(f"[Email Debug] EMAIL_RECIPIENT={recipient}")
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass, sender, recipient]):
        print("[Email Debug] Missing SMTP or email config!")
        raise RuntimeError("Missing SMTP or email config.")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender, [recipient], msg.as_string())
        print("[Email Debug] Email sent successfully.")
    except Exception as e:
        print(f"[Email Debug] Exception: {e}")
        raise


def format_button_notification_body(
    *,
    user,
    button: str,
    action: str = "Pressed",
    pin_number=None,
    request_meta=None,
) -> str:
    """Build a detailed plain-text notification for door button activity."""
    from utils.timezone_utils import get_effective_timezone_info, local_now

    meta = request_meta or {}
    client = meta.get("client") or {}
    local_time = local_now(current_app).isoformat(timespec="seconds")
    timezone_info = get_effective_timezone_info(current_app)

    lines = [
        "Invisible Key button activity",
        "",
        f"Time: {local_time} ({timezone_info['name']})",
        f"User: {getattr(user, 'username', 'Unknown')}",
        f"Role: {getattr(user, 'role', 'Unknown')}",
        f"Button: {button or 'Unknown'}",
        f"Action: {action}",
    ]

    if pin_number is not None:
        lines.append(f"GPIO pin: {pin_number}")

    lines.extend([
        "",
        "Client details",
        f"IP address: {meta.get('ip') or 'Unknown'}",
        f"Device: {client.get('device') or 'Unknown'}",
        f"OS: {client.get('os') or 'Unknown'}",
        f"Browser: {client.get('browser') or 'Unknown'}",
        f"Language: {client.get('language') or 'Unknown'}",
        f"Accept-Language: {client.get('accept_language') or 'Unknown'}",
        f"Request: {client.get('method') or 'Unknown'} {client.get('path') or 'Unknown'}",
        f"User-Agent: {meta.get('user_agent') or 'Unknown'}",
    ])

    return "\n".join(lines)
