"""Upstage(Solar) API 호출 공통 래퍼. 키는 서버 환경변수에서만 읽는다 (NFR-06).

Upstage는 OpenAI 호환 Chat Completions API라서 httpx로 직접 호출한다.
"""

import json

import httpx

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
    if not settings.upstage_api_key:
        raise LLMError("AI_NOT_CONFIGURED", "AI 기능이 아직 설정되지 않았습니다. (UPSTAGE_API_KEY)")

    payload = {
        "model": settings.upstage_model,
        # 추론 토큰도 max_tokens에 포함되므로 여유를 둔다.
        "max_tokens": max_tokens + 2000,
        "reasoning_effort": effort,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "result", "strict": True, "schema": schema},
        },
    }
    try:
        res = httpx.post(
            f"{settings.upstage_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.upstage_api_key}"},
            json=payload,
            timeout=60.0,
        )
    except httpx.TimeoutException:
        raise LLMError("AI_TIMEOUT", "AI 응답이 너무 늦어졌습니다. 잠시 후 다시 시도해 주세요.")
    except httpx.HTTPError:
        raise LLMError("AI_UNAVAILABLE", "AI 서버에 연결하지 못했습니다.")

    if res.status_code == 429:
        raise LLMError("AI_BUSY", "AI 요청이 많아 잠시 후 다시 시도해 주세요.")
    if res.status_code != 200:
        raise LLMError("AI_ERROR", "AI 요청 처리 중 오류가 발생했습니다.")

    try:
        choice = res.json()["choices"][0]
        content = choice["message"].get("content")
        finish = choice.get("finish_reason")
    except (ValueError, KeyError, IndexError, TypeError):
        raise LLMError("AI_BAD_OUTPUT", "AI 응답을 해석하지 못했습니다.")

    if finish == "length":
        raise LLMError("AI_TRUNCATED", "AI 응답이 길어서 끝까지 만들지 못했습니다.")
    if finish == "content_filter":
        raise LLMError("AI_REFUSED", "AI가 이 요청에는 답할 수 없다고 판단했습니다.")
    try:
        result = json.loads(content or "")
    except json.JSONDecodeError:
        raise LLMError("AI_BAD_OUTPUT", "AI 응답을 해석하지 못했습니다.")
    if not isinstance(result, dict):
        raise LLMError("AI_BAD_OUTPUT", "AI 응답을 해석하지 못했습니다.")
    return result
