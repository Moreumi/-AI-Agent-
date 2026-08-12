# Order Cancel Policy v1

## 1. 목적

이 문서는 온라인 쇼핑몰 AI Agent의 `order_cancel` 기능에서
주문 취소 가능 여부, 사용자 최종 승인, 결제 취소 및 환불 처리 기준을 정의한다.

주문 취소 여부와 환불 처리 방식은 LLM이 임의로 판단하지 않는다.

확정된 주문/배송/결제 상태와 본 Policy를 기준으로
Python Business Rule에서 판단한다.

---

## 2. 사용 상태값

### order_status

```text
order_completed
→ 정상적으로 접수된 주문

order_canceled
→ 취소된 주문

order_failed
→ 정상적으로 완료되지 않은 주문
```

### delivery_status

```text
preparing_shipment
→ 배송준비중

in_transit
→ 배송중

delivered
→ 배송완료
```

### payment_method

```text
card
→ 카드 결제

cash
→ 계좌이체
```

### payment_status

```text
payment_completed
→ 결제 완료

payment_canceled
→ 결제 취소

payment_failed
→ 결제 실패
```

### refund_status

```text
not_requested
→ 환불 절차가 시작되지 않은 상태

refund_account_required
→ 환불계좌 입력이 필요한 상태

refund_processing
→ 환불 처리 중

refund_completed
→ 실제 환불 완료

refund_failed
→ 환불 처리 실패
```

`payment_status`와 `refund_status`는 서로 다른 의미를 가진다.

```text
payment_canceled
≠
refund_completed
```

결제 취소가 완료되었다고 해서
고객에게 실제 금액 반환까지 완료되었다고 판단하지 않는다.

---

## 3. 주문 취소 가능 여부

주문 취소 가능 여부는 먼저 `order_status`를 확인한 뒤,
정상 주문인 경우 `delivery_status`를 확인한다.

### order_status = order_completed

#### delivery_status = preparing_shipment

```text
cancel_judgment = cancelable
```

배송준비중인 주문만 취소할 수 있다.

취소 가능 판정 이후에도 바로 주문을 취소하지 않고
반드시 사용자에게 최종 승인을 요청한다.

---

#### delivery_status = in_transit

```text
cancel_judgment = not_cancelable
reason = in_transit
```

배송이 시작된 주문은 취소할 수 없다.

고객 안내:

```text
현재 배송 중인 주문은 취소가 어렵습니다.
상품을 수령하신 후 취소를 원하시는 경우에는
교환/환불 카테고리로 문의해 주세요.
```

현재 MVP에서는 교환/환불 Flow로 자동 Routing하지 않고
카테고리 안내만 제공한다.

향후 교환/환불 기능 구현 후에는
사용자 동의를 받아 `exchange_refund` Flow로 연결할 수 있다.

---

#### delivery_status = delivered

```text
cancel_judgment = not_cancelable
reason = delivered
```

배송이 완료된 주문은 주문 취소로 처리하지 않는다.

고객 안내:

```text
배송이 이미 완료되어 현재 주문 취소는 어렵습니다.
배송 완료된 주문에 대해 취소를 원하시는 경우에는
교환/환불 카테고리로 문의해 주세요.
```

현재 MVP에서는 교환/환불 Flow로 자동 Routing하지 않는다.

향후에는 다음과 같이 확장할 수 있다.

```text
"교환 또는 환불 절차를 확인해드릴까요?"
↓
사용자 동의
↓
exchange_refund Flow
```

---

## 4. 이미 취소된 주문

### 사용자가 이미 취소된 주문을 다시 취소하려는 경우

```text
order_status = order_canceled
cancel_judgment = already_canceled
```

Cancel Action을 다시 호출하지 않는다.

고객 안내:

```text
이미 정상적으로 주문이 취소되었습니다.
```

---

### 사용자가 취소된 주문을 다시 복구하려는 경우

예:

```text
"취소한 주문 다시 살려줘."
"아까 취소한 주문 다시 주문된 것으로 해줘."
```

이미 취소된 주문을 `order_completed` 상태로 되돌리지 않는다.

고객 안내:

