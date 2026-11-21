"""app/data/builtin_policies.json 의 내장 환불 규정을 DB에 넣는다 (서버 시작 시 실행).

JSON 항목은 프론트 src/data/service-types.ts 의 Policy 와 같은 형식이다
(현재 파일은 src/data/shopping-policies.ts 의 shoppingPolicies 를 내보낸 것).
같은 id가 이미 있으면 JSON 내용으로 갱신한다.
"""

import json
import logging
from datetime import date
from pathlib import Path

from sqlmodel import Session

from app.constants import SOURCE_BUILT_IN
from app.models import Policy

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "builtin_policies.json"


def _int_or_none(value, name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name}는 정수 또는 null 이어야 합니다: {value!r}")
    return value


def _parse_item(item: dict) -> tuple[str, dict]:
    base = item.get("baseDate", "receivedDate")
    if base not in ("receivedDate", "orderDate"):
        raise ValueError(f"baseDate는 receivedDate 또는 orderDate 여야 합니다: {base}")
    verification = item.get("verificationStatus", "unverified")
    if verification not in ("verified", "unverified"):
        raise ValueError(f"verificationStatus가 올바르지 않습니다: {verification}")
    exclusions = item.get("exclusions", [])
    if not isinstance(exclusions, list):
        raise ValueError("exclusions는 배열이어야 합니다.")
    fee = item.get("returnFee") or {}
    defect = item.get("defect") or {}
    fields = {
        "platform": str(item["platform"]).strip(),
        "site_url": item.get("siteUrl"),
        "return_days": _int_or_none(item.get("returnDays"), "returnDays"),
        "base_date": base,
        "include_start_day": bool(item.get("includeStartDay", False)),
        "holiday_adjustment": item.get("holidayAdjustment", "not-applied"),
        "return_fee": {
            "basicFee": _int_or_none(fee.get("basicFee"), "basicFee"),
            "roundTripFee": _int_or_none(fee.get("roundTripFee"), "roundTripFee"),
            "currency": fee.get("currency", "KRW"),
            "note": str(fee.get("note", "")),
        },
        "exclusions": [str(e) for e in exclusions],
        "how_to": item.get("howTo"),
        "defect": {
            "fromReceiptMonths": _int_or_none(defect.get("fromReceiptMonths"), "fromReceiptMonths"),
            "fromDiscoveryDays": _int_or_none(defect.get("fromDiscoveryDays"), "fromDiscoveryDays"),
            "note": str(defect.get("note", "")),
        },
        "source_url": item.get("sourceUrl"),
        "collected_at": date.fromisoformat(item["collectedAt"]) if item.get("collectedAt") else None,
        "verification_status": verification,
        "evidence_note": str(item.get("evidenceNote", "")),
    }
    return str(item["id"]), fields


def seed_builtin_policies(session: Session, path: Path = DEFAULT_PATH) -> int:
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    items = json.loads(text) if text else []
    count = 0
    for item in items:
        try:
            policy_id, fields = _parse_item(item)
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("내장 규정 항목을 건너뜁니다 (%s): %s", exc, item)
            continue
        existing = session.get(Policy, policy_id)
        if existing is None:
            session.add(Policy(id=policy_id, user_id=None, source_type=SOURCE_BUILT_IN, **fields))
        elif existing.user_id is None:
            for key, value in fields.items():
                setattr(existing, key, value)
            session.add(existing)
        else:
            logger.warning("사용자 규정과 id가 겹쳐 건너뜁니다: %s", policy_id)
            continue
        count += 1
    session.commit()
    return count
