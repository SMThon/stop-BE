from datetime import date

from app.models import Policy, Purchase
from app.schemas.policy import PolicyResponse
from app.schemas.purchase import PurchaseResponse
from app.services.deadline import (
    LEGAL_DEFAULT_BASE_DATE,
    LEGAL_DEFAULT_RETURN_DAYS,
    compute_refund_deadline,
    dday,
    effective_status,
    level_for,
)


def purchase_deadline(purchase: Purchase, policy: Policy | None) -> tuple[date | None, str]:
    """(마감일, 적용 기준). 규정이 없으면 법정 기본값 7일을 쓴다."""
    if policy is not None:
        days, kind, basis = policy.return_days, policy.base_date, "policy"
    else:
        days, kind, basis = LEGAL_DEFAULT_RETURN_DAYS, LEGAL_DEFAULT_BASE_DATE, "legal_default"
    deadline = compute_refund_deadline(kind, purchase.order_date, purchase.received_date, days)
    return deadline, basis


def to_response(purchase: Purchase, policy: Policy | None, today: date) -> PurchaseResponse:
    deadline, basis = purchase_deadline(purchase, policy)
    days_left = dday(deadline, today) if deadline else None
    return PurchaseResponse(
        id=purchase.id,
        platform=purchase.platform,
        policy_id=purchase.policy_id,
        product_name=purchase.product_name,
        price=purchase.price,
        order_date=purchase.order_date,
        received_date=purchase.received_date,
        status=effective_status(purchase.status, deadline, today),
        deadline=deadline,
        dday=days_left,
        level=level_for(days_left) if days_left is not None else None,
        deadline_basis=basis if deadline else None,
        policy=PolicyResponse.model_validate(policy) if policy else None,
        created_at=purchase.created_at,
    )
