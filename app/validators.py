"""S1-16: Input validation utilities.

Every validator returns the cleaned value or raises ValidationError.
"""
import re

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

PASSWORD_MIN_LENGTH = 8
# bcrypt only uses the first 72 bytes, so we cap the length explicitly.
PASSWORD_MAX_BYTES = 72

MAX_SCORE = 1_000_000
MAX_DURATION_SECONDS = 24 * 60 * 60
MAX_FOOD_EATEN = 100_000
DIFFICULTIES = ("easy", "normal", "hard")


class ValidationError(ValueError):
    """Raised when user input is invalid."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.message = message
        self.field = field


def validate_username(value):
    if not isinstance(value, str):
        raise ValidationError("Username must be a string.", "username")
    value = value.strip()
    if not USERNAME_RE.match(value):
        raise ValidationError(
            "Username must be 3-20 characters: letters, numbers and underscores only.",
            "username",
        )
    return value


def validate_email(value):
    if not isinstance(value, str):
        raise ValidationError("Email must be a string.", "email")
    value = value.strip().lower()
    if len(value) > 254 or not EMAIL_RE.match(value):
        raise ValidationError("Enter a valid email address.", "email")
    return value


def validate_password(value):
    if not isinstance(value, str):
        raise ValidationError("Password must be a string.", "password")
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters.", "password"
        )
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValidationError(
            f"Password must be at most {PASSWORD_MAX_BYTES} bytes.", "password"
        )
    if not (re.search(r"[a-z]", value) and re.search(r"[A-Z]", value)
            and re.search(r"\d", value)):
        raise ValidationError(
            "Password must contain an uppercase letter, a lowercase letter and a digit.",
            "password",
        )
    return value


def validate_int(value, field, minimum=0, maximum=None):
    # bool is a subclass of int in Python, so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer.", field)
    if value < minimum:
        raise ValidationError(f"{field} must be at least {minimum}.", field)
    if maximum is not None and value > maximum:
        raise ValidationError(f"{field} must be at most {maximum}.", field)
    return value


def validate_difficulty(value):
    if not isinstance(value, str) or value.strip().lower() not in DIFFICULTIES:
        raise ValidationError(
            f"Difficulty must be one of: {', '.join(DIFFICULTIES)}.", "difficulty"
        )
    return value.strip().lower()


def validate_limit(value, default=10, maximum=100):
    """Parse a `limit` query-string value."""
    if value is None or value == "":
        return default
    try:
        limit = int(value)
    except (TypeError, ValueError):
        raise ValidationError("limit must be an integer.", "limit")
    if limit < 1 or limit > maximum:
        raise ValidationError(
            f"limit must be between 1 and {maximum}.", "limit")
    return limit
