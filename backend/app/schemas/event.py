import datetime as dt

from pydantic import Field

from app.schemas.base import CamelModel


class EventCreate(CamelModel):
    title: str = Field(min_length=1, max_length=100)
    date: dt.date
    memo: str | None = Field(default=None, max_length=500)


class EventUpdate(CamelModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    date: dt.date | None = None
    memo: str | None = Field(default=None, max_length=500)


class EventResponse(CamelModel):
    id: int
    title: str
    date: dt.date
    memo: str | None
