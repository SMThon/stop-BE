import json
from datetime import date, timedelta

import pytest
from sqlmodel import Session

from app.database import engine
from app.services import extractor, legal_chat, scraper
from app.services.deadline import today_kst
from app.services.llm import LLMError
from app.services.scraper import ScrapedPage, ScrapeError, html_to_text, validate_public_url
from app.services.seed import seed_builtin_policies

TODAY = date(2026, 11, 21)


def _raw(**over):
    raw = {
        "platform": None, "returnDays": None, "baseDate": None, "basicFee": None, "roundTripFee": None,
        "returnFeeNote": None, "exclusions": [], "howTo": None,
        "defectFromReceiptMonths": None, "defectFromDiscoveryDays": None, "defectNote": None,
    }
    raw.update(over)
    return raw


# ---------- 스크래퍼 보안 (SSRF 방어) ----------

@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data/",  # 클라우드 메타데이터
        "http://10.0.0.5/",
        "http://192.168.0.1/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://127.0.0.1:8000/",
    ],
)
def test_scraper_blocks_internal_addresses(url):
    with pytest.raises(ScrapeError) as exc:
        validate_public_url(url)
    assert exc.value.code in ("URL_NOT_ALLOWED", "HOST_NOT_FOUND")


@pytest.mark.parametrize("url", ["ftp://example.com/", "file:///etc/passwd", "javascript:alert(1)", "http://user:pw@example.com/"])
def test_scraper_rejects_bad_scheme_or_credentials(url):
    with pytest.raises(ScrapeError) as exc:
        validate_public_url(url)
    assert exc.value.code == "INVALID_URL"


def test_html_to_text_strips_scripts_and_styles():
    html = "<html><head><style>a{}</style><script>alert(1)</script></head><body><h1>반품 안내</h1><p>7일 이내</p></body></html>".encode()
    text = html_to_text(html)
    assert "반품 안내" in text and "7일 이내" in text
    assert "alert" not in text and "a{}" not in text


# ---------- 추출 결과 가공 ----------

def test_build_result_ok():
    raw = _raw(platform="테스트몰", returnDays=14, baseDate="receivedDate", basicFee=3000, roundTripFee=6000,
               returnFeeNote="단순 변심은 구매자 부담", exclusions=["택 제거"], howTo="마이페이지에서 신청",
               defectFromReceiptMonths=3, defectFromDiscoveryDays=30)
    res = extractor.build_scrape_result(raw, source_url="https://shop.example.com/refund", platform_hint=None, today=TODAY)
    assert res.status == "ok" and res.missing_fields == [] and res.fallback_applied == {}
    d = res.draft
    assert d.return_days == 14 and d.base_date == "receivedDate"
    assert d.return_fee.basic_fee == 3000 and d.return_fee.round_trip_fee == 6000 and d.return_fee.currency == "KRW"
    assert d.defect.from_receipt_months == 3 and d.defect.from_discovery_days == 30
    assert d.site_url == "https://shop.example.com" and d.collected_at == TODAY


def test_build_result_partial_keeps_unknowns_null():
    raw = _raw(returnFeeNote="무료")
    res = extractor.build_scrape_result(raw, source_url="https://shop.example.com/refund", platform_hint=None, today=TODAY)
    assert res.status == "partial"
    assert set(res.missing_fields) == {"returnDays", "baseDate", "howTo", "exclusions", "defect"}
    # 모르는 반품 기간을 법정 7일로 채우지 않는다 (null = 미확인)
    assert res.draft.return_days is None
    assert res.draft.return_fee.basic_fee is None and res.draft.return_fee.note == "무료"
    assert res.draft.base_date == "receivedDate" and "baseDate" in res.fallback_applied
    assert res.draft.platform == "shop.example.com"


def test_build_result_failed_when_nothing_found():
    res = extractor.build_scrape_result(_raw(), source_url=None, platform_hint=None, today=TODAY)
    assert res.status == "failed" and res.draft is None and res.error_code == "NOTHING_FOUND"


def test_sanitize_rejects_out_of_range_and_bad_types():
    clean = extractor.sanitize_raw(
        _raw(returnDays=99999, baseDate="TOMORROW", basicFee=-5, returnFeeNote=123, exclusions=["a", "", 5, "b"], howTo="  ")
    )
    assert clean["returnDays"] is None and clean["baseDate"] is None and clean["basicFee"] is None
    assert clean["returnFeeNote"] is None and clean["howTo"] is None
    assert clean["exclusions"] == ["a", "b"]


# ---------- 엔드포인트 ----------

