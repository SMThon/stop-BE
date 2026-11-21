from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from app.models.ids import new_id


class User(SQLModel, table=True):
    __tablename__ = "app_users"

    id: str = Field(default_factory=new_id, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
