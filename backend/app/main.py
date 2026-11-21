from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.config import settings
from app.database import engine, init_db
from app.errors import register_error_handlers
from app.routers import auth, calendar, chat, events, notifications, policies, purchases
from app.services.seed import seed_builtin_policies


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with Session(engine) as session:
        seed_builtin_policies(session)
    yield


app = FastAPI(
    title="환불정거장 API",
    description="환불 규정 수집, 환불 마감일 캘린더, AI 환불상담 백엔드",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

for module in (auth, policies, purchases, events, calendar, notifications, chat):
    app.include_router(module.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
