# 환불정거장 — 데이터셋 및 협업 안내

> **업데이트:** Railway용 PostgreSQL 백엔드와 구매·구독 API가 추가되었습니다. 설정과 API 사용법은 [백엔드 안내](backend/README.md)를 참고하세요. 아래 구현 현황은 기존 데이터 모듈 기준의 기록이며, 백엔드 추가 전 상태를 설명합니다.



온라인 쇼핑몰·구독 서비스의 공식 환불 안내를 정형 데이터로 정리한 프로젝트입니다. 팀원은 이 문서에서 **제공 데이터, 연결 방법, 미구현 범위, 다음 작업**을 확인할 수 있습니다.

> 현재는 **데이터 모듈·날짜 계산 함수·검증용 뷰어**가 있는 상태입니다. 완성된 백엔드 API 서버가 아닙니다. **Neon 사용 예정이지만, 이 소스에는 Neon 연결 코드·DB 테이블·마이그레이션·구매/구독 저장 API가 아직 없습니다.**

문서 기준일: **2026-11-21 UTC**. 공식 원문 확인은 인용한 조항과 명시된 범위에 한정됩니다. 개별 환불 승인이나 이후 약관 변경 없음은 보장하지 않습니다.

## 1. 처음 읽는 팀원을 위한 순서

1. 이 문서에서 구현 상태와 제공 목록을 확인합니다.
2. [공통 타입](src/data/service-types.ts)에서 필드와 관계를 확인합니다.
3. [공식 환불 데이터](src/data/verified-refund-policies.ts)의 조건·기간·출처를 읽습니다.
4. [데이터 인수인계](src/data/DATA-HANDOFF.md)에서 연결 방법과 계산의 한계를 확인합니다.
5. [공식 원문 검증 기록](src/data/VERIFICATION-REPORT.md)에서 채택·제외 사유를 확인합니다.

## 2. 현재 구현 상태

| 구분 | 상태 | 내용 |
| --- | --- | --- |
| 공식 환불 안내 | 구현 | 직접 원문을 대조한 10곳, 조건·예외·출처·확인일 포함 |
| 쇼핑몰 정책 | 구현 | 제공용 4곳, 초안 별도 분리 |
| 구독 요금 프리셋 | 구현 | 네이버플러스 1곳, 월/연 2개 요금제 |
| 날짜 계산 | 구현 | UTC 날짜 계산, D-day 경고, 결제 기준일 보존 |
| 가상 시연 데이터 | 구현 | 구매 2건·구독 2건, 기준일과 `isMock` 명시 |
| 검증용 뷰어 | 구현·유지 | 전체/쇼핑몰/구독/앱마켓 필터, 검색, 공식 근거 표시 |
| Neon 연결·테이블 | 미구현 | DB 사용 계획만 있음 |
| 구매·구독 저장/조회/수정/삭제 API | 미구현 | 현재는 타입과 가상 데이터만 있음 |
| 로그인·사용자별 접근 제어 | 미구현 | 실제 사용자 데이터 저장 전 설계 필요 |
| 자동 수집·정기 재검증·알림 발송 | 미구현 | 날짜 계산이 알림 발송을 의미하지 않음 |
| 공공 분쟁 통계 | 원자료 미확보 | 빈 배열 유지 |

현재 기술 구성은 **TypeScript, TanStack Start, React, Tailwind CSS, Vitest**입니다. `src/data`는 네트워크 요청이나 DB 연결 없이 사용할 수 있습니다.

## 3. 실제 서비스에서 사용할 데이터

### 공식 환불 안내: 10곳

| 화면 분류 | 사이트 | 제공 모듈 |
| --- | --- | --- |
| 쇼핑몰 4곳 | 쿠팡, 11번가, G마켓, Amazon | `verifiedRefundPolicies`, `shoppingPolicies` |
| 구독 서비스 4곳 | 네이버플러스, Spotify, YouTube Premium, ChatGPT Plus | `verifiedRefundPolicies` |
| 앱마켓 2곳 | Apple App Store, Google Play | `verifiedRefundPolicies` |

