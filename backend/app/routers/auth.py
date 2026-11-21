from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import Event, NotificationSetting, Policy, Purchase, User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, WithdrawRequest
from app.schemas.user import UserResponse
from app.services.auth_service import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(body: SignupRequest, session: Session = Depends(get_session)):
    """이메일/비밀번호로 회원가입 (FR-16)."""
    email = body.email.strip().lower()
    if session.exec(select(User).where(User.email == email)).first():
        raise AppError("EMAIL_EXISTS", "이미 가입된 이메일입니다.", 409)
    user = User(email=email, password_hash=hash_password(body.password))
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise AppError("EMAIL_EXISTS", "이미 가입된 이메일입니다.", 409)
    session.refresh(user)
    session.add(NotificationSetting(user_id=user.id))
    session.commit()
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    """로그인하면 액세스 토큰을 발급한다 (FR-17)."""
    user = session.exec(select(User).where(User.email == body.email.strip().lower())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout", status_code=204)
def logout(_: User = Depends(get_current_user)):
    """토큰 방식이라 서버에 세션이 없다. 프론트가 저장한 토큰을 지우면 로그아웃된다 (FR-17)."""
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/withdraw", status_code=204)
def withdraw(
    body: WithdrawRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """회원 탈퇴: 비밀번호를 확인한 뒤 해당 사용자의 모든 데이터를 삭제한다 (FR-18)."""
    if not verify_password(body.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "비밀번호가 올바르지 않습니다.", 401)
    session.exec(delete(Purchase).where(Purchase.user_id == user.id))
    session.exec(delete(Event).where(Event.user_id == user.id))
    session.exec(delete(NotificationSetting).where(NotificationSetting.user_id == user.id))
    session.exec(delete(Policy).where(Policy.user_id == user.id))
    session.exec(delete(User).where(User.id == user.id))
    session.commit()
    return Response(status_code=204)
