from datetime import date

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.ids import new_id


def _default_return_fee() -> dict:
    return {"basicFee": None, "roundTripFee": None, "currency": "KRW", "note": ""}


def _default_defect() -> dict:
    return {"fromReceiptMonths": None, "fromDiscoveryDays": None, "note": ""}


class Policy(SQLModel, table=True):
    """환불 규정. 필드는 프론트 src/data/service-types.ts 의 Policy 와 같은 이름·값을 쓴다.

    null(None)은 '미확인'이지 0원·반품 불가가 아니다.
    """

    __tablename__ = "app_policies"

    # 내장 규정은 "coupang" 같은 슬러그, 사용자 규정은 UUID
    id: str = Field(default_factory=new_id, primary_key=True, max_length=64)
    # user_id가 없으면 내장 규정, 있으면 해당 사용자가 저장한 규정
    user_id: str | None = Field(default=None, foreign_key="app_users.id", index=True)
    source_type: str = "user-input"  # built-in | user-input
    platform: str = Field(index=True, max_length=100)
    site_url: str | None = None
    return_days: int | None = None
    base_date: str = "receivedDate"  # receivedDate | orderDate
    include_start_day: bool = False
    holiday_adjustment: str = "not-applied"
    return_fee: dict = Field(default_factory=_default_return_fee, sa_column=Column(JSON))
    exclusions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    how_to: str | None = None
    defect: dict = Field(default_factory=_default_defect, sa_column=Column(JSON))
    source_url: str | None = None
    collected_at: date | None = None
    verification_status: str = "unverified"  # verified | unverified
    evidence_note: str = ""
