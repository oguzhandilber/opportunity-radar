"""JWT token handling for authentication."""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from app.config import get_settings

settings = get_settings()


class JWTHandler:
    """Handle JWT token generation and validation."""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def generate_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate access and refresh tokens."""
        now = datetime.now(timezone.utc)

        # Access token payload
        access_payload = {
            "sub": str(user_data["user_id"]),
            "email": user_data["email"],
            "workspace_id": str(user_data.get("workspace_id", "")),
            "role": user_data.get("role", "member"),
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "iat": now,
            "type": "access",
        }

        # Refresh token payload
        refresh_payload = {
            "sub": str(user_data["user_id"]),
            "exp": now + timedelta(days=self.refresh_token_expire_days),
            "iat": now,
            "type": "refresh",
        }

        access_token = jwt.encode(
            access_payload, self.secret_key, algorithm=self.algorithm
        )
        refresh_token = jwt.encode(
            refresh_payload, self.secret_key, algorithm=self.algorithm
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Generate new access token from refresh token."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        # Generate new access token
        now = datetime.now(timezone.utc)
        access_payload = {
            "sub": payload["sub"],
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
            "iat": now,
            "type": "access",
        }

        access_token = jwt.encode(
            access_payload, self.secret_key, algorithm=self.algorithm
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }
