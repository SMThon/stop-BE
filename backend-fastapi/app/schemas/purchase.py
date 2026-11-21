"""구매 스키마. 필드명·상태값은 프론트 src/data/service-types.ts 의 Purchase 와 맞춘다."""

import datetime as dt
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.base import CamelModel
from app.schemas.policy import PolicyResponse

# 기한 지남은 서버가 마감일로 계산해서 내려주는 값이라 직접 저장할 수 없다.
EditableStatus = Literal["보관 중", "반품 신청", "환불 완료"]
ResponseStatus = Literal["보관 중", "반품 신청", "환불 완료", "기한 지남"]


class PurchaseCreate(CamelModel):
    platform: str = Field(min_length=1, max_length=100)
    policy_id: str | None = Field(default=None, max_length=64)
    product_name: str = Field(min_length=1, max_length=200)
    price: int = Field(ge=0, le=2_147_483_647)
    order_date: dt.date
    received_date: dt.date | None = None

    @model_validator(mode="after")
    def _check_dates(self):
        if self.received_date and self.received_date < self.order_date:
            raise ValueError("수령일은 주문일보다 빠를 수 없습니다.")
        return self


class PurchaseUpdate(CamelModel):
    platform: str | None = Field(default=None, min_length=1, max_length=100)
    policy_id: str | None = Field(default=None, max_length=64)
    product_name: str | None = Field(default=None, min_length=1, max_length=200)
    price: int | None = Field(default=None, ge=0, le=2_147_483_647)
    order_date: dt.date | None = None
    received_date: dt.date | None = None
    status: EditableStatus | None = None


class PurchaseResponse(CamelModel):
    id: str
    platform: str
    policy_id: str | None
    product_name: str
    price: int
    order_date: dt.date
    received_date: dt.date | None
    status: ResponseStatus
    # 규정이 없거나 반품 기간(returnDays)이 미확인이면 null. 법정 기준으로 임의 대체하지 않는다.
    deadline: dt.date | None
    dday: int | None
    level: Literal["red", "yellow", "green", "gray"] | None
    policy: PolicyResponse | None
    created_at: dt.datetime
