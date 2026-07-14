import os
import io
import cv2
import numpy as np
from datetime import datetime
from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename
import jwt
from rcnn_loader import get_rcnn_model
import torch
import torch.nn as nn
from torchvision import transforms
from database import db
from models import Pothole, User
from yolo_loader import get_yolo_model
from processing import process_severity, find_duplicate_pothole

potholes_bp = Blueprint("potholes", __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "pothole_secret_key_change_in_production")


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def get_user_id_from_request():
    """Returns user_id int if valid token present, else None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(
            auth_header.split(" ")[1], SECRET_KEY, algorithms=["HS256"]
        )
        return payload.get("user_id")
    except Exception:
        return None


def get_auth_payload():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        return jwt.decode(auth_header.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None


def get_role_from_request():
    payload = get_auth_payload()
    if not payload:
        return None
    return payload.get("role")


def require_role(allowed_roles):
    payload = get_auth_payload()
    if not payload:
        return None, (jsonify({"error": "authorization required"}), 401)
    role = payload.get("role")
    if role not in allowed_roles:
        return None, (jsonify({"error": "insufficient permission"}), 403)
    return payload, None


def pothole_with_urls(pothole):
    base_url = request.host_url.rstrip("/")
    d = pothole.to_dict()
    d["imageUrl"] = f"{base_url}/uploads/{pothole.image_path}" if pothole.image_path else None
    d["afterImageUrl"] = f"{base_url}/uploads/{pothole.after_image_path}" if pothole.after_image_path else None
    return d


# ─── Detect pothole (YOLO) ────────────────────────────────────────────────────

@potholes_bp.route("/detect", methods=["POST"])
def detect_pothole():
    lat = request.form.get("latitude")
    lon = request.form.get("longitude")
    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400
    try:
        latitude  = float(lat)
        longitude = float(lon)
    except ValueError:
        return jsonify({"error": "invalid coordinates"}), 400

    image_file = request.files.get("image") or request.files.get("file")
    if not image_file or image_file.filename == "":
        return jsonify({"error": "image file required"}), 400

    image_data = image_file.read()
    if not image_data:
        return jsonify({"error": "empty image received"}), 400
    data  = np.frombuffer(image_data, dtype=np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"error": "invalid image file format"}), 400

    model = get_yolo_model()
    if not model:
        return jsonify({"error": "YOLO model not configured internally"}), 500

    results = model(frame, verbose=False)

    valid_boxes = []
    best_conf   = 0.0

    if len(results) > 0:
        boxes = results[0].boxes
        for box in boxes:
            conf = float(box.conf[0])
            if conf >= 0.25:
                if conf > best_conf:
                    best_conf = conf
                box_coords = box.xywhn[0].cpu().numpy().tolist()
                valid_boxes.append(box_coords)

    if len(valid_boxes) == 0:
        return jsonify({"detected": False})

    largest_area_ratio = max(box[2] * box[3] for box in valid_boxes)
    severity = process_severity(largest_area_ratio, best_conf)

    # ─── Duplicate check ──────────────────────────────────────────────────────
    # Admin callers never receive duplicate=True — they use the map to see all
    # markers and don't need a "pothole X metres ahead" proximity alert.
    # The DB insert is still skipped for duplicates regardless of role.
    caller_role = get_role_from_request()
    # duplicate = find_duplicate_pothole(
    #     Pothole, db.session, latitude, longitude, distance_threshold=15.0
    # )
    # Temporary: Disable duplicate detection for testing purposes
    duplicate = False
    
    if duplicate:
        return jsonify({
            "detected":   True,
            "duplicate":  caller_role != "admin",  # False for admin, True for users
            "confidence": best_conf,
            "severity":   severity,
            "boxes":      valid_boxes,
        }), 200

    row = None
    if best_conf >= 0.7:
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        safe_name  = secure_filename(image_file.filename) or "capture.jpg"
        ts         = datetime.utcnow()
        fname      = f"ph_detect_{int(ts.timestamp())}_{safe_name}"
        abs_path   = os.path.join(upload_dir, fname)
        cv2.imwrite(abs_path, frame)

        user_id = get_user_id_from_request()

        row = Pothole(
            latitude    = latitude,
            longitude   = longitude,
            timestamp   = ts,
            confidence  = best_conf,
            severity    = severity,
            image_path  = fname,
            reported_by_user_id = user_id,
            status      = "open",
        )
        db.session.add(row)
        db.session.commit()

    response_data = {
        "detected":   True,
        "duplicate":  False,
        "confidence": best_conf,
        "severity":   severity,
        "boxes":      valid_boxes,
    }
    if row:
        response_data["saved_record"] = row.to_dict()

    return jsonify(response_data), 201 if row else 200


# ─── CHANGE 1: Get all potholes — admin sees ALL statuses, users skip approved ─

@potholes_bp.route("/", methods=["GET"])
def get_potholes():
    role = get_role_from_request()
    rows = Pothole.query.order_by(Pothole.timestamp.desc()).limit(500).all()
    if role == "admin":
        res = [pothole_with_urls(r) for r in rows]           # admin sees ALL
    else:
        res = [pothole_with_urls(r) for r in rows if r.status != "approved"]  # users skip approved
    return jsonify(res)


# ─── Get potholes reported by the logged-in user ──────────────────────────────

@potholes_bp.route("/my", methods=["GET"])
def get_my_potholes():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "authorization required"}), 401
    rows = (
        Pothole.query
        .filter_by(reported_by_user_id=user_id)
        .order_by(Pothole.timestamp.desc())
        .all()
    )
    return jsonify([pothole_with_urls(r) for r in rows])


@potholes_bp.route("/user/<int:user_id>", methods=["GET"])
def get_user_potholes(user_id):
    payload, err = require_role(("user", "admin"))
    if err:
        return err
    if payload["role"] == "user" and payload["user_id"] != user_id:
        return jsonify({"error": "can only access your own reports"}), 403
    rows = (
        Pothole.query
        .filter_by(reported_by_user_id=user_id)
        .order_by(Pothole.timestamp.desc())
        .all()
    )
    return jsonify([pothole_with_urls(r) for r in rows]), 200


# ─── Update pothole status (maintenance or admin) ─────────────────────────────

@potholes_bp.route("/<int:pothole_id>/status", methods=["PATCH"])
def update_status(pothole_id):
    role = get_role_from_request()
    if role not in ("maintenance", "admin"):
        return jsonify({"error": "only maintenance or admin can update status"}), 403

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    new_status = data.get("status")
    if new_status not in ("open", "in_progress", "fixed", "awaiting_approval", "approved"):
        return jsonify({"error": "invalid status"}), 400

    pothole.status      = new_status
    pothole.status_note = data.get("note", pothole.status_note)
    pothole.updated_at  = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "status updated", "pothole": pothole.to_dict()}), 200


# ─── Assign worker (kept for backwards compat but not used in new workflow) ───

@potholes_bp.route("/<int:pothole_id>/assign", methods=["POST"])
def assign_worker(pothole_id):
    payload, err = require_role(("admin",))
    if err:
        return err

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404

    data      = request.get_json() or {}
    worker_id = data.get("worker_id")
    if not worker_id:
        return jsonify({"error": "worker_id required"}), 400

    worker = User.query.get(worker_id)
    if not worker or worker.role != "maintenance" or not worker.is_active:
        return jsonify({"error": "valid active maintenance worker required"}), 400

    pothole.assigned_to_worker_id = worker_id
    if pothole.status == "open":
        pothole.status = "in_progress"
    pothole.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "worker assigned", "pothole": pothole_with_urls(pothole)}), 200


# ─── CHANGE 3: Submit fix — assigned-worker check removed ─────────────────────

@potholes_bp.route("/<int:pothole_id>/submit-fix", methods=["POST"])
def submit_fix(pothole_id):
    payload, err = require_role(("maintenance",))
    if err:
        return err

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404

    # REMOVED: assigned_to_worker_id check — maintenance can pick up any job
    if pothole.status not in ("open", "in_progress"):
        return jsonify({"error": "can only submit a fix for open or in_progress potholes"}), 400

    after_image = request.files.get("after_image") or request.files.get("image")
    if not after_image or not after_image.filename:
        return jsonify({"error": "after_image file required"}), 400

    try:
        fix_latitude  = float(request.form.get("fix_latitude"))
        fix_longitude = float(request.form.get("fix_longitude"))
    except Exception:
        return jsonify({"error": "valid fix_latitude and fix_longitude required"}), 400

    fix_notes  = (request.form.get("fix_notes") or "").strip()
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    safe_name  = secure_filename(after_image.filename) or "after.jpg"
    ts         = datetime.utcnow()
    fname      = f"ph_fix_{int(ts.timestamp())}_{safe_name}"
    abs_path   = os.path.join(upload_dir, fname)
    after_image.save(abs_path)

    pothole.after_image_path = fname
    pothole.fix_notes        = fix_notes or None
    pothole.fix_timestamp    = ts
    pothole.fix_latitude     = fix_latitude
    pothole.fix_longitude    = fix_longitude
    pothole.status           = "awaiting_approval"
    pothole.updated_at       = ts
    db.session.commit()

    return jsonify({
        "message": "fix submitted for admin approval",
        "pothole": pothole_with_urls(pothole),
    }), 200


# ─── Approve fix ──────────────────────────────────────────────────────────────

@potholes_bp.route("/<int:pothole_id>/approve", methods=["POST"])
def approve_fix(pothole_id):
    payload, err = require_role(("admin",))
    if err:
        return err

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404
    if pothole.status != "awaiting_approval":
        return jsonify({"error": "pothole is not awaiting approval"}), 400

    ts = datetime.utcnow()
    pothole.status               = "approved"
    pothole.approved_by_admin_id = payload["user_id"]
    pothole.approval_timestamp   = ts
    pothole.updated_at           = ts
    db.session.commit()
    return jsonify({
        "message": "fix approved",
        "pothole": pothole_with_urls(pothole),
    }), 200


# ─── Reject fix ───────────────────────────────────────────────────────────────

@potholes_bp.route("/<int:pothole_id>/reject", methods=["POST"])
def reject_fix(pothole_id):
    payload, err = require_role(("admin",))
    if err:
        return err

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404
    if pothole.status != "awaiting_approval":
        return jsonify({"error": "pothole is not awaiting approval"}), 400

    pothole.status     = "in_progress"
    pothole.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        "message": "fix rejected — returned to in_progress",
        "pothole": pothole_with_urls(pothole),
    }), 200


# ─── CHANGE 2: DELETE endpoint — admin can delete approved potholes only ──────

@potholes_bp.route("/<int:pothole_id>", methods=["DELETE"])
def delete_pothole(pothole_id):
    _, err = require_role(("admin",))
    if err:
        return err

    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404
    if pothole.status != "approved":
        return jsonify({"error": "can only delete approved potholes"}), 400

    db.session.delete(pothole)
    db.session.commit()
    return jsonify({"message": "pothole deleted"}), 200


# ─── CHANGE 4: Maintenance tasks — all open/in_progress, not just assigned ───

@potholes_bp.route("/maintenance/tasks", methods=["GET"])
def maintenance_tasks():
    payload, err = require_role(("maintenance",))
    if err:
        return err

    rows = (
        Pothole.query
        .filter(Pothole.status.in_(["open", "in_progress"]))
        .order_by(Pothole.timestamp.desc())
        .all()
    )
    return jsonify([pothole_with_urls(r) for r in rows]), 200


# ─── Admin stats ──────────────────────────────────────────────────────────────

@potholes_bp.route("/admin/stats", methods=["GET"])
def admin_stats():
    _, err = require_role(("admin",))
    if err:
        return err

    total       = Pothole.query.count()
    open_count  = Pothole.query.filter_by(status="open").count()
    in_progress = Pothole.query.filter_by(status="in_progress").count()
    awaiting    = Pothole.query.filter_by(status="awaiting_approval").count()
    approved    = Pothole.query.filter_by(status="approved").count()

    return jsonify({
        "total":       total,
        "open":        open_count,
        "in_progress": in_progress,
        "pending":     open_count + awaiting,
        "awaiting_approval": awaiting,
        "fixed":       approved,
    }), 200


# ─── Admin pending approvals ──────────────────────────────────────────────────

@potholes_bp.route("/admin/pending-approvals", methods=["GET"])
def admin_pending_approvals():
    _, err = require_role(("admin",))
    if err:
        return err

    rows = (
        Pothole.query
        .filter_by(status="awaiting_approval")
        .order_by(Pothole.updated_at.desc())
        .all()
    )
    return jsonify([pothole_with_urls(r) for r in rows]), 200


# ─── Admin user management ────────────────────────────────────────────────────

@potholes_bp.route("/admin/users", methods=["GET"])
def admin_users():
    _, err = require_role(("admin",))
    if err:
        return err
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


@potholes_bp.route("/admin/users/<int:user_id>/deactivate", methods=["POST"])
def deactivate_user(user_id):
    _, err = require_role(("admin",))
    if err:
        return err
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    user.is_active = False
    db.session.commit()
    return jsonify({"message": "user deactivated", "user": user.to_dict()}), 200


# ─── Single pothole detail ────────────────────────────────────────────────────

@potholes_bp.route("/<int:pothole_id>", methods=["GET"])
def get_pothole(pothole_id):
    pothole = Pothole.query.get(pothole_id)
    if not pothole:
        return jsonify({"error": "pothole not found"}), 404
    return jsonify(pothole_with_urls(pothole)), 200


# ─── R-CNN detection ──────────────────────────────────────────────────────────

RCNN_CONF_THRESH = 0.7
RCNN_NMS_THRESH  = 0.3

rcnn_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


def rcnn_sliding_window(img_h, img_w, scales=(0.25, 0.4, 0.6), step=0.2):
    proposals = []
    for s in scales:
        bh = int(img_h * s)
        bw = int(img_w * s)
        sy = max(1, int(img_h * step))
        sx = max(1, int(img_w * step))
        for y in range(0, img_h - bh + 1, sy):
            for x in range(0, img_w - bw + 1, sx):
                proposals.append((x, y, x + bw, y + bh))
    return proposals


def rcnn_nms(boxes, scores, thresh):
    if not boxes:
        return []
    boxes  = np.array(boxes,  dtype=float)
    scores = np.array(scores, dtype=float)
    order  = scores.argsort()[::-1]
    keep   = []
    while len(order):
        i = order[0]
        keep.append(i)
        if len(order) == 1:
            break
        rest = order[1:]

        def _iou(a, b):
            xA, yA = max(a[0], b[0]), max(a[1], b[1])
            xB, yB = min(a[2], b[2]), min(a[3], b[3])
            inter  = max(0, xB - xA) * max(0, yB - yA)
            union  = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
            return inter / union if union > 0 else 0.0

        iou_vals = np.array([_iou(boxes[i], boxes[j]) for j in rest])
        order    = rest[iou_vals < thresh]
    return keep


@potholes_bp.route("/detect-rcnn", methods=["POST"])
def detect_rcnn():
    lat = request.form.get("latitude")
    lon = request.form.get("longitude")
    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400
    try:
        latitude  = float(lat)
        longitude = float(lon)
    except ValueError:
        return jsonify({"error": "invalid coordinates"}), 400

    image_file = request.files.get("image") or request.files.get("file")
    if not image_file or image_file.filename == "":
        return jsonify({"error": "image file required"}), 400

    image_data = image_file.read()
    if not image_data:
        return jsonify({"error": "empty image received"}), 400
    data  = np.frombuffer(image_data, dtype=np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "invalid image"}), 400

    rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]

    model = get_rcnn_model()
    if model is None:
        return jsonify({"error": "R-CNN model not loaded"}), 500

    device    = next(model.parameters()).device
    softmax   = nn.Softmax(dim=1)
    proposals = rcnn_sliding_window(h, w)

    crops, valid_props = [], []
    for (x1, y1, x2, y2) in proposals:
        crop = rgb[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        crops.append(rcnn_transform(crop))
        valid_props.append((x1, y1, x2, y2))

    if not crops:
        return jsonify({"detected": False}), 200

    batch = torch.stack(crops).to(device)
    with torch.no_grad():
        probs = softmax(model(batch))[:, 1].cpu().numpy()

    pos_boxes  = [valid_props[i] for i in range(len(probs)) if probs[i] >= RCNN_CONF_THRESH]
    pos_scores = [float(probs[i]) for i in range(len(probs)) if probs[i] >= RCNN_CONF_THRESH]

    if not pos_boxes:
        return jsonify({"detected": False}), 200

    kept = rcnn_nms(pos_boxes, pos_scores, RCNN_NMS_THRESH)

    norm_boxes = []
    for idx in kept:
        x1, y1, x2, y2 = pos_boxes[idx]
        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        norm_boxes.append([cx, cy, bw, bh])

    best_conf = max(pos_scores[i] for i in kept)

    # ─── Duplicate check — suppressed for admin callers ───────────────────────
    caller_role = get_role_from_request()
    duplicate = find_duplicate_pothole(
        Pothole, db.session, latitude, longitude, distance_threshold=15.0
    )
    if duplicate:
        return jsonify({
            "detected":   True,
            "duplicate":  caller_role != "admin",  # False for admin, True for users
            "confidence": best_conf,
            "boxes":      norm_boxes,
        }), 200

    row = None
    if best_conf >= RCNN_CONF_THRESH:
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        ts         = datetime.utcnow()
        fname      = f"ph_rcnn_{int(ts.timestamp())}.jpg"
        cv2.imwrite(os.path.join(upload_dir, fname), frame)

        user_id  = get_user_id_from_request()
        severity = process_severity(
            max((b[2] * b[3]) for b in norm_boxes), best_conf
        )

        row = Pothole(
            latitude            = latitude,
            longitude           = longitude,
            timestamp           = ts,
            confidence          = best_conf,
            severity            = severity,
            image_path          = fname,
            reported_by_user_id = user_id,
            status              = "open",
        )
        db.session.add(row)
        db.session.commit()

    return jsonify({
        "detected":     True,
        "duplicate":    False,
        "confidence":   best_conf,
        "boxes":        norm_boxes,
        "saved_record": row.to_dict() if row else None,
    }), 201 if row else 200