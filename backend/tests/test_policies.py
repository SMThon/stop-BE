import json
from datetime import date

import pytest
from sqlmodel import Session

from app.database import engine
from app.services import extractor, legal_chat, scraper
from app.services.llm import LLMError
from app.services.scraper import ScrapedPage, ScrapeError, html_to_text, validate_public_url
from app.services.seed import seed_builtin_policies

TODAY = date(2026, 11, 21)


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
    raw = {"platform": "테스트몰", "returnDays": 14, "baseDate": "RECEIVED", "returnFee": "편도 3,000원",
           "exclusions": ["택 제거"], "howTo": "마이페이지에서 신청"}
    res = extractor.build_scrape_result(raw, source_url="https://shop.example.com/refund", platform_hint=None, today=TODAY)
    assert res.status == "ok" and res.missing_fields == [] and res.fallback_applied == {}
    assert res.draft.return_days == 14
    assert res.draft.site_url == "https://shop.example.com"
    assert res.draft.collected_at == TODAY


def test_build_result_partial_applies_legal_default():
    raw = {"platform": None, "returnDays": None, "baseDate": None, "returnFee": "무료", "exclusions": [], "howTo": None}
    res = extractor.build_scrape_result(raw, source_url="https://shop.example.com/refund", platform_hint=None, today=TODAY)
    assert res.status == "partial"
    assert set(res.missing_fields) == {"returnDays", "baseDate", "howTo", "exclusions"}
    assert res.draft.return_days == 7 and res.draft.base_date == "RECEIVED"
    assert "returnDays" in res.fallback_applied
    assert res.draft.platform == "shop.example.com"


def test_build_result_failed_when_nothing_found():
    raw = {"platform": None, "returnDays": None, "baseDate": None, "returnFee": None, "exclusions": [], "howTo": None}
    res = extractor.build_scrape_result(raw, source_url=None, platform_hint=None, today=TODAY)
    assert res.status == "failed" and res.draft is None and res.error_code == "NOTHING_FOUND"


def test_sanitize_rejects_out_of_range_and_bad_types():
    clean = extractor.sanitize_raw(
        {"returnDays": 99999, "baseDate": "TOMORROW", "returnFee": 123, "exclusions": ["a", "", 5, "b"], "howTo": "  "}
    )
    assert clean["returnDays"] is None and clean["baseDate"] is None
    assert clean["returnFee"] is None and clean["howTo"] is None
    assert clean["exclusions"] == ["a", "b"]


# ---------- 엔드포인트 ----------

