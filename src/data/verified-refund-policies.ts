import { daysUntil } from "./date-rules";
import type { OfficialSource, VerifiedRefundPolicy, VerifiedRefundRule } from "./service-types";

export const VERIFIED_AT = "2026-11-21";
const source = (id: string, title: string, url: string, section: string, quote: string,
  language: "ko" | "en" = "ko"): OfficialSource => ({ id, title, url, section, quote, language, checkedAt: VERIFIED_AT });
const rule = (id: string, note: string, outcome: VerifiedRefundRule["outcome"],
  period: VerifiedRefundRule["period"], conditions: string[], sourceIds: string[],
  refundPercent: number | null = null): VerifiedRefundRule => ({ id, note, outcome, period, conditions, sourceIds, refundPercent });
const policy = (data: Omit<VerifiedRefundPolicy, "sourceUrl" | "collectedAt" | "verificationStatus" | "evidenceNote">): VerifiedRefundPolicy => ({
  ...data, sourceUrl: data.sources[0]?.url ?? "", collectedAt: VERIFIED_AT, verificationStatus: "verified",
  evidenceNote: "공식 원문을 직접 열어 아래 인용·적용 범위를 대조함. 법률 검수나 개별 환불 승인, 전체 약관의 완전한 수집을 뜻하지 않음.",
});

