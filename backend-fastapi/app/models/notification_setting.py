from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class NotificationSetting(SQLModel, table=True):
    __tablename__ = "app_notification_settings"

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="app_users.id", unique=True, index=True)
    enabled: bool = True
    days_before: list[int] = Field(default_factory=lambda: [3, 1], sa_column=Column(JSON))
