from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import User
from app.schemas.chat import LegalCheckRequest, LegalCheckResponse
from app.services import legal_chat
from app.services.llm import LLMError
from app.services.policy_service import get_visible_policy

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/legal-check", response_model=LegalCheckResponse)
def legal_check(
    body: LegalCheckRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """AI 환불상담: 환불 규정이 법에 어긋나는지 점검한다 (FR-15)."""
    policy = get_visible_policy(session, user.id, body.policy_id) if body.policy_id else None
    try:
        answer, basis = legal_chat.answer(body.question, policy)
    except LLMError as e:
        raise AppError(e.code, e.message, 503)
    return LegalCheckResponse(answer=answer, basis=basis, disclaimer=legal_chat.DISCLAIMER)
