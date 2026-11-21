import { describe, it, expect } from "vitest";
import { checkRefund } from "./refund-policies";
describe("checkRefund", () => {
  it("쿠팡 7일 이내 미사용은 전액 환불", () => {
    expect(checkRefund({ policyId: "coupang", purchaseDate: "2026-11-15", today: "2026-11-21", used: false })?.refund).toBe("full");
  });
  it("쿠팡 8일 경과는 불가", () => {
    expect(checkRefund({ policyId: "coupang", purchaseDate: "2026-11-13", today: "2026-11-21", used: false })?.eligible).toBe(false);
  });
  it("멜론 사용 후는 부분 환불", () => {
    expect(checkRefund({ policyId: "melon", purchaseDate: "2026-11-20", today: "2026-11-21", used: true })?.refund).toBe("prorated");
  });
});

import { getFreshness as gf, refundPolicies as rp, verifiedPolicyIds as vids } from "./refund-policies";
import { it as it2, expect as ex2 } from "vitest";
it2("freshness: unverified unless confirmed; 30/90 day thresholds", () => {
  const p = rp[0];
  if (!p) throw new Error("환불 규정 데이터 누락");
  ex2(gf(p, "2026-11-21").status).toBe("unverified");
  vids.push(p.id);
  ex2(gf(p, "2026-12-21").status).toBe("fresh");
  ex2(gf(p, "2027-01-30").status).toBe("stale");
  ex2(gf(p, "2027-03-01").status).toBe("outdated");
  vids.pop();
});
