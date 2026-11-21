// 호환용 미검증 초안 22곳. 운영 화면·신규 환불 판단에서 사용하지 않는다.
// 공식 원문 검증 데이터는 verified-refund-policies.ts. 아래 값에는 확인된 오류가 있으며
// 기존 소비자 호환을 위해 보존할 뿐이다. lastChecked는 원문 확인일이 아니다.
export type Category = "shopping" | "subscription";
export type RefundType = "full" | "prorated" | "none" | "conditional";

export interface RefundRule {
  /** 구매/결제일로부터 이 일수 이내면 적용 (null = 기간 제한 없음) */
  withinDays: number | null;
  /** 사용 이력이 없어야 하는지 */
  requiresUnused: boolean;
  refund: RefundType;
  note: string;
}

export interface RefundPolicy {
  id: string;
  name: string;
  category: Category;
  subcategory: string;
  rules: RefundRule[]; // 위에서부터 순서대로 판정
  defectWithinDays: number | null; // 제품 하자/오배송 시 기간
  cancelEffect: string; // 해지 시 처리
  sourceUrl: string;
  lastChecked: string;
}

const LC = "2026-11-21";
const ECOMMERCE_ACT = {
  withinDays: 7,
  requiresUnused: true,
  refund: "full" as const,
  note: "전자상거래법 제17조: 상품 수령 후 7일 이내 청약철회 (단순변심 시 왕복배송비 고객 부담)",
};

