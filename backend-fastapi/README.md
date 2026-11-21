# 환불정거장 백엔드 (FastAPI)

환불 기한 관리 서비스의 API 서버. Python · FastAPI · SQLModel · PostgreSQL(Railway). Swagger: `/docs`.

> 기존 `backend/`(Node)와 충돌하지 않도록 별도 폴더 `backend-fastapi/`에 두었고,
> 프론트 `src/data/service-types.ts`의 필드명·값을 그대로 따른다.

## 프론트와 맞춘 계약

- 규정(Policy): `id`(슬러그/UUID), `platform`, `siteUrl`, `sourceType`(`built-in`|`user-input`), `returnDays`(null=미확인),
  `baseDate`(`receivedDate`|`orderDate`), `includeStartDay`, `returnFee{basicFee,roundTripFee,currency,note}`,
  `exclusions[]`, `howTo`, `defect{...}`, `verificationStatus`, `evidenceNote` 등
- 구매 상태: `보관 중` / `반품 신청` / `환불 완료` / `기한 지남`(서버가 마감일로 계산)
- 마감일 = 기준일 + returnDays − (includeStartDay ? 1 : 0). 기간을 모르면 마감일도 null (법정 7일로 대체하지 않음)
- D-day 색: 지남 gray, D-2 이하 red, D-5 이하 yellow, 그 외 green
- ID는 UUID 문자열

## DB 공유 (Railway PostgreSQL)

기존 Node 백엔드의 `api_users`/`purchases`/`subscriptions`와 겹치지 않도록 테이블에 `app_` 접두사를 쓴다
(`app_users`, `app_policies`, `app_purchases`, `app_events`, `app_notification_settings`).

## 실행

```bash
python -m venv .venv && .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY 입력
uvicorn app.main:app --reload
pytest
```

`DATABASE_URL`은 Railway의 PostgreSQL URL (`postgres://`도 자동 변환). 로컬에서는 public URL을 쓴다.

## 배포 (Railway)

서비스의 Root Directory를 `backend-fastapi`로 지정하면 `railway.toml`(start: uvicorn, healthcheck `/health`)이 적용된다.
루트의 `railway.toml`은 기존 Node 서비스용이다.

## 내장 규정

`app/data/builtin_policies.json` — 프론트 `src/data/shopping-policies.ts`의 `shoppingPolicies`를 내보낸 파일.
서버 시작 시 id 기준으로 upsert 한다.

## 주요 API

| 영역 | 엔드포인트 |
|---|---|
| 인증 | `POST /api/auth/signup`, `login`, `logout`, `GET /me`, `POST /withdraw` |
| 규정 | `GET/POST /api/policies`, `POST /scrape`, `POST /parse-text`, `GET/PATCH/DELETE /{id}` |
| 구매 | `GET/POST /api/purchases`, `GET/PATCH/DELETE /{id}` |
| 일정 | `POST /api/events`, `GET/PATCH/DELETE /{id}` |
| 캘린더 | `GET /api/calendar?month=YYYY-MM`, `GET /api/deadlines/upcoming` |
| 알림 | `GET/PUT /api/notifications/settings` |
| AI 상담 | `POST /api/chat/legal-check` |