앱마켓은 데이터의 `category`에서는 `subscription`에 포함되고, `subcategory === "앱마켓"`으로 구분합니다. 따라서 데이터 범주는 쇼핑 4곳·구독 6곳이고, 화면은 쇼핑 4곳·구독 4곳·앱마켓 2곳입니다.

### 가격 자동입력: 네이버플러스만 제공

| 요금제 ID | 이름 | 확인한 가격 | 주기 |
| --- | --- | --- | --- |
| `naver-monthly` | 월간 이용권 | 4,900원 | 월 |
| `naver-yearly` | 연간 이용권 | 46,800원 | 연 |

환불 안내 검증이 가격 검증을 뜻하지 않습니다. `getPresetDefaults()`는 제외된 서비스나 잘못된 요금제 ID에 `null`을 반환합니다. 호출부는 직접입력 또는 선택 불가를 처리해야 합니다.

### 운영에 연결하면 안 되는 데이터

- `refund-policies.ts` / `checkRefund()`: 초기 22곳의 **미검증 호환용 초안**입니다. 기존 오류가 남아 있으므로 실제 환불 판정에 사용하지 않습니다.
- `draftShoppingPolicies`: 9곳의 초안 후보입니다. 제공용 `shoppingPolicies`와 합치지 않습니다.
- `draftSubscriptionPresets`: 6곳·16개 요금제 후보 묶음입니다. 네이버의 확인된 값도 포함하지만 실제 선택 목록은 필터링된 `subscriptionPresets`만 사용합니다.
- `standardPolicy`: 현행 법령 전문 검수가 끝나지 않은 템플릿입니다. `autoApprove: false`입니다.
- `publicDisputeStats`: 실제 원자료가 없어 `[]`입니다.
- 기존에 공유한 `refund-policies.json`·`refund-policies.csv`: 초기 초안의 내보내기 파일이므로 검증된 10곳의 데이터로 사용하지 않습니다.

## 4. 주요 파일

| 파일 | 역할 |
| --- | --- |
| [service-types.ts](src/data/service-types.ts) | Purchase / Subscription / Policy 및 출처·검증 타입 |
| [verified-refund-policies.ts](src/data/verified-refund-policies.ts) | 제공용 환불 안내 10곳, 조건·근거·확인일 |
| [shopping-policies.ts](src/data/shopping-policies.ts) | 제공 정책 4곳·격리 초안·법령 템플릿·빈 통계 |
| [subscription-presets.ts](src/data/subscription-presets.ts) | 제공 요금 프리셋·격리 후보·기본값 함수 |
| [date-rules.ts](src/data/date-rules.ts) | UTC 날짜 계산·경고·결제일 보정 |
| [demo-data.ts](src/data/demo-data.ts) | 기준일을 명시한 가상 구매·구독 |
| [refund-policies.ts](src/data/refund-policies.ts) | 초기 호환용 초안, 운영 사용 금지 |
| [src/routes/index.tsx](src/routes/index.tsx) | 검증용 뷰어 |
| [DATA-HANDOFF.md](src/data/DATA-HANDOFF.md) | 연결 상세·데이터 계약·계산 한계 |
| [VERIFICATION-REPORT.md](src/data/VERIFICATION-REPORT.md) | 25곳 접근 결과·10곳 채택·15곳 제외 사유 |

## 5. 데이터 구조와 필드 의미

| 타입 | 역할 | 주요 필드 |
| --- | --- | --- |
| `VerifiedRefundPolicy` | 공식 환불 안내 | `id`, `name`, `category`, `subcategory`, `scope`, `rules`, `exclusions`, `sources`, `collectedAt` |
| `VerifiedRefundRule` | 조건부 규칙 | `outcome`, `refundPercent`, `period`, `conditions`, `sourceIds` |
| `OfficialSource` | 공식 원문 근거 | `url`, `section`, `quote`, `language`, `checkedAt` |
| `Policy` | 구매 마감일 계산용 정책 | `returnDays`, `baseDate`, `includeStartDay`, `returnFee`, `defect` |
| `Purchase` | 구매 기록 | `policyId`, `productName`, `price`, `orderDate`, `receivedDate`, `deadline`, `status` |
| `Subscription` | 구독 기록 | `presetId`, `planId`, `price`, `cycle`, `nextBillingDate`, `trialEndDate`, `deadline`, `cancelReminderDate`, `status` |
| `SubscriptionPreset` / `SubscriptionPlan` | 요금 프리셋 | `defaultPlanId`, `plans`, `price`, `cycle`, `billingChannel`, 검증 정보 |

