# 환불정거장 데이터 인수인계

## 2026-11-21 공식 원문 검증 후 업데이트

현재 제공 목록과 확인 범위는 [공식 원문 검증 기록](./VERIFICATION-REPORT.md)을 기준으로 한다.

- 이용자 환불 안내는 `verified-refund-policies.ts`의 **`verifiedRefundPolicies` 10곳**만 사용한다. 첫 화면도 이 목록으로 전환했다. 각 규칙에 기간 단위·기준일·조건·관련 출처가 있고, 출처에 실제 원문 인용·섹션·언어·대조일을 기록했다.
- `shoppingPolicies`는 **쿠팡·11번가·G마켓·Amazon 4곳**으로 바뀌었다. 기존 9곳은 `draftShoppingPolicies`로 분리했다. 무료 반품 금액을 확인한 것이 아니므로 배송비 금액은 `null` 유지.
- `subscriptionPresets`는 **네이버플러스 1곳·월/연 2개 요금제**만 실제 제공한다. `getPresetDefaults()`는 제외한 서비스에 `null`을 반환하므로 호출부는 직접입력 또는 선택 불가를 처리해야 한다. 기존 6곳·16개 요금제는 `draftSubscriptionPresets`로 분리했다.
- 디즈니+는 이번 재접속에서 미국 상품·달러 요금이 나왔으므로 기존 한국 요금을 현재 검증 가격으로 제공하지 않는다. 넷플릭스는 해지 안내만 확인했고 한국 환불 약관을 확인하지 못해 제외했다.
- 네이버는 미사용·회차 미종료 조건에서 청약철회 이후 **90% 환불**도 가능하다. Spotify는 최초 구매 **14일**과 갱신 **7일**을 구분한다. Apple의 기존 **90일**, Google Play의 **48시간 내 전액 환불**은 근거 없는 초안이므로 제공하지 않는다.
- 호환용 `refund-policies.ts`/`checkRefund()`는 기존 오류가 남아 있는 **미검증 초안**이다. 실제 판정에 사용하지 말고 새 검증 목록의 조건과 원문을 확인한다. 해당 초안의 `verifiedPolicyIds`를 채우지 않는다.
- 넷플릭스·YouTube 가상 구독은 가격을 검증한 것처럼 보이지 않도록 `presetId`·`planId`를 `null`로 끊었다. 시연 4건·날짜·금액은 계속 가상이다.
- 25곳의 접근 결과, 10곳 채택 이유, 15곳 제외 사유·상세 주소와 남은 한계는 `VERIFICATION-REPORT.md`에서 확인한다.

## 검증된 데이터 연동 예

```ts
import { verifiedRefundPolicies } from "@/data/verified-refund-policies";
import { shoppingPolicies } from "@/data/shopping-policies";
import { getPresetDefaults } from "@/data/subscription-presets";

const rules = verifiedRefundPolicies; // 원문 대조한 10곳, 개인 환불 승인은 아님
const shops = shoppingPolicies; // 대조한 4곳, 배송비 금액·상품 예외 별도 확인
const naver = getPresetDefaults("naver-plus", "naver-yearly"); // 46,800원
const netflix = getPresetDefaults("netflix"); // null: 요금 프리셋 제공 제외
```

검사: `bunx vitest run src/data/service-data.test.ts src/data/refund-policies.test.ts src/data/verified-refund-policies.test.ts src/test/app-routing.test.tsx`

## 파일 구성

| 파일 | 용도 |
| --- | --- |
| `service-types.ts` | Purchase / Subscription / Policy, 공식 출처·검증 규칙 타입 |
| `verified-refund-policies.ts` | 공식 원문 대조한 환불 안내 10곳, 출처·인용·조건·기간 단위 |
| `VERIFICATION-REPORT.md` | 25곳 접근 결과와 채택·제외 이유, 변경된 데이터 계약 |
| `shopping-policies.ts` | 제공용 4곳, 격리한 초안 9곳, 미검증 법령 검수 템플릿·빈 통계 |
| `subscription-presets.ts` | 제공용 네이버 월·연 요금, 격리한 요금 후보 |
| `demo-data.ts` | 기준일이 명시된 가상 구매 2건·구독 2건 |
| `date-rules.ts` | UTC 날짜 계산·D-day 경고·월말 결제일 보정 |
| `refund-policies.ts` | 오류가 남은 초기 22곳 호환용 초안; 운영 사용 금지 |

