from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session, col, or_, select, update

from app.config import settings
from app.constants import SOURCE_USER_INPUT
from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import Policy, Purchase, User
from app.schemas.policy import (
    ParseTextRequest,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
    ScrapeRequest,
    ScrapeResponse,
)
from app.services import extractor, scraper
from app.services.deadline import today_kst
from app.services.llm import LLMError
from app.services.policy_service import get_visible_policy, policy_columns
from app.services.scraper import ScrapeError

router = APIRouter(prefix="/api/policies", tags=["policies"])


def _failed(code: str, message: str) -> ScrapeResponse:
    # 수집·추출 실패는 오류(4xx/5xx)가 아니라 status=failed 로 알려서,
    # 프론트가 직접 입력 화면으로 자연스럽게 넘어가게 한다 (NFR-03).
    return ScrapeResponse(status="failed", message=message, error_code=code)


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    source_type: Literal["built-in", "user-input"] | None = Query(default=None, alias="sourceType"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """내장 환불 규정 + 내가 저장한 규정 목록 (FR-01)."""
    stmt = select(Policy).where(or_(col(Policy.user_id).is_(None), Policy.user_id == user.id))
    if source_type:
        stmt = stmt.where(Policy.source_type == source_type)
    return session.exec(stmt.order_by(Policy.platform)).all()


@router.post("/scrape", response_model=ScrapeResponse)
def scrape_policy(body: ScrapeRequest, _: User = Depends(get_current_user)):
    """URL의 환불 안내 페이지를 수집해 규정 초안을 만든다. 저장은 하지 않는다 (FR-02)."""
    try:
        page = scraper.fetch_page(body.url, settings.scrape_timeout_seconds)
        raw = extractor.extract_policy(page.text)
    except ScrapeError as e:
        return _failed(e.code, e.message)
    except LLMError as e:
        return _failed(e.code, e.message)
    return extractor.build_scrape_result(raw, source_url=page.final_url, platform_hint=None, today=today_kst())


@router.post("/parse-text", response_model=ScrapeResponse)
def parse_policy_text(body: ParseTextRequest, _: User = Depends(get_current_user)):
    """수집이 안 될 때 사용자가 붙여넣은 규정 텍스트에서 초안을 만든다 (FR-03)."""
    try:
        raw = extractor.extract_policy(body.text, body.platform)
    except LLMError as e:
        return _failed(e.code, e.message)
    return extractor.build_scrape_result(
        raw, source_url=body.source_url, platform_hint=body.platform, today=today_kst()
    )


@router.post("", response_model=PolicyResponse, status_code=201)
def create_policy(
    body: PolicyCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """사용자가 확인·수정한 환불 규정을 저장한다 (FR-03). 사용자 입력 규정은 항상 미검증(unverified)이다."""
    fields = policy_columns(body.model_dump())
    fields["platform"] = fields["platform"].strip()
    if fields.get("collected_at") is None:
        fields["collected_at"] = today_kst()
    policy = Policy(
        **fields,
        user_id=user.id,
        source_type=SOURCE_USER_INPUT,
        verification_status="unverified",
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """환불 규정 카드 (FR-08)."""
    return get_visible_policy(session, user.id, policy_id)


@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    policy = get_visible_policy(session, user.id, policy_id)
    if policy.user_id != user.id:
        raise AppError("POLICY_READONLY", "내장 환불 규정은 수정할 수 없습니다.", 403)
    data = body.model_dump(exclude_unset=True)
    # 비울 수 없는 항목에 null이 오면 무시한다. (return_days의 null은 '미확인'이라 허용)
    for required in ("platform", "base_date", "include_start_day", "exclusions", "return_fee", "defect", "evidence_note"):
        if required in data and data[required] is None:
            data.pop(required)
    for key, value in policy_columns(data).items():
        setattr(policy, key, value)
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
def delete_policy(
    policy_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    policy = get_visible_policy(session, user.id, policy_id)
    if policy.user_id != user.id:
        raise AppError("POLICY_READONLY", "내장 환불 규정은 삭제할 수 없습니다.", 403)
    session.exec(update(Purchase).where(Purchase.policy_id == policy.id).values(policy_id=None))
    session.delete(policy)
    session.commit()
    return Response(status_code=204)
