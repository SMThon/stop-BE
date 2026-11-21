import datetime as dt
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import CamelModel
from app.schemas.policy import PolicyResponse

# EXPIRED(기한 지남)는 서버가 마감일로 계산해서 내려주는 값이라 직접 저장할 수 없다.
EditableStatus = Literal["KEEPING", "RETURN_REQUESTED", "REFUNDED"]
ResponseStatus = Literal["KEEPING", "RETURN_REQUESTED", "REFUNDED", "EXPIRED"]


class PurchaseCreate(CamelModel):
    platform: str = Field(min_length=1, max_length=100)
    policy_id: int | None = None
    product_name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0, le=100_000_000)
    order_date: dt.date
    received_date: dt.date | None = None

    @model_validator(mode="after")
    def _check_dates(self):
        if self.received_date and self.received_date < self.order_date:
            raise ValueError("수령일은 주문일보다 빠를 수 없습니다.")
        return self


class PurchaseUpdate(CamelModel):
    platform: str | None = Field(default=None, min_length=1, max_length=100)
    policy_id: int | None = None
    product_name: str | None = Field(default=None, min_length=1, max_length=200)
    price: int | None = Field(default=None, ge=0, le=100_000_000)
    order_date: dt.date | None = None
    received_date: dt.date | None = None
    status: EditableStatus | None = None


class PurchaseResponse(CamelModel):
    id: int
    platform: str
    policy_id: int | None
    product_name: str
    price: int
    order_date: dt.date
    received_date: dt.date | None
    status: ResponseStatus
    deadline: dt.date | None
    dday: int | None
    level: Literal["red", "yellow", "green", "gray"] | None
    # policy: 연결된 환불 규정 기준 / legal_default: 규정이 없어 법정 기본값(7일) 적용
    deadline_basis: Literal["policy", "legal_default"] | None
    policy: PolicyResponse | None
    created_at: dt.datetime
