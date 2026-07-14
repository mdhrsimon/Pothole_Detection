import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from database import db
from routes.potholes import potholes_bp
from routes.auth import auth_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Fixed credentials (change these!) ─────────────────────────────────────────
DEFAULT_ACCOUNTS = [
    {
        "username": "admin",
        "email":    "admin@pothole.com",
        "password": "Admin@1234",
        "role":     "admin",
    },
    {
        "username": "maintenance",
        "email":    "maintenance@pothole.com",
        "password": "Maintenance@1234",
        "role":     "maintenance",
    },
]

def seed_default_accounts():
    """Creates fixed admin and maintenance accounts if they don't exist yet."""
    from models import User
    for account in DEFAULT_ACCOUNTS:
        if not User.query.filter_by(email=account["email"]).first():
            user = User(
                username  = account["username"],
                email     = account["email"],
                role      = account["role"],
                is_active = True,
            )
            user.set_password(account["password"])
            db.session.add(user)
            print(f"[seed] Created {account['role']} account: {account['email']}")
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "postgresql://postgres:root@127.0.0.1:5432/pothole_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    upload_folder = os.path.join(BASE_DIR, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    CORS(app)
    db.init_app(app)

    app.register_blueprint(potholes_bp, url_prefix="/api/potholes")
    app.register_blueprint(auth_bp,     url_prefix="/api/auth")

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    with app.app_context():
        db.create_all()
        seed_default_accounts()   # ← seeds admin + maintenance on every start

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))