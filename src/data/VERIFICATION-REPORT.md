# 공식 환불 안내 검증 기록

## 확인 기준

- 확인일: **2026-11-21 UTC**. 자동화된 웹 접근으로 공식 페이지 본문을 직접 확보하여 규정과 대조했다. 로그인·보안문자 우회는 하지 않았다.
- 기존 환불 초안 22곳과 신규 쇼핑몰 3곳, 총 **25곳**을 확인 대상으로 삼았다. 홈페이지가 열리거나 검색 결과에 문구가 있다는 이유만으로 검증 완료 처리하지 않았다.
- 검색은 공식 상세 주소 발견에만 사용했다. 최종 채택 근거는 해당 주소에서 직접 읽은 공식 원문이다.
- **10곳 채택, 15곳 제공 제외.** 검증은 인용한 조항과 명시한 범위에 한정하며 법률 전문 검수·개별 환불 승인·모든 상품 예외 확인은 아니다.
- 전체 HTML·수집 응답·이미지는 저장하지 않고 짧은 원문 인용, 상세 URL, 섹션, 언어, 대조일과 해석을 코드에 남겼다. 접근 시도일은 원문 확인일과 구분한다.

## 채택한 10곳

| 사이트 | 직접 읽은 공식 원문 | 확인 결과·보완점 |
| --- | --- | --- |
| 쿠팡 | [취소/반품](https://www.coupang.com/returnPolicy.pang), [이용약관](https://www.coupang.com/np/policies/terms) 제24·25조 | 단순변심 수령 후 7일, 하자 3개월·인지 가능 후 30일 별도 보존. 일반 배송비 부담자 확인, 금액·와우 혜택은 미확인. 안내의 ‘혹은’과 약관의 병기 차이를 보존하며 임의 택일 계산하지 않음. |
| 11번가 | [서비스이용약관](https://www.11st.co.kr/annc/AnncMainPreview.tmall?anncCd=01&method=getProvision) 제23조 | 수령 후 7일, 귀책자 왕복 배송비 부담. 반품 제외 사유와 접수 후 미반환 제한 확인. 해당 조항에 공통 하자 3개월·30일이 없으므로 비워 둠. |
| G마켓 | [안전거래센터 반품규정](https://help.gmarket.co.kr/SecurityCenter/Partial/_Guide?lkind=04&mkind=07&skind=47) | 수령 후 7일·배송비 귀책자 부담. 원문 하자 ‘3개월 또는 30일’ 표현과 문서 내 2013년 법령 인용의 한계 명시. 현행 법령 전체를 검증한 것으로 표시하지 않음. |
| Amazon | [Amazon.com Return Policy](https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7) | 미국 사이트 대부분 30일, 원래/미사용 상태·검수 조건. 15~365일 품목 예외와 2026년 시즌 연장도 명시. 한국 무료 반송으로 일반화 금지. |
| 네이버플러스 | [해지 및 환불 요청](https://help.naver.com/service/23168/contents/20281?lang=ko), [연간 요금](https://help.naver.com/service/23168/contents/22358?osType=COMMONOS) | 디지털 콘텐츠 미사용·회차 미종료 시 이용 시작 다음 날부터 7일 내 100%, 이후 90%. 연간 중도 해지 차감 기준과 회차 말일 제한도 확인. 월 4,900원·연 46,800원 재대조. |
| Spotify | [한국 이용약관](https://www.spotify.com/kr-ko/legal/end-user-agreement/) ‘결제 및 해지’ | 평가판 없는 최초 구매 14일, 이후 매월·평가판 종료 후 청구 7일; 기간 내 사용 시 철회권 소멸. 일반 해지 잔여 기간 비환불과 예외 구분. |
| YouTube Premium | [한국어 환불 안내](https://support.google.com/youtube/answer/12014038?hl=ko), [해지 안내](https://support.google.com/youtube/answer/6308278) | 일반 취소 잔여 기간 비환불, 기능 장애 환불 승인 가능, Apple·Google Play 결제 경로 구분. 공식 번역 오류 가능성 공지도 확인. |
| ChatGPT Plus | [OpenAI Terms of Use](https://openai.com/policies/terms-of-use) ‘Paid accounts’ | 일반 비환불 원칙은 법률상 의무 환불의 예외가 있음. 서비스 중단 시 선불 미사용분 예외 확인. 한국 고정 환불 기간·앱마켓별 환불 기준은 확인하지 않음. |
| Apple App Store | [환불 요청](https://support.apple.com/ko-kr/118223), [구독 취소](https://support.apple.com/ko-kr/118428) | 심사 요청 절차. 기존 ‘90일 내 요청’은 이 원문에 근거 없음. 24~48시간은 요청 업데이트 대기 시간이지 신청 마감이나 입금 보장이 아님. |
| Google Play | [앱·게임·정기 결제 환불](https://support.google.com/googleplay/answer/15574908?hl=ko), [정책 목록](https://support.google.com/googleplay/answer/2479637?hl=ko) | 48시간 이내 ‘가능할 수도 있음’; 전액 자동 환불 아님. 이후 개발자 문의. 시간 단위를 보존하고 날짜만으로 판정하지 않음. |

`verified-refund-policies.ts`의 각 `sources`에 짧은 원문 인용·섹션·언어·확인일을, 각 `rules.sourceIds`에 관련 출처를 기록했다. 더 자세한 조항은 표의 원문 링크에서 확인한다.

## 제공에서 제외한 15곳

아래는 **접근 시도 기록**이며 확인 완료 규정이 아니다. 해당 사이트의 규정이 없거나 환불이 불가능하다는 뜻도 아니다.

| 사이트 | 직접 접근한 주소 | 이번 접근 결과·제외 이유 |
| --- | --- | --- |
| 네이버 스마트스토어 | https://shopping.naver.com/ | 보안문자 확인 화면. 판매자별 반품 원문 미확보. |
| SSG.COM | https://www.ssg.com/ | 자동화 접근 감지에 따른 접속 제한 안내. 반품 본문 미확보. |
| 무신사 | https://www.musinsa.com/ , https://www.musinsa.com/app/cs/faq | 홈페이지는 글로벌 국가 선택 화면. 국내 FAQ는 질문 목록만 확보하고 답변의 기간·비용을 확인하지 못함. 글로벌 약관을 국내 규정으로 대체하지 않음. |
| 컬리 | https://www.kurly.com/ | 수집 엔진에서 원문 확보 실패. 품질 접수 2일 초안을 확정하지 않음. |
| AliExpress | https://www.aliexpress.com/ | 상품·프로모션 페이지는 열렸으나 기존 ‘15일 무료 반품’의 공통 적용 조항을 확인하지 못함. |
| 넷플릭스 | https://help.netflix.com/ko/node/407 , https://help.netflix.com/legal/termsofuse?locale=ko , https://help.netflix.com/ko/legal/termsofuse | 한국어 해지·잔여 기간 이용은 확인. 약관은 미국 Netflix, Inc.·미국 중재 조항의 영어 본문으로 표시되어 한국 환불 조항을 검증하지 못함. 해지 확인만으로 환불 규정 완료 처리하지 않음. |
| 티빙 | https://www.tving.com/ | 수집 엔진에서 원문 확보 실패. |
| 웨이브 | https://www.wavve.com/ | 콘텐츠 홈페이지만 확보, 환불 조항 본문 없음. |
| 디즈니+ | https://help.disneyplus.com/ , https://help.disneyplus.com/ko/article/disneyplus-refunds , https://help.disneyplus.com/article/disneyplus-refunds , https://www.disneyplus.com/ko-kr | 고객센터 목록·빈 안내 또는 과도한 리디렉션. 한국 URL의 요금표는 미국 달러·Hulu 결합 상품으로 표시됨. 한국 환불·현 요금 재검증 실패, 기존 요금 확인 상태를 현재 목록에 사용하지 않음. |
| 쿠팡 와우 | https://www.coupang.com/ | 일반 홈페이지만 확보. 와우 환불·혜택 사용 조건과 현 가입 요금 원문 미확보. 일반 배송상품 반품과 별개. |
| 멜론 | https://www.melon.com/ | 음악 홈페이지만 확보, 이용권별 해지·공제 조항 원문 없음. |
| 밀리의 서재 | https://www.millie.co.kr/ | 콘텐츠 홈페이지만 확보, 환불 조항 원문 없음. |
| 29CM | https://www.29cm.co.kr/ | 이번에는 상품 홈페이지가 열림. 기존 접근 차단과 달리 접속은 가능했지만 반품 규정은 확인하지 못함. |
| 지그재그 | https://zigzag.kr/ | 수집 엔진에서 원문 확보 실패. |
| 에이블리 | https://m.a-bly.com/ | 이번에는 상품·프로모션 홈페이지가 열림. 판매자별 반품 규정은 확인하지 못함. |

## 협업할 때 변경된 계약

1. **실제 제공:** `verifiedRefundPolicies` 10곳, `shoppingPolicies` 4곳(쿠팡·11번가·G마켓·Amazon).
2. **가격 자동입력:** `subscriptionPresets`는 환불 원문과 요금을 모두 확인한 네이버플러스 1곳·2개 요금제만 제공. 나머지 사이트의 환불 안내가 검증되어도 요금을 확인하지 않았다면 가격 프리셋에는 없음.
3. **격리된 초안:** `draftShoppingPolicies` 9곳, `draftSubscriptionPresets` 6곳·16개 요금제, `refund-policies.ts` 22곳은 호환·검수용으로만 보존. 실제 제공 목록에 결합하거나 `checkRefund()`를 검증 판정기로 사용하지 말 것.
4. **가상 시연:** 기존 구매·구독 4건은 `isMock: true` 유지. 넷플릭스·YouTube 시연 가격은 실제 검증 가격이 아니며 `presetId`, `planId`를 `null`로 끊어 직접입력 사례로 보존.
5. **원문 확인일:** 화면은 `collectedAt`/`sources.checkedAt`만 사용. 30일 이내 최근 확인, 31~90일 확인 권장, 91일 이상 오래됨. 이후 변경 없음은 보장하지 않음.
6. **일반 날짜 계산:** `calculatePurchaseDeadline()`은 날짜 계산만 담당. 상품별 예외·시즌 연장·공휴일 법적 연장·기산 세부 해석·환불 승인에는 사용하지 말 것.
7. **통계·법령:** 이번에는 공공 통계와 현행 법령 원문을 별도로 대조하지 않았다. `publicDisputeStats`는 빈 배열, `standardPolicy`는 미검증 검수용 유지.

## 다음 검수

- 제외한 사이트는 국내 고객센터의 공개 상세 원문·상품/판매자 범위 확보 후 재검수한다. 외국 지역 약관이나 개별 판매자의 조건을 공통 규정으로 전환하지 않는다.
- 필드 단위로 확인한 값만 변경하고 기간·금액·신청 기한을 추정하지 않는다. 출처·짧은 인용·확인일·조건을 함께 추가하고 검사도 변경한다.
- 법령 기간의 관계와 공휴일 처리, 플랫폼별 최초일 산입 여부는 전문 검수 후 계산기에 연결한다.

검사: `bunx vitest run src/data/service-data.test.ts src/data/refund-policies.test.ts src/data/verified-refund-policies.test.ts src/test/app-routing.test.tsx`