import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { verifiedRefundPolicies, getVerifiedFreshness } from "@/data/verified-refund-policies";
import type { Freshness } from "@/data/refund-policies";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "환불정거장 — 공식 원문으로 확인한 환불 규정" },
      { name: "description", content: "공식 원문을 대조한 10곳의 환불 규정, 적용 범위, 예외 조건과 실제 확인일을 확인하세요." },
      { property: "og:title", content: "환불정거장 — 공식 환불 규정 확인" },
      { property: "og:description", content: "공식 환불 안내의 근거와 실제 확인일을 함께 보여드립니다. 미확인 사이트는 제공 목록에서 제외했습니다." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Index,
});

const LABEL: Record<Freshness, { text: string; cls: string; hint: string }> = {
  fresh: { text: "최근 확인", cls: "bg-primary text-primary-foreground", hint: "30일 이내 공식 원문 대조 · 이후 변경 가능" },
  stale: { text: "확인 권장", cls: "bg-secondary text-secondary-foreground", hint: "확인한 지 31~90일 지남" },
  outdated: { text: "오래됨", cls: "bg-destructive text-destructive-foreground", hint: "확인한 지 90일 넘음" },
  unverified: { text: "확인일 점검", cls: "bg-muted text-muted-foreground border border-border", hint: "현재 날짜와 확인일의 관계를 점검하세요" },
};

type Tab = "all" | "shopping" | "subscription" | "appstore";
const TABS: { id: Tab; label: string }[] = [
  { id: "all", label: "전체" }, { id: "shopping", label: "쇼핑몰" },
  { id: "subscription", label: "구독 서비스" }, { id: "appstore", label: "앱마켓" },
];
const tabOf = (p: (typeof verifiedRefundPolicies)[number]): Tab =>
  p.subcategory === "앱마켓" ? "appstore" : p.category === "shopping" ? "shopping" : "subscription";

function Index() {
  const [today, setToday] = useState("2026-11-21");
  const [tab, setTab] = useState<Tab>("all");
  const [q, setQ] = useState("");
  const query = q.trim().toLowerCase();
  const list = verifiedRefundPolicies.filter((p) =>
    (tab === "all" || tabOf(p) === tab) &&
    (!query || `${p.name} ${p.id} ${p.subcategory}`.toLowerCase().includes(query)));
  useEffect(() => setToday(new Date().toISOString().slice(0, 10)), []);
  return (
    <main className="mx-auto max-w-4xl px-4 py-10 bg-background text-foreground">
      <h1 className="text-3xl font-bold">환불정거장</h1>
      <p className="mt-2 text-muted-foreground">공식 원문을 확인한 {verifiedRefundPolicies.length}곳의 환불 안내입니다. 미확인 사이트는 제외했으며, 확인은 아래 적용 범위에 한정됩니다. 개별 환불 승인이나 이후 변경 없음은 보장하지 않습니다.</p>
      <ul className="mt-4 flex flex-wrap gap-3 text-xs">
        {(Object.keys(LABEL) as Freshness[]).map((k) => (
          <li key={k} className="flex items-center gap-1"><span className={`rounded px-2 py-0.5 ${LABEL[k].cls}`}>{LABEL[k].text}</span><span className="text-muted-foreground">{LABEL[k].hint}</span></li>
        ))}
      </ul>
      <div className="mt-6 flex flex-wrap gap-2" role="tablist">
        {TABS.map((t) => {
          const n = verifiedRefundPolicies.filter((p) => t.id === "all" || tabOf(p) === t.id).length;
          return (
            <button key={t.id} role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)}
              className={`rounded-full border border-border px-3 py-1 text-sm ${tab === t.id ? "bg-primary text-primary-foreground" : "bg-card"}`}>
              {t.label} ({n})
            </button>
          );
        })}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="사이트 이름이나 분류로 검색 (예: 쿠팡, 음악)"
          aria-label="사이트 검색" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
        {q && <button onClick={() => setQ("")} className="shrink-0 rounded-md border border-border px-3 py-2 text-sm">지우기</button>}
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{list.length}곳 표시 중</p>
      {list.length === 0 && <p className="mt-6 rounded-lg border border-dashed border-border p-6 text-center text-muted-foreground">일치하는 사이트가 없습니다. 검색어나 분류를 바꿔 보세요.</p>}
      <div className="mt-4 grid gap-3">
        {list.map((p) => {
          const f = getVerifiedFreshness(p.collectedAt, today);
          const l = LABEL[f.status];
          return (
            <article key={p.id} className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center justify-between gap-2">
                <h2 className="font-semibold">{p.name} <span className="ml-1 rounded bg-muted px-1.5 py-0.5 text-xs font-normal text-muted-foreground">{TABS.find((t) => t.id === tabOf(p))?.label} · {p.subcategory}</span></h2>
                <span title={l.hint} className={`rounded px-2 py-0.5 text-xs ${l.cls}`}>{l.text}</span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">적용 범위: {p.scope}</p>
              <ul className="mt-2 list-disc pl-5 text-sm">{p.rules.map((r, i) => <li key={i}>{r.note}</li>)}</ul>
              <p className="mt-3 text-sm"><span className="font-medium">신청 방법</span> · {p.howTo}</p>
              <details className="mt-3 text-sm">
                <summary className="cursor-pointer text-primary">예외 조건과 공식 근거</summary>
                <ul className="mt-2 list-disc pl-5 text-muted-foreground">{p.exclusions.map((item) => <li key={item}>{item}</li>)}</ul>
                {p.sources.map((s) => (
                  <div key={s.id} className="mt-3 border-l-2 border-border pl-3">
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-primary underline">{s.title} ↗</a>
                    <p className="mt-1 text-xs text-muted-foreground">{s.section} · {s.language === "ko" ? "한국어" : "영어"} 원문 · 대조일 {s.checkedAt}</p>
                    <blockquote className="mt-1 break-words text-muted-foreground">“{s.quote}”</blockquote>
                  </div>
                ))}
              </details>
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                <a href={p.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-primary underline">출처 약관 보기 ↗</a>
                <span>마지막 원문 확인일: {p.collectedAt}{f.daysSince >= 0 ? ` (${f.daysSince}일 전)` : " (현재 날짜 점검 필요)"}</span>
              </div>
            </article>
          );
        })}
      </div>
    </main>
  );
}
