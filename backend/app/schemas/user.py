import datetime as dt

from app.schemas.base import CamelModel


class UserResponse(CamelModel):
    id: int
    email: str
    created_at: dt.datetime
