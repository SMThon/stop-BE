import { describe, expect, it } from "vitest";
import { VERIFIED_AT, verifiedRefundPolicies, getVerifiedFreshness } from "./verified-refund-policies";
import { shoppingPolicies, draftShoppingPolicies } from "./shopping-policies";
import { subscriptionPresets, getPresetDefaults } from "./subscription-presets";
import { refundPolicies, verifiedPolicyIds } from "./refund-policies";

function getRule(policyId: string, ruleId: string) {
  const value = verifiedRefundPolicies.find((p) => p.id === policyId)?.rules.find((r) => r.id === ruleId);
  if (!value) throw new Error(`규칙 누락: ${policyId}/${ruleId}`);
  return value;
}

describe("공식 원문만 제공", () => {
  it("원문 대조를 완료한 10곳만 제공한다", () => {
    expect(verifiedRefundPolicies.map((p) => p.id).sort()).toEqual([
      "coupang", "11st", "gmarket", "amazon", "naver-plus", "spotify", "youtube-premium", "chatgpt-plus", "app-store", "google-play",
    ].sort());
  });
  it("제공용 규칙은 확인일과 실제 출처 참조가 필요하다", () => {
    expect(VERIFIED_AT).toBe("2026-11-21");
    for (const p of verifiedRefundPolicies) {
      expect(p.verificationStatus).toBe("verified");
      expect(p.collectedAt).toBe("2026-11-21");
      expect(p.sources.length).toBeGreaterThan(0);
      expect(p.sourceUrl).toBe(p.sources[0]?.url);
      for (const s of p.sources) {
        expect(s.checkedAt).toBe("2026-11-21");
        expect(new URL(s.url).protocol).toBe("https:");
      }
      for (const r of p.rules) {
        expect(r.sourceIds.length).toBeGreaterThan(0);
        for (const id of r.sourceIds) expect(p.sources.some((s) => s.id === id)).toBe(true);
      }
    }
  });
  it("호환용 초안 22곳과 미검증 쇼핑몰은 검증 완료로 승격하지 않는다", () => {
    expect(refundPolicies).toHaveLength(22);
    expect(verifiedPolicyIds).toEqual([]);
    expect(draftShoppingPolicies).toHaveLength(9);
    expect(shoppingPolicies.map((p) => p.id).sort()).toEqual(["amazon", "coupang", "11st", "gmarket"].sort());
    expect(shoppingPolicies.every((p) => p.verificationStatus === "verified" && p.collectedAt === VERIFIED_AT)).toBe(true);
  });
  it.each(["netflix", "youtube-premium", "tving", "coupang-play", "disney-plus"])("요금까지 재검증하지 못한 %s 프리셋은 제공하지 않는다", (id) => {
    expect(subscriptionPresets.some((p) => p.id === id)).toBe(false);
    expect(getPresetDefaults(id)).toBeNull();
  });
});