## 필드 취급과 계산의 한계

- `null`은 미확인이지 무료·반품 불가가 아니다. 확인되지 않은 반품비를 0으로 채우지 않는다.
- `collectedAt: null`은 실제 원문 확인일 없음이다. 접근 실패나 초안 작성일을 확인일로 쓰지 않는다.
- `sources`의 인용은 검증한 짧은 발췌이며 전체 약관을 대체하지 않는다. 각 `rules.sourceIds`로 조항의 근거를 연결한다.
- `period`는 `value`, `unit`(일/시간/달력 월), `basis`를 분리한다. 하자 3개월을 90일로 바꾸거나 Google Play 48시간을 날짜 2일로 바꾸지 않는다.
- `outcome: request`는 요청·심사 절차, `conditional`은 조건 확인 필요를 뜻한다. 환불 승인이나 전액 환불 보장이 아니다.
- `calculatePurchaseDeadline()`은 수령 당일 제외의 일반 날짜 계산만 한다. 상품 예외·Amazon 시즌 연장·공휴일 법적 연장을 자동 적용하지 않는다. 플랫폼별 정확한 기산 해석은 원문·법률 검수 후 확정한다.
- 마감일은 날짜이지 23:59까지 신청 가능하다는 보장 시각이 아니다.
- 구독 `deadline`은 결제 예정일(체험 종료일 우선), `cancelReminderDate`는 전날의 권장 알림일이지 실제 해지 마감이 아니다.
- `advanceBillingDate()`에는 최초 결제 기준일을 보존해 전달해야 월말 보정이 누적되지 않는다. 해지 완료 구독에는 적용하지 않는다.
- 가상 시연 데이터는 `isMock: true`이다. 실제 수집·가입·청구 결과로 표시하지 않는다.
- `createDemoData("2026-11-01")`은 같은 달 4건 시연용이다. 고정 `demoData`는 11/21 기준으로 넷플릭스가 12/03(D-12)이므로 '이번 달 4건'과 동시에 일치하지 않는다.
- 법령 템플릿은 `autoApprove: false`, 공공 통계는 원자료가 없어 `[]`로 유지한다.

## 팀원별 다음 작업

1. 화면·등록 담당자는 제공용 목록만 연결하고 제외된 프리셋의 `null` 결과를 처리한다. 초기 `checkRefund()`와 격리된 초안은 연결하지 않는다.
2. 데이터 담당자는 검증 기록에 적힌 제외 사유를 바탕으로 국내 공식 상세 원문과 상품·판매자 범위를 확보한다. 확인한 항목만 수정하고 출처·인용·확인일·검사를 함께 변경한다.
3. 요금 담당자는 웹·앱·제휴·프로모션·기존 가입자 요금을 분리한다. 환불 안내 확인이 가격 확인을 뜻하지 않는다.
4. 법률·정책 담당자는 기간의 관계·기산·공휴일 처리와 상품별 예외를 검수한다. 계산 결과를 환불 자격 승인으로 사용하지 않는다.
5. 통계 담당자는 한국소비자원 등 실제 원자료를 확보해 연도·분류·단위·통계 종류·출처·확인일을 정리한다. 상담 건수와 피해구제 건수를 합산하지 않는다.

확인 결과: 데이터·날짜·요금·경로 검사 **63개 통과**. 실제 첫 화면에서 10곳 표시, 네이버·Google Play 근거 펼치기와 출처 링크, 모바일 가로 넘침 없음·실행 오류 없음을 확인했다.
