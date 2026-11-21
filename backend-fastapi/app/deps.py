from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_session
from app.errors import AppError
from app.models import User
from app.services.auth_service import decode_token

# Swagger(/docs)에 Authorize 버튼이 생겨 토큰을 넣고 바로 API를 호출해 볼 수 있다.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise AppError("UNAUTHORIZED", "로그인이 필요합니다.", 401)
    user = session.get(User, decode_token(credentials.credentials))
    if user is None:
        raise AppError("UNAUTHORIZED", "존재하지 않는 사용자입니다.", 401)
    return user
