from datetime import timedelta

from app.services.deadline import today_kst
from tests.conftest import make_user


def _policy(client, headers, platform="테스트몰", days=7, base="RECEIVED"):
    res = client.post(
        "/api/policies",
        headers=headers,
        json={"platform": platform, "returnDays": days, "baseDate": base, "exclusions": ["택 제거"]},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _purchase(client, headers, **kw):
    body = {"platform": "테스트몰", "productName": "러닝화", "price": 59000, "orderDate": str(today_kst())}
    body.update(kw)
    res = client.post("/api/purchases", headers=headers, json=body)
    assert res.status_code == 201, res.text
    return res.json()


def test_purchase_deadline_uses_linked_policy(client, auth):
    policy_id = _policy(client, auth)
    today = today_kst()
    p = _purchase(client, auth, policyId=policy_id, receivedDate=str(today))
    assert p["deadline"] == str(today + timedelta(days=7))
    assert p["dday"] == 7
    assert p["level"] == "green"
    assert p["deadlineBasis"] == "policy"
    assert p["policy"]["id"] == policy_id
    assert p["status"] == "KEEPING"


def test_purchase_without_received_date_has_no_deadline(client, auth):
    p = _purchase(client, auth)
    assert p["deadline"] is None and p["dday"] is None and p["level"] is None


def test_purchase_without_policy_uses_legal_default(client, auth):
    today = today_kst()
    p = _purchase(client, auth, platform="규정없는몰", receivedDate=str(today))
    assert p["policy"] is None
    assert p["deadlineBasis"] == "legal_default"
    assert p["deadline"] == str(today + timedelta(days=7))


def test_expired_purchase_is_flagged(client, auth):
    policy_id = _policy(client, auth)
    old = today_kst() - timedelta(days=30)
    p = _purchase(client, auth, policyId=policy_id, orderDate=str(old), receivedDate=str(old))
    assert p["status"] == "EXPIRED"
    assert p["level"] == "gray"
    assert p["dday"] < 0


def test_purchase_update_and_status(client, auth):
    policy_id = _policy(client, auth)
    p = _purchase(client, auth, policyId=policy_id)
    pid = p["id"]
    res = client.patch(f"/api/purchases/{pid}", headers=auth, json={"receivedDate": str(today_kst()), "status": "RETURN_REQUESTED"})
    assert res.status_code == 200
    assert res.json()["status"] == "RETURN_REQUESTED"
    assert res.json()["deadline"] is not None
    # EXPIRED는 직접 저장할 수 없다.
    assert client.patch(f"/api/purchases/{pid}", headers=auth, json={"status": "EXPIRED"}).status_code == 422
    # 수령일이 주문일보다 빠르면 거부
    bad = client.patch(f"/api/purchases/{pid}", headers=auth, json={"receivedDate": str(today_kst() - timedelta(days=5))})
    assert bad.status_code == 422
    assert client.delete(f"/api/purchases/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/purchases/{pid}", headers=auth).status_code == 404


def test_calendar_and_upcoming(client):
    _, headers = make_user(client)
    policy_id = _policy(client, headers)
    today = today_kst()
    # 수령 6일 전 → 마감 D-1 (빨강, 임박)
    near = _purchase(client, headers, policyId=policy_id, orderDate=str(today - timedelta(days=6)), receivedDate=str(today - timedelta(days=6)))
    assert near["dday"] == 1 and near["level"] == "red"
    # 환불 완료된 건은 캘린더에서 빠진다.
    done = _purchase(client, headers, policyId=policy_id, receivedDate=str(today))
    client.patch(f"/api/purchases/{done['id']}", headers=headers, json={"status": "REFUNDED"})
    ev = client.post("/api/events", headers=headers, json={"title": "넷플릭스 결제일", "date": str(today + timedelta(days=10)), "memo": "13,500원"})
    assert ev.status_code == 201

    month = (today + timedelta(days=1)).strftime("%Y-%m")
    res = client.get("/api/calendar", headers=headers, params={"month": month})
    assert res.status_code == 200
    body = res.json()
    types = {e["type"] for e in body["events"]}
    assert "refund" in types
    assert body["imminentCount"] == 1
    assert all(e["refId"] != done["id"] or e["type"] != "refund" for e in body["events"])

    up = client.get("/api/deadlines/upcoming", headers=headers).json()
    assert [i["type"] for i in up["items"]] == ["refund", "custom"]
    assert up["items"][0]["dday"] == 1
    assert up["items"][1]["title"] == "넷플릭스 결제일"
    assert up["imminentCount"] == 1


def test_calendar_rejects_bad_month(client, auth):
    res = client.get("/api/calendar", headers=auth, params={"month": "2026-13"})
    assert res.status_code == 422
    assert res.json()["code"] == "INVALID_MONTH"


def test_event_crud(client, auth):
    created = client.post("/api/events", headers=auth, json={"title": "유튜브 프리미엄", "date": "2026-12-03"}).json()
    eid = created["id"]
    assert created["memo"] is None
    res = client.patch(f"/api/events/{eid}", headers=auth, json={"date": "2026-12-05", "memo": "연장"})
    assert res.json()["date"] == "2026-12-05" and res.json()["memo"] == "연장"
    assert client.delete(f"/api/events/{eid}", headers=auth).status_code == 204
    assert client.get(f"/api/events/{eid}", headers=auth).status_code == 404


def test_users_cannot_see_each_others_data(client):
    _, a = make_user(client)
    _, b = make_user(client)
    pa = _purchase(client, a)
    ea = client.post("/api/events", headers=a, json={"title": "A의 일정", "date": "2026-12-03"}).json()
    own_policy = _policy(client, a, platform="A전용몰")

    assert client.get(f"/api/purchases/{pa['id']}", headers=b).status_code == 404
    assert client.patch(f"/api/purchases/{pa['id']}", headers=b, json={"price": 1}).status_code == 404
    assert client.delete(f"/api/purchases/{pa['id']}", headers=b).status_code == 404
    assert client.get(f"/api/events/{ea['id']}", headers=b).status_code == 404
    assert client.get(f"/api/policies/{own_policy}", headers=b).status_code == 404
    assert client.get("/api/purchases", headers=b).json() == []
    # B가 A의 규정으로 구매를 등록하려 해도 막힌다.
    res = client.post(
        "/api/purchases", headers=b,
        json={"platform": "x", "productName": "y", "price": 1, "orderDate": str(today_kst()), "policyId": own_policy},
    )
    assert res.status_code == 404
