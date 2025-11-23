from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import timedelta
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


ALGORITHM = "HS256"
PWD_ALGORITHM = "pbkdf2_sha256"
PWD_ITERATIONS = 600_000
PWD_SALT_BYTES = 16


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class TokenDecodeError(Exception):
    """Raised when an access token cannot be decoded or validated."""


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a random salt."""

    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")

    salt = os.urandom(PWD_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PWD_ITERATIONS,
    )
    return f"{PWD_ALGORITHM}${PWD_ITERATIONS}${_b64_encode(salt)}${_b64_encode(dk)}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against the stored PBKDF2 hash."""

    try:
        algorithm, iterations_str, salt_b64, hash_b64 = hashed_password.split("$", 3)
    except ValueError:
        return False

    if algorithm != PWD_ALGORITHM:
        return False

    try:
        iterations = int(iterations_str)
    except ValueError:
        return False

    try:
        salt = _b64_decode(salt_b64)
        expected_hash = _b64_decode(hash_b64)
    except Exception:  # pragma: no cover - 防御性
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed, expected_hash)


def create_access_token(
    data: Dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT access token using HS256.

    The payload must be JSON-serializable; the caller is responsible for
    including a ``sub`` field with the user identifier.
    """

    to_encode = dict(data)
    now_ts = int(time.time())
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    exp_ts = now_ts + int(expires_delta.total_seconds())
    to_encode["exp"] = exp_ts

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = _b64_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    payload_b64 = _b64_encode(
        json.dumps(to_encode, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret = settings.SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    signature_b64 = _b64_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate an HS256 JWT token.

    Raises TokenDecodeError on any failure (format, signature, expiry).
    """

    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
    except ValueError as exc:  # pragma: no cover - 防御性
        raise TokenDecodeError("Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret = settings.SECRET_KEY.encode("utf-8")
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()

    try:
        provided_sig = _b64_decode(signature_b64)
    except Exception as exc:  # pragma: no cover - 防御性
        raise TokenDecodeError("Invalid token signature") from exc

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise TokenDecodeError("Token signature mismatch")

    try:
        payload_raw = _b64_decode(payload_b64)
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception as exc:  # pragma: no cover - 防御性
        raise TokenDecodeError("Invalid token payload") from exc

    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and time.time() > float(exp):
        raise TokenDecodeError("Token expired")

    return payload


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve the current authenticated user from the access token."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
    except TokenDecodeError:
        raise credentials_exception from None

    sub = payload.get("sub")
    if not isinstance(sub, (str, int)):
        raise credentials_exception
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency that requires the current user to be a superuser."""

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理权限",
        )
    return current_user


__all__ = [
    "ALGORITHM",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_current_active_superuser",
    "TokenDecodeError",
]
