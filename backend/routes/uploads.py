"""
Image upload routes — admin can upload door photos served to the guest dashboard.
Images are stored in backend/uploads/ and served at /api/uploads/<filename>.
"""
import json
import os
from flask import Blueprint, abort, current_app, request, jsonify, send_from_directory
from PIL import Image, UnidentifiedImageError
from flask_jwt_extended import jwt_required
from utils.decorators import require_roles

uploads_bp = Blueprint("uploads", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
STORED_EXTENSION = "webp"
FALLBACK_EXTENSION = "jpg"
STORED_EXTENSIONS = (STORED_EXTENSION, FALLBACK_EXTENSION)
MAX_IMAGE_DIMENSION = 1400
WEBP_QUALITY = 78
JPEG_QUALITY = 82
DOOR_KEYS = ("building_door", "apartment_door")


def _uploads_dir():
    return os.path.join(os.path.dirname(__file__), "..", "uploads")


def _meta_path():
    return os.path.join(_uploads_dir(), "door_image_meta.json")


def _default_meta():
    return {"position_x": 50, "position_y": 50, "zoom": 1.0}


def _load_meta():
    try:
        with open(_meta_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}

    result = {}
    for key in DOOR_KEYS:
        raw = data.get(key) if isinstance(data, dict) else {}
        result[key] = _normalize_meta(raw if isinstance(raw, dict) else {})
    return result


def _save_meta(meta):
    udir = _uploads_dir()
    os.makedirs(udir, exist_ok=True)
    with open(_meta_path(), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)


def _clamp_float(value, default, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def _normalize_meta(raw):
    defaults = _default_meta()
    return {
        "position_x": _clamp_float(raw.get("position_x"), defaults["position_x"], 0, 100),
        "position_y": _clamp_float(raw.get("position_y"), defaults["position_y"], 0, 100),
        "zoom": _clamp_float(raw.get("zoom"), defaults["zoom"], 1, 2),
    }


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _prepare_image(file_storage):
    try:
        image = Image.open(file_storage.stream)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid image file.") from exc

    image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        background = Image.new("RGB", image.size, "white")
        alpha = image.convert("RGBA").getchannel("A")
        background.paste(image.convert("RGBA"), mask=alpha)
        return background

    return image.convert("RGB")


def _optimized_save(file_storage, temp_paths):
    image = _prepare_image(file_storage)

    try:
        image.save(temp_paths[STORED_EXTENSION], "WEBP", quality=WEBP_QUALITY, method=4)
        return STORED_EXTENSION
    except (OSError, ValueError, KeyError) as exc:
        current_app.logger.warning("WebP door image save failed; falling back to JPEG: %s", exc)
        try:
            os.remove(temp_paths[STORED_EXTENSION])
        except FileNotFoundError:
            pass

    image.save(temp_paths[FALLBACK_EXTENSION], "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return FALLBACK_EXTENSION


def _current_images():
    """Return current image URLs plus display metadata for both doors."""
    result = {}
    udir = _uploads_dir()
    meta = _load_meta()
    for key in DOOR_KEYS:
        found = None
        for ext in (*STORED_EXTENSIONS, *sorted(ALLOWED_EXTENSIONS - set(STORED_EXTENSIONS))):
            candidate = os.path.join(udir, f"{key}.{ext}")
            if os.path.exists(candidate):
                found = f"/api/uploads/{key}.{ext}"
                break
        result[key] = {"url": found, **meta[key]}
    return result


@uploads_bp.route("/<filename>")
def serve_image(filename):
    """Serve an uploaded image. No auth required — guests need to load these."""
    if filename == os.path.basename(_meta_path()):
        abort(404)
    return send_from_directory(_uploads_dir(), filename)


@uploads_bp.route("/images", methods=["GET"])
def get_images():
    """Return current image URLs for both doors."""
    return jsonify(_current_images()), 200


@uploads_bp.route("/images/<door_key>", methods=["POST"])
@jwt_required()
@require_roles("admin")
def upload_image(door_key):
    """Upload a door image. door_key must be 'building_door' or 'apartment_door'."""
    if door_key not in DOOR_KEYS:
        return jsonify({"error": "Invalid door key. Use 'building_door' or 'apartment_door'."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if not file.filename or not _allowed(file.filename):
        return jsonify({"error": "Invalid file type. Use jpg, png, or webp."}), 400

    udir = _uploads_dir()
    os.makedirs(udir, exist_ok=True)

    temp_paths = {
        ext: os.path.join(udir, f".{door_key}.upload.{ext}")
        for ext in STORED_EXTENSIONS
    }
    for temp_path in temp_paths.values():
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass

    try:
        saved_ext = _optimized_save(file, temp_paths)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # keep old image in place if optimization fails unexpectedly
        current_app.logger.exception("Door image upload failed: %s", exc)
        return jsonify({"error": "Could not process image."}), 500

    final_path = os.path.join(udir, f"{door_key}.{saved_ext}")
    os.replace(temp_paths[saved_ext], final_path)

    # Remove previous files for this key after the replacement succeeds.
    for old_ext in ALLOWED_EXTENSIONS | set(STORED_EXTENSIONS):
        old_path = os.path.join(udir, f"{door_key}.{old_ext}")
        if old_path != final_path and os.path.exists(old_path):
            os.remove(old_path)

    for temp_path in temp_paths.values():
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass

    meta = _load_meta()
    meta[door_key] = _default_meta()
    _save_meta(meta)

    return jsonify({"url": f"/api/uploads/{door_key}.{saved_ext}", **meta[door_key]}), 200


@uploads_bp.route("/images/<door_key>/display", methods=["PATCH"])
@jwt_required()
@require_roles("admin")
def update_image_display(door_key):
    """Save non-destructive display position/zoom for a door image."""
    if door_key not in DOOR_KEYS:
        return jsonify({"error": "Invalid door key. Use 'building_door' or 'apartment_door'."}), 400

    payload = request.get_json(silent=True) or {}
    meta = _load_meta()
    meta[door_key] = _normalize_meta(payload)
    _save_meta(meta)

    return jsonify(meta[door_key]), 200
