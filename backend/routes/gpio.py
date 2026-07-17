"""GPIO routes."""
import threading
import time

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import current_app

from services import gpio_service
from services.audit_service import get_request_metadata, log_event
from utils.decorators import require_roles
from utils.guest_access import guest_stay_has_ended

gpio_bp = Blueprint("gpio", __name__)
MAX_PULSE_SECONDS = 30


@gpio_bp.route("/pins", methods=["GET"])
@jwt_required()
@require_roles("admin")
def list_pins():
    pins = gpio_service.get_all_pins()
    # Sync live hardware state into DB before returning so the UI is accurate
    result = []
    for p in pins:
        try:
            gpio_service.read_pin_state(p.pin_number)  # syncs live→DB
        except Exception:
            pass
        result.append(p.to_dict())
    return jsonify(result), 200


@gpio_bp.route("/pins", methods=["POST"])
@jwt_required()
@require_roles("admin")
def add_pin():
    data = request.get_json(silent=True) or {}
    pin_number = data.get("pin_number")
    label = data.get("label", "")
    direction = data.get("direction", "output")

    if pin_number is None:
        return jsonify({"error": "pin_number is required."}), 400

    try:
        pin = gpio_service.configure_pin(int(pin_number), label, direction)
    except (ValueError, Exception) as exc:
        return jsonify({"error": str(exc)}), 400

    admin_id = int(get_jwt_identity())
    log_event("gpio_pin_added", user_id=admin_id, detail={"pin": pin_number, "label": label})
    return jsonify(pin.to_dict()), 201


@gpio_bp.route("/pins/<int:pin_number>", methods=["GET"])
@jwt_required()
@require_roles("admin")
def get_pin(pin_number):
    try:
        state = gpio_service.read_pin_state(pin_number)
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify({"pin_number": pin_number, "state": state}), 200


@gpio_bp.route("/pins/<int:pin_number>/toggle", methods=["POST"])
@jwt_required()
@require_roles("admin")
def toggle_pin(pin_number):
    from models.user import User
    from services.email_service import format_button_notification_body, send_notification_email
    claims = get_jwt()
    role = claims.get("role")
    user_id = int(get_jwt_identity())

    try:
        current_state = gpio_service.read_pin_state(pin_number)
        pin = gpio_service.set_pin_state(pin_number, not current_state)
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # Gather details for email
    user = User.query.get(user_id)
    if user and guest_stay_has_ended(user.valid_until, app=current_app):
        return jsonify({"error": "Your stay has ended."}), 403
    button_label = getattr(pin, "label", f"Pin {pin_number}")
    action = "Unlocked" if pin.state else "Locked"
    subject = f"[Invisible Key] {action} by {user.username}"
    body = format_button_notification_body(
        user=user,
        button=button_label,
        action=action,
        pin_number=pin_number,
        request_meta=get_request_metadata(),
    )
    try:
        send_notification_email(subject, body)
    except Exception as e:
        # Log but do not block the action
        print(f"[Email] Failed to send notification: {e}")

    log_event("gpio_toggle", user_id=user_id, detail={"pin": pin_number, "new_state": pin.state})
    return jsonify(pin.to_dict()), 200


@gpio_bp.route("/pins/<int:pin_number>/set", methods=["POST"])
@jwt_required()
@require_roles("admin")
def set_pin(pin_number):
    """Explicitly set a pin to ON or OFF. Used for reliable pulse control."""
    data = request.get_json(silent=True) or {}
    state = data.get("state")
    if state is None:
        return jsonify({"error": "state (true/false) is required."}), 400
    try:
        pin = gpio_service.set_pin_state(pin_number, bool(state))
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(pin.to_dict()), 200


@gpio_bp.route("/pins/<int:pin_number>/pulse", methods=["POST"])
@jwt_required()
def pulse_pin(pin_number):
    """Turn an output on briefly, then force it off server-side."""
    from models.user import User

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({"error": "User is inactive."}), 403
    if user.role not in ("admin", "master", "user", "cleaner", "guest"):
        return jsonify({"error": "Insufficient permissions."}), 403
    if user.role == "guest" and guest_stay_has_ended(user.valid_until, app=current_app):
        return jsonify({"error": "Your stay has ended."}), 403

    data = request.get_json(silent=True) or {}
    requested = data.get("duration", 5)
    try:
        duration = min(max(float(requested), 0.1), MAX_PULSE_SECONDS)
        current_app.logger.info(
            "GPIO pulse start requested: pin=%s duration=%s user_id=%s role=%s",
            pin_number,
            duration,
            user_id,
            user.role,
        )
        pin = gpio_service.set_pin_state(pin_number, True)
    except (TypeError, ValueError) as exc:
        current_app.logger.warning("GPIO pulse rejected: pin=%s error=%s", pin_number, exc)
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        current_app.logger.warning("GPIO pulse pin missing: pin=%s error=%s", pin_number, exc)
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        current_app.logger.exception("GPIO pulse failed while turning on: pin=%s", pin_number)
        return jsonify({"error": "GPIO pulse failed."}), 500

    app = current_app._get_current_object()

    button_label = getattr(pin, "label", "") or f"Pin {pin_number}"
    actor_username = user.username
    actor_role = user.role
    request_meta = get_request_metadata()

    def turn_off_later() -> None:
        time.sleep(duration)
        with app.app_context():
            try:
                gpio_service.set_pin_state(pin_number, False)
                app.logger.info("GPIO pulse ended: pin=%s duration=%s", pin_number, duration)
                log_event("gpio_pulse_ended", detail={"pin": pin_number, "duration": duration})
            except Exception as exc:
                app.logger.exception("Failed to end GPIO%s pulse: %s", pin_number, exc)

    def notify_unlock_later() -> None:
        with app.app_context():
            try:
                from types import SimpleNamespace
                from services.email_service import format_button_notification_body, send_notification_email

                actor = SimpleNamespace(username=actor_username, role=actor_role)
                log_event(
                    "button_press",
                    user_id=user_id,
                    detail={"button": button_label, "pin": pin_number, "duration": duration},
                )
                subject = f"[Invisible Key] {button_label} pressed by {actor_username}"
                body = format_button_notification_body(
                    user=actor,
                    button=button_label,
                    action="Pressed",
                    pin_number=pin_number,
                    request_meta=request_meta,
                )
                send_notification_email(subject, body)
            except Exception:
                app.logger.exception(
                    "Failed to send GPIO pulse notification: pin=%s user_id=%s",
                    pin_number,
                    user_id,
                )

    threading.Thread(target=turn_off_later, daemon=True).start()
    current_app.logger.info("GPIO pulse accepted: pin=%s duration=%s", pin_number, duration)
    log_event("gpio_pulse_started", user_id=user_id, detail={"pin": pin_number, "duration": duration})
    threading.Thread(target=notify_unlock_later, daemon=True).start()
    return jsonify({**pin.to_dict(), "pulse_duration": duration}), 200



@gpio_bp.route("/pins/<int:pin_number>", methods=["DELETE"])
@jwt_required()
@require_roles("admin")
def delete_pin(pin_number):
    try:
        gpio_service.delete_pin(pin_number)
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404

    admin_id = int(get_jwt_identity())
    log_event("gpio_pin_deleted", user_id=admin_id, detail={"pin": pin_number})
    return jsonify({"message": f"Pin BCM{pin_number} removed."}), 200
