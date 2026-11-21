import { describe, expect, it } from "vitest";
import { addDays, advanceBillingDate, calculatePurchaseDeadline, daysUntil, getDeadlineWarning, subscriptionDates } from "./date-rules";
import { createDemoData, demoData } from "./demo-data";
import { shoppingPolicies, draftShoppingPolicies, standardPolicy, publicDisputeStats } from "./shopping-policies";
import { getPresetDefaults, subscriptionPresets } from "./subscription-presets";

describe("기능 정의서 데이터 규칙", () => {
  it("수령일 11/18 + 7일 = 11/25 (수령 당일 제외)", () => {
    const policy = shoppingPolicies.find((p) => p.id === "coupang");
    if (!policy) throw new Error("쿠팡 규정 누락");
    expect(calculatePurchaseDeadline(policy, { orderDate: "2026-11-15", receivedDate: "2026-11-18" })).toBe("2026-11-25");
  });
  it("수령일을 포함하면 하루 짧아진다", () => {
    const policy = shoppingPolicies.find((p) => p.id === "coupang");
    if (!policy) throw new Error("쿠팡 규정 누락");
    expect(calculatePurchaseDeadline({ ...policy, includeStartDay: true }, { orderDate: "2026-11-15", receivedDate: "2026-11-18" })).toBe("2026-11-24");
  });
  it("수령일이 없으면 계산하지 않는다", () => {
    const policy = shoppingPolicies.find((p) => p.id === "coupang");
    if (!policy) throw new Error("쿠팡 규정 누락");
    expect(calculatePurchaseDeadline(policy, { orderDate: "2026-11-15", receivedDate: null })).toBeNull();
  });
  it("기간을 모르는 규정은 7일로 자동 대체하지 않는다", () => {
    const policy = draftShoppingPolicies.find((p) => p.id === "29cm");
    if (!policy) throw new Error("29CM 누락");
    expect(calculatePurchaseDeadline(policy, { orderDate: "2026-11-15", receivedDate: "2026-11-18" })).toBeNull();
  });
  it.each([[-1, "gray"], [0, "red"], [1, "red"], [2, "red"], [3, "yellow"], [5, "yellow"], [6, "green"]] as const)("D-%s의 경고는 %s", (days, warning) => {
    expect(getDeadlineWarning(addDays("2026-11-21", days), "2026-11-21")).toBe(warning);
  });
  it("무료체험 종료일이 구독 마감일이고 예방용 알림은 전날이다", () => {
    expect(subscriptionDates("2026-12-03", "2026-11-25")).toEqual({ deadline: "2026-11-25", cancelReminderDate: "2026-11-24" });
  });
  it("일반 구독 마감일은 다음 결제 예정일이다", () => {
    expect(subscriptionDates("2026-12-03")).toEqual({ deadline: "2026-12-03", cancelReminderDate: "2026-12-02" });
  });
  it("월 갱신 시 말일을 보정하고 다음 달에는 원래 결제일을 보존한다", () => {
    expect(advanceBillingDate("2027-01-31", "월", "2027-02-01")).toBe("2027-02-28");
    expect(advanceBillingDate("2027-01-31", "월", "2027-03-01")).toBe("2027-03-31");
  });
  it("결제일 당일에는 임의로 다음 주기로 이동하지 않는다", () => {
    expect(advanceBillingDate("2026-11-21", "월", "2026-11-21")).toBe("2026-11-21");
  });
  it("연간 갱신 시 윤일은 말일로 보정한다", () => {
    expect(advanceBillingDate("2024-02-29", "연", "2025-02-01")).toBe("2025-02-28");
  });
  it("존재하지 않는 날짜는 거절한다", () => {
    expect(() => addDays("2026-02-30", 7)).toThrow();
  });
  it("법정 안내값은 7일, 하자는 3개월과 인지 후 30일이며 자동 승인하지 않는다", () => {
    expect(standardPolicy.returnDays).toBe(7);
    expect(standardPolicy.defect).toEqual({ fromReceiptMonths: 3, fromDiscoveryDays: 30 });
    expect(standardPolicy.autoApprove).toBe(false);
  });
});

describe("데이터 연결과 시연", () => {
  it("제공용 쇼핑몰은 원문을 대조한 4곳으로 한정된다", () => {
    expect(shoppingPolicies.map((p) => p.id).sort()).toEqual(["coupang", "11st", "gmarket", "amazon"].sort());
  });
  it("미대조 쇼핑몰을 확인한 것처럼 날짜를 부여하지 않는다", () => {
    expect(draftShoppingPolicies.every((p) => p.verificationStatus === "unverified" && p.collectedAt === null)).toBe(true);
  });
  it("넷플릭스 스탠다드 시연 금액은 13,500원이나 미검증 가격 자동 확정은 막는다", () => {
    expect(demoData.subscriptions.find((s) => s.id === "s01")?.price).toBe(13500);
    expect(getPresetDefaults("netflix")).toBeNull();
    expect(demoData.subscriptions.find((s) => s.id === "s01")?.presetId).toBeNull();
  });
  it.each([["naver-plus", "naver-monthly", 4900], ["naver-plus", "naver-yearly", 46800]] as const)("확인된 %s / %s 요금은 %s원", (preset, plan, amount) => {
    expect(getPresetDefaults(preset, plan)?.price).toBe(amount);
  });
  it("모든 요금제 선택과 기본값은 실제 프리셋을 참조한다", () => {
    expect(subscriptionPresets.map((p) => p.id)).toEqual(["naver-plus"]);
    for (const preset of subscriptionPresets) expect(preset.plans.some((p) => p.id === preset.defaultPlanId)).toBe(true);
    for (const sub of demoData.subscriptions) {
      if (sub.presetId === null) expect(sub.planId).toBeNull();
      else expect(subscriptionPresets.find((p) => p.id === sub.presetId)?.plans.some((p) => p.id === sub.planId)).toBe(true);
    }
    for (const purchase of demoData.purchases) expect(demoData.policies.some((p) => p.id === purchase.policyId)).toBe(true);
  });
  it.each(["2026-11-21", "2027-02-28"])("%s 시연에서도 구매 2건·구독 2건과 러닝화 D-1을 유지한다", (today) => {
    const demo = createDemoData(today);
    expect(demo.isMock).toBe(true);
    expect(demo.purchases).toHaveLength(2);
    expect(demo.subscriptions).toHaveLength(2);
    const shoe = demo.purchases.find((p) => p.id === "p01");
    if (!shoe?.deadline) throw new Error("러닝화 마감일 누락");
    expect(daysUntil(shoe.deadline, today)).toBe(1);
    expect(getDeadlineWarning(shoe.deadline, today)).toBe("red");
    expect(daysUntil(demo.subscriptions.find((s) => s.id === "s01")?.deadline ?? "", today)).toBe(12);
  });
  it("공공 통계는 원자료가 없으면 꾸며 넣지 않는다", () => {
    expect(publicDisputeStats).toEqual([]);
  });
});