import { addDays, calculatePurchaseDeadline, parseDate, subscriptionDates } from "./date-rules";
import { shoppingPolicies } from "./shopping-policies";
import type { Policy, Purchase, Subscription } from "./service-types";

/** 네트워크 수집 결과로 사용하지 않는, 확인 화면 시연 전용 가상 규정. */
export const demoCustomPolicy: Policy = {
  id: "demo-knit-policy", platform: "시연용 소규모 쇼핑몰", siteUrl: "", sourceType: "user-input",
  returnDays: 7, baseDate: "receivedDate", includeStartDay: false, holidayAdjustment: "not-applied",
  returnFee: { basicFee: 3000, roundTripFee: 6000, currency: "KRW", note: "가상 규정: 최초 무료배송이면 왕복 비용, 도서산간 추가금은 별도" },
  exclusions: ["택 제거", "착용 흔적"], howTo: "가상 규정: 주문 내역에서 반품 신청",
  defect: { fromReceiptMonths: null, fromDiscoveryDays: null, note: "시연 범위 외" },
  sourceUrl: "", collectedAt: null, verificationStatus: "unverified",
  evidenceNote: "시연용 가상 규정이며 실제 쇼핑몰·실제 수집 결과가 아님. URL 수집 성공으로 표시하지 말 것",
};

/** 기준일을 명시적으로 전달: 시연 날짜가 바뀌어도 러닝화는 D-1. 현재 시간을 숨겨 읽지 않는다. */
export function createDemoData(today: string) {
  parseDate(today);
  const coupang = shoppingPolicies.find((p) => p.id === "coupang");
  if (!coupang) throw new Error("쿠팡 시연 규정이 없습니다.");
  const shoeDates = { orderDate: addDays(today, -8), receivedDate: addDays(today, -6) };
  const knitDates = { orderDate: addDays(today, -5), receivedDate: addDays(today, -2) };
  const purchases: Purchase[] = [
    { id: "p01", platform: "쿠팡", policyId: coupang.id, productName: "러닝화", price: 59000,
      ...shoeDates, deadline: calculatePurchaseDeadline(coupang, shoeDates), status: "보관 중" },
    { id: "p02", platform: demoCustomPolicy.platform, policyId: demoCustomPolicy.id, productName: "니트", price: 39000,
      ...knitDates, deadline: calculatePurchaseDeadline(demoCustomPolicy, knitDates), status: "보관 중" },
  ];
  const netflixDate = addDays(today, 12);
  const youtubeDate = addDays(today, 7);
  const subscriptions: Subscription[] = [
    { id: "s01", serviceName: "넷플릭스", presetId: null, planId: null, price: 13500,
      cycle: "월", nextBillingDate: netflixDate, trialEndDate: null, ...subscriptionDates(netflixDate), status: "이용 중" },
    { id: "s02", serviceName: "YouTube Premium", presetId: null, planId: null, price: 14900,
      cycle: "월", nextBillingDate: youtubeDate, trialEndDate: null, ...subscriptionDates(youtubeDate), status: "이용 중" },
  ];
  return { isMock: true as const, referenceDate: today, persona: "김상명 (가상 사용자)",
    note: "가상 구매·구독 및 시연 금액. 미검증 요금의 구독은 프리셋 연결 없이 직접입력 시연으로 유지. 같은 달 4건을 보여주려면 기준일을 월초(예: 2026-11-01)로 고정할 것. 전날은 권장 알림일이지 법적 해지 마감이 아님",
    policies: [...shoppingPolicies, demoCustomPolicy], purchases, subscriptions };
}

/** 정의서 예시의 11/18 수령 → 11/25 마감, 12/03 결제를 재현하는 고정 시연 데이터. */
export const demoData = createDemoData("2026-11-21");