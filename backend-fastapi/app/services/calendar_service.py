from datetime import date

from sqlmodel import Session, col, select

from app.constants import STATUS_REFUNDED
from app.models import Event, Policy, Purchase
from app.schemas.calendar import CalendarEvent
from app.services.deadline import dday, is_imminent, level_for
from app.services.purchase_service import purchase_deadline


def collect_events(session: Session, user_id: str, today: date) -> list[CalendarEvent]:
    """환불 마감일(서버 계산) + 사용자가 직접 추가한 일정을 한 목록으로 합친다."""
    events: list[CalendarEvent] = []

    purchases = session.exec(
        select(Purchase).where(Purchase.user_id == user_id, Purchase.status != STATUS_REFUNDED)
    ).all()
    policy_ids = {p.policy_id for p in purchases if p.policy_id is not None}
    policies: dict[str, Policy] = {}
    if policy_ids:
        rows = session.exec(select(Policy).where(col(Policy.id).in_(policy_ids))).all()
        policies = {p.id: p for p in rows}

    for p in purchases:
        deadline = purchase_deadline(p, policies.get(p.policy_id))
        if deadline is None:
            continue
        days_left = dday(deadline, today)
        events.append(
            CalendarEvent(
                date=deadline,
                type="refund",
                ref_id=p.id,
                title=f"{p.platform} · {p.product_name} 환불 마감",
                dday=days_left,
                level=level_for(days_left),
            )
        )

    for e in session.exec(select(Event).where(Event.user_id == user_id)).all():
        days_left = dday(e.due_date, today)
        events.append(
            CalendarEvent(
                date=e.due_date,
                type="custom",
                ref_id=e.id,
                title=e.title,
                dday=days_left,
                level=level_for(days_left),
            )
        )

    events.sort(key=lambda ev: (ev.date, ev.type, ev.ref_id))
    return events


def count_imminent(events: list[CalendarEvent]) -> int:
    return sum(1 for ev in events if is_imminent(ev.dday))
