from datetime import date

from app.services.deadline import (
    compute_refund_deadline,
    dday,
    effective_status,
    is_imminent,
    level_for,
)


def test_deadline_from_received_date():
    d = compute_refund_deadline("receivedDate", date(2026, 11, 15), date(2026, 11, 18), 7)
    assert d == date(2026, 11, 25)


def test_deadline_from_order_date():
    d = compute_refund_deadline("orderDate", date(2026, 11, 15), None, 7)
    assert d == date(2026, 11, 22)


def test_include_start_day_counts_base_day_as_day_one():
    # 프론트 date-rules.ts: addDays(base, returnDays - (includeStartDay ? 1 : 0))
    d = compute_refund_deadline("receivedDate", date(2026, 11, 15), date(2026, 11, 18), 7, include_start_day=True)
    assert d == date(2026, 11, 24)


def test_deadline_is_none_when_received_date_missing():
    assert compute_refund_deadline("receivedDate", date(2026, 11, 15), None, 7) is None


def test_deadline_is_none_when_return_days_unknown_or_invalid():
    # 기간을 모르면(null) 법정 기준으로 대체하지 않고 마감일도 null
    assert compute_refund_deadline("receivedDate", date(2026, 11, 15), date(2026, 11, 18), None) is None
    assert compute_refund_deadline("receivedDate", date(2026, 11, 15), date(2026, 11, 18), 0) is None


def test_deadline_crosses_month_and_year():
    d = compute_refund_deadline("receivedDate", date(2026, 12, 20), date(2026, 12, 28), 7)
    assert d == date(2027, 1, 4)


def test_dday_values():
    today = date(2026, 11, 21)
    assert dday(date(2026, 11, 21), today) == 0
    assert dday(date(2026, 11, 25), today) == 4
    assert dday(date(2026, 11, 20), today) == -1


def test_level_boundaries_match_frontend_warning():
    assert level_for(-1) == "gray"
    assert level_for(0) == "red"
    assert level_for(2) == "red"
    assert level_for(3) == "yellow"
    assert level_for(5) == "yellow"
    assert level_for(6) == "green"


def test_imminent_is_today_through_d2():
    assert not is_imminent(-1)
    assert is_imminent(0)
    assert is_imminent(2)
    assert not is_imminent(3)


def test_effective_status():
    today = date(2026, 11, 21)
    assert effective_status("보관 중", date(2026, 11, 20), today) == "기한 지남"
    assert effective_status("보관 중", date(2026, 11, 21), today) == "보관 중"
    assert effective_status("환불 완료", date(2026, 11, 20), today) == "환불 완료"
    assert effective_status("보관 중", None, today) == "보관 중"
