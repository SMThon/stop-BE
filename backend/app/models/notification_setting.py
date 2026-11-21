from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class NotificationSetting(SQLModel, table=True):
    __tablename__ = "notification_settings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    enabled: bool = True
    days_before: list[int] = Field(default_factory=lambda: [3, 1], sa_column=Column(JSON))
