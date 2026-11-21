"""프론트(src/data/service-types.ts)의 PurchaseStatus 값과 동일하게 맞춘 상태값."""

STATUS_KEEPING = "보관 중"
STATUS_RETURN_REQUESTED = "반품 신청"
STATUS_REFUNDED = "환불 완료"
STATUS_EXPIRED = "기한 지남"  # 서버가 마감일로 계산해서 내려주는 값. 직접 저장하지 않는다.

SOURCE_BUILT_IN = "built-in"
SOURCE_USER_INPUT = "user-input"
