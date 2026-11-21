from pydantic import Field, field_validator

from app.schemas.base import CamelModel


class NotificationSettings(CamelModel):
    enabled: bool = True
    days_before: list[int] = Field(default_factory=lambda: [3, 1], max_length=5)

    @field_validator("days_before")
    @classmethod
    def _check_days(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 30 for d in v):
            raise ValueError("알림 시점은 0~30일 사이여야 합니다.")
        return sorted(set(v), reverse=True)
