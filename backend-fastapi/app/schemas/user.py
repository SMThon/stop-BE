import datetime as dt

from app.schemas.base import CamelModel


class UserResponse(CamelModel):
    id: str
    email: str
    created_at: dt.datetime
