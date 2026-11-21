from datetime import date

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Policy(SQLModel, table=True):
    __tablename__ = "policies"

    id: int | None = Field(default=None, primary_key=True)
    # user_id가 없으면 내장(builtin) 규정, 있으면 해당 사용자가 저장한 규정
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    source_type: str = "user"  # builtin | user
    platform: str = Field(index=True, max_length=100)
    site_url: str | None = None
    return_days: int
    base_date: str = "RECEIVED"  # RECEIVED(수령일) | ORDERED(주문일)
    return_fee: str | None = None
    exclusions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    how_to: str | None = None
    source_url: str | None = None
    collected_at: date | None = None
