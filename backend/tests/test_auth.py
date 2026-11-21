from sqlmodel import Session, func, select

from app.database import engine
from app.models import Event, Purchase, User
from tests.conftest import make_user


def test_signup_login_me(client):
    email, headers = make_user(client)
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == email
    assert "passwordHash" not in res.json()


def test_signup_duplicate_email(client):
    email, _ = make_user(client)
    res = client.post("/api/auth/signup", json={"email": email.upper(), "password": "password123"})
    assert res.status_code == 409
    assert res.json()["code"] == "EMAIL_EXISTS"


def test_signup_rejects_bad_email_and_short_password(client):
    assert client.post("/api/auth/signup", json={"email": "nope", "password": "password123"}).status_code == 422
    assert client.post("/api/auth/signup", json={"email": "a@example.com", "password": "short"}).status_code == 422


def test_login_wrong_password(client):
    email, _ = make_user(client)
    res = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email_gives_same_error(client):
    res = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "password123"})
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_CREDENTIALS"


def test_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/purchases").status_code == 401
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert res.status_code == 401
    assert res.json()["code"] == "INVALID_TOKEN"


def test_logout(client, auth):
    assert client.post("/api/auth/logout", headers=auth).status_code == 204


def test_withdraw_deletes_all_user_data(client):
    email, headers = make_user(client)
    client.post("/api/events", headers=headers, json={"title": "넷플릭스", "date": "2026-12-03"})
    client.post(
        "/api/purchases",
        headers=headers,
        json={"platform": "테스트몰", "productName": "러닝화", "price": 59000, "orderDate": "2026-11-15"},
    )
    me = client.get("/api/auth/me", headers=headers).json()

    # 비밀번호가 틀리면 탈퇴되지 않는다.
    assert client.post("/api/auth/withdraw", headers=headers, json={"password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/withdraw", headers=headers, json={"password": "password123"}).status_code == 204

    with Session(engine) as s:
        assert s.exec(select(func.count()).select_from(User).where(User.id == me["id"])).one() == 0
        assert s.exec(select(func.count()).select_from(Event).where(Event.user_id == me["id"])).one() == 0
        assert s.exec(select(func.count()).select_from(Purchase).where(Purchase.user_id == me["id"])).one() == 0

    # 탈퇴한 계정은 로그인도, 기존 토큰 사용도 안 된다.
    assert client.post("/api/auth/login", json={"email": email, "password": "password123"}).status_code == 401
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_notification_settings(client, auth):
    res = client.get("/api/notifications/settings", headers=auth)
    assert res.status_code == 200
    assert res.json() == {"enabled": True, "daysBefore": [3, 1]}

    res = client.put("/api/notifications/settings", headers=auth, json={"enabled": False, "daysBefore": [1, 7, 7]})
    assert res.status_code == 200
    assert res.json() == {"enabled": False, "daysBefore": [7, 1]}
    assert client.get("/api/notifications/settings", headers=auth).json()["enabled"] is False

    assert client.put("/api/notifications/settings", headers=auth, json={"enabled": True, "daysBefore": [99]}).status_code == 422
