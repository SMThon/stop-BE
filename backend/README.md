# Railway PostgreSQL 백엔드

이 서버는 기존 검증용 화면과 별도로 실행되는 HTTP API입니다. Railway 프로젝트에 PostgreSQL 서비스와 이 저장소의 앱 서비스를 추가하고 앱 서비스의 `DATABASE_URL`을 PostgreSQL 서비스의 `DATABASE_URL` 변수 참조로 설정합니다. Railway가 제공하는 `PORT`를 사용합니다. 빌드 명령은 `npm ci --legacy-peer-deps`, 시작 명령은 `npm run db:migrate && npm start`로 설정합니다. 스키마 생성에는 CREATE 권한이 필요합니다. PostgreSQL은 외부 공개 없이 내부 네트워크로 연결합니다.

## API

- `GET /health`: DB 연결 상태 확인
- `POST /api/users`: 익명 사용자와 접근 토큰 생성. 응답의 `token`은 한 번만 표시됩니다. 안전하게 보관하세요. 토큰을 분실하면 기존 기록에 접근할 수 없습니다.
- `GET /api/purchases`, `POST /api/purchases`, `GET /api/purchases/:id`, `PUT /api/purchases/:id`, `DELETE /api/purchases/:id`
- `GET /api/subscriptions`, `POST /api/subscriptions`, `GET /api/subscriptions/:id`, `PUT /api/subscriptions/:id`, `DELETE /api/subscriptions/:id`

기록 API는 `Authorization: Bearer <token>`이 필요하며 생성·수정 요청은 `Content-Type: application/json`을 사용합니다. PUT은 전체 레코드를 교체합니다. 목록은 최대 200건입니다. 본문은 `src/data/service-types.ts`의 Purchase 또는 Subscription에서 `id`를 제외한 필드를 사용하며 모든 필드가 필요합니다. 날짜는 유효한 `YYYY-MM-DD`, 가격은 0 이상의 정수입니다. 토큰은 사용자 비밀번호나 로그인 시스템을 대신하는 임시 접근 수단으로, 공유하거나 브라우저 코드에 고정하지 마세요. 운영 시 계정 복구, 토큰 폐기, 요청 제한과 인증 체계를 추가해야 합니다.

예시 구매 생성 본문:
```json
{"platform":"쿠팡","policyId":"coupang","productName":"상품","price":10000,"orderDate":"2026-11-21","receivedDate":null,"deadline":null,"status":"보관 중"}
```

서버는 마감일을 자동 계산하지 않습니다. 기존 날짜 계산 함수와 프론트엔드 연동은 별도로 필요합니다. 환불 정책 데이터는 기존 소스에 있으며 이 API가 DB로 자동 적재하지 않습니다.
