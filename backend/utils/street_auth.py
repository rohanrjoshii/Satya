import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_secret_key() -> str:
    return os.environ.get("STREET_SECRET_KEY", "dev-secret-change-me")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(*, subject: str, expires_delta_minutes: int = 60 * 24) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_delta_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, get_secret_key(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, get_secret_key(), algorithms=["HS256"])
    except JWTError as e:
        raise ValueError("Invalid token") from e

