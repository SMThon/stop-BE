from datetime import date

from app.models import Policy, Purchase
from app.schemas.policy import PolicyResponse
from app.schemas.purchase import PurchaseResponse
from app.services.deadline import compute_refund_deadline, dday, effective_status, level_for


def purchase_deadline(purchase: Purchase, policy: Policy | None) -> date | None:
    """연결된 규정이 없거나 반품 기간이 미확인이면 None (법정 기준으로 대체하지 않는다)."""
    if policy is None:
        return None
    return compute_refund_deadline(
        policy.base_date,
        purchase.order_date,
        purchase.received_date,
        policy.return_days,
        policy.include_start_day,
    )


def to_response(purchase: Purchase, policy: Policy | None, today: date) -> PurchaseResponse:
    deadline = purchase_deadline(purchase, policy)
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
        policy=PolicyResponse.model_validate(policy) if policy else None,
        created_at=purchase.created_at,
    )