이 타입은 현재 코드의 데이터 계약이며 **이미 생성된 DB 테이블이나 API 응답 명세가 아닙니다.**

- `null`은 미확인/값 없음입니다. 무료, 0원, 반품 불가로 바꾸지 않습니다.
- 날짜는 `YYYY-MM-DD`입니다. 타입 별칭은 문자열이므로 외부 입력은 별도로 검증합니다.
- `collectedAt`/`checkedAt`은 실제 원문 대조일입니다. 접근 실패일이나 초안 작성일로 대체하지 않습니다.
- `period`의 `value`, `unit`, `basis`를 함께 읽습니다. 3개월을 90일로, 48시간을 날짜 2일로 바꾸지 않습니다.
- `outcome: "request"`는 요청·심사 절차, `"conditional"`은 조건 확인 필요입니다. 환불 승인 결과가 아닙니다.
- `sourceIds`는 같은 정책의 `sources` 근거를 가리킵니다. DB로 옮길 때도 연결을 보존합니다.
- 최근 확인은 30일 이내, 확인 권장은 31~90일, 오래됨은 91일 이상입니다. 최근 확인이 현행 약관 보장은 아닙니다.

## 6. 연결 예시

아래 상대 경로는 `src` 바로 아래 파일에서 사용하는 예시입니다. 별도 백엔드 저장소에서는 모듈을 함께 옮기고 경로를 맞춥니다.

```ts
import { verifiedRefundPolicies } from "./data/verified-refund-policies";
import { shoppingPolicies } from "./data/shopping-policies";
import { getPresetDefaults } from "./data/subscription-presets";
import { calculatePurchaseDeadline } from "./data/date-rules";
import { createDemoData } from "./data/demo-data";

const guidance = verifiedRefundPolicies; // 확인한 10곳
const yearly = getPresetDefaults("naver-plus", "naver-yearly");
// yearly?.price: 46800
const unavailable = getPresetDefaults("netflix"); // null, 직접입력 처리

const policy = shoppingPolicies.find((item) => item.id === "coupang");
if (policy) {
  const deadline = calculatePurchaseDeadline(policy, {
    orderDate: "2026-11-16",
    receivedDate: "2026-11-18",
  });
  // deadline: "2026-11-25" — 일반 날짜 계산이지 환불 승인 아님
}

const demo = createDemoData("2026-11-01"); // isMock: true, 구매 2건·구독 2건
```

### 날짜 계산의 한계

- `calculatePurchaseDeadline()`은 기준일과 기간으로 날짜만 계산합니다. 수령일 또는 기간이 없으면 `null`입니다.
- 상품 예외, Amazon 시즌 연장, 공휴일 법적 연장, 플랫폼별 기산 해석을 자동 처리하지 않습니다.
- 날짜 마감이 해당 날짜 23:59까지 신청 가능하다는 보장 시각은 아닙니다. Google Play의 48시간 조건도 이 함수로 판정할 수 없습니다.
- `subscriptionDates()`의 `deadline`은 체험 종료일 또는 다음 결제 예정일입니다. `cancelReminderDate`는 전날의 권장 알림일이지 실제 해지 마감이 아닙니다.
- `advanceBillingDate()`에는 최초 결제 기준일을 유지해 전달합니다. 보정된 2월 말일을 새 기준으로 사용하면 원래 결제일이 바뀔 수 있습니다. 해지 완료 구독에는 적용하지 않습니다.
- 고정 `demoData`는 2026-11-21 기준입니다. 넷플릭스 결제일은 12월 3일이므로 ‘이번 달 4건’ 시연에는 월초 기준을 사용합니다.
- 넷플릭스·YouTube 시연 금액은 가상이며 `presetId`·`planId`는 `null`입니다. 검증 가격으로 표시하지 않습니다.

