from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings


def _normalize_url(url: str) -> str:
    # Railway는 postgres:// 또는 postgresql:// 로 주소를 주는데,
    # psycopg(v3) 드라이버를 쓰려면 postgresql+psycopg:// 형식이어야 한다.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


_url = _normalize_url(settings.database_url)
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)


def init_db() -> None:
    from app import models  # noqa: F401  (테이블 정의를 불러와 등록)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
