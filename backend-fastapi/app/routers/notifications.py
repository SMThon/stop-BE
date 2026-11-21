from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models import NotificationSetting, User
from app.schemas.notification import NotificationSettings

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _get_or_create(session: Session, user: User) -> NotificationSetting:
    setting = session.exec(
        select(NotificationSetting).where(NotificationSetting.user_id == user.id)
    ).first()
    if setting is None:
        setting = NotificationSetting(user_id=user.id)
        session.add(setting)
        session.commit()
        session.refresh(setting)
    return setting


@router.get("/settings", response_model=NotificationSettings)
def get_settings(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """알림 설정 조회 (FR-19). 실제 알림 발송은 아직 구현하지 않았다 (FR-13)."""
    return _get_or_create(session, user)


@router.put("/settings", response_model=NotificationSettings)
def put_settings(
    body: NotificationSettings,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    setting = _get_or_create(session, user)
    setting.enabled = body.enabled
    setting.days_before = list(body.days_before)
    session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting
