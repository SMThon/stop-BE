"""환불 마감일·D-day·색상 단계 계산 (DB·네트워크 없이 동작하는 순수 함수).

프론트 src/data/date-rules.ts 의 calculatePurchaseDeadline / getDeadlineWarning 과 같은 규칙이다.
- 기간(returnDays)을 모르면 마감일은 null. 법정 기준(7일 등)을 판매처 규정으로 자동 대체하지 않는다.
- 마감일 = 기준일 + returnDays - (includeStartDay ? 1 : 0)
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.constants import STATUS_EXPIRED, STATUS_KEEPING

KST = ZoneInfo("Asia/Seoul")


def today_kst() -> date:
    return datetime.now(KST).date()


def compute_refund_deadline(
    base_date_kind: str,
    order_date: date,
    received_date: date | None,
    return_days: int | None,
    include_start_day: bool = False,
) -> date | None:
    """기준일(orderDate|receivedDate)이 없거나 반품 기간이 미확인(null)·1일 미만이면 None."""
    base = order_date if base_date_kind == "orderDate" else received_date
    if base is None or return_days is None or return_days < 1:
        return None
    return base + timedelta(days=return_days - (1 if include_start_day else 0))


def dday(deadline: date, today: date | None = None) -> int:
    """남은 일수. 오늘이 마감이면 0, 지났으면 음수."""
    return (deadline - (today or today_kst())).days


def level_for(days_left: int) -> str:
    """D-2 이하 빨강, D-3~5 노랑, 여유 초록, 지남 회색 (FR-09)."""
    if days_left < 0:
        return "gray"
    if days_left <= 2:
        return "red"
    if days_left <= 5:
        return "yellow"
    return "green"


def is_imminent(days_left: int) -> bool:
    """마감 임박 배너 대상 (FR-11): 오늘~D-2."""
    return 0 <= days_left <= 2


def effective_status(status: str, deadline: date | None, today: date | None = None) -> str:
    """보관 중인데 마감일이 지났으면 '기한 지남'으로 취급한다."""
    if status == STATUS_KEEPING and deadline is not None and deadline < (today or today_kst()):
        return STATUS_EXPIRED
    return status
