from pydantic import Field

from app.schemas.base import CamelModel


class LegalCheckRequest(CamelModel):
    policy_id: str | None = Field(default=None, max_length=64)
    question: str = Field(min_length=1, max_length=1000)


class LegalCheckResponse(CamelModel):
    answer: str
    basis: list[str]
    disclaimer: str
