from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel


class Purchase(SQLModel, table=True):
    __tablename__ = "purchases"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    platform: str = Field(max_length=100)
    policy_id: int | None = Field(default=None, foreign_key="policies.id")
    product_name: str = Field(max_length=200)
    price: int
    order_date: date
    received_date: date | None = None
    status: str = "KEEPING"  # KEEPING | RETURN_REQUESTED | REFUNDED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
