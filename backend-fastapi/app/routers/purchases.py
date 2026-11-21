from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, col, select

from app.database import get_session
from app.deps import get_current_user
from app.errors import AppError
from app.models import Policy, Purchase, User
from app.schemas.purchase import PurchaseCreate, PurchaseResponse, PurchaseUpdate
from app.services.deadline import today_kst
from app.services.policy_service import find_builtin_policy, get_visible_policy
from app.services.purchase_service import to_response

router = APIRouter(prefix="/api/purchases", tags=["purchases"])

StatusFilter = Literal["보관 중", "반품 신청", "환불 완료", "기한 지남"]


def _get_owned(session: Session, user: User, purchase_id: str) -> Purchase:
    purchase = session.get(Purchase, purchase_id)
    if purchase is None or purchase.user_id != user.id:
        raise AppError("PURCHASE_NOT_FOUND", "구매 내역을 찾을 수 없습니다.", 404)
    return purchase


def _policy_of(session: Session, purchase: Purchase) -> Policy | None:
    return session.get(Policy, purchase.policy_id) if purchase.policy_id else None


@router.get("", response_model=list[PurchaseResponse])
def list_purchases(
    status: StatusFilter | None = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """구매내역 목록. 마감이 가까운 순으로 정렬된다 (FR-09)."""
    today = today_kst()
    purchases = session.exec(select(Purchase).where(Purchase.user_id == user.id)).all()
    policy_ids = {p.policy_id for p in purchases if p.policy_id is not None}
    policies: dict[str, Policy] = {}
    if policy_ids:
        policies = {
            p.id: p for p in session.exec(select(Policy).where(col(Policy.id).in_(policy_ids))).all()
        }
    items = [to_response(p, policies.get(p.policy_id), today) for p in purchases]
    if status:
        items = [i for i in items if i.status == status]
    items.sort(key=lambda i: (i.deadline is None, i.deadline or date.max, i.id))
    return items


@router.post("", response_model=PurchaseResponse, status_code=201)
def create_purchase(
    body: PurchaseCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """구매 등록. 규정을 지정하지 않으면 같은 이름의 내장 규정을 자동 연결한다 (FR-04)."""
    if body.policy_id is not None:
        policy = get_visible_policy(session, user.id, body.policy_id)
    else:
        policy = find_builtin_policy(session, body.platform)
    purchase = Purchase(
        user_id=user.id,
        platform=body.platform.strip(),
        policy_id=policy.id if policy else None,
        product_name=body.product_name.strip(),
        price=body.price,
        order_date=body.order_date,
        received_date=body.received_date,
    )
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    return to_response(purchase, policy, today_kst())


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
    purchase_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    purchase = _get_owned(session, user, purchase_id)
    return to_response(purchase, _policy_of(session, purchase), today_kst())


@router.patch("/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(
    purchase_id: str,
    body: PurchaseUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    purchase = _get_owned(session, user, purchase_id)
    data = body.model_dump(exclude_unset=True)

    if "policy_id" in data:
        policy_id = data.pop("policy_id")
        purchase.policy_id = get_visible_policy(session, user.id, policy_id).id if policy_id else None
    elif "platform" in data and data["platform"] is not None:
        # 쇼핑몰이 바뀌었는데 규정을 따로 지정하지 않았으면 내장 규정을 다시 연결한다.
        policy = find_builtin_policy(session, data["platform"])
        purchase.policy_id = policy.id if policy else None

    for key in ("platform", "product_name", "price", "order_date", "status"):
        if data.get(key) is not None:
            setattr(purchase, key, data[key].strip() if isinstance(data[key], str) else data[key])
    if "received_date" in data:
        purchase.received_date = data["received_date"]

    if purchase.received_date and purchase.received_date < purchase.order_date:
        raise AppError("INVALID_DATES", "수령일은 주문일보다 빠를 수 없습니다.", 422)

    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    return to_response(purchase, _policy_of(session, purchase), today_kst())


@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(
    purchase_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    purchase = _get_owned(session, user, purchase_id)
    session.delete(purchase)
    session.commit()
    return Response(status_code=204)
