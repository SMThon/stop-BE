import datetime as dt
from typing import Literal

from app.schemas.base import CamelModel

Level = Literal["red", "yellow", "green", "gray"]


class CalendarEvent(CamelModel):
    date: dt.date
    type: Literal["refund", "custom"]
    ref_id: int
    title: str
    dday: int
    level: Level


class CalendarResponse(CamelModel):
    month: str
    events: list[CalendarEvent]
    imminent_count: int


class UpcomingResponse(CamelModel):
    items: list[CalendarEvent]
    imminent_count: int
