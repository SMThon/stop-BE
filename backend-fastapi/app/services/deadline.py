"""환불 마감일·D-day·색상 단계 계산 (DB·네트워크 없이 동작하는 순수 함수)."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

# 환불 규정을 찾지 못했을 때 쓰는 법정 기본값: 단순변심 청약철회 7일
LEGAL_DEFAULT_RETURN_DAYS = 7
LEGAL_DEFAULT_BASE_DATE = "RECEIVED"


def today_kst() -> date:
    return datetime.now(KST).date()


def compute_refund_deadline(
    base_date_kind: str,
    order_date: date,
    received_date: date | None,
    return_days: int,
) -> date | None:
    """기준일 + 반품 가능 일수. 기준일이 아직 없으면(수령일 미입력) None.

    마감일은 기준일로부터 return_days일 뒤 날짜이며, 그날까지 신청 가능한 것으로 본다.
    """
    base = order_date if base_date_kind == "ORDERED" else received_date
    if base is None:
        return None
    return base + timedelta(days=return_days)


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
    if status == "KEEPING" and deadline is not None and deadline < (today or today_kst()):
        return "EXPIRED"
    return status