## 7. 실행 및 검사

전체 소스가 있는 저장소 루트에서 실행합니다. Bun이 설치되어 있어야 합니다.

```sh
bun install
bun run dev
```

개발 서버 주소는 실행 시 터미널에 표시됩니다. 데이터만 별도 백엔드로 가져가는 경우 UI 의존성을 전부 복사할 필요는 없지만, 가져온 모듈이 참조하는 데이터·타입 파일은 함께 옮겨야 합니다.

```sh
# 전체 검사
bun run test

# 데이터와 첫 화면 경로 검사
bunx vitest run src/data/service-data.test.ts src/data/refund-policies.test.ts src/data/verified-refund-policies.test.ts src/test/app-routing.test.tsx
```

레거시 검사 통과는 초안 동작 유지 확인이며 공식 규정 검증 완료를 뜻하지 않습니다. 정책 변경 시 공식 규칙 검사와 관련 날짜·프리셋 검사를 함께 갱신합니다.

## 8. 담당별 다음 작업

| 담당 | 다음 작업 |
| --- | --- |
| 백엔드 | railway 연결, 정책·출처·요금·구매·구독 저장 구조, API 입력 검증, 사용자별 접근 제어 |
| 프론트엔드 | 제공용 목록만 연결, `null` 값·조건부 안내·미확인 가격 처리, 기존 뷰어 참고 |
| 데이터 | 제외한 15곳의 국내 공식 상세 원문 확보, 값별 출처·인용·범위·확인일 추가 |
| 요금 | 웹/앱/제휴/프로모션 가격 구분, 확인한 요금만 제공 목록에 반영 |
| 정책·법률 검수 | 기산일, 하자 기간 관계, 상품 예외, 공휴일 연장 검수 |
| 통계 | 공공 원자료 확보, 연도·분류·단위·상담/피해구제 구분 |

### Neon 연동 체크리스트 — 현재 미구현

- [ ] 접속 정보는 서버의 비밀 설정으로 관리하고 코드·문서·브라우저에 넣지 않기
- [ ] 공식 출처·규칙 조건·기간 단위·확인일을 보존하는 저장 구조 설계
- [ ] 제공용 목록과 격리 초안을 분리해 초기 데이터 적재
- [ ] 구매·구독 입력 검증 및 사용자별 조회·수정 권한 적용
- [ ] 날짜 계산 결과와 환불 승인을 구분한 API 계약 작성
- [ ] 실제 DB에서 저장 → 조회 → 수정 → 삭제 검증
- [ ] 가상 시연 데이터와 실제 사용자 기록 분리

## 9. 변경·공유 규칙

1. 공식 상세 원문을 직접 읽은 항목만 검증 완료로 반영합니다. 검색 결과·홈페이지 접속만으로 승격하지 않습니다.
2. 정책 변경은 **규칙 + 조건/범위 + 출처/인용 + 확인일 + 검사 + 인수인계 문서**를 함께 수정합니다.
3. 미확인 요금·반품비·신청 기한을 추정하지 않습니다. 사이트 제공 제외가 ‘환불 불가’를 뜻하지 않습니다.
4. 기존 모듈의 필드·내보내기를 변경할 때 소비 코드와 호환성을 확인합니다.
5. GitHub에는 필요한 소스와 문서만 올립니다. `.env`, 비밀키, `node_modules`, 생성 빌드 결과, 다른 저장소의 `.git`은 올리지 않습니다.
6. 이 README를 저장소 루트에 놓으면 GitHub에서 첫 안내로 보입니다. 데이터 폴더를 다른 위치로 옮기면 상대 링크도 맞춥니다.

상세 원문과 제외 사유는 [검증 기록](src/data/VERIFICATION-REPORT.md), 상세 연결 계약은 [인수인계 문서](src/data/DATA-HANDOFF.md)를 기준으로 확인합니다.
