from sqlmodel import Session, col, select

from app.errors import AppError
from app.models import Policy


def get_visible_policy(session: Session, user_id: str, policy_id: str) -> Policy:
    """내장 규정이거나 본인이 저장한 규정만 볼 수 있다."""
    policy = session.get(Policy, policy_id)
    if policy is None or policy.user_id not in (None, user_id):
        raise AppError("POLICY_NOT_FOUND", "환불 규정을 찾을 수 없습니다.", 404)
    return policy


def _norm(name: str) -> str:
    return "".join(name.lower().split())


def find_builtin_policy(session: Session, platform: str) -> Policy | None:
    """쇼핑몰 이름(또는 내장 규정 id)이 같은 내장 규정을 찾는다 (대소문자·공백 무시)."""
    target = _norm(platform)
    builtin = session.exec(select(Policy).where(col(Policy.user_id).is_(None))).all()
    for policy in builtin:
        if target in (_norm(policy.platform), _norm(policy.id)):
            return policy
    return None


def policy_columns(fields: dict) -> dict:
    """PolicyInput/PolicyUpdate의 model_dump 결과를 DB 컬럼 값으로 바꾼다.

    중첩 객체(returnFee, defect)는 프론트와 같은 camelCase 키로 JSON 컬럼에 저장한다.
    """
    out = dict(fields)
    for key in ("return_fee", "defect"):
        value = out.get(key)
        if value is not None and not isinstance(value, dict):
            out[key] = value.model_dump(by_alias=True)
    return out