export const refundPolicies: RefundPolicy[] = [
  // ---------- 쇼핑 ----------
  { id: "coupang", name: "쿠팡", category: "shopping", subcategory: "종합몰",
    rules: [{ ...ECOMMERCE_ACT, note: "수령 후 7일 이내 반품. 로켓배송 단순변심 시 반품비 부과(와우 회원 무료 반품 대상 상품 제외)" }],
    defectWithinDays: 30, cancelEffect: "출고 전 취소 시 즉시 전액 환불",
    sourceUrl: "https://www.coupang.com/np/policies/terms", lastChecked: LC },
  { id: "11st", name: "11번가", category: "shopping", subcategory: "오픈마켓",
    rules: [ECOMMERCE_ACT], defectWithinDays: 90, cancelEffect: "발송 전 취소 시 전액 환불",
    sourceUrl: "https://www.11st.co.kr/", lastChecked: LC },
  { id: "gmarket", name: "G마켓", category: "shopping", subcategory: "오픈마켓",
    rules: [ECOMMERCE_ACT], defectWithinDays: 90, cancelEffect: "발송 전 취소 시 전액 환불",
    sourceUrl: "https://www.gmarket.co.kr/", lastChecked: LC },
  { id: "ssg", name: "SSG.COM", category: "shopping", subcategory: "종합몰",
    rules: [{ ...ECOMMERCE_ACT, note: "수령 후 7일 이내 반품. 신선식품은 수령 당일 신고 원칙" }],
    defectWithinDays: 90, cancelEffect: "배송 준비 전 취소 시 전액 환불",
    sourceUrl: "https://www.ssg.com/", lastChecked: LC },
  { id: "naver-shopping", name: "네이버 스마트스토어", category: "shopping", subcategory: "오픈마켓",
    rules: [{ ...ECOMMERCE_ACT, note: "수령 후 7일 이내 반품 요청. 판매자별 상세 규정 상이" }],
    defectWithinDays: 90, cancelEffect: "발송 전 취소 시 전액 환불",
    sourceUrl: "https://shopping.naver.com/", lastChecked: LC },
  { id: "musinsa", name: "무신사", category: "shopping", subcategory: "패션",
    rules: [{ ...ECOMMERCE_ACT, note: "수령 후 7일 이내, 택·포장 훼손 없을 때 반품" }],
    defectWithinDays: 90, cancelEffect: "출고 전 취소 시 전액 환불",
    sourceUrl: "https://www.musinsa.com/", lastChecked: LC },
  { id: "kurly", name: "컬리", category: "shopping", subcategory: "식품",
    rules: [{ withinDays: 0, requiresUnused: true, refund: "conditional", note: "신선식품 단순변심 반품 불가. 품질 문제는 수령일 기준 2일 이내 사진 접수" }],
    defectWithinDays: 2, cancelEffect: "배송 준비 전 취소 시 전액 환불",
    sourceUrl: "https://www.kurly.com/", lastChecked: LC },
  { id: "amazon", name: "Amazon", category: "shopping", subcategory: "해외직구",
    rules: [{ withinDays: 30, requiresUnused: true, refund: "full", note: "대부분 상품 수령 후 30일 이내 반품. 해외배송 시 반송비 발생 가능" }],
    defectWithinDays: 30, cancelEffect: "발송 전 취소 시 전액 환불",
    sourceUrl: "https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7", lastChecked: LC },
  { id: "aliexpress", name: "AliExpress", category: "shopping", subcategory: "해외직구",
    rules: [{ withinDays: 15, requiresUnused: true, refund: "conditional", note: "'무료 반품' 표시 상품은 수령 후 15일 이내 반품. 그 외 판매자 협의" }],
    defectWithinDays: 15, cancelEffect: "발송 전 취소 시 전액 환불",
    sourceUrl: "https://www.aliexpress.com/", lastChecked: LC },

  // ---------- 구독 ----------
  { id: "netflix", name: "넷플릭스", category: "subscription", subcategory: "OTT",
    rules: [{ withinDays: null, requiresUnused: false, refund: "none", note: "결제 금액 환불 없음. 해지 시 결제 주기 종료일까지 이용" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://help.netflix.com/ko/node/407", lastChecked: LC },
  { id: "tving", name: "티빙", category: "subscription", subcategory: "OTT",
    rules: [
      { withinDays: 7, requiresUnused: true, refund: "full", note: "결제 후 7일 이내 미시청 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "none", note: "그 외 해지 예약(잔여 기간 이용)" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://www.tving.com/", lastChecked: LC },
  { id: "wavve", name: "웨이브", category: "subscription", subcategory: "OTT",
    rules: [
      { withinDays: 7, requiresUnused: true, refund: "full", note: "결제 후 7일 이내 미이용 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "none", note: "이용 후에는 해지 예약" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://www.wavve.com/", lastChecked: LC },
  { id: "disney-plus", name: "디즈니+", category: "subscription", subcategory: "OTT",
    rules: [{ withinDays: null, requiresUnused: false, refund: "none", note: "부분 환불 없음. 해지 시 결제 기간 종료까지 이용" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://help.disneyplus.com/", lastChecked: LC },
  { id: "coupang-play", name: "쿠팡 와우(쿠팡플레이)", category: "subscription", subcategory: "멤버십",
    rules: [
      { withinDays: null, requiresUnused: true, refund: "full", note: "혜택 미사용 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "none", note: "혜택 사용 시 해지 예약" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://www.coupang.com/", lastChecked: LC },
  { id: "naver-plus", name: "네이버플러스 멤버십", category: "subscription", subcategory: "멤버십",
    rules: [
      { withinDays: 7, requiresUnused: true, refund: "full", note: "결제 후 7일 이내 혜택 미사용 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "none", note: "그 외 해지 예약" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://nid.naver.com/membership/", lastChecked: LC },
  { id: "youtube-premium", name: "YouTube Premium", category: "subscription", subcategory: "OTT/음악",
    rules: [{ withinDays: null, requiresUnused: false, refund: "none", note: "원칙적으로 부분 환불 없음. 해지 후 결제 기간 종료까지 이용" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://support.google.com/youtube/answer/6308278", lastChecked: LC },
  { id: "melon", name: "멜론", category: "subscription", subcategory: "음악",
    rules: [
      { withinDays: 7, requiresUnused: true, refund: "full", note: "결제 후 7일 이내 미사용 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "prorated", note: "사용 후 해지 시 이용일수·사용량 차감 후 환불(위약금 10% 공제 가능)" }],
    defectWithinDays: null, cancelEffect: "즉시 해지 또는 해지 예약 선택",
    sourceUrl: "https://www.melon.com/", lastChecked: LC },
  { id: "spotify", name: "Spotify", category: "subscription", subcategory: "음악",
    rules: [{ withinDays: null, requiresUnused: false, refund: "none", note: "부분 기간 환불 없음(현지 법률상 요구 시 제외)" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 Free 전환",
    sourceUrl: "https://www.spotify.com/kr-ko/legal/end-user-agreement/", lastChecked: LC },
  { id: "millie", name: "밀리의 서재", category: "subscription", subcategory: "전자책",
    rules: [
      { withinDays: 7, requiresUnused: true, refund: "full", note: "결제 후 7일 이내 미이용 시 전액 환불" },
      { withinDays: null, requiresUnused: false, refund: "none", note: "이용 시 해지 예약" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://www.millie.co.kr/", lastChecked: LC },
  { id: "chatgpt-plus", name: "ChatGPT Plus", category: "subscription", subcategory: "AI",
    rules: [{ withinDays: null, requiresUnused: false, refund: "none", note: "원칙적으로 환불 없음(법적 요구 시 제외). 해지 후 기간 종료까지 이용" }],
    defectWithinDays: null, cancelEffect: "다음 결제일부터 청구 중단",
    sourceUrl: "https://openai.com/policies/terms-of-use", lastChecked: LC },
  { id: "app-store", name: "Apple App Store 구독", category: "subscription", subcategory: "앱마켓",
    rules: [{ withinDays: 90, requiresUnused: false, refund: "conditional", note: "reportaproblem.apple.com에서 환불 요청(애플 심사)" }],
    defectWithinDays: 90, cancelEffect: "다음 갱신일부터 청구 중단",
    sourceUrl: "https://support.apple.com/ko-kr/118223", lastChecked: LC },
  { id: "google-play", name: "Google Play 구독", category: "subscription", subcategory: "앱마켓",
    rules: [
      { withinDays: 2, requiresUnused: false, refund: "full", note: "결제 후 48시간 이내 Google Play에 환불 요청 가능" },
      { withinDays: null, requiresUnused: false, refund: "conditional", note: "48시간 이후는 앱 개발자에게 문의" }],
    defectWithinDays: null, cancelEffect: "다음 갱신일부터 청구 중단",
    sourceUrl: "https://support.google.com/googleplay/answer/2479637", lastChecked: LC },
];

export interface CheckInput { policyId: string; purchaseDate: string; today: string; used: boolean; }
export interface CheckResult { eligible: boolean; refund: RefundType; note: string; daysElapsed: number; daysLeft: number | null; }

export function checkRefund({ policyId, purchaseDate, today, used }: CheckInput): CheckResult | null {
  const p = refundPolicies.find((x) => x.id === policyId);
  if (!p) return null;
  const days = Math.floor((Date.parse(today) - Date.parse(purchaseDate)) / 86400000);
  for (const r of p.rules) {
    if (r.withinDays !== null && days > r.withinDays) continue;
    if (r.requiresUnused && used) continue;
    return { eligible: r.refund !== "none", refund: r.refund, note: r.note, daysElapsed: days,
      daysLeft: r.withinDays === null ? null : r.withinDays - days };
  }
  return { eligible: false, refund: "none", note: "환불 가능 기간이 지났거나 조건을 충족하지 않습니다.", daysElapsed: days, daysLeft: 0 };
}

// ---------- 정보 최신 여부 ----------
/** 실제 출처 페이지를 열어 대조한 정책 id 목록. 대조 후 여기에 추가하고 lastChecked를 갱신할 것. */
export const verifiedPolicyIds: string[] = [];
export type Freshness = "fresh" | "stale" | "outdated" | "unverified";
export const FRESH_DAYS = 30;
export const STALE_DAYS = 90;

export function getFreshness(p: RefundPolicy, today: string): { status: Freshness; daysSince: number } {
  const daysSince = Math.floor((Date.parse(today) - Date.parse(p.lastChecked)) / 86400000);
  if (!verifiedPolicyIds.includes(p.id)) return { status: "unverified", daysSince };
  if (daysSince <= FRESH_DAYS) return { status: "fresh", daysSince };
  if (daysSince <= STALE_DAYS) return { status: "stale", daysSince };
  return { status: "outdated", daysSince };
}
