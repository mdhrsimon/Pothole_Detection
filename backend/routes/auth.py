from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import jwt
import os

from database import db
from models import User

auth_bp = Blueprint("auth", __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "pothole_secret_key_change_in_production")
TOKEN_EXPIRY_DAYS = 30


def generate_token(user):
    payload = {
        "user_id": user.id,
        "email":   user.email,
        "role":    user.role,
        "exp":     datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """Returns decoded payload or raises exception."""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


# ─── Register ─────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    username = data.get("username", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate
    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400

    # Check duplicate email
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    role = data.get("role", "user")
    if role != "user":
        return jsonify({"error": "only user self-registration is allowed"}), 403

    user = User(username=username, email=email, role="user", is_active=True)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)
    return jsonify({
        "message": "registered successfully",
        "token":   token,
        "user":    user.to_dict(),
    }), 201


# ─── Login ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    selected_role = data.get("role", "user")
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if selected_role not in ("user", "admin", "maintenance"):
        return jsonify({"error": "invalid role selected"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "account is deactivated"}), 403
    if user.role != selected_role:
        return jsonify({"error": "selected role does not match this account"}), 403

    token = generate_token(user)
    return jsonify({
        "message": "login successful",
        "token":   token,
        "user":    user.to_dict(),
    }), 200


# ─── Get current user (verify token) ─────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "authorization header required"}), 401
    try:
        payload = decode_token(auth_header.split(" ")[1])
        user = User.query.get(payload["user_id"])
        if not user:
            return jsonify({"error": "user not found"}), 404
        if not user.is_active:
            return jsonify({"error": "account is deactivated"}), 403
        return jsonify({"user": user.to_dict()}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "token expired"}), 401
    except Exception:
        return jsonify({"error": "invalid token"}), 401


@auth_bp.route("/admin/create-account", methods=["POST"])
def admin_create_account():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "authorization header required"}), 401
    try:
        payload = decode_token(auth_header.split(" ")[1])
        admin = User.query.get(payload["user_id"])
        if not admin or admin.role != "admin":
            return jsonify({"error": "admin access required"}), 403
    except Exception:
        return jsonify({"error": "invalid token"}), 401

    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")

    if role not in ("admin", "maintenance"):
        return jsonify({"error": "role must be admin or maintenance"}), 400
    if not username or not email or not password:
        return jsonify({"error": "username, email and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(username=username, email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "account created", "user": user.to_dict()}), 201