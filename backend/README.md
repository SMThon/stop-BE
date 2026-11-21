# 환불정거장 백엔드

FastAPI + PostgreSQL(SQLModel). 배포는 Railway.

## 실행

```
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env        # DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY 채우기
.venv\Scripts\python -m uvicorn app.main:app --reload
```

- Swagger: http://localhost:8000/docs (우측 상단 Authorize에 로그인 토큰을 넣으면 바로 호출 가능)
- 테스트: `.venv\Scripts\python -m pytest` (임시 SQLite를 쓰므로 실제 DB에 영향 없음)

## 환경변수

| 이름 | 설명 |
|---|---|
| `DATABASE_URL` | 로컬 개발은 Railway의 `DATABASE_PUBLIC_URL`. Railway 배포 서비스에서는 PostgreSQL 서비스의 `DATABASE_URL`을 참조 변수로 연결 |
| `SECRET_KEY` | 로그인 토큰 서명용 임의의 긴 문자열 (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ANTHROPIC_API_KEY` | 규정 추출(FR-02)·AI 환불상담(FR-15). 비어 있으면 해당 기능만 `AI_NOT_CONFIGURED`로 응답 |
| `ANTHROPIC_MODEL` | 기본 `claude-sonnet-5-5` |
| `CORS_ORIGINS` | 프론트 주소 (쉼표로 여러 개) |
| `SCRAPE_TIMEOUT_SECONDS` | URL 수집 타임아웃 (기본 10) |

## API 요약

모든 응답 JSON은 camelCase입니다. 오류는 `{"code": "...", "message": "..."}` 형식입니다.
회원가입·로그인·`/health` 외에는 `Authorization: Bearer <토큰>`이 필요합니다.

| 영역 | 엔드포인트 |
|---|---|
| 인증 | `POST /api/auth/signup` · `login` · `logout` · `withdraw`, `GET /api/auth/me` |
| 환불 규정 | `GET /api/policies?sourceType=`, `POST /api/policies/scrape`, `POST /api/policies/parse-text`, `POST/GET/PATCH/DELETE /api/policies/{id}` |
| 구매내역 | `GET/POST /api/purchases`, `GET/PATCH/DELETE /api/purchases/{id}` |
| 내 일정 | `POST /api/events`, `GET/PATCH/DELETE /api/events/{id}` |
| 캘린더 | `GET /api/calendar?month=YYYY-MM`, `GET /api/deadlines/upcoming?limit=` |
| 알림 설정 | `GET/PUT /api/notifications/settings` (설정 저장만, 실제 발송은 미구현) |
| AI 환불상담 | `POST /api/chat/legal-check` |

구매 상태값: `KEEPING`(보관 중), `RETURN_REQUESTED`(반품 신청), `REFUNDED`(환불 완료), `EXPIRED`(기한 지남, 서버가 계산).
D-day 색상 `level`: `red`(D-2 이하), `yellow`(D-3~5), `green`, `gray`(지남).

## 내장 환불 규정 채우기

`app/data/builtin_policies.json`에 아래 형식으로 적으면 서버가 시작될 때 DB에 들어갑니다
(같은 `platform`이 있으면 갱신). 각 사이트의 공지·고객센터 원문을 **직접 확인한 값만** 넣고 `collectedAt`을 기록하세요.

```json
[
  {
    "platform": "쿠팡",
    "siteUrl": "https://www.coupang.com",
    "returnDays": 7,
    "baseDate": "RECEIVED",
    "returnFee": "단순 변심 시 고객 부담",
    "exclusions": ["포장 개봉 후 재판매 곤란한 상품"],
    "howTo": "마이쿠팡 > 주문목록 > 반품신청",
    "sourceUrl": "https://...",
    "collectedAt": "2026-11-21"
  }
]
```

`baseDate`는 `RECEIVED`(수령일 기준) 또는 `ORDERED`(주문일 기준)입니다.
위 예시의 값은 형식을 보여주기 위한 것이며 실제 확인된 내용이 아닙니다.
