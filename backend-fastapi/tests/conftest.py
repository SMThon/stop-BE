import os
import tempfile
import uuid
from pathlib import Path

# app을 import 하기 전에 테스트용 설정을 환경변수로 먼저 지정한다.
# (환경변수는 .env 파일보다 우선하므로 실제 DB에 접속하지 않는다.)
_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_tmp_dir) / 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["UPSTAGE_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def make_user(client: TestClient, password: str = "password123") -> tuple[str, dict[str, str]]:
    email = f"user-{uuid.uuid4().hex[:10]}@example.com"
    res = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert res.status_code == 201, res.text
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return email, {"Authorization": f"Bearer {res.json()['accessToken']}"}


@pytest.fixture
def auth(client):
    """새 사용자를 만들고 로그인한 Authorization 헤더를 돌려준다."""
    return make_user(client)[1]
