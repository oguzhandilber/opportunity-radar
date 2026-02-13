"""Password hashing and validation utilities."""

import bcrypt
import secrets
import re
from typing import Tuple, List


class PasswordManager:
    """Manage password hashing and validation."""

    def __init__(self):
        self.salt_rounds = 12

    def hash_password(self, password: str) -> str:
        """Hash a password with bcrypt."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.salt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def generate_reset_token(self) -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)

    def generate_verification_token(self) -> str:
        """Generate an email verification token."""
        return secrets.token_urlsafe(32)

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors


# Global instance
password_manager = PasswordManager()
