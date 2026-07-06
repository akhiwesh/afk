"""
Password hashing and JWT token utilities.

Uses the `bcrypt` library directly instead of `passlib`. Passlib has been
unmaintained since 2020 and crashes at import/startup with bcrypt >= 4.1
("password cannot be longer than 72 bytes" during its backend self-test).
Direct bcrypt usage is simpler, maintained, and version-proof.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Union

import bcrypt
from jose import jwt

from backend.app.core.settings import get_settings

settings = get_settings()

# JWT configuration comes from environment-driven settings.
# No secrets are hardcoded in source.
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# bcrypt operates on the first 72 bytes of input. We truncate consistently
# in both hash and verify so behavior is deterministic; the registration
# API also enforces sane password lengths before this layer is reached.
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def get_password_hash(password: str) -> str:
    hashed = bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            _to_bcrypt_bytes(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Malformed stored hash — treat as authentication failure,
        # never as a server crash.
        return False


def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jose.JWTError on invalid tokens."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
