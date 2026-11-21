/** 기능 정의서의 필드명 유지. 미확인 값은 null이며 0원/반품불가를 뜻하지 않는다. */
export type ISODate = string;
export type VerificationStatus = "verified" | "unverified";
export interface Evidence {
  sourceUrl: string;
  collectedAt: ISODate | null;
  verificationStatus: VerificationStatus;
  evidenceNote: string;
}
/** 검증은 인용한 안내와 적용 범위에 한정하며 개인의 환불 자격을 승인하지 않는다. */
export interface OfficialSource {
  id: string;
  title: string;
  url: string;
  section: string;
  quote: string;
  language: "ko" | "en";
  checkedAt: ISODate;
}
export interface VerifiedRefundRule {
  id: string;
  note: string;
  outcome: "conditional" | "percentage" | "none" | "request";
  refundPercent: number | null;
  period: {
    value: number;
    unit: "days" | "hours" | "calendar-months";
    basis: "receivedDate" | "discoveredDate" | "serviceStartDate" | "purchaseDate" | "billingDate";
  } | null;
  conditions: string[];
  sourceIds: string[];
}
export interface VerifiedRefundPolicy extends Evidence {
  id: string;
  name: string;
  category: "shopping" | "subscription";
  subcategory: string;
  verificationStatus: "verified";
  collectedAt: ISODate;
  scope: string;
  rules: VerifiedRefundRule[];
  exclusions: string[];
  howTo: string;
  cancelEffect: string;
  sources: OfficialSource[];
}
export interface ReturnFee {
  basicFee: number | null;
  roundTripFee: number | null;
  currency: "KRW" | "USD";
  note: string;
}
export interface Policy extends Evidence {
  id: string;
  platform: string;
  siteUrl: string;
  sourceType: "built-in" | "user-input";
  returnDays: number | null;
  baseDate: "receivedDate" | "orderDate";
  includeStartDay: boolean;
  holidayAdjustment: "not-applied";
  returnFee: ReturnFee;
  exclusions: string[];
  howTo: string | null;
  defect: { fromReceiptMonths: number | null; fromDiscoveryDays: number | null; note: string };
}
export type PurchaseStatus = "보관 중" | "반품 신청" | "환불 완료" | "기한 지남";
export interface Purchase {
  id: string;
  platform: string;
  policyId: string;
  productName: string;
  price: number;
  orderDate: ISODate;
  receivedDate: ISODate | null;
  deadline: ISODate | null;
  status: PurchaseStatus;
}
export type BillingCycle = "월" | "연";
export interface Subscription {
  id: string;
  serviceName: string;
  presetId: string | null;
  planId: string | null;
  price: number;
  cycle: BillingCycle;
  nextBillingDate: ISODate;
  trialEndDate: ISODate | null;
  deadline: ISODate;
  cancelReminderDate: ISODate;
  status: "이용 중" | "해지 예정" | "해지 완료";
}
export interface SubscriptionPlan extends Evidence {
  id: string;
  name: string;
  price: number | null;
  cycle: BillingCycle;
  currency: "KRW";
  billingChannel: "web";
}
export interface SubscriptionPreset {
  id: string;
  serviceName: string;
  defaultPlanId: string;
  plans: SubscriptionPlan[];
}
export interface StandardPolicy extends Evidence {
  id: string;
  title: string;
  returnDays: number;
  baseDate: "receivedDate";
  defect: { fromReceiptMonths: number; fromDiscoveryDays: number };
  exceptions: string[];
  autoApprove: false;
}
export interface DisputeStat extends Evidence {
  year: number;
  category: string;
  disputeType: string;
  count: number;
  unit: "건";
  metric: "상담" | "피해구제";
}