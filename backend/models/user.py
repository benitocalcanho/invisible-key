"""
User model — stores credentials and role information.
Fields:
    id: Primary key
    username: Unique username for login
    password_hash: Hashed password
    role: User role ('admin', 'master', 'cleaner', 'guest')
    is_active: Is the user active
    created_at: UTC timestamp of creation
    created_by: How the account was created ('manual', 'calendar')
    calendar_event_id: Optional reference to Google Calendar event
    audit_logs: Relationship to AuditLog
"""
from datetime import datetime, timezone
import unicodedata
import bcrypt
from models import db
from utils.datetime_utils import utc_isoformat


class User(db.Model):
    __tablename__ = "users"

    MIN_PASSWORD_LENGTH = 8
    GUEST_MIN_PASSWORD_LENGTH = 4

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="master")  # User role: 'admin', 'master', 'cleaner', 'guest'
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    # Source of account creation: 'manual' (created by admin) or 'calendar' (auto-created from Google Calendar)
    created_by = db.Column(db.String(50), nullable=False, default="manual")
    # Optional reference to the Google Calendar event ID that created this user
    calendar_event_id = db.Column(db.String(200), nullable=True)
    # Guests cannot log in on or after this date (set from calendar event DTEND)
    valid_until = db.Column(db.Date, nullable=True)

    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    @staticmethod
    def normalize_username(username: str) -> str:
        """Normalize login names while keeping Unicode letters intact."""
        return unicodedata.normalize("NFKC", username.strip()).casefold()

    @classmethod
    def find_by_username(cls, username: str):
        """Find a user with Unicode-aware case-insensitive username matching."""
        normalized = cls.normalize_username(username)
        exact = cls.query.filter_by(username=normalized).first()
        if exact:
            return exact

        ascii_case_match = cls.query.filter(db.func.lower(cls.username) == normalized).first()
        if ascii_case_match:
            return ascii_case_match

        for user in cls.query.all():
            if cls.normalize_username(user.username) == normalized:
                return user
        return None

    def minimum_password_length(self) -> int:
        return self.GUEST_MIN_PASSWORD_LENGTH if self.role == "guest" else self.MIN_PASSWORD_LENGTH

    def set_password(self, raw_password: str) -> None:
        min_length = self.minimum_password_length()
        if len(raw_password) < min_length:
            raise ValueError(f"Password must be at least {min_length} characters.")
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": utc_isoformat(self.created_at),
            "created_by": self.created_by,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        }

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"
