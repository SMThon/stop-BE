import type { BillingCycle, SubscriptionPlan, SubscriptionPreset, VerificationStatus } from "./service-types";
import { verifiedRefundPolicies } from "./verified-refund-policies";

function plan(id: string, name: string, price: number | null, cycle: BillingCycle, sourceUrl: string,
  verificationStatus: VerificationStatus, evidenceNote: string): SubscriptionPlan {
  return { id, name, price, cycle, currency: "KRW", billingChannel: "web", sourceUrl,
    collectedAt: verificationStatus === "verified" ? "2026-11-21" : null, verificationStatus, evidenceNote };
}
const netflixUrl = "https://help.netflix.com/ko/node/24926";
const tvingUrl = "https://www.tving.com";
const disneyUrl = "https://www.disneyplus.com/ko-kr";
const naverUrl = "https://help.naver.com/service/23168/contents/22358?osType=COMMONOS";
const secondary = "비공식 비교표 https://huntlab.app/ott-price-comparison-2026/ 를 참고한 미검증 후보. 공식 페이지에서 한국 요금을 확인하지 못함. 자동 확정 금지";
const disneyNote = "이전 확인 기록의 후보값. 이번 재접속에서는 미국 달러·Hulu 결합 상품이 표시되어 한국 요금을 재검증하지 못함. 현재 제공 목록 제외";

export const draftSubscriptionPresets: SubscriptionPreset[] = [
  { id: "netflix", serviceName: "넷플릭스", defaultPlanId: "netflix-standard", plans: [
    plan("netflix-ads", "광고형 스탠다드", 7000, "월", netflixUrl, "unverified", secondary),
    plan("netflix-standard", "스탠다드", 13500, "월", netflixUrl, "unverified", secondary),
    plan("netflix-premium", "프리미엄", 17000, "월", netflixUrl, "unverified", secondary),
  ] },
  { id: "youtube-premium", serviceName: "YouTube Premium", defaultPlanId: "youtube-individual", plans: [
    plan("youtube-individual", "개인", 14900, "월", "https://www.youtube.com/premium", "unverified", "웹 페이지에서 요금 본문 미노출. 비공식 비교표 https://bestlink365.com/guide/ott-sites-prices-cancel-rules/ 의 후보값. 결제 채널·실제 청구서 대조 필요"),
  ] },
  { id: "coupang-play", serviceName: "쿠팡 와우", defaultPlanId: "coupang-wow-monthly", plans: [
    plan("coupang-wow-monthly", "와우 멤버십", 7890, "월", "https://news.coupang.com/archives/44584/", "unverified", "공식 2024-07-09 공지에서 7,890원 확인. 2026년 현재 가입 요금은 대조하지 못했으므로 후보값으로 유지"),
  ] },
  { id: "naver-plus", serviceName: "네이버플러스 멤버십", defaultPlanId: "naver-monthly", plans: [
    plan("naver-monthly", "월간 이용권", 4900, "월", naverUrl, "verified", "공식 고객센터 연간 이용권 결제 방법 본문의 월간 4,900원(VAT 포함) 대조"),
    plan("naver-yearly", "연간 이용권", 46800, "연", naverUrl, "verified", "공식 고객센터 본문의 1년마다 46,800원(VAT 포함) 대조"),
  ] },
  { id: "tving", serviceName: "티빙", defaultPlanId: "tving-standard", plans: [
    plan("tving-ads", "광고형 스탠다드", 5500, "월", tvingUrl, "unverified", secondary),
    plan("tving-basic", "베이직", 9500, "월", tvingUrl, "unverified", secondary),
    plan("tving-standard", "스탠다드", 13500, "월", tvingUrl, "unverified", secondary),
    plan("tving-premium", "프리미엄", 17000, "월", tvingUrl, "unverified", secondary),
  ] },
  { id: "disney-plus", serviceName: "디즈니+", defaultPlanId: "disney-standard-monthly", plans: [
    plan("disney-ads-monthly", "광고형 스탠다드", 7000, "월", disneyUrl, "unverified", disneyNote),
    plan("disney-standard-monthly", "스탠다드", 11500, "월", disneyUrl, "unverified", disneyNote),
    plan("disney-standard-yearly", "스탠다드", 115000, "연", disneyUrl, "unverified", disneyNote),
    plan("disney-premium-monthly", "프리미엄", 16500, "월", disneyUrl, "unverified", disneyNote),
    plan("disney-premium-yearly", "프리미엄", 165000, "연", disneyUrl, "unverified", disneyNote),
  ] },
];

/** 환불 원문과 현재 요금 원문 모두 확인한 프리셋만 실제 등록용으로 제공한다. */
export const subscriptionPresets: SubscriptionPreset[] = draftSubscriptionPresets
  .filter((p) => verifiedRefundPolicies.some((r) => r.id === p.id))
  .map((p) => ({ ...p, plans: p.plans.filter((v) => v.verificationStatus === "verified" && v.collectedAt !== null) }))
  .filter((p) => p.plans.some((v) => v.id === p.defaultPlanId));

/** 미검증 후보는 가격을 자동 확정하지 않으며 사용자 확인·입력이 필요하다. */
export function getPresetDefaults(presetId: string, planId?: string) {
  const preset = subscriptionPresets.find((p) => p.id === presetId);
  const selected = preset?.plans.find((p) => p.id === (planId ?? preset.defaultPlanId));
  if (!preset || !selected) return null;
  return { serviceName: preset.serviceName, planId: selected.id, cycle: selected.cycle,
    price: selected.verificationStatus === "verified" ? selected.price : null,
    suggestedPrice: selected.price, requiresConfirmation: selected.verificationStatus !== "verified" };
}