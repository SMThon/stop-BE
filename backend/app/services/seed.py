"""app/data/builtin_policies.json 의 내장 환불 규정을 DB에 넣는다 (서버 시작 시 실행).

내장 규정은 팀원이 각 사이트 원문을 직접 확인해 JSON에 적는다. 형식은 README 참고.
같은 쇼핑몰 이름이 이미 있으면 JSON 내용으로 갱신한다.
"""

import json
import logging
from datetime import date
from pathlib import Path

from sqlmodel import Session, col, select

from app.models import Policy

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "builtin_policies.json"


def _parse_item(item: dict) -> dict:
    base = item.get("baseDate", "RECEIVED")
    if base not in ("RECEIVED", "ORDERED"):
        raise ValueError(f"baseDate는 RECEIVED 또는 ORDERED 여야 합니다: {base}")
    return {
        "platform": str(item["platform"]).strip(),
        "site_url": item.get("siteUrl"),
        "return_days": int(item["returnDays"]),
        "base_date": base,
        "return_fee": item.get("returnFee"),
        "exclusions": list(item.get("exclusions", [])),
        "how_to": item.get("howTo"),
        "source_url": item.get("sourceUrl"),
        "collected_at": date.fromisoformat(item["collectedAt"]) if item.get("collectedAt") else None,
    }


def seed_builtin_policies(session: Session, path: Path = DEFAULT_PATH) -> int:
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    items = json.loads(text) if text else []
    count = 0
    for item in items:
        try:
            fields = _parse_item(item)
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("내장 규정 항목을 건너뜁니다 (%s): %s", exc, item)
            continue
        existing = session.exec(
            select(Policy).where(col(Policy.user_id).is_(None), Policy.platform == fields["platform"])
        ).first()
        if existing is None:
            session.add(Policy(user_id=None, source_type="builtin", **fields))
        else:
            for key, value in fields.items():
                setattr(existing, key, value)
            session.add(existing)
        count += 1
    session.commit()
    return count