def test_scrape_endpoint_success(client, auth, monkeypatch):
    monkeypatch.setattr(scraper, "fetch_page", lambda url, timeout: ScrapedPage("https://shop.example.com/refund", "텍스트" * 30))
    monkeypatch.setattr(extractor, "extract_policy", lambda text, hint=None: _raw(platform="예시몰", returnDays=10, baseDate="orderDate"))
    res = client.post("/api/policies/scrape", headers=auth, json={"url": "https://shop.example.com/refund"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "partial"
    assert body["draft"]["returnDays"] == 10 and body["draft"]["baseDate"] == "orderDate"
    assert body["draft"]["sourceUrl"] == "https://shop.example.com/refund"
    assert body["draft"]["returnFee"]["basicFee"] is None
    assert "returnFee" in body["missingFields"]


def test_scrape_endpoint_failure_is_not_an_http_error(client, auth, monkeypatch):
    def boom(url, timeout):
        raise ScrapeError("ACCESS_DENIED", "로그인이 필요합니다.")

    monkeypatch.setattr(scraper, "fetch_page", boom)
    res = client.post("/api/policies/scrape", headers=auth, json={"url": "https://shop.example.com/refund"})
    assert res.status_code == 200
    assert res.json()["status"] == "failed" and res.json()["errorCode"] == "ACCESS_DENIED"
    assert res.json()["draft"] is None


def test_scrape_endpoint_blocks_internal_url(client, auth):
    res = client.post("/api/policies/scrape", headers=auth, json={"url": "http://127.0.0.1:8000/health"})
    assert res.status_code == 200
    assert res.json()["status"] == "failed" and res.json()["errorCode"] == "URL_NOT_ALLOWED"


def test_parse_text_without_ai_key_reports_failure(client, auth):
    res = client.post("/api/policies/parse-text", headers=auth, json={"text": "단순 변심 반품은 수령 후 7일 이내 가능합니다."})
    assert res.status_code == 200
    assert res.json()["status"] == "failed" and res.json()["errorCode"] == "AI_NOT_CONFIGURED"


def test_policy_crud_uses_frontend_policy_shape(client, auth):
    created = client.post(
        "/api/policies", headers=auth,
        json={
            "platform": " 내몰 ", "returnDays": 14, "exclusions": ["착용 흔적"], "sourceUrl": "https://example.com/refund",
            "returnFee": {"basicFee": 3000, "roundTripFee": None, "currency": "KRW", "note": "단순 변심 구매자 부담"},
            "defect": {"fromReceiptMonths": 3, "fromDiscoveryDays": 30, "note": ""},
            # 서버가 정하는 값은 요청으로 바꿀 수 없다.
            "verificationStatus": "verified", "sourceType": "built-in",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["platform"] == "내몰" and body["collectedAt"] is not None
    assert body["sourceType"] == "user-input" and body["verificationStatus"] == "unverified"
    assert body["baseDate"] == "receivedDate" and body["includeStartDay"] is False
    assert body["holidayAdjustment"] == "not-applied"
    assert body["returnFee"] == {"basicFee": 3000, "roundTripFee": None, "currency": "KRW", "note": "단순 변심 구매자 부담"}
    assert body["defect"]["fromReceiptMonths"] == 3
    pid = body["id"]

    res = client.patch(f"/api/policies/{pid}", headers=auth, json={"returnDays": 30, "platform": None, "includeStartDay": True})
    assert res.status_code == 200
    assert res.json()["returnDays"] == 30 and res.json()["platform"] == "내몰" and res.json()["includeStartDay"] is True

    # returnDays를 null로 되돌리면 '미확인'이 된다.
    res = client.patch(f"/api/policies/{pid}", headers=auth, json={"returnDays": None})
    assert res.json()["returnDays"] is None

    mine = client.get("/api/policies", headers=auth, params={"sourceType": "user-input"}).json()
    assert [p["id"] for p in mine] == [pid]

    assert client.delete(f"/api/policies/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/policies/{pid}", headers=auth).status_code == 404


def test_policy_rejects_unsafe_urls_and_bad_values(client, auth):
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": 7, "siteUrl": "javascript:alert(1)"}).status_code == 422
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": -1}).status_code == 422
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": 7, "baseDate": "DELIVERED"}).status_code == 422


# ---------- 내장 규정 시드 ----------

def test_real_seed_data_is_loaded_in_frontend_format(client, auth):
    builtin = client.get("/api/policies", headers=auth, params={"sourceType": "built-in"}).json()
    by_id = {p["id"]: p for p in builtin}
    # src/data/shopping-policies.ts 의 shoppingPolicies 4곳
    assert {"coupang", "11st", "gmarket", "amazon"} <= set(by_id)
    coupang = by_id["coupang"]
    assert coupang["sourceType"] == "built-in" and coupang["verificationStatus"] == "verified"
    assert coupang["returnDays"] == 7 and coupang["baseDate"] == "receivedDate"
    assert coupang["returnFee"]["basicFee"] is None  # 미확인은 0원이 아니라 null
    assert coupang["collectedAt"] == "2026-11-21" and coupang["sourceUrl"].startswith("https://")
    assert by_id["amazon"]["returnFee"]["currency"] == "USD"


def test_builtin_policy_auto_links_by_name_or_id_and_is_readonly(client, auth):
    today = today_kst()
    p = client.post(
        "/api/purchases", headers=auth,
        json={"platform": "쿠팡", "productName": "니트", "price": 39000, "orderDate": str(today), "receivedDate": str(today)},
    ).json()
    assert p["policyId"] == "coupang"
    assert p["deadline"] == str(today + timedelta(days=7)) and p["policy"]["verificationStatus"] == "verified"

    by_id = client.post(
        "/api/purchases", headers=auth,
        json={"platform": "Coupang", "productName": "양말", "price": 3000, "orderDate": str(today)},
    ).json()
    assert by_id["policyId"] == "coupang"

    assert client.patch("/api/policies/coupang", headers=auth, json={"returnDays": 1}).status_code == 403
    assert client.delete("/api/policies/coupang", headers=auth).status_code == 403


def test_seed_loader_upserts_and_skips_invalid_items(client, auth, tmp_path):
    seed = tmp_path / "builtin.json"
    seed.write_text(
        json.dumps(
            [
                {"id": "seed-mall", "platform": "시드몰", "siteUrl": "https://seed.example.com", "sourceType": "built-in",
                 "returnDays": 7, "baseDate": "orderDate", "includeStartDay": True, "holidayAdjustment": "not-applied",
                 "returnFee": {"basicFee": 3000, "roundTripFee": None, "currency": "KRW", "note": "구매자 부담"},
                 "exclusions": ["택 제거"], "howTo": "마이페이지", "defect": {"fromReceiptMonths": 3, "fromDiscoveryDays": 30, "note": ""},
                 "sourceUrl": "https://seed.example.com/refund", "collectedAt": "2026-11-21",
                 "verificationStatus": "verified", "evidenceNote": "원문 대조"},
                {"id": "bad", "platform": "잘못된몰", "returnDays": "abc"},  # 형식 오류 항목은 건너뛴다
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with Session(engine) as s:
        assert seed_builtin_policies(s, seed) == 1
        assert seed_builtin_policies(s, seed) == 1  # 다시 실행해도 중복 생성되지 않는다

    p = client.get("/api/policies/seed-mall", headers=auth).json()
    assert p["sourceType"] == "built-in" and p["baseDate"] == "orderDate" and p["includeStartDay"] is True
    assert p["returnFee"]["basicFee"] == 3000 and p["evidenceNote"] == "원문 대조"
    assert client.get("/api/policies/bad", headers=auth).status_code == 404


# ---------- AI 환불상담 ----------

def test_legal_check_without_ai_key(client, auth):
    res = client.post("/api/chat/legal-check", headers=auth, json={"question": "택 제거하면 반품 불가라는데 맞나요?"})
    assert res.status_code == 503
    assert res.json()["code"] == "AI_NOT_CONFIGURED"


def test_legal_check_returns_fixed_disclaimer(client, auth, monkeypatch):
    monkeypatch.setattr(legal_chat, "answer", lambda q, p: ("문제 소지가 있습니다.", ["전자상거래법 제17조"]))
    res = client.post("/api/chat/legal-check", headers=auth, json={"policyId": "coupang", "question": "반품 불가 조항이 합법인가요?"})
    assert res.status_code == 200
    body = res.json()
    assert body["answer"] == "문제 소지가 있습니다." and body["basis"] == ["전자상거래법 제17조"]
    assert body["disclaimer"] == legal_chat.DISCLAIMER and "1372" in body["disclaimer"]


def test_legal_check_unknown_policy(client, auth):
    res = client.post("/api/chat/legal-check", headers=auth, json={"policyId": "does-not-exist", "question": "질문"})
    assert res.status_code == 404


def test_llm_error_is_mapped(client, auth, monkeypatch):
    def boom(q, p):
        raise LLMError("AI_TIMEOUT", "느림")

    monkeypatch.setattr(legal_chat, "answer", boom)
    res = client.post("/api/chat/legal-check", headers=auth, json={"question": "질문"})
    assert res.status_code == 503 and res.json()["code"] == "AI_TIMEOUT"


def test_describe_policy_marks_unknowns_instead_of_zero(client):
    from app.models import Policy

    p = Policy(platform="몰", return_days=None, exclusions=[], return_fee={"basicFee": None, "roundTripFee": None, "currency": "KRW", "note": ""})
    text = legal_chat._describe_policy(p)
    assert "확인되지 않음" in text and "0원" not in text
