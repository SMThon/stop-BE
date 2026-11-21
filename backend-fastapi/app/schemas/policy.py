import datetime as dt
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import CamelModel

BaseDate = Literal["RECEIVED", "ORDERED"]


def _check_http_url(v: str | None) -> str | None:
    if v is None or v == "":
        return None
    if not (v.startswith("http://") or v.startswith("https://")):
        raise ValueError("http:// 또는 https:// 로 시작하는 주소여야 합니다.")
    return v


class PolicyFields(CamelModel):
    platform: str = Field(min_length=1, max_length=100)
    site_url: str | None = Field(default=None, max_length=500)
    return_days: int = Field(ge=0, le=365)
    base_date: BaseDate = "RECEIVED"
    return_fee: str | None = Field(default=None, max_length=200)
    exclusions: list[str] = Field(default_factory=list, max_length=30)
    how_to: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    collected_at: dt.date | None = None

    _urls = field_validator("site_url", "source_url")(_check_http_url)


class PolicyCreate(PolicyFields):
    pass


class PolicyUpdate(CamelModel):
    platform: str | None = Field(default=None, min_length=1, max_length=100)
    site_url: str | None = Field(default=None, max_length=500)
    return_days: int | None = Field(default=None, ge=0, le=365)
    base_date: BaseDate | None = None
    return_fee: str | None = Field(default=None, max_length=200)
    exclusions: list[str] | None = Field(default=None, max_length=30)
    how_to: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=1000)
    collected_at: dt.date | None = None

    _urls = field_validator("site_url", "source_url")(_check_http_url)


class PolicyResponse(PolicyFields):
    id: int
    source_type: Literal["builtin", "user"]


class PolicyDraft(CamelModel):
    """수집·추출 결과 초안. 저장 전이라 모든 값이 비어 있을 수 있다."""

    platform: str | None = None
    site_url: str | None = None
    return_days: int | None = None
    base_date: BaseDate | None = None
    return_fee: str | None = None
    exclusions: list[str] = Field(default_factory=list)
    how_to: str | None = None
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
