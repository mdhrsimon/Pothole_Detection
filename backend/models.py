from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash


# ─── User Model ───────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default="user")
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    potholes      = db.relationship(
        'Pothole',
        backref='reporter',
        lazy=True,
        foreign_keys='Pothole.reported_by_user_id',
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


# ─── Pothole Model ────────────────────────────────────────────────────────────
class Pothole(db.Model):
    __tablename__ = 'potholes'

    id           = db.Column(db.Integer, primary_key=True)
    latitude     = db.Column(db.Float, nullable=False)
    longitude    = db.Column(db.Float, nullable=False)
    confidence   = db.Column(db.Float, nullable=False)
    severity     = db.Column(db.String(50), nullable=False)
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)
    image_path   = db.Column(db.String(255), nullable=False)

    # who reported it
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # status managed by maintenance dept
    # 'open' | 'in_progress' | 'fixed' | 'awaiting_approval' | 'approved'
    status       = db.Column(db.String(30), nullable=False, default='open')
    status_note  = db.Column(db.String(255), nullable=True)   # optional note from maintenance
    updated_at   = db.Column(db.DateTime, nullable=True)      # when status last changed
    assigned_to_worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    after_image_path      = db.Column(db.String(255), nullable=True)
    fix_notes             = db.Column(db.String(255), nullable=True)
    fix_timestamp         = db.Column(db.DateTime, nullable=True)
    fix_latitude          = db.Column(db.Float, nullable=True)
    fix_longitude         = db.Column(db.Float, nullable=True)
    approved_by_admin_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_timestamp    = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id":          self.id,
            "latitude":    self.latitude,
            "longitude":   self.longitude,
            "confidence":  self.confidence,
            "severity":    self.severity,
            "timestamp":   self.timestamp.isoformat() if self.timestamp else None,
            "image_path":  self.image_path,
            "reported_by_user_id": self.reported_by_user_id,
            "status":      self.status,
            "status_note": self.status_note,
            "updated_at":  self.updated_at.isoformat() if self.updated_at else None,
            "assigned_to_worker_id": self.assigned_to_worker_id,
            "after_image_path": self.after_image_path,
            "fix_notes": self.fix_notes,
            "fix_timestamp": self.fix_timestamp.isoformat() if self.fix_timestamp else None,
            "fix_latitude": self.fix_latitude,
            "fix_longitude": self.fix_longitude,
            "approved_by_admin_id": self.approved_by_admin_id,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
        }