from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class Event(SQLModel, table=True):
    """사용자가 캘린더에 직접 추가한 일정 (구독 만료일 등)."""

    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=100)
    due_date: date
    memo: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