def test_scrape_endpoint_success(client, auth, monkeypatch):
    monkeypatch.setattr(scraper, "fetch_page", lambda url, timeout: ScrapedPage("https://shop.example.com/refund", "텍스트" * 30))
    monkeypatch.setattr(
        extractor, "extract_policy",
        lambda text, hint=None: {"platform": "예시몰", "returnDays": 10, "baseDate": "ORDERED", "returnFee": None, "exclusions": [], "howTo": None},
    )
    res = client.post("/api/policies/scrape", headers=auth, json={"url": "https://shop.example.com/refund"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "partial"
    assert body["draft"]["returnDays"] == 10 and body["draft"]["baseDate"] == "ORDERED"
    assert body["draft"]["sourceUrl"] == "https://shop.example.com/refund"
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


def test_policy_crud(client, auth):
    created = client.post(
        "/api/policies", headers=auth,
        json={"platform": " 내몰 ", "returnDays": 14, "exclusions": ["착용 흔적"], "sourceUrl": "https://example.com/refund"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["platform"] == "내몰" and body["sourceType"] == "user" and body["collectedAt"] is not None
    pid = body["id"]

    res = client.patch(f"/api/policies/{pid}", headers=auth, json={"returnDays": 30, "returnDays2": 1, "platform": None})
    assert res.status_code == 200
    assert res.json()["returnDays"] == 30 and res.json()["platform"] == "내몰"

    mine = client.get("/api/policies", headers=auth, params={"sourceType": "user"}).json()
    assert [p["id"] for p in mine] == [pid]

    assert client.delete(f"/api/policies/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/policies/{pid}", headers=auth).status_code == 404


def test_policy_rejects_unsafe_urls_and_bad_values(client, auth):
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": 7, "siteUrl": "javascript:alert(1)"}).status_code == 422
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": -1}).status_code == 422
    assert client.post("/api/policies", headers=auth, json={"platform": "x", "returnDays": 7, "baseDate": "DELIVERED"}).status_code == 422


def test_builtin_seed_links_and_is_readonly(client, auth, tmp_path):
    seed = tmp_path / "builtin.json"
    seed.write_text(
        json.dumps(
            [
                {"platform": "시드몰", "siteUrl": "https://seed.example.com", "returnDays": 7, "baseDate": "RECEIVED",
                 "returnFee": "3,000원", "exclusions": ["택 제거"], "howTo": "마이페이지", "sourceUrl": "https://seed.example.com/refund", "collectedAt": "2026-11-21"},
                {"platform": "잘못된몰", "returnDays": "abc"},  # 형식 오류 항목은 건너뛴다
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with Session(engine) as s:
        assert seed_builtin_policies(s, seed) == 1
        assert seed_builtin_policies(s, seed) == 1  # 다시 실행해도 중복 생성되지 않는다

    builtin = client.get("/api/policies", headers=auth, params={"sourceType": "builtin"}).json()
    seeded = [p for p in builtin if p["platform"] == "시드몰"]
    assert len(seeded) == 1 and seeded[0]["sourceType"] == "builtin"
    pid = seeded[0]["id"]

    assert client.patch(f"/api/policies/{pid}", headers=auth, json={"returnDays": 1}).status_code == 403
    assert client.delete(f"/api/policies/{pid}", headers=auth).status_code == 403

    # 쇼핑몰 이름만 적어도 내장 규정이 자동 연결된다 (FR-04).
    res = client.post(
        "/api/purchases", headers=auth,
        json={"platform": " 시드 몰 ", "productName": "니트", "price": 39000, "orderDate": "2026-11-15", "receivedDate": "2026-11-18"},
    )
    assert res.status_code == 201
    assert res.json()["policyId"] == pid
    assert res.json()["deadline"] == "2026-11-25" and res.json()["deadlineBasis"] == "policy"


# ---------- AI 환불상담 ----------

def test_legal_check_without_ai_key(client, auth):
    res = client.post("/api/chat/legal-check", headers=auth, json={"question": "택 제거하면 반품 불가라는데 맞나요?"})
    assert res.status_code == 503
    assert res.json()["code"] == "AI_NOT_CONFIGURED"


def test_legal_check_returns_fixed_disclaimer(client, auth, monkeypatch):
    monkeypatch.setattr(legal_chat, "answer", lambda q, p: ("문제 소지가 있습니다.", ["전자상거래법 제17조"]))
    res = client.post("/api/chat/legal-check", headers=auth, json={"question": "반품 불가 조항이 합법인가요?"})
    assert res.status_code == 200
    body = res.json()
    assert body["answer"] == "문제 소지가 있습니다." and body["basis"] == ["전자상거래법 제17조"]
    assert body["disclaimer"] == legal_chat.DISCLAIMER and "1372" in body["disclaimer"]


def test_legal_check_unknown_policy(client, auth):
    res = client.post("/api/chat/legal-check", headers=auth, json={"policyId": 999999, "question": "질문"})
    assert res.status_code == 404


def test_llm_error_is_mapped(client, auth, monkeypatch):
    def boom(q, p):
        raise LLMError("AI_TIMEOUT", "느림")

    monkeypatch.setattr(legal_chat, "answer", boom)
    res = client.post("/api/chat/legal-check", headers=auth, json={"question": "질문"})
    assert res.status_code == 503 and res.json()["code"] == "AI_TIMEOUT"