/** 이용자 제공용. 호환용 refund-policies.ts의 초안 및 checkRefund()와 혼용하지 않는다. */
export const verifiedRefundPolicies: VerifiedRefundPolicy[] = [
  policy({
    id: "coupang", name: "쿠팡", category: "shopping", subcategory: "종합몰",
    scope: "국내 배송상품의 일반 반품 안내. 와우 회원·로켓배송별 추가 혜택은 이번에 검증하지 않음.",
    sources: [
      source("return", "쿠팡 취소/반품 안내", "https://www.coupang.com/returnPolicy.pang", "반품방법·배송비 부담 여부", "단순 변심인 경우 : 상품 수령 후 7일 이내 신청"),
      source("terms", "쿠팡 이용약관", "https://www.coupang.com/np/policies/terms", "제24조③·제25조④", "당해 상품 등을 공급받은 날부터 3개월 이내, 그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내에 청약철회 등을 할 수 있습니다."),
    ],
    rules: [
      rule("change-of-mind", "단순 변심은 수령 후 7일 이내 신청. 상품 상태·제외 조건 확인이 필요하며 최초 배송비를 포함한 왕복 배송비는 고객 부담입니다.", "conditional", { value: 7, unit: "days", basis: "receivedDate" }, ["반품 제외 사유에 해당하지 않는 배송상품", "상품 확인 후 환불", "배송비 금액은 상품별 확인"], ["return", "terms"]),
      rule("defect-receipt", "표시·광고 또는 계약과 다른 상품: 공급받은 날부터 3개월 기준과 인지·인지 가능일부터 30일 기준을 함께 확인하세요. 반환 비용은 회사 부담입니다.", "conditional", { value: 3, unit: "calendar-months", basis: "receivedDate" }, ["표시·광고 또는 계약과 다르게 이행", "인지 후 30일 기준도 함께 확인; 두 기간을 임의로 택일하지 않음"], ["terms"]),
      rule("defect-discovery", "같은 하자 규정의 인지·인지 가능일 기준은 30일입니다. 3개월을 90일로 환산하지 않습니다.", "conditional", { value: 30, unit: "days", basis: "discoveredDate" }, ["공급일 3개월 기준과 함께 확인"], ["terms"]),
    ],
    exclusions: ["구매자 책임으로 멸실·훼손(내용 확인을 위한 포장 훼손은 제외)", "사용·소비 또는 시간 경과로 가치가 현저히 감소", "복제 가능 상품 포장 훼손", "제공이 개시된 용역·디지털 콘텐츠의 제한(미제공 가분 부분 예외)", "사전 고지·서면 동의 요건을 충족한 주문제작 상품", "상품별 추가 제한과 와우 혜택 별도 확인"],
    howTo: "마이쿠팡에서 반품 신청 → 택배기사 방문 수거 → 상품 확인 후 환불",
    cancelEffect: "결제완료는 즉시 환불, 발송 이후는 반품 회수·검수 후 환불 절차를 따릅니다.",
  }),
  policy({
    id: "11st", name: "11번가", category: "shopping", subcategory: "오픈마켓",
    scope: "국내 11번가 서비스이용약관 제23조. 개별 판매자의 상품 공지를 플랫폼 공통 규정으로 일반화하지 않음.",
    sources: [source("terms", "11번가 서비스이용약관", "https://www.11st.co.kr/annc/AnncMainPreview.tmall?anncCd=01&method=getProvision", "제23조①·③·⑩·⑬", "구매자는 상품을 배송받은 날로부터 7일 이내에 반품 또는 교환을 요청할 수 있으며")],
    rules: [
      rule("change-of-mind", "배송받은 날부터 7일 이내 반품·교환 요청. 왕복 배송비와 기타 비용은 귀책사유가 있는 쪽에서 부담합니다.", "conditional", { value: 7, unit: "days", basis: "receivedDate" }, ["상품 상태·제외 조건 확인", "반품송장번호 미기재 시 처리 지연 가능", "접수 후 14일 내 미반환·연락 불가 시 철회 간주 가능"], ["terms"]),
    ],
    exclusions: ["구매자 귀책 훼손", "사용·소비 또는 시간 경과로 가치가 현저히 감소", "복제 가능한 상품 포장 훼손", "사전 고지·서면 동의 요건을 충족한 주문제작 상품"],
    howTo: "11번가에 반품·교환 의사를 접수하면 판매자에게 통보됩니다. 반품송장번호를 기재하세요.",
    cancelEffect: "발송 전 구매 취소 가능. 배송 중이면 반품 절차로 처리합니다.",
  }),
  policy({
    id: "gmarket", name: "G마켓", category: "shopping", subcategory: "오픈마켓",
    scope: "G마켓 안전거래센터의 반품·교환 운영 정책. 문서 내 법령 인용은 2013년 시행본으로, 현행 법령 전체 검증은 아님.",
    sources: [source("guide", "G마켓 안전거래센터 반품규정", "https://help.gmarket.co.kr/SecurityCenter/Partial/_Guide?lkind=04&mkind=07&skind=47", "청약철회 가능 기간·배송비 정책", "반품/교환 배송비는 반품/교환의 원인을 제공한 자가 부담하도록 되어 있습니다.")],
    rules: [
      rule("change-of-mind", "상품 수령일부터 7일 이내 교환·반품 신청. 단순 변심은 구매자가, 판매자 책임의 오배송·파손은 판매자가 배송비를 부담합니다.", "conditional", { value: 7, unit: "days", basis: "receivedDate" }, ["반품 제외 사유에 해당하지 않는 상품", "관련 법령이 판매자 조건보다 우선"], ["guide"]),
      rule("defect-receipt", "표시·광고 또는 계약과 다른 상품은 원문에 ‘수령 후 3개월 이내 또는 사실을 안 날부터 30일 이내’로 안내됩니다. 두 기간의 법적 관계는 별도 검수 대상입니다.", "conditional", { value: 3, unit: "calendar-months", basis: "receivedDate" }, ["표시·광고 또는 계약과 다르게 이행", "두 기간 중 유리한 날짜 자동 선택 금지"], ["guide"]),
      rule("defect-discovery", "같은 원문에서 사실을 안 날부터 30일 기준도 안내합니다.", "conditional", { value: 30, unit: "days", basis: "discoveredDate" }, ["수령 후 3개월 기준과 함께 확인"], ["guide"]),
    ],
    exclusions: ["반품요청 기간 경과", "구매자 책임 훼손(확인용 포장 훼손 제외)", "사용·소비 또는 시간 경과로 가치가 현저히 감소", "복제 가능한 상품 포장 훼손", "판매·생산 특성상 판매자에게 회복 불가능한 손해가 발생하는 경우(법령 요건 별도 확인)"],
    howTo: "게시판·G마켓 웹사이트·전화로 교환·반품 신청. 분쟁은 G마켓 고객센터에 문의하세요.",
    cancelEffect: "반품 도착일부터 3영업일 이내 환불 또는 필요한 조치. 배송비 환불유보 예외가 있습니다.",
  }),
  policy({
    id: "amazon", name: "Amazon", category: "shopping", subcategory: "해외직구",
    scope: "Amazon.com 미국 사이트의 일반 정책. 한국 반송 비용·다른 국가 Amazon·개별 판매자 조건을 일괄 보장하지 않음.",
    sources: [source("return", "Amazon Return Policy", "https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7", "Return Window·2026 Holiday Season Extended Return Window", "Most items can be returned for a refund or replacement/exchange within 30 days of delivery as long as they are in original or unused condition.", "en")],
    rules: [
      rule("standard", "대부분의 상품은 배송 후 30일 이내 원래 상태 또는 미사용 상태로 반품 가능. 상품별 적격 여부와 주문 내 반품 기한이 우선입니다.", "conditional", { value: 30, unit: "days", basis: "receivedDate" }, ["대상 상품의 반품 적격 확인", "태그·구성품·원래 포장 보존", "Amazon 또는 판매자 수령·검수 후 승인", "한국 반송 무료 여부 미확인"], ["return"]),
      rule("holiday-2026", "2026년 11월 1일~12월 31일 구매한 대부분의 대상 상품은 2027년 1월 31일까지 연장 반품. Apple 브랜드는 2027년 1월 15일까지입니다.", "conditional", null, ["해당 구매 기간·프로모션 대상 상품", "상품별 예외와 주문 내 표시 기한 확인"], ["return"]),
    ],
    exclusions: ["일부 신선식품·주문제작·약국·디지털 상품·Final Sale 등 반품 불가", "새 Apple 브랜드·일부 Haul 상품은 일반 15일; 일부 다른 상품은 90~365일", "반품 불가 상품의 하자·손상·오배송은 고객센터 문의"],
    howTo: "Your Orders에서 해당 상품의 Return Items 선택 후 표시된 반송 지침·기한을 따릅니다.",
    cancelEffect: "반품 환불은 수령·검수 후 적격 판정이 필요합니다. 모든 상품의 즉시 환불을 보장하지 않습니다.",
  }),
  policy({
    id: "naver-plus", name: "네이버플러스 멤버십", category: "subscription", subcategory: "멤버십",
    scope: "기본 멤버십 월 회차의 즉시 종료와 연간 이용권 중도 해지. 디지털 콘텐츠 추가 구매·업그레이드 결제는 별도 규정.",
    sources: [
      source("refund", "네이버플러스 멤버십 해지 및 환불 요청", "https://help.naver.com/service/23168/contents/20281?lang=ko", "멤버십 즉시 종료하기·정기결제 해지하기", "네이버플러스 멤버십 청약철회 기한은 이용 시작 다음 날부터 7일 이내입니다."),
      source("annual", "네이버플러스 연간 이용권 중도 해지", "https://help.naver.com/service/23168/contents/20281?lang=ko", "연간 이용권 사용자", "환불 수수료는 사용한 달만큼의 개월 수에 정가 4,900원을 곱한 금액입니다."),
    ],
    rules: [
      rule("withdrawal", "디지털 콘텐츠를 전혀 사용하지 않고 이용 시작 다음 날부터 7일 이내 즉시 종료하면 100% 환불됩니다. 적립·예정 포인트와 혜택은 회수됩니다.", "percentage", { value: 7, unit: "days", basis: "serviceStartDate" }, ["디지털 콘텐츠 미사용", "이용 기간이 끝나지 않은 회차", "이용 시작 당일 제외", "포인트 회수·마이너스 잔액 발생 가능"], ["refund"], 100),
      rule("after-withdrawal", "청약철회 기간 이후에도 디지털 콘텐츠 미사용·이용 기간 미종료 회차는 즉시 종료 시 90% 환불 가능합니다.", "percentage", null, ["청약철회 기간 경과", "디지털 콘텐츠 미사용", "해당 회차 이용 기간 미종료"], ["refund"], 90),
      rule("annual-early", "연간 이용권 중도 해지는 이번 회차 이용 후 종료하며, 결제금액에서 사용 개월 수 × 정가 4,900원을 차감합니다. 음수 예상 금액·회차 마지막 날 제한은 고객센터 확인이 필요합니다.", "conditional", null, ["연간 이용권 중도 해지 선택", "회차 마지막 날에는 중도 해지 불가", "환불 수수료가 결제금액보다 크면 초과금 입금 안내 확인"], ["annual"]),
    ],
    exclusions: ["디지털 콘텐츠 사용 시 해당 회차 즉시 종료 환불 불가", "이용 기간 종료 회차는 미사용이어도 즉시 종료 환불 불가", "추가 구매·업그레이드는 별도 해지 필요"],
    howTo: "네이버플러스 마이 멤버십 > 설정 > 멤버십 관리 > 멤버십 해지하기에서 즉시 종료 또는 정기결제 해지를 선택합니다.",
    cancelEffect: "정기결제 해지는 다음 회차 청구 중단. 월간은 현재 회차까지 이용; 연간은 12회차 이용 후 종료 또는 중도 해지 선택.",
  }),
  policy({
    id: "spotify", name: "Spotify", category: "subscription", subcategory: "음악",
    scope: "Spotify 한국어 이용약관의 직접 유료 구독. 최초 구매·갱신·평가판을 구분하며 제휴 결제는 해당 채널 조건을 확인.",
    sources: [source("terms", "Spotify 한국 이용 약관", "https://www.spotify.com/kr-ko/legal/end-user-agreement/", "결제 및 해지·청약철회 권리", "평가판을 사용하지 않고 유료 구독을 구입한 경우에는 회원은 구입일로부터 14일, 최초 구입일 이후에는 매달 합의된 금액의 청구일로부터 7일 동안 청약철회 권리를 보유하지만")],
    rules: [
      rule("initial", "평가판 없이 최초 유료 구독 구매 시 14일 동안 청약철회 권리가 있습니다. 해당 기간 서비스를 사용하면 권리를 상실합니다.", "conditional", { value: 14, unit: "days", basis: "purchaseDate" }, ["평가판 없는 최초 유료 구매", "기간 중 Spotify 서비스 미사용"], ["terms"]),
      rule("renewal", "최초 구매 이후 매월 청구 또는 평가판 종료 후 청구는 청구일부터 7일 이내 청약철회 가능. 해당 기간 서비스를 사용하면 권리를 상실합니다.", "conditional", { value: 7, unit: "days", basis: "billingDate" }, ["매월 갱신 또는 평가판 종료 후 청구", "기간 중 Spotify 서비스 미사용"], ["terms"]),
      rule("ordinary-cancel", "일반 해지는 청구 기간 종료 시 무료 계정으로 전환됩니다. 약관에 명시된 예외 외에는 기간 일부의 환불·크레딧을 제공하지 않습니다.", "none", null, ["청약철회·서비스 중단 등 약관 예외 제외"], ["terms"]),
    ],
    exclusions: ["청약철회 기간 내 서비스 이용 시 청약철회권 소멸", "평가판 청약철회는 체험 개시부터 14일로 별도 안내", "Spotify의 서비스 중단 등 선불 미사용분 환불 예외 존재"],
    howTo: "Spotify 계정 페이지 안내에 따라 해지하거나 Spotify 고객지원으로 청약철회·환불을 문의합니다.",
    cancelEffect: "달리 정하지 않는 한 해지한 청구 기간 종료 시 무료 계정으로 전환됩니다.",
  }),
  policy({
    id: "youtube-premium", name: "YouTube Premium", category: "subscription", subcategory: "OTT/음악",
    scope: "YouTube Premium·Music Premium 환불 안내. 채널 멤버십은 제외; Apple·Google Play 결제는 해당 결제 채널 확인.",
    sources: [source("refund", "YouTube Premium 또는 YouTube Music Premium 환불받기", "https://support.google.com/youtube/answer/12014038?hl=ko", "환불 정책", "멤버십을 취소하는 시점과 멤버십이 종료되는 시점 사이의 기간에 대해서는 환불되지 않습니다.")],
    rules: [
      rule("ordinary-cancel", "일반 멤버십 취소는 자동 갱신만 중단하며 결제 주기 마지막 날까지 혜택 유지. 취소일부터 종료일까지의 잔여 기간은 환불되지 않습니다.", "none", null, ["단순 멤버십 취소", "기능 장애 등 환불 예외는 별도"], ["refund"]),
      rule("fault", "구매한 동영상·기능이 작동하지 않으면 환불을 받을 수 있습니다. 요청 승인 후 Premium 이용 권한이 삭제됩니다.", "request", null, ["구매 관련 동영상 또는 기능 장애", "환불 요청 승인 필요", "Apple 구매는 Apple 승인·정책 적용"], ["refund"]),
    ],
    exclusions: ["일부 사용한 선불·연간 요금제는 환불 불가", "Apple 구매는 Apple의 환불 정책·승인 적용"],
    howTo: "YouTube 지원팀으로 즉시 취소·환불 문의. Google Play·Apple 결제는 청구 방식을 확인해 해당 채널로 요청합니다.",
    cancelEffect: "재가입하지 않는 한 추가 청구 중단, 결제 주기 마지막 날까지 혜택 유지. 환불 승인 시 혜택 종료.",
  }),
  policy({
    id: "chatgpt-plus", name: "ChatGPT Plus", category: "subscription", subcategory: "AI",
    scope: "OpenAI 개인용 서비스 일반 이용약관. 한국법에 따른 구체적 환불 기간과 앱마켓 별도 결제 규정은 미확인.",
    sources: [source("terms", "OpenAI Terms of Use", "https://openai.com/policies/terms-of-use", "Paid accounts — Cancellation", "Payments are non-refundable, except where required by law. These Terms do not override any mandatory local laws regarding your cancellation rights.", "en")],
    rules: [rule("ordinary-cancel", "일반 약관상 결제는 환불 불가이나 법률이 요구하는 환불은 예외입니다. 현지법의 의무적인 취소 권리를 약관이 대체하지 않습니다.", "none", null, ["법률상 환불 의무·서비스 중단의 선불 미사용분 등 예외 제외", "한국의 구체적 기간은 별도 확인"], ["terms"])],
    exclusions: ["법률상 환불 의무는 환불 불가 원칙의 예외", "OpenAI 서비스 중단 시 선불 미사용 서비스 환불 안내 존재"],
    howTo: "OpenAI 도움말의 구독 취소·환불 경로 이용. 앱마켓 결제는 해당 결제 채널 규정을 확인하세요.",
    cancelEffect: "유료 구독은 언제든 취소 가능. 정확한 청구 중단 시각은 이 약관에서 확인하지 않았습니다.",
  }),
  policy({
    id: "app-store", name: "Apple App Store 구독", category: "subscription", subcategory: "앱마켓",
    scope: "Apple로 청구된 앱·구독·콘텐츠의 환불 요청 절차. 특정 기간 내 자동 승인이나 90일 환불 기한을 뜻하지 않음.",
    sources: [
      source("refund", "Apple에서 구입한 앱 또는 콘텐츠의 환불 요청하기", "https://support.apple.com/ko-kr/118223", "환불 요청하기·요청 업데이트", "요청에 대한 업데이트를 받을 때까지 24~48시간 기다리기"),
      source("cancel", "Apple 구독 취소하기", "https://support.apple.com/ko-kr/118428", "구독 취소", "웹 또는 기기를 사용하여 Apple 구독 또는 App Store의 앱으로 구입한 구독을 취소할 수 있습니다."),
    ],
    rules: [rule("request", "일부 구입 항목은 환불 대상이 될 수 있습니다. reportaproblem.apple.com에서 요청하고 24~48시간 후 업데이트를 확인하세요. 이는 신청 기한·입금 보장 시간이 아닙니다.", "request", null, ["Apple로 청구된 앱·구독·콘텐츠", "Apple 승인 필요", "국가·지역에 따라 적격성 다름", "청구 보류 중에는 환불 요청 불가", "미결제 주문은 먼저 결제"], ["refund"])],
    exclusions: ["Apple을 통해 청구되지 않은 구입은 별도 제공업체 확인", "고정 90일 환불 기한은 이 문서에 없음"],
    howTo: "reportaproblem.apple.com 로그인 > 문제 선택 > 환불 요청 > 이유 선택 > 앱·구독 선택 > 제출",
    cancelEffect: "원치 않는 구독의 취소와 기존 결제의 환불 요청은 별개 절차입니다.",
  }),
  policy({
    id: "google-play", name: "Google Play 구독", category: "subscription", subcategory: "앱마켓",
    scope: "Google Play 앱·게임·인앱 구매(정기 결제 포함). 콘텐츠 종류·국가·결제수단별 추가 정책을 함께 확인.",
    sources: [source("apps", "앱, 게임, 인앱 구매(정기 결제 포함) 환불 정책", "https://support.google.com/googleplay/answer/15574908?hl=ko", "구매 후 경과 시간에 따른 환불", "48시간 이내: 구매 세부정보에 따라 환불이 가능할 수도 있습니다.")],
    rules: [
      rule("within-48h", "구매 후 48시간 이내에는 구매 세부정보에 따라 환불이 가능할 수도 있습니다. 전액 환불·자동 승인이 아닙니다.", "request", { value: 48, unit: "hours", basis: "purchaseDate" }, ["앱·게임·인앱 구매(정기 결제 포함)", "구매 세부정보에 따른 승인", "정확한 결제 시각 필요; 날짜만으로 48시간 판정 금지"], ["apps"]),
      rule("after-48h", "48시간 이후에는 개발자에게 문의하세요. 개발자 정책과 관련 법규에 따라 환불 가능 여부를 확인합니다.", "request", null, ["구매 후 48시간 경과", "개발자 정책·관련 법규 확인"], ["apps"]),
    ],
    exclusions: ["앱·게임 환불은 1회; 다시 구매하면 환불 불가 안내", "환불 시 해당 항목 이용 불가", "한 번에 여러 상품 구매 시 전체 환불 안내", "공식 한국어 페이지에 AI 번역 오류 가능성 안내가 있음"],
    howTo: "Google Play 환불 요청 페이지에서 접수. 48시간 경과 시 앱 개발자에게 문의합니다.",
    cancelEffect: "이 문서는 환불 정책이며 구독 갱신 중단은 별도 취소 절차로 확인해야 합니다.",
  }),
];

/** ‘최신’은 최근 원문 대조를 뜻할 뿐, 이후 변경이 없다는 보장은 아니다. */
export function getVerifiedFreshness(checkedAt: string, today: string) {
  const daysSince = daysUntil(today, checkedAt);
  if (daysSince < 0) return { status: "unverified" as const, daysSince };
  return { status: daysSince <= 30 ? "fresh" as const : daysSince <= 90 ? "stale" as const : "outdated" as const, daysSince };
}