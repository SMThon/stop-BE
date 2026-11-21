"""환불 규정 스키마. 프론트 src/data/service-types.ts 의 Policy 필드명·값과 맞춘다."""

import datetime as dt
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import CamelModel

BaseDate = Literal["receivedDate", "orderDate"]


def _check_http_url(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("http:// 또는 https:// 로 시작하는 주소여야 합니다.")
    return v


class ReturnFee(CamelModel):
    basic_fee: int | None = Field(default=None, ge=0)
    round_trip_fee: int | None = Field(default=None, ge=0)
    currency: Literal["KRW", "USD"] = "KRW"
    note: str = Field(default="", max_length=2000)


class Defect(CamelModel):
    from_receipt_months: int | None = Field(default=None, ge=0, le=60)
    from_discovery_days: int | None = Field(default=None, ge=0, le=365)
    note: str = Field(default="", max_length=2000)


class PolicyInput(CamelModel):
    """사용자가 입력·수정할 수 있는 규정 항목."""

    platform: str = Field(min_length=1, max_length=100)
    site_url: str | None = Field(default=None, max_length=500)
    return_days: int | None = Field(default=None, ge=0, le=365)  # null = 미확인
    base_date: BaseDate = "receivedDate"
    include_start_day: bool = False
    holiday_adjustment: Literal["not-applied"] = "not-applied"
    return_fee: ReturnFee = Field(default_factory=ReturnFee)
    exclusions: list[str] = Field(default_factory=list, max_length=50)
    how_to: str | None = Field(default=None, max_length=1000)
    defect: Defect = Field(default_factory=Defect)
    source_url: str | None = Field(default=None, max_length=1000)
    collected_at: dt.date | None = None
    evidence_note: str = Field(default="", max_length=4000)

    _urls = field_validator("site_url", "source_url")(_check_http_url)


class PolicyCreate(PolicyInput):
    pass


class PolicyUpdate(CamelModel):
    platform: str | None = Field(default=None, min_length=1, max_length=100)
    site_url: str | None = Field(default=None, max_length=500)
    return_days: int | None = Field(default=None, ge=0, le=365)
    base_date: BaseDate | None = None
    include_start_day: bool | None = None
    return_fee: ReturnFee | None = None
    exclusions: list[str] | None = Field(default=None, max_length=50)
    how_to: str | None = Field(default=None, max_length=1000)
    defect: Defect | None = None
    source_url: str | None = Field(default=None, max_length=1000)
    collected_at: dt.date | None = None
    evidence_note: str | None = Field(default=None, max_length=4000)

    _urls = field_validator("site_url", "source_url")(_check_http_url)


class PolicyResponse(PolicyInput):
    id: str
    source_type: Literal["built-in", "user-input"]
    verification_status: Literal["verified", "unverified"]


class PolicyDraft(CamelModel):
    """수집·추출 결과 초안. 저장 전이라 값이 비어 있을 수 있다 (null = 미확인)."""

    platform: str | None = None
    site_url: str | None = None
    return_days: int | None = None
    base_date: BaseDate | None = None
    include_start_day: bool = False
    return_fee: ReturnFee | None = None
    exclusions: list[str] = Field(default_factory=list)
    how_to: str | None = None
    defect: Defect | None = None
    source_url: str | None = None
    collected_at: dt.date | None = None


class ScrapeRequest(CamelModel):
    url: str = Field(min_length=8, max_length=1000)


class ParseTextRequest(CamelModel):
    text: str = Field(min_length=20, max_length=30000)
    platform: str | None = Field(default=None, max_length=100)
    source_url: str | None = Field(default=None, max_length=1000)

    _urls = field_validator("source_url")(_check_http_url)


class ScrapeResponse(CamelModel):
    status: Literal["ok", "partial", "failed"]
    draft: PolicyDraft | None = None
    missing_fields: list[str] = Field(default_factory=list)
    fallback_applied: dict[str, str] = Field(default_factory=dict)
    message: str | None = None
    error_code: str | None = None
