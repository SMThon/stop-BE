"""Claude API 호출 공통 래퍼. 키는 서버 환경변수에서만 읽는다 (NFR-06)."""

import json

import anthropic

from app.config import settings


class LLMError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def call_structured(
    *,
    system: str,
    user: str,
    schema: dict,
    max_tokens: int = 2000,
    effort: str = "low",
) -> dict:
    """JSON 스키마에 맞는 구조화된 응답을 받아 dict로 돌려준다."""
    if not settings.anthropic_api_key:
        raise LLMError("AI_NOT_CONFIGURED", "AI 기능이 아직 설정되지 않았습니다. (ANTHROPIC_API_KEY)")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=30.0, max_retries=1)
    try:
        response = client.beta.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            # 안전 분류기가 요청을 거절하면 서버가 대체 모델로 다시 시도한다.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.APITimeoutError:
        raise LLMError("AI_TIMEOUT", "AI 응답이 너무 늦어졌습니다. 잠시 후 다시 시도해 주세요.")
    except anthropic.RateLimitError:
        raise LLMError("AI_BUSY", "AI 요청이 많아 잠시 후 다시 시도해 주세요.")
    except anthropic.APIConnectionError:
        raise LLMError("AI_UNAVAILABLE", "AI 서버에 연결하지 못했습니다.")
    except anthropic.APIStatusError:
        raise LLMError("AI_ERROR", "AI 요청 처리 중 오류가 발생했습니다.")

    if response.stop_reason == "refusal":
        raise LLMError("AI_REFUSED", "AI가 이 요청에는 답할 수 없다고 판단했습니다.")
    if response.stop_reason == "max_tokens":
        raise LLMError("AI_TRUNCATED", "AI 응답이 길어서 끝까지 만들지 못했습니다.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise LLMError("AI_BAD_OUTPUT", "AI 응답을 해석하지 못했습니다.")
