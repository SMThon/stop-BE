import re

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import User
from app.schemas.calendar import CalendarResponse, UpcomingResponse
from app.services.calendar_service import collect_events, count_imminent
from app.services.deadline import today_kst

router = APIRouter(prefix="/api", tags=["calendar"])

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    month: str = Query(description="YYYY-MM 형식. 예: 2026-11"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """월간 캘린더: 환불 마감일과 직접 추가한 일정을 함께 돌려준다 (FR-07)."""
    if not _MONTH_RE.match(month):
        raise AppError("INVALID_MONTH", "month는 YYYY-MM 형식이어야 합니다.", 422)
    all_events = collect_events(session, user.id, today_kst())
    return CalendarResponse(
        month=month,
        events=[e for e in all_events if e.date.strftime("%Y-%m") == month],
        imminent_count=count_imminent(all_events),
    )


@router.get("/deadlines/upcoming", response_model=UpcomingResponse)
def get_upcoming(
    limit: int = Query(default=10, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """다가오는 마감 목록 + 마감 임박(D-2 이하) 건수 (FR-09, FR-11)."""
    all_events = collect_events(session, user.id, today_kst())
    upcoming = [e for e in all_events if e.dday >= 0][:limit]
    return UpcomingResponse(items=upcoming, imminent_count=count_imminent(all_events))
