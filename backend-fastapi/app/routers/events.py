from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import Event, User
from app.schemas.event import EventCreate, EventResponse, EventUpdate

router = APIRouter(prefix="/api/events", tags=["events"])


def _to_response(event: Event) -> EventResponse:
    return EventResponse(id=event.id, title=event.title, date=event.due_date, memo=event.memo)


def _get_owned(session: Session, user: User, event_id: str) -> Event:
    event = session.get(Event, event_id)
    if event is None or event.user_id != user.id:
        raise AppError("EVENT_NOT_FOUND", "일정을 찾을 수 없습니다.", 404)
    return event


@router.post("", response_model=EventResponse, status_code=201)
def create_event(
    body: EventCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """캘린더에 만료일 같은 일정을 직접 추가한다."""
    event = Event(user_id=user.id, title=body.title.strip(), due_date=body.date, memo=body.memo)
    session.add(event)
    session.commit()
    session.refresh(event)
    return _to_response(event)


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _to_response(_get_owned(session, user, event_id))


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    body: EventUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event = _get_owned(session, user, event_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("title") is not None:
        event.title = data["title"].strip()
    if data.get("date") is not None:
        event.due_date = data["date"]
    if "memo" in data:
        event.memo = data["memo"]
    session.add(event)
    session.commit()
    session.refresh(event)
    return _to_response(event)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    session.delete(_get_owned(session, user, event_id))
    session.commit()
    return Response(status_code=204)
