from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel

from app.models.ids import new_id


class Event(SQLModel, table=True):
    """사용자가 캘린더에 직접 추가한 일정 (구독 만료일 등)."""

    __tablename__ = "app_events"

    id: str = Field(default_factory=new_id, primary_key=True)
    user_id: str = Field(foreign_key="app_users.id", index=True)
    title: str = Field(max_length=100)
    due_date: date
    memo: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
