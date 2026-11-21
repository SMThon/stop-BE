import type { BillingCycle, ISODate, Policy } from "./service-types";

const DAY = 86_400_000;
export function parseDate(value: ISODate): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error("날짜는 YYYY-MM-DD 형식이어야 합니다.");
  const date = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== value) {
    throw new Error("존재하지 않는 날짜입니다.");
  }
  return date;
}
export function addDays(value: ISODate, days: number): ISODate {
  if (!Number.isInteger(days)) throw new Error("일수는 정수여야 합니다.");
  return new Date(parseDate(value).getTime() + days * DAY).toISOString().slice(0, 10);
}
export function daysUntil(deadline: ISODate, today: ISODate): number {
  return (parseDate(deadline).getTime() - parseDate(today).getTime()) / DAY;
}
/** 기간을 모르면 null. 법정 기준을 판매처의 확인된 규정으로 자동 대체하지 않는다. */
export function calculatePurchaseDeadline(
  policy: Policy,
  dates: { orderDate: ISODate; receivedDate: ISODate | null },
): ISODate | null {
  const base = dates[policy.baseDate];
  if (!base || policy.returnDays === null) return null;
  if (!Number.isInteger(policy.returnDays) || policy.returnDays < 1) return null;
  return addDays(base, policy.returnDays - (policy.includeStartDay ? 1 : 0));
}
export type DeadlineWarning = "red" | "yellow" | "green" | "gray";
export function getDeadlineWarning(deadline: ISODate, today: ISODate): DeadlineWarning {
  const remaining = daysUntil(deadline, today);
  if (remaining < 0) return "gray";
  if (remaining <= 2) return "red";
  if (remaining <= 5) return "yellow";
  return "green";
}
/** 다음 결제일은 예정일이지 해지 보장 시각이 아니다. 전날 날짜는 예방용 알림일이다. */
export function subscriptionDates(nextBillingDate: ISODate, trialEndDate: ISODate | null = null) {
  parseDate(nextBillingDate);
  const deadline = trialEndDate ?? nextBillingDate;
  return { deadline, cancelReminderDate: addDays(deadline, -1) };
}
/** 최초 다음 결제일을 기준으로 이동하여 31→28→31의 원래 결제일을 보존한다. */
export function advanceBillingDate(anchor: ISODate, cycle: BillingCycle, today: ISODate): ISODate {
  const start = parseDate(anchor);
  const now = parseDate(today);
  if (start >= now) return anchor;
  const step = cycle === "월" ? 1 : 12;
  const diff = (now.getUTCFullYear() - start.getUTCFullYear()) * 12 + now.getUTCMonth() - start.getUTCMonth();
  let periods = Math.max(0, Math.floor(diff / step));
  const candidate = (count: number) => {
    const first = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + count * step, 1));
    const lastDay = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
    first.setUTCDate(Math.min(start.getUTCDate(), lastDay));
    return first.toISOString().slice(0, 10);
  };
  if (parseDate(candidate(periods)) < now) periods += 1;
  return candidate(periods);
}