describe("원문 대조로 바로잡은 규칙", () => {
  it.each(["coupang", "11st", "gmarket"])("%s 단순변심은 수령 후 7일의 조건부 안내다", (id) => {
    const r = getRule(id, "change-of-mind");
    expect(r.period).toEqual({ value: 7, unit: "days", basis: "receivedDate" });
    expect(r.outcome).toBe("conditional");
    expect(r.refundPercent).toBeNull();
  });
  it.each(["coupang", "gmarket"])("%s 하자는 3개월과 인지 후 30일을 별도로 보존한다", (id) => {
    expect(getRule(id, "defect-receipt").period).toEqual({ value: 3, unit: "calendar-months", basis: "receivedDate" });
    expect(getRule(id, "defect-discovery").period).toEqual({ value: 30, unit: "days", basis: "discoveredDate" });
  });
  it("11번가 원문에 없는 공통 하자 기간은 채우지 않는다", () => {
    expect(shoppingPolicies.find((p) => p.id === "11st")?.defect.fromReceiptMonths).toBeNull();
    expect(shoppingPolicies.find((p) => p.id === "11st")?.defect.fromDiscoveryDays).toBeNull();
  });
  it("반품비 원문은 부담자만 확인했고 금액 미확인을 무료로 바꾸지 않는다", () => {
    for (const p of shoppingPolicies) {
      expect(p.returnFee.basicFee).toBeNull();
      expect(p.returnFee.roundTripFee).toBeNull();
    }
  });
  it("Amazon 일반 30일은 검수·적격성을 전제로 한다", () => {
    const r = getRule("amazon", "standard");
    expect(r.period).toEqual({ value: 30, unit: "days", basis: "receivedDate" });
    expect(r.outcome).toBe("conditional");
  });
  it("네이버 청약철회는 구매일이 아닌 이용 시작일 기준 7일·100%다", () => {
    const r = getRule("naver-plus", "withdrawal");
    expect(r.period).toEqual({ value: 7, unit: "days", basis: "serviceStartDate" });
    expect(r.refundPercent).toBe(100);
  });
  it("네이버는 청약철회 이후 미사용·회차 미종료 시 90% 환불 안내다", () => {
    expect(getRule("naver-plus", "after-withdrawal").refundPercent).toBe(90);
    expect(getRule("naver-plus", "after-withdrawal").outcome).toBe("percentage");
  });
  it("네이버 연간 중도 해지를 자동 환불 불가로 처리하지 않는다", () => {
    expect(getRule("naver-plus", "annual-early").outcome).toBe("conditional");
    expect(getPresetDefaults("naver-plus", "naver-monthly")?.price).toBe(4900);
    expect(getPresetDefaults("naver-plus", "naver-yearly")?.price).toBe(46800);
  });
  it("Spotify 평가판 없는 최초 구매는 14일이다", () => {
    expect(getRule("spotify", "initial").period).toEqual({ value: 14, unit: "days", basis: "purchaseDate" });
    expect(getRule("spotify", "initial").outcome).toBe("conditional");
  });
  it("Spotify 갱신·평가판 종료 후 청구는 청구일부터 7일이다", () => {
    expect(getRule("spotify", "renewal").period).toEqual({ value: 7, unit: "days", basis: "billingDate" });
  });
  it("YouTube 일반 잔여 기간 환불 불가와 기능 장애 요청을 구분한다", () => {
    expect(getRule("youtube-premium", "ordinary-cancel").outcome).toBe("none");
    expect(getRule("youtube-premium", "fault").outcome).toBe("request");
  });
  it("OpenAI 일반 비환불 원칙에 고정 한국 환불 기한을 부여하지 않는다", () => {
    expect(getRule("chatgpt-plus", "ordinary-cancel").outcome).toBe("none");
    expect(getRule("chatgpt-plus", "ordinary-cancel").period).toBeNull();
  });
  it("Apple에 근거 없는 90일 환불 기한을 부여하지 않는다", () => {
    expect(getRule("app-store", "request").period).toBeNull();
    expect(getRule("app-store", "request").outcome).toBe("request");
  });
  it("Google Play 48시간은 전액 환불이 아닌 심사 요청이다", () => {
    const r = getRule("google-play", "within-48h");
    expect(r.period).toEqual({ value: 48, unit: "hours", basis: "purchaseDate" });
    expect(r.outcome).toBe("request");
    expect(r.refundPercent).toBeNull();
  });
  it("Google Play 48시간 이후도 개발자에게 확인하도록 남긴다", () => {
    expect(getRule("google-play", "after-48h").outcome).toBe("request");
    expect(getRule("google-play", "after-48h").period).toBeNull();
  });
});

describe("원문 확인일의 경과", () => {
  it.each([["2026-12-21", "fresh", 30], ["2026-12-22", "stale", 31], ["2027-02-19", "stale", 90], ["2027-02-20", "outdated", 91]] as const)("%s에는 %s", (today, status, daysSince) => {
    expect(getVerifiedFreshness("2026-11-21", today)).toEqual({ status, daysSince });
  });
  it("미래 확인일을 최근 확인으로 표시하지 않는다", () => {
    expect(getVerifiedFreshness("2026-11-21", "2026-11-20")).toEqual({ status: "unverified", daysSince: -1 });
  });
});