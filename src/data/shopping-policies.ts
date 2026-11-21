import { refundPolicies } from "./refund-policies";
import { verifiedRefundPolicies } from "./verified-refund-policies";
import type { Policy, StandardPolicy, DisputeStat } from "./service-types";

const targets = ["coupang", "naver-shopping", "11st", "gmarket", "ssg", "musinsa"];
/** 기존 데이터는 원문 미대조 초안. 출처 주소가 있다는 이유로 확인 완료 처리하지 않는다. */
export const draftShoppingPolicies: Policy[] = refundPolicies.filter((p) => targets.includes(p.id)).map((p) => ({
  id: p.id,
  platform: p.name,
  siteUrl: new URL(p.sourceUrl).origin,
  sourceType: "built-in",
  returnDays: p.rules[0]?.withinDays ?? null,
  baseDate: "receivedDate",
  includeStartDay: false,
  holidayAdjustment: "not-applied",
  returnFee: { basicFee: null, roundTripFee: null, currency: "KRW", note: "판매자·상품·배송비·회원 혜택에 따라 달라짐. 금액 원문 확인 필요" },
  exclusions: [],
  howTo: null,
  defect: { fromReceiptMonths: null, fromDiscoveryDays: null, note: "판매처 원문 미확인. 공공 기준은 별도로 안내하며 기존 단일 하자 기간을 그대로 사용하지 않음" },
  sourceUrl: p.sourceUrl,
  collectedAt: null,
  verificationStatus: "unverified",
  evidenceNote: `기존 초안에서 이관. 기간도 미검증. 제외 조건의 빈 배열은 제외 조건 없음이 아닌 미수집을 의미함. 기존 메모: ${p.rules.map((r) => r.note).join(" / ")}`,
}));

for (const p of [
  { id: "29cm", platform: "29CM", siteUrl: "https://www.29cm.co.kr", note: "공식 홈페이지 접근 차단(403). 고객센터의 반품 규정 원문 확보 필요" },
  { id: "zigzag", platform: "지그재그", siteUrl: "https://zigzag.kr", note: "공식 홈페이지는 열렸으나 반품 규정 본문 없음. 스토어별 반품 안내 원문 확보 필요" },
  { id: "ably", platform: "에이블리", siteUrl: "https://m.a-bly.com", note: "공식 홈페이지 보안 확인(403). 판매자별 반품 규정 원문 확보 필요" },
]) {
  draftShoppingPolicies.push({
    id: p.id, platform: p.platform, siteUrl: p.siteUrl, sourceType: "built-in",
    returnDays: null, baseDate: "receivedDate", includeStartDay: false, holidayAdjustment: "not-applied",
    returnFee: { basicFee: null, roundTripFee: null, currency: "KRW", note: "미확인 — 상품별 반품비 필요" },
    exclusions: [], howTo: null,
    defect: { fromReceiptMonths: null, fromDiscoveryDays: null, note: "미확인" },
    sourceUrl: p.siteUrl, collectedAt: null, verificationStatus: "unverified",
    evidenceNote: `2026-11-21 접근 시도: ${p.note}. 링크는 규정 원문이 아닌 공식 홈페이지이며, 아직 등록 화면에서 확정 규정으로 사용하면 안 됨`,
  });
}

/** 초안은 위 배열에 격리하고 제공용 수치는 직접 대조한 규칙에서만 가져온다. */
export const shoppingPolicies: Policy[] = verifiedRefundPolicies.filter((p) => p.category === "shopping").map((p) => {
  const standard = p.rules.find((r) => r.id === "change-of-mind" || r.id === "standard");
  const receipt = p.rules.find((r) => r.id === "defect-receipt");
  const discovery = p.rules.find((r) => r.id === "defect-discovery");
  return {
    id: p.id, platform: p.name, siteUrl: new URL(p.sourceUrl).origin, sourceType: "built-in",
    returnDays: standard?.period?.unit === "days" ? standard.period.value : null,
    baseDate: "receivedDate", includeStartDay: false, holidayAdjustment: "not-applied",
    returnFee: { basicFee: null, roundTripFee: null, currency: p.id === "amazon" ? "USD" : "KRW",
      note: p.id === "amazon" ? "한국 반송 비용은 미확인. 무료 반품을 보장하지 않음." : "단순 변심은 구매자 부담, 판매자 귀책은 판매자 부담. 상품별 편도·왕복 금액은 미확인" },
    exclusions: p.exclusions, howTo: p.howTo,
    defect: { fromReceiptMonths: receipt?.period?.unit === "calendar-months" ? receipt.period.value : null,
      fromDiscoveryDays: discovery?.period?.unit === "days" ? discovery.period.value : null,
      note: receipt?.note ?? "이 원문에서 공통 하자 기간을 확인하지 않음; 임의로 법정 기준을 채우지 않음" },
    sourceUrl: p.sourceUrl, collectedAt: p.collectedAt, verificationStatus: "verified",
    evidenceNote: `${p.scope} ${p.evidenceNote} 날짜 계산은 일반 기간만 계산하며 상품 예외·Amazon 시즌 연장·법적 환불 자격을 판정하지 않음. 모든 근거는 verifiedRefundPolicies.sources 확인`,
  };
});

/** 법적 판단이 아닌 안내용 템플릿. 예외·상품 유형을 확인한 후 사용자가 확정해야 한다. */
export const standardPolicy: StandardPolicy = {
  id: "kr-ecommerce-withdrawal", title: "전자상거래법 제17조 안내용 기본 기준",
  returnDays: 7, baseDate: "receivedDate",
  defect: { fromReceiptMonths: 3, fromDiscoveryDays: 30 },
  exceptions: ["사용·훼손으로 가치가 감소한 상품", "시간 경과로 재판매가 어려운 상품", "청약철회 제한 요건을 충족하는 주문제작·디지털 콘텐츠 등"],
  autoApprove: false,
  sourceUrl: "https://www.law.go.kr/법령/전자상거래등에서의소비자보호에관한법률/제17조",
  collectedAt: null, verificationStatus: "unverified",
  evidenceNote: "법령 페이지에 접근했으나 제17조 본문을 추출하지 못함. 일반적으로 알려진 기준의 검수용 초안. 하자는 수령 후 3개월과 사실을 안 날부터 30일의 관계 및 예외를 원문 대조할 것. 3개월을 90일로 바꾸지 말 것",
};

/** 실제 공공 통계를 확보하기 전에는 수치를 생성하지 않는다. */
export const publicDisputeStats: DisputeStat[] = [];