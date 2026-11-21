from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.errors import AppError

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _require_secret() -> str:
    if not settings.secret_key:
        raise AppError("SERVER_MISCONFIGURED", "서버 설정(SECRET_KEY)이 비어 있습니다.", 500)
    return settings.secret_key


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, _require_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _require_secret(), algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise AppError("TOKEN_EXPIRED", "로그인이 만료되었습니다. 다시 로그인해 주세요.", 401)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AppError("INVALID_TOKEN", "유효하지 않은 로그인 정보입니다.", 401)
