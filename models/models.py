from datetime import datetime
from zoneinfo import ZoneInfo

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


# ---------- Indian Standard Time ----------
IST = ZoneInfo("Asia/Kolkata")


def ist_now():
    """Return current date and time in IST."""
    return datetime.now(IST).replace(tzinfo=None)


# ---------- User ----------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='citizen')   # citizen / admin

    created_at = db.Column(db.DateTime, default=ist_now)

    complaints = db.relationship('Complaint', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------- Department ----------
class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    complaints = db.relationship('Complaint', backref='department', lazy='dynamic')


# ---------- Complaint ----------
class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)

    # Location Details
    address = db.Column(db.String(255))
    landmark = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # AI Priority
    priority = db.Column(db.String(20))        # Critical / High / Medium / Low
    priority_reason = db.Column(db.Text)

    # Complaint Status
    status = db.Column(db.String(20), default='Open')   # Open / In Progress / Resolved / Closed

    image_path = db.Column(db.String(255))
    
    # Resolution Details
    resolution_remarks = db.Column(db.Text)
    resolution_image_path = db.Column(db.String(255))
    resolved_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=ist_now)
    updated_at = db.Column(
        db.DateTime,
        default=ist_now,
        onupdate=ist_now
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))

    status_history = db.relationship(
        'StatusHistory',
        backref='complaint',
        lazy='dynamic'
    )

    feedback = db.relationship(
        'Feedback',
        backref='complaint',
        uselist=False
    )


# ---------- Status History ----------
class StatusHistory(db.Model):
    __tablename__ = 'status_history'

    id = db.Column(db.Integer, primary_key=True)

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey('complaints.id'),
        nullable=False
    )

    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id')
    )

    changed_at = db.Column(db.DateTime, default=ist_now)

    remarks = db.Column(db.Text)


# ---------- Feedback ----------
class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey('complaints.id'),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)   # 1-5

    comments = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=ist_now)


# ---------- Notification ----------
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    message = db.Column(db.String(255), nullable=False)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=ist_now)


# ---------- Password Reset Token ----------
class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=ist_now)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic'))