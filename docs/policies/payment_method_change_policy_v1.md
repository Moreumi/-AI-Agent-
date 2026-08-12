# Payment Method Change Policy v1

## 1. 목적

결제가 완료된 주문에 대해
고객이 결제수단 변경을 요청했을 때 적용하는 정책을 정의한다.

현재 서비스에서는 결제가 완료된 주문의
결제수단을 직접 변경하는 기능을 제공하지 않는다.

다른 결제수단을 이용하려는 경우에는
기존 주문을 취소한 뒤
원하는 결제수단으로 다시 주문해야 한다.

---

## 2. 기본 정책

결제가 완료된 주문의 결제수단은
직접 변경할 수 없다.

```text
결제 완료된 주문
+
결제수단 변경 요청

→ not_changeable
```

Policy 결과는 다음과 같다.

```text
payment_method_change_judgment
→ not_changeable

recommended_action
→ cancel_and_reorder
```

---

## 3. 고객 안내 원칙

결제수단 변경이 불가능한 경우
고객에게 다음 내용을 안내한다.

```text
결제가 완료된 주문은
결제수단을 직접 변경할 수 없음

↓

다른 결제수단을 이용하려면
기존 주문을 취소한 후 다시 주문해야 함
```

예시:

```text
결제가 완료된 주문은 결제수단을 직접 변경할 수 없습니다.

다른 결제수단을 이용하시려면
기존 주문을 취소한 후
원하시는 결제수단으로 다시 주문해 주세요.
```

---

## 4. 주문 취소 Flow와의 책임 분리

결제수단 변경 문의에서는
주문 취소를 자동으로 실행하지 않는다.

다음 두 기능은 서로 독립적인 Flow로 처리한다.

```text
payment_method_change

책임:
결제수단 변경 가능 여부 및 대안 안내
```

```text
order_cancel

책임:
실제 주문 취소 가능 여부 판단
→ 사용자 승인
→ 주문 취소 Action
```

따라서 다음과 같은 처리는 하지 않는다.

```text
결제수단 변경 문의
→ 자동으로 주문 취소 Flow 실행
```

대신 다음과 같이 처리한다.

```text
Customer
"결제수단을 변경하고 싶어."

↓

payment_method_change

↓

결제수단 직접 변경 불가 안내
+
취소 후 재주문 안내

↓

Flow 종료
```

이후 고객이 별도로 주문 취소를 요청하면
새로운 사용자 요청으로 처리한다.

```text
Customer
"주문을 취소하고 싶어."

↓

새로운 Intent Classification

↓

order_cancel

↓

기존 주문 취소 Flow 실행
```

---

## 5. State 사용 여부

결제수단 변경 문의에서는
Multi-turn State를 생성하지 않는다.

```text
pending_action
→ 생성하지 않음

candidate_orders
→ 사용하지 않음

selected_order_id
→ 사용하지 않음

pending_data
→ 사용하지 않음
```

결제수단 변경 안내가 완료되면
해당 Flow는 즉시 종료한다.

이를 통해 다음 사용자 입력을
새로운 Intent로 다시 분류할 수 있다.

예:

```text
1턴

Customer
"결제수단 변경하고 싶어."

↓

payment_method_change

↓

안내 후 종료


2턴

Customer
"주문 취소하고 싶어."

↓

새로운 Intent Classification

↓

order_cancel
```

---

## 6. 주문 및 배송 데이터 조회 여부

현재 Policy에서는
개별 주문 데이터나 배송 상태를 조회하지 않는다.

다음 정보는 사용하지 않는다.

```text
order_id
order_status
delivery_status
payment_method
```

결제수단 변경 문의 자체의 목적은

```text
현재 주문의 취소 가능 여부를 판단하는 것
```

이 아니라

```text
결제 완료 후 결제수단을 직접 변경할 수 있는지 안내하는 것
```

이기 때문이다.

실제 주문 취소 가능 여부가 필요한 경우에는
별도의 `order_cancel` Flow에서 판단한다.

---

## 7. Write Action 사용 여부

결제수단 변경 기능에서는
실제 데이터를 변경하는 Write Action을 실행하지 않는다.

다음과 같은 작업을 수행하지 않는다.

```text
결제수단 변경
주문 취소
결제 취소
환불 처리
```

따라서 사용자 최종 승인 단계도 필요하지 않다.

```text
Policy
→ Guidance Response
→ Flow 종료
```

로 처리한다.

---

## 8. 전체 처리 Flow

```text
사용자 결제수단 변경 문의
↓
Intent Classification
↓
intent = cs
cs_category = order_payment
sub_intent = payment_method_change
↓
Orchestrator Routing
↓
Payment Method Change Policy
↓
payment_method_change_judgment
= not_changeable
↓
recommended_action
= cancel_and_reorder
↓
고객 안내
↓
State 생성 없이 Flow 종료
```

---

## 9. 주문 취소 요청이 이어지는 경우

결제수단 변경 안내 이후
고객이 별도로 주문 취소를 요청하면
기존 `order_cancel` Flow를 그대로 재사용한다.

```text
Customer
"결제수단 변경하고 싶어."

↓

payment_method_change

↓

"결제수단은 직접 변경할 수 없습니다.
기존 주문을 취소한 후 다시 주문해 주세요."

↓

Flow 종료


Customer
"주문을 취소하고 싶어."

↓

Intent Classification

↓

order_cancel

↓

주문 특정
↓

Order Cancel Policy
↓

사용자 최종 승인
↓

Order Cancel Action
```

`payment_method_change`와 `order_cancel`을
코드에서 직접 연결하지 않는다.

사용자의 새로운 요청을 기준으로
기존 Intent Routing 구조를 통해
적절한 Flow로 진입하도록 한다.

---

## 10. 설계 원칙

이 기능에서는 필요한 처리만 수행한다.

```text
필요

Intent Classification
Policy
Routing
Response
```

```text
불필요

주문 조회
배송 상태 조회
State
pending_data
사용자 승인
Write Action
주문 취소 자동 실행
```

모든 CS 기능에 동일한 복잡도의 Agent Flow를 적용하지 않고,
실제 Business Rule과 기능의 성격에 따라
필요한 Component만 사용한다.