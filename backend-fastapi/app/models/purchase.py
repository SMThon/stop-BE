from datetime import date, datetime, timezone

from sqlmodel import Field, SQLModel

from app.constants import STATUS_KEEPING
from app.models.ids import new_id


class Purchase(SQLModel, table=True):
    __tablename__ = "app_purchases"

    id: str = Field(default_factory=new_id, primary_key=True)
    user_id: str = Field(foreign_key="app_users.id", index=True)
    platform: str = Field(max_length=100)
    policy_id: str | None = Field(default=None, foreign_key="app_policies.id")
    product_name: str = Field(max_length=200)
    price: int
    order_date: date
    received_date: date | None = None
    status: str = STATUS_KEEPING  # 보관 중 | 반품 신청 | 환불 완료 (기한 지남은 계산값)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