```text
현재 주문이 정상적으로 취소되었습니다.
상품 구매를 원하신다면, 다시 구매해주시면 감사드립니다.
```

---

## 5. 주문 실패 상태

```text
order_status = order_failed
cancel_judgment = not_cancelable
reason = order_failed
```

정상적으로 완료되지 않은 주문이므로
Cancel Action을 호출하지 않는다.

---

## 6. 사용자 최종 승인

```text
cancel_judgment = cancelable
```

이라고 판단되더라도 주문을 즉시 취소하지 않는다.

Orchestrator는 사용자에게 최종 확인을 요청한다.

예:

```text
10002번 주문을 취소하시겠어요?
```

### 사용자 승인

명확한 승인 의사가 확인된 경우에만 Cancel Action을 호출한다.

```text
YES
→ Cancel Action 실행
```

### 사용자 거절

```text
NO
→ Cancel Action 실행하지 않음
→ State 초기화
```

LLM의 추측만으로 주문 취소 Action을 실행하지 않는다.

---

## 7. 주문 취소 Action

사용자의 최종 승인이 확인되면 주문 취소를 실행한다.

주문 취소 성공 시:

```text
order_status
order_completed
→ order_canceled
```

주문 취소와 함께 해당 주문의 결제도 취소 처리한다.

```text
payment_status
payment_completed
→ payment_canceled
```

주문만 취소하고 결제를 완료 상태로 남겨두지 않는다.

---

## 8. 카드 결제 취소

```text
payment_method = card
```

인 경우:

```text
order_status = order_canceled
payment_status = payment_canceled
refund_status = refund_processing
```

으로 처리한다.

고객 안내:

```text
주문이 정상적으로 취소되었습니다.
카드 결제 취소는 카드사를 통해 처리되며,
환불 완료까지 영업일 기준 7일 정도 소요될 수 있습니다.
```

환불 완료가 실제로 확인된 경우에만:

```text
refund_status = refund_completed
```

로 변경한다.

---

## 9. 계좌이체 결제 취소

```text
payment_method = cash
```

인 경우 주문과 결제를 먼저 취소한다.

```text
order_status = order_canceled
payment_status = payment_canceled
refund_status = refund_account_required
```

이후 환불을 위해 사용자에게 환불계좌 정보를 요청한다.

고객 안내:

```text
주문이 정상적으로 취소되었습니다.
환불을 위해 환불받으실 계좌 정보를 입력해 주세요.
```

필요한 환불계좌 정보:

```text
bank_name
account_number
account_holder
```

예:

```text
bank_name = 국민은행
account_number = 1234567890
account_holder = 홍길동
```

계좌 정보가 모두 확인되면:

```text
refund_status
refund_account_required
→ refund_processing
```

으로 변경한다.

고객 안내:

```text
환불계좌가 정상적으로 등록되었습니다.
계좌이체 환불은 영업일 기준 3~5일 정도 소요될 수 있습니다.
```

실제 환불 완료가 확인된 경우에만:

```text
refund_status = refund_completed
```

로 변경한다.

---

## 10. Action 실패

취소 Action이 실패한 경우
주문 취소가 완료되었다고 안내하지 않는다.

예:

```text
result_type = action_failed
```

이 경우 성공 응답을 생성하지 않고
추가 확인이 필요한 상태로 처리한다.

---

## 11. 처리 원칙

### 원칙 1

주문 취소 가능 여부는 LLM이 아니라
Python Business Rule에서 판단한다.

### 원칙 2

배송준비중인 주문만 취소할 수 있다.

### 원칙 3

취소 가능한 주문도 사용자의 최종 승인 없이
Action을 실행하지 않는다.

### 원칙 4

주문 취소 성공 시 결제도 함께 취소 처리한다.

### 원칙 5

결제 취소와 실제 환불 완료를 별도의 상태로 관리한다.

```text
payment_status
→ 결제 상태

refund_status
→ 실제 금액 반환 상태
```

### 원칙 6

배송중 또는 배송완료 주문은 주문 취소로 처리하지 않고
교환/환불 카테고리 이용을 안내한다.

### 원칙 7

현재 구현되지 않은 교환/환불 기능으로
자동 Routing하지 않는다.