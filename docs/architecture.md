# Chatbot Architecture

## 1. 목적

이 문서는 온라인 쇼핑몰 AI Agent의 현재 처리 구조와
각 Component의 책임을 정의한다.

사용자 질문이 입력된 이후
질문을 이해하고 필요한 기능을 선택한 뒤,
데이터 조회와 정책 판단을 거쳐 최종 응답을 생성하기까지의
전체 흐름을 관리하는 것을 목표로 한다.

---

## 2. 전체 처리 흐름

현재 CS Agent는 모든 요청을 동일한 순서로 처리하는
단순 Chain이나 모든 기능을 동시에 실행하는 병렬 구조가 아니라,
**앞 단계의 결과에 따라 다음 Component를 선택하는 조건 분기형 순차 Orchestration**으로 구성한다.

사용자의 질문 종류뿐 아니라
주문 조회 결과, Policy 판단 결과, 사용자 승인 여부,
수량 계산 결과, 결제수단 등에 따라 다음에 필요한 작업이 달라지기 때문이다.

또한 대부분의 후속 작업은 이전 단계의 결과가 확정되어야 실행할 수 있으므로,
현재 핵심 Flow는 병렬 실행보다 순차적인 조건 분기가 적합하다.

현재 구현된 CS Flow는 기능의 성격에 따라
Read Flow, Guidance Flow, Read + Policy Flow, Write Flow로 구분된다.

```text
User
↓
FastAPI Router
↓
Orchestrator
↓
Pending State 확인
│
├─ 진행 중인 State 존재
│   → 기존 Multi-turn Flow 계속 처리
│
└─ 진행 중인 State 없음
    ↓
    Intent Classification
    ↓
    Routing
    │
    ├─ Read Flow
    │   │
    │   ├─ order_confirmation
    │   ├─ payment_confirmation
    │   │   ↓
    │   │   Order / Payment Service
    │   │   ↓
    │   │   Policy Layer
    │   │   ↓
    │   │   Order-Payment Consistency Check
    │   │   ↓
    │   │   Response Generation
    │   │
    │   └─ delivery_status
    │       ↓
    │       Delivery Service
    │       ↓
    │       현재 배송 상태 조회
    │       ↓
    │       Response
    │
    ├─ Guidance Flow
    │   │
    │   ├─ payment_method_change
    │   │   ↓
    │   │   Payment Method Change Policy
    │   │   ↓
    │   │   Guidance Response
    │   │
    │   └─ delivery_eta / general
    │       ↓
    │       Delivery ETA Policy
    │       ↓
    │       일반 배송기간 안내
    │       ↓
    │       State 생성 없이 Flow 종료
    │
    ├─ Read + Policy Flow
    │   │
    │   └─ delivery_eta / order_specific
    │       ↓
    │       주문 조회 / 선택
    │       ↓
    │       Delivery Service
    │       ↓
    │       실제 order_status / delivery_status 조회
    │       ↓
    │       Delivery ETA Policy
    │       ↓
    │       실제 배송 상태 + 일반 배송 기준 조합
    │       ↓
    │       Contextual Response
    │
    └─ Write Flow
        │
        ├─ order_cancel
        │   ↓
        │   주문 조회
        │   ↓
        │   Order Cancel Policy
        │   ↓
        │   사용자 최종 승인
        │   ↓
        │   Write Action
        │   ├─ 주문 취소
        │   └─ 결제 취소
        │       ↓
        │       Refund 처리
        │
        ├─ delivery_address_change
        │   ↓
        │   주문 조회
        │   ↓
        │   Delivery Address Change Policy
        │   ↓
        │   새 배송지 수집
        │   ↓
        │   State 임시 저장
        │   ↓
        │   사용자 최종 승인
        │   ↓
        │   Action 직전 상태 재검증
        │   ↓
        │   Delivery Address Change Action
        │   ↓
        │   Final Response
        │
        └─ order_change
            ↓
            주문 / 결제 조회
            ↓
            Order Change Policy
            ↓
            변경 가능 여부 판단
            ↓
            현재 수량 기준 목표 수량 계산
            ↓
            주문금액 / 결제 차액 계산
            ↓
            변경 Preview
            ↓
            사용자 최종 승인
            ↓
            Action 직전 주문 / 배송 / 결제 상태 재검증
            ↓
            Order Change Action
            ├─ quantity 변경
            └─ total_price 변경
                ↓
            Payment Adjustment 생성
            ↓
            차액 유형에 따른 후속 Flow 분기
            │
            ├─ additional_payment_required
            │   ↓
            │   추가 결제 필요 상태 유지
            │
            └─ partial_refund_required
                ↓
                Refund Service
                ↓
                결제수단 확인
                │
                ├─ 카드
                │   ↓
                │   Refund 데이터 생성
                │   ↓
                │   refund_processing
                │
                └─ 계좌이체
                    ↓
                    Refund 데이터 생성
                    ↓
                    refund_account_required
                    ↓
                    Pending State 저장
                    ↓
                    환불계좌 입력
                    ↓
                    refund_processing
            ↓
            Final Response
```

---

## 3. Component 역할

### FastAPI Router

사용자의 HTTP 요청을 받아
Agent 처리 흐름으로 전달한다.

Router는 비즈니스 판단을 담당하지 않고,
외부 요청과 내부 Agent Logic을 연결하는 역할만 담당한다.

---

### Intent Classification

사용자의 질문을 분석하여
어떤 기능으로 처리해야 하는지 판단한다.

현재 주요 CS Intent 중 구현된 기능은 다음과 같다.

```text
order_confirmation
payment_confirmation
payment_method_change
order_cancel
order_change
delivery_address_change
delivery_status
delivery_eta
```

`delivery_eta`는 동일한 배송 예상 시기 문의라도
필요한 정보의 범위에 따라 `delivery_eta_scope`를 함께 반환한다.

```text
general
→ 특정 주문과 무관한 일반 배송기간 문의

order_specific
→ 사용자의 실제 주문 또는 특정 주문의 도착 시기 문의
```

예를 들어:

```text
"배송은 보통 얼마나 걸려?"
→ sub_intent = delivery_eta
→ delivery_eta_scope = general

"내 주문 언제 와?"
→ sub_intent = delivery_eta
→ delivery_eta_scope = order_specific
```

따라서 Intent Classification은 단순히 기능 종류만 분류하는 것이 아니라,
해당 기능에서 어떤 처리 경로가 필요한지도
Structured Output으로 Orchestrator에 전달한다.

분류 결과는 Orchestrator가 다음 처리 경로를 결정하는 데 사용한다.

`order_change`는 사용자의 수량 변경 표현을
추가 Structured Output으로 반환한다.

```text
quantity_change_type
→ set
→ increase
→ decrease

quantity_value
→ 사용자가 말한 수량 또는 증감 수량
```

예:

```text
"3개로 바꿔줘"
→ quantity_change_type = set
→ quantity_value = 3

"2개 더 추가해줘"
→ quantity_change_type = increase
→ quantity_value = 2

"1개 줄여줘"
→ quantity_change_type = decrease
→ quantity_value = 1
```

LLM은 사용자가 말한 변경 표현만 구조화하며,
실제 현재 주문 수량을 조회하거나 `target_quantity`를 계산하지 않는다.

최종 목표 수량은 Service에서 실제 주문 데이터를 조회한 이후
Python Business Logic으로 계산한다.

---

### Orchestrator

전체 Agent Flow의 중심 Component이다.

현재 구조에서 Orchestrator는
각 Component를 직접 대체하는 것이 아니라,
**현재 사용자 요청과 처리 결과를 기준으로
어떤 Component를 어떤 순서로 호출할지 결정한다.**

주요 역할은 다음과 같다.

- Pending State 우선 확인
- Intent 결과에 따른 Routing
- 필요한 정보가 충분한지 확인
- Service 호출
- Policy 결과 확인
- Consistency 결과 확인
- Response Mode 결정
- 최종 응답 생성 Component 호출
- Write Action 실행 전 사용자 최종 승인 확인
- 진행 중인 Action에 따라 Multi-turn State 계속 처리
- 주문 취소 이후 결제 방식에 따른 Refund 처리 분기
- 배송지 변경 과정에서 주문 선택, 새 주소 수집, 최종 승인 흐름 제어
- 결제수단 변경과 같은 Policy 안내형 CS의 Guidance Flow Routing
- 배송 상태 확인 과정에서 주문 조회, 다중 주문 선택 및 Read Flow 종료 제어
- `delivery_eta_scope`에 따라 일반 Policy 안내와 특정 주문 기반 Read + Policy Flow 분기
- 주문 수량 변경 과정에서 주문 선택, 수량 추가 입력, Preview, 최종 승인 흐름 제어
- 주문 수량 변경 승인 이후 Action-time Recheck 및 Payment Adjustment 생성 흐름 연결
- 수량 감소 시 `partial_refund_required` 결과를 Refund Service에 연결
- 카드와 계좌이체 결제수단에 따라 부분 환불 후속 Flow 분기
- 계좌이체 부분 환불 시 환불계좌 입력을 위한 Pending State 생성 및 후속 처리

즉 개별 기능을 직접 수행하기보다
**각 Component의 실행 순서와 조건 분기를 제어하는 역할**을 담당한다.

#### 분기 구조를 사용하는 이유

현재 CS Flow에서는 동일한 사용자 요청이라도
중간 처리 결과에 따라 다음 행동이 달라질 수 있다.

예를 들어 주문 수량 변경의 경우:

```text
목표 수량 > 현재 수량
→ 추가 결제 필요

목표 수량 < 현재 수량
→ 부분 환불 필요

목표 수량 = 현재 수량
→ 변경 없음

목표 수량 = 0
→ 주문 취소 안내

목표 수량 < 0
→ 잘못된 수량
```

수량 감소가 확인된 이후에도 결제수단에 따라 다시 분기된다.

```text
부분 환불 필요
↓
카드
→ 바로 refund_processing

계좌이체
→ 환불계좌 추가 입력 필요
→ Pending State
→ 다음 사용자 입력 후 refund_processing
```

따라서 모든 Component를 동일한 순서로 실행하지 않고,
앞 단계의 결과를 기준으로 필요한 기능만 선택적으로 호출한다.

---

### State

멀티턴 대화에서 이전 처리 상태와
다음 사용자 입력까지 유지해야 하는 임시 정보를 관리한다.

예를 들어 고객에게 여러 주문이 존재하는 경우
Agent가 임의로 주문을 선택하지 않고 추가 질문을 한다.

```text
사용자
"내 주문 제대로 들어갔어?"

↓

여러 주문 존재

↓

State 저장
- 현재 처리 중인 기능
- 선택 가능한 주문 목록

↓

Agent
"확인할 주문번호를 선택해주세요."

↓

사용자
"10002번"

↓

기존 State를 확인하여
order_confirmation Flow 계속 처리
```

주문 취소 Flow에서는
Action 실행 전 사용자 승인을 기다리거나,
계좌이체 환불을 위한 추가 정보를 수집하는 데 State를 사용한다.

배송지 변경 Flow에서는
선택한 주문번호와 사용자가 입력한 새 배송지를 저장한 뒤
사용자의 최종 승인을 기다리는 데 State를 사용한다.

현재 주요 State 값은 다음과 같다.

```text
pending_action
→ 현재 이어서 처리해야 할 작업

candidate_orders
→ 사용자가 선택할 수 있는 주문 목록

selected_order_id
→ 현재 처리 중인 주문번호

pending_data
→ 다음 턴까지 유지해야 하는 기능별 임시 데이터
```

배송지 변경의 예:

```python
state = {
    "pending_action": "confirm_delivery_address_change",
    "candidate_orders": [],
    "selected_order_id": 10001,
    "pending_data": {
        "new_delivery_address": "서울시 강남구 테헤란로 123"
    },
}
```

`pending_data`는 배송지 변경 전용 필드가 아니라,
다른 Multi-turn Write Flow에서도
임시 데이터를 저장하기 위한 공통 Interface로 사용한다.

#### 주문 수량 변경 State

주문 수량 변경 Flow에서도 `pending_data`를 사용한다.

이 기능에서는 처리 단계에 따라
저장해야 하는 임시 정보가 달라진다.

고객에게 여러 주문이 존재하여
먼저 주문을 선택해야 하는 경우에는
첫 번째 사용자 요청에서 추출한 수량 변경 정보를 저장한다.

```python
state = {
    "pending_action": "order_change_selection",
    "candidate_orders": [...],
    "selected_order_id": None,
    "pending_data": {
        "quantity_change_type": "increase",
        "quantity_value": 1,
    },
}
```

예를 들어 사용자가

```text
"주문 수량 1개 더 추가해줘"
```

라고 요청했지만 여러 주문이 존재하는 경우,
Agent는 먼저 주문번호를 추가로 확인한다.

사용자가 다음 턴에 주문번호만 입력하더라도
`pending_data`에 저장된 `increase / 1` 정보를 복구하여
선택한 주문의 실제 현재 수량을 기준으로
목표 수량을 계산할 수 있다.

수량과 금액 계산이 완료된 뒤에는
사용자의 최종 승인을 기다리기 위해
다른 형태의 임시 정보를 저장한다.

```python
state = {
    "pending_action": "order_change_confirmation",
    "candidate_orders": [],
    "selected_order_id": 10007,
    "pending_data": {
        "target_quantity": 2,
        "current_quantity": 3,
        "current_total_price": 60000,
        "new_total_price": 40000,
        "adjustment_type": "partial_refund_required",
        "adjustment_amount": 20000,
    },
}
```

이 State를 통해 다음 사용자 입력인

```text
"예"
"아니오"
```

를 새로운 Intent로 다시 분류하지 않고
기존 `order_change` Flow의 최종 승인 입력으로 처리한다.

단, State에 저장된 Preview 값은
실제 Action 실행 시점의 현재 데이터와 동일하다고 보장할 수 없다.

따라서 최종 승인이 들어오면
State의 이전 판단만 신뢰하지 않고
현재 주문 상태, 배송 상태, 결제 상태를 다시 확인한 뒤
조건이 유지되는 경우에만 Write Action을 실행한다.

```text
State에 저장된 Preview
≠
Action 실행 시점의 현재 데이터
```

#### 부분 환불 계좌 입력 State

수량 감소로 부분 환불이 발생하고
결제수단이 계좌이체인 경우에는
환불 처리를 위해 추가적인 사용자 정보가 필요하다.

이때 Order Change Flow를 종료하지 않고
다음 사용자 입력까지 Refund 정보를 State에 저장한다.

```python
state = {
    "pending_action": "collect_partial_refund_account",
    "candidate_orders": [],
    "selected_order_id": 10007,
    "pending_data": {
        "refund_id": 70001,
        "refund_amount": 20000,
        "refund_type": "partial",
        "source": "order_change",
    },
}
```

다음 사용자 입력:

```text
"국민은행 / 1234567890 / 홍길동"
```

을 새로운 Intent로 분류하지 않고
현재 진행 중인 부분 환불 Flow의 계좌정보로 처리한다.

```text
Pending State 확인
↓
collect_partial_refund_account
↓
refund_id 확인
↓
계좌정보 추출
↓
Refund Service
↓
해당 Refund 데이터에 계좌정보 저장
↓
refund_processing
↓
State 초기화
```

부분 환불 State에서는 `order_id`만으로 환불 데이터를 찾지 않고
`refund_id`를 저장하여 처리한다.

하나의 주문에서 향후 여러 환불 기록이 생성될 수 있으므로,
현재 진행 중인 환불 건을 명확히 식별하기 위해서이다.

현재 MVP에서는 Python Dictionary 기반 State를 사용한다.

State는 서버 메모리에 저장되므로
서버가 재시작되면 진행 중인 State가 초기화된다.

향후 실제 서비스에서는
사용자 또는 Session 단위의 State 관리와
영속 저장 방식이 필요하다.

#### 배송 상태 확인 State

배송 상태 확인 Flow에서도 고객에게 주문이 여러 건 존재하면
`pending_action`과 `candidate_orders`를 사용하여
배송 상태를 확인할 주문번호를 추가로 입력받는다.

배송 상태 확인은 Read Flow이므로
주문번호가 선택되면 즉시 조회를 수행하고 Flow가 종료된다.

따라서 주문 취소나 배송지 변경과 달리
선택된 주문번호를 이후 단계까지 유지하기 위한
`selected_order_id`나 추가 정보를 위한 `pending_data`는 사용하지 않는다.

#### 배송 예상 시기 State

배송 예상 시기 문의에서도 `order_specific` 질문에 대해
고객의 주문이 여러 건 존재하면 State를 사용한다.

```text
pending_action = delivery_eta_selection
candidate_orders = 사용자가 선택할 수 있는 주문 목록
```

예:

```text
사용자
"내 주문 언제 와?"

↓
여러 주문 존재

↓
delivery_eta_selection State 저장

↓
Agent
"배송 예정 시기를 확인할 주문을 선택해 주세요."

↓
사용자
"10002번"

↓
Pending State 우선 처리

↓
선택한 주문의 Delivery Status 조회

↓
Delivery ETA Policy 적용

↓
응답 후 State 초기화
```

두 번째 사용자 입력은 새로운 Intent로 다시 분류하지 않고,
기존 `delivery_eta` Flow의 후속 입력으로 처리한다.

---

### Service / Data

고객의 주문·결제·환불 데이터를 조회하고,
Policy 판단에 필요한 결과를 반환한다.

또한 Orchestrator에서 확정된 Write Action 요청이 전달되면
실제 데이터 상태 변경을 수행한다.

주요 조회 데이터 예시는 다음과 같다.

```text
Order
- order_id
- order_status
- order_date
- quantity
- unit_price
- total_price
- delivery_status
- delivery_address

Payment
- payment_id
- payment_status
- payment_method
- payment_amount
- payment_date

Refund
- refund_id
- payment_id
- order_id
- refund_type
- refund_amount
- refund_reason
- refund_status
- adjustment_id
- bank_name
- account_number
- account_holder

Payment Adjustment
- adjustment_id
- order_id
- payment_id
- adjustment_type
- adjustment_amount
- adjustment_status
```

현재 주요 Write Action은 다음과 같다.

```text
cancel_order()
→ 주문 상태 변경
→ 결제 상태 변경
→ 주문 취소에 따른 환불 상태 생성

change_delivery_address()
→ Action 직전 주문 / 배송 상태 재검증
→ 주문의 delivery_address 변경

change_order_quantity()
→ Action 직전 주문 / 배송 / 결제 상태 재검증
→ 주문 quantity 변경
→ 주문 total_price 변경
→ payment_amount는 기존 실제 결제금액으로 유지
→ Payment Adjustment를 pending 상태로 생성
```

#### Refund Service

주문 수량 감소로 발생한 부분 환불은
Order Change Service 내부에서 직접 처리하지 않고
별도의 Refund Service로 분리한다.

Orchestrator는 `change_order_quantity()`의 결과가
`partial_refund_required`인 경우에만 Refund Service를 호출한다.

```text
Order Change Service
↓
partial_refund_required
↓
Orchestrator
↓
Refund Service
```

주요 기능은 다음과 같다.

```text
start_refund()

입력
→ payments
→ refunds
→ order_id
→ refund_amount
→ refund_type
→ refund_reason
→ adjustment_id(optional)

처리
→ 주문에 연결된 결제정보 확인
→ 환불금액 검증
→ 결제수단 확인
→ Refund 데이터 생성

카드
→ refund_processing

계좌이체
→ refund_account_required
```

계좌이체 부분 환불의 후속 처리에서는
환불 건의 `refund_id`를 기준으로 계좌정보를 등록한다.

```text
register_refund_account()

입력
→ refunds
→ refund_id
→ bank_name
→ account_number
→ account_holder

처리
→ 해당 Refund 데이터 조회
→ refund_account_required 상태 확인
→ 계좌정보 저장
→ refund_processing으로 변경
```

현재 외부 PG(Payment Gateway) 환불 API는 연결되어 있지 않다.

따라서 Refund Service가 환불 절차를 시작하더라도
실제 환불 완료를 의미하는 `refund_completed`로 변경하지 않고
현재 MVP에서 보장할 수 있는 `refund_processing` 상태까지만 관리한다.

현재 주문 취소 Flow는 기존 Order / Payment Service 내부의
환불 처리 구조를 유지하고 있으며,
이번에 분리한 Refund Service는 우선
주문 수량 감소에 따른 부분 환불 Flow에 연결되어 있다.

향후 환불 처리 Interface가 안정화되면
주문 취소 및 직접 환불 요청도 동일한 Refund Service로
통합할 수 있다.

#### 주문금액과 결제금액

주문 수량 변경에서는
주문금액과 실제 결제금액을 동일한 값으로 강제로 맞추지 않는다.

```text
orders.total_price
→ 현재 변경된 주문의 금액

payments.payment_amount
→ 실제로 이미 결제된 금액

payment_adjustments
→ 추가 결제 또는 부분 환불이 필요한 결제 차액

refunds
→ 실제 환불 절차의 진행 상태
```

예를 들어 3개, 60,000원의 주문을
2개, 40,000원으로 변경하면:

```text
orders.total_price
60,000 → 40,000

payments.payment_amount
60,000 유지

payment_adjustments
20,000
partial_refund_required
pending

refunds
20,000
partial
refund_processing
```

실제 PG 결제·환불을 수행하지 않은 상태에서
`payment_amount`를 임의로 수정하면
실제 결제 또는 환불이 완료된 것처럼 표현될 수 있다.

따라서 주문 데이터,
실제 결제 데이터,
처리해야 할 결제 차액,
환불 진행 상태를 각각 분리하여 관리한다.

Service는 데이터를 조회하여
Policy 판단에 필요한 결과를 반환하고,
확정된 Action 요청이 전달되면 데이터 상태 변경을 수행한다.

Write Action은 Orchestrator가
필요한 조건과 사용자의 명확한 승인을 확인한 이후에만 호출한다.

#### Delivery Service

배송 상태 확인 기능에서는 별도의 `Delivery Service`를 사용한다.

```text
check_delivery_status()

입력
→ orders
→ customer_id
→ order_id(optional)

처리
→ 고객 주문 조회
→ 주문 식별
→ 다중 주문 여부 확인
→ 현재 order_status / delivery_status 조회

출력
→ success
→ not_found
→ need_order_selection
```

`check_delivery_status()`는 `delivery_status` 전용으로 중복 구현하지 않고,
특정 주문의 배송 예상 시기를 안내하는 `delivery_eta / order_specific`
Flow에서도 재사용한다.

```text
delivery_status
→ Delivery Service
→ 현재 배송 상태 자체를 안내

delivery_eta / order_specific
→ Delivery Service
→ 실제 배송 상태 조회
→ Delivery ETA Policy
→ 현재 상태를 고려한 배송 예상 안내
```

동일한 주문 식별 및 배송 상태 조회 책임을
여러 기능에서 공유하고,
각 기능에서 필요한 이후 판단만 분리한다.

---

### Policy Layer

Service에서 조회된 데이터 또는 서비스의 Business Rule을 기준으로
각 기능에서 필요한 업무적 판단을 수행한다.

Policy는 고객에게 보여줄 문장을 직접 결정하는 것이 아니라,
Orchestrator가 다음 처리 단계를 선택할 수 있도록
명시적인 판단 결과를 반환한다.

현재 구현된 주요 Policy는 다음과 같다.

```text
Order Completion Policy
→ 주문 완료 여부 판단

Payment Completion Policy
→ 결제 완료 여부 판단

Order-Payment Consistency Policy
→ 주문 상태와 결제 상태의 일관성 검증

Order Cancel Policy
→ 주문 취소 가능 여부 판단

Order Change Policy
→ 주문 상태, 배송 상태, 결제 상태를 기준으로 수량 변경 가능 여부 판단

Delivery Address Change Policy
→ 배송지 변경 가능 여부 판단

Payment Method Change Policy
→ 결제 완료 후 결제수단 변경 가능 여부 및 대안 판단

Delivery ETA Policy
→ 일반 배송기간 기준 제공 및 실제 주문 상태에 따른 배송 예상 안내 가능 여부 판단
```

Order Change Policy에서는
다음 조건을 모두 만족하면
주문 수량을 변경할 수 있는 상태로 판단한다.

```text
order_status = order_completed
delivery_status = preparing_shipment
payment_status = payment_completed

→ changeable
```

반대로 배송이 이미 시작되었거나,
주문 또는 결제 상태가 정상적이지 않으면
수량 변경 Write Flow로 진행하지 않는다.

---

#### Action 가능 여부를 판단하는 Policy

주문 취소, 배송지 변경, 주문 수량 변경처럼
실제 데이터를 변경할 가능성이 있는 기능에서는
Policy가 **Action을 실행할 수 있는 상태인지** 먼저 판단한다.

예를 들어 배송지 변경의 경우:

```text
order_completed
+
preparing_shipment

→ changeable
```

이라고 판단할 수 있다.

하지만 Policy는 실제 Write Action을 수행하지 않는다.

```text
Policy 판단
→ changeable

≠

실제 데이터 변경
```

`changeable`은 현재 상태에서 해당 Action이 가능하다는
Business 판단 결과일 뿐이다.

실제 Write Action은 이후 Orchestrator에서

```text
사용자 최종 승인
→ Action 직전 상태 재검증
→ Write Action
```

과정을 거친 뒤 실행한다.

따라서 다음 세 단계는 서로 분리한다.

```text
Policy 판단
≠
사용자 승인
≠
Write Action
```

---

#### 안내 자체가 결과가 되는 Guidance Policy

모든 Policy가 Write Action이나
실제 데이터 조회로 이어지는 것은 아니다.

`Payment Method Change Policy`처럼
서비스의 Business Rule 자체를 안내하는 기능도 있다.

현재 결제수단 변경 정책은 다음과 같다.

```text
결제가 완료된 주문
+
결제수단 변경 요청

→ 직접 변경 불가
→ 기존 주문 취소 후 재주문 안내
```

이 경우 Policy 판단 이후
추가적인 Write Action이 필요하지 않다.

```text
Payment Method Change Policy
↓
not_changeable
+
cancel_and_reorder
↓
Guidance Response
↓
Flow 종료
```

따라서 `payment_method_change`에서는 다음 Component를 사용하지 않는다.

```text
주문 조회
State 저장
사용자 최종 승인
Write Action
```

필요하지 않은 Component를 추가하지 않고
Policy 결과를 고객 안내로 연결한 뒤 Flow를 종료한다.

---

### Order-Payment Consistency Policy

주문 상태와 결제 상태를 함께 확인하여
두 상태가 서로 모순되지 않는지 검증한다.

예:

```text
order_completed
+
payment_completed

→ consistent_completed
```

반면,

```text
order_completed
+
payment_failed

→ needs_review
```

처럼 관련 데이터가 서로 일치하지 않는 경우
정상 완료 응답을 바로 생성하지 않는다.

---

### Response Mode Selection

Orchestrator는 최종 결과의 성격에 따라
응답 방식을 선택한다.

#### fact_summary

객관적인 조회 결과를 전달할 때 사용한다.

예:

- 주문 완료 확인
- 결제 완료 확인

```text
핵심 결과

- 상태
- 날짜
- 금액

고객 응대 마무리
```

#### narrative_guidance

추가 설명이나 안내가 필요한 경우 사용한다.

예:

- 주문/결제 상태 불일치
- Policy 설명
- 예외 상황

```text
핵심 결과
→ 상황 설명
→ 필요한 후속 행동
```

---

### Output Prompt + LLM

앞 단계에서 이미 확정된 사실과 Policy를
고객이 이해하기 쉬운 자연어 응답으로 변환한다.

LLM은 다음 사항을 새롭게 판단하지 않는다.

- 주문 완료 여부
- 결제 완료 여부
- 주문 취소 가능 여부
- 주문 수량 변경 가능 여부
- 배송지 변경 가능 여부
- 쇼핑몰 정책
- 데이터 불일치 해결 방법
- Write Action 실행 여부
- 환불 가능 여부 또는 환불 완료 여부

즉 현재 구조에서 LLM은

```text
판단
```

보다

```text
표현
```

을 담당한다.

일부 Multi-turn 확인 응답과
Write Action 및 Refund Flow 관련 고정 응답은
현재 Python 코드에서 직접 생성하고 있다.

#### 조회 결과와 Policy를 함께 사용하는 Flow

모든 기능이 순수 Read, Guidance, Write 중 하나로만 처리되는 것은 아니다.

`delivery_eta / order_specific`에서는
실제 주문의 현재 상태와 쇼핑몰의 일반 배송 기준이 모두 필요하다.

```text
Delivery Service
→ order_status / delivery_status

+

Delivery ETA Policy
→ 일반 배송 소요 기준

↓

현재 주문 상황을 반영한 배송 예상 안내
```

예를 들어:

```text
delivery_status = preparing_shipment
→ 현재 배송 준비 중이라는 실제 사실

+

배송 시작 후 일반 지역 3~5 영업일이라는 Policy

↓

배송 시작 이후의 일반적인 소요기간 안내
```

반면:

```text
delivery_status = delivered
→ 이미 배송 완료
→ 배송 예상 기간을 추가로 안내하지 않음
```

현재 MVP에는 실시간 택배사 Tracking 정보나
확정 배송 예정일 데이터가 없기 때문에,
Policy를 이용해 실제 데이터에 존재하지 않는
정확한 도착 날짜를 생성하지 않는다.

---

## 4. Multi-turn Flow

정보가 부족하거나
Write Action 수행을 위해 추가 정보가 필요한 경우
State를 이용해 다음 사용자 입력까지 Flow를 유지한다.

기본 구조는 다음과 같다.

```text
사용자 질문
↓
Pending State 확인
│
├─ 기존 작업 존재
│   → 기존 Flow 계속
│
└─ 기존 작업 없음
    → Intent Classification
    → Orchestrator
    → 필요한 기능 실행
```

Pending State를 Intent Classification보다 먼저 확인하는 이유는
다음 사용자 입력이 새로운 질문이 아니라
이전 작업에 대한 답변일 수 있기 때문이다.

예를 들어:

```text
1턴
"주문 수량 바꾸고 싶어"

↓

Agent
"변경할 수량을 입력해 주세요."

↓

2턴
"2개로"
```

두 번째 `"2개로"`는 독립적인 Intent가 아니므로,
기존 State를 확인한 뒤 `order_change` Flow를 이어서 처리한다.

데이터 조회가 필요한 경우에는
기능의 성격에 따라 필요한 Component만 사용한다.

객관적인 데이터 조회만 필요한 경우:

```text
Service
→ Response
```

예:

```text
delivery_status
→ Delivery Service
→ 현재 배송 상태 조회
→ Response
```

조회된 상태에 대한 Business 판단이 필요한 경우:

```text
Service
→ Policy
→ 필요한 추가 검증
→ Response
```

예:

```text
order_confirmation / payment_confirmation
→ Service
→ Policy
→ Order-Payment Consistency Check
→ Response
```

Policy 안내만 필요한 경우:

```text
Policy
→ Guidance Response
→ Flow 종료
```

정보가 부족한 경우:

```text
State 저장
→ 추가 질문
→ 다음 사용자 입력
→ Pending State 확인
→ 기존 Flow 계속 처리
```

### 배송 상태 확인 Multi-turn

배송 상태 확인의 경우
고객에게 주문이 여러 건 존재하면 다음과 같이 처리한다.

```text
사용자
"내 주문 배송 상태 알려줘"

↓
여러 주문 존재

↓
pending_action = delivery_status_selection
candidate_orders 저장

↓
Agent
"배송 상태를 확인할 주문번호를 선택해 주세요."

↓
사용자
"10002번"

↓
Pending State 확인
↓
선택 가능한 주문번호인지 검증
↓
Delivery Service 호출
↓
현재 delivery_status 조회
↓
Response
↓
State 초기화
```

배송 상태 확인은 Read Flow이므로
주문번호가 선택되면 바로 조회를 수행하고 Flow가 종료된다.

따라서 주문 취소나 배송지 변경처럼
선택된 주문번호를 이후 단계까지 유지하기 위한
`selected_order_id`나 추가 정보를 저장하기 위한
`pending_data`는 사용하지 않는다.

### 배송지 변경 Multi-turn

배송지 변경의 경우에는 다음과 같이 여러 턴을 사용한다.

```text
사용자
"10001번 주문 배송지 바꿔줘"

↓
변경 가능 여부 확인

↓
pending_action = collect_delivery_address

Agent
"변경할 새로운 배송지를 입력해 주세요."

↓
사용자
"서울시 강남구 테헤란로 123"

↓
pending_data에 새 주소 임시 저장
pending_action = confirm_delivery_address_change

↓
Agent
"이 배송지로 변경하시겠어요?"

↓
사용자
"예"

↓
Action 직전 상태 재검증
↓
Write Action 실행
↓
State 초기화
```

### 주문 수량 변경 Multi-turn

주문 수량 변경에서는
주문 선택, 수량 추가 입력, 변경 Preview 및 최종 승인을 위해
여러 단계의 State를 사용할 수 있다.

예:

```text
사용자
"주문 수량 1개 더 추가해줘"

↓
여러 주문 존재

↓
pending_action = order_change_selection
pending_data = increase / 1

↓
사용자
"10007번"

↓
실제 현재 수량 조회
↓
목표 수량 / 주문금액 / 결제 차액 계산
↓
Preview 생성
↓
pending_action = order_change_confirmation

↓
사용자
"예"

↓
Action 직전 상태 재검증
↓
Write Action
↓
Payment Adjustment 생성
↓
결제 차액 유형 확인
```

수량 증가인 경우:

```text
additional_payment_required
↓
추가 결제 필요 상태 기록
↓
State 초기화
```

수량 감소인 경우:

```text
partial_refund_required
↓
Refund Service
↓
결제수단 확인
```

카드 결제:

```text
카드
↓
Refund 데이터 생성
↓
refund_processing
↓
State 초기화
```

계좌이체:

```text
계좌이체
↓
Refund 데이터 생성
↓
refund_account_required
↓
pending_action = collect_partial_refund_account
↓
refund_id / refund_amount 저장

↓

사용자
"국민은행 / 1234567890 / 홍길동"

↓

Pending State 확인
↓
계좌정보 추출
↓
Refund Service
↓
계좌정보 저장
↓
refund_processing
↓
State 초기화
```

이처럼 Multi-turn State는 모든 기능에서 동일하게 사용하는 것이 아니라,
해당 기능이 다음 사용자 입력까지 어떤 정보를 유지해야 하는지에 따라
필요한 State 값만 사용한다.

---

## 5. 현재 구현 범위

현재 End-to-End로 구현된 기능은 다음과 같다.

```text
CS
├─ 주문/결제
│   ├─ 주문 완료 확인
│   │
│   ├─ 결제 완료 확인
│   │
│   ├─ 결제수단 변경
│   │   ├─ Payment Method Change Policy
│   │   ├─ 직접 변경 불가 안내
│   │   ├─ 취소 후 재주문 안내
│   │   └─ State 없이 Flow 종료
│   │
│   ├─ 주문 취소
│   │   ├─ 주문 취소 가능 여부 판단
│   │   ├─ 사용자 최종 승인
│   │   ├─ 주문 / 결제 취소 Action
│   │   └─ 환불 처리
│   │       ├─ 카드
│   │       │   → refund_processing
│   │       └─ 계좌이체
│   │           → 환불계좌 수집
│   │           → refund_processing
│   │
│   ├─ 주문 수량 변경
│   │   ├─ 주문 / 결제 조회
│   │   ├─ 수량 변경 가능 여부 판단
│   │   ├─ 목표 수량 계산
│   │   ├─ 주문금액 / 결제 차액 계산
│   │   ├─ 변경 Preview
│   │   ├─ 사용자 최종 승인
│   │   ├─ Action 직전 상태 재검증
│   │   ├─ 주문 수량 / 주문금액 변경
│   │   ├─ Payment Adjustment 생성
│   │   └─ 결제 차액에 따른 후속 처리
│   │       ├─ 수량 증가
│   │       │   → additional_payment_required
│   │       │   → 추가 결제 대기
│   │       │
│   │       └─ 수량 감소
│   │           → partial_refund_required
│   │           → Refund Service
│   │           ├─ 카드
│   │           │   → refund_processing
│   │           │
│   │           └─ 계좌이체
│   │               → refund_account_required
│   │               → 환불계좌 수집
│   │               → refund_processing
│   │
│   └─ 배송지 변경
│       ├─ 주문 선택
│       ├─ 배송지 변경 가능 여부 판단
│       ├─ 새 배송지 수집
│       ├─ State 임시 저장
│       ├─ 사용자 최종 승인
│       ├─ Action 직전 상태 재검증
│       └─ 배송지 변경 Action
│
└─ 배송
    ├─ 배송 상태 확인
    │   ├─ 주문 조회
    │   ├─ 단일 주문 자동 선택
    │   ├─ 다중 주문 선택
    │   ├─ Multi-turn State 처리
    │   ├─ 현재 배송 상태 조회
    │   └─ Response
    │
    └─ 배송 예상 시기
        ├─ general
        │   → 일반 배송기간 Policy 안내
        │
        └─ order_specific
            → 주문 조회 / 선택
            → 현재 배송 상태 조회
            → Delivery ETA Policy
            → 현재 상태 기반 배송 예상 안내
```

현재 전체 자동 테스트 **140개가 통과한다.**

주문 수량 변경 및 부분 환불 기능은 다음 범위를 테스트했다.

```text
Order Change Policy
수량 계산
Routing
State
Preview
사용자 승인
Write Action
Action-time Recheck
Payment Adjustment
Refund Service
카드 부분 환불
계좌이체 부분 환불
환불계좌 Pending State
End-to-End Flow
```

전체 Regression Test에서도
**140개 테스트가 모두 통과하여**
새로운 Refund Flow가 기존 CS 기능에 영향을 주지 않는지 확인했다.

또한 FastAPI Swagger를 통해 다음 카드 부분 환불 Flow를 실제 HTTP 요청으로 확인했다.

```text
"10007번 주문 1개 줄여줘"
↓
3개 → 2개 Preview
↓
부분 환불 예정 금액 20,000원
↓
사용자 "예"
↓
실제 주문 수량 / 금액 변경
↓
카드 부분 환불 시작
↓
refund_processing
```

---

## 6. 현재 Architecture의 핵심 원칙

### 판단과 표현을 분리한다

```text
사용자 자연어 이해
→ LLM

Business 판단
→ Python / Policy

실제 데이터 계산 및 변경
→ Python Service

자연어 표현
→ LLM 또는 Response Layer
```

LLM이 자연어를 이해하는 역할과
실제 Business Rule을 판단하는 역할을 분리한다.

예를 들어 주문 수량 변경에서 LLM은:

```text
"2개 더 추가해줘"
→ increase / 2
```

까지만 추출한다.

실제 목표 수량은:

```text
현재 수량 3
+
increase 2
→ target_quantity = 5
```

처럼 실제 주문 데이터와 Python Logic을 기준으로 계산한다.

---

### Agent 흐름은 Orchestrator가 제어한다

LLM이 임의로 다음 행동을 선택하기보다
Orchestrator가 명시적인 Routing 기준과 State를 기반으로
다음 Component를 호출한다.

현재 구조는 조건 분기를 중심으로 한다.

```text
현재 상태
+
이전 Component의 결과
↓
다음에 필요한 Component 선택
```

따라서 필요하지 않은 Service나 Policy를
모든 요청에서 일괄 실행하지 않는다.

---

### 관련 데이터의 일관성을 확인한다

하나의 데이터만 보고 최종 결과를 확정하지 않고,
필요한 경우 관련된 주문과 결제 상태를 함께 검증한다.

특히 주문 수량 변경은 다음 상태를 함께 확인한다.

```text
order_status
delivery_status
payment_status
```

---

### 정보가 부족하면 추가 질문한다

필요한 정보가 없는 상태에서 추측하지 않고
State를 유지한 채 사용자에게 추가 정보를 요청한다.

```text
정보 부족
↓
Pending State 저장
↓
추가 질문
↓
다음 사용자 입력
↓
기존 Flow 계속
```

---

### 판단과 Write Action을 분리한다

Policy에서 Action 가능 여부를 판단했다고 해서
즉시 실제 데이터를 변경하지 않는다.

```text
Policy 판단
≠
사용자 승인
≠
Write Action
```

실제 데이터를 변경하는 기능은
필요한 정보가 모두 확인되고
사용자가 명확하게 승인한 이후에만 실행한다.

---

### Write Action 직전에 상태를 재검증한다

최초 Policy 판단 이후
사용자와의 Multi-turn 대화가 진행되는 동안
실제 데이터 상태가 변경될 수 있다.

따라서 주문 취소, 배송지 변경, 주문 수량 변경처럼
현재 상태에 따라 실행 가능 여부가 달라지는 Write Action은
실제 실행 직전에 Policy를 다시 적용한다.

예:

```text
주문 취소
→ 최초 delivery_status = preparing_shipment
→ cancelable
→ 사용자 승인 대기
→ 그 사이 delivery_status = in_transit
→ Action 직전 Order Cancel Policy 재검증
→ 취소 Action 차단
```

배송지 변경 역시
Action 직전에 주문 상태와 배송 상태를 다시 확인한다.

주문 수량 변경은
주문 상태와 배송 상태뿐 아니라
결제 상태도 함께 다시 확인한다.

```text
최초 Preview 생성
→ order_completed
→ preparing_shipment
→ payment_completed

↓

사용자 승인 대기

↓

Action 실행 시점
→ 현재 주문 / 배송 / 결제 상태 재조회

↓

조건 유지
→ Write Action

조건 변경
→ Write Action 차단
```

---

### 주문금액, 실제 결제금액, 결제 차액, 환불 상태를 분리한다

주문 수량 변경으로 주문금액이 변경되었다고 해서
실제 결제 또는 환불까지 즉시 완료된 것으로 처리하지 않는다.

예를 들어 기존 3개, 60,000원 주문을
2개, 40,000원으로 변경한 경우:

```text
orders.total_price
60,000 → 40,000
→ 변경된 주문의 현재 금액

payments.payment_amount
60,000 유지
→ 실제로 이미 결제된 금액

payment_adjustments
20,000
partial_refund_required
pending
→ 주문 변경으로 발생한 결제 차액

refunds
20,000
partial
refund_processing
→ 실제 환불 절차의 현재 진행 상태
```

이를 통해 다음 네 가지 의미를 분리한다.

```text
주문금액
≠
실제 결제금액
≠
결제 차액
≠
환불 진행 상태
```

실제 PG 연동이 없는 현재 MVP에서는
환불 절차를 시작할 수는 있지만
실제 금융 거래가 완료되었다고 보장할 수 없다.

따라서 환불 데이터는
`refund_completed`가 아닌
`refund_processing` 상태까지만 변경한다.

---

### 하나의 기능이 다른 후속 Flow를 필요로 하면 Orchestrator에서 연결한다

주문 수량 변경 자체의 책임은
주문의 수량과 금액을 변경하고
발생한 차액을 계산하는 것이다.

수량 감소 결과가 부분 환불을 요구한다고 해서
Order Change Service 내부에 환불 Business Logic까지 모두 포함하지 않는다.

```text
Order Change
↓
partial_refund_required
↓
Orchestrator
↓
Refund Service
```

이렇게 분리함으로써
주문 변경과 환불이라는 서로 다른 책임을 분리하면서도
하나의 사용자 요청 안에서 End-to-End Flow로 연결할 수 있다.

---

### 기능의 성격에 따라 필요한 Component만 사용한다

모든 CS 기능에 동일한 처리 단계를 적용하지 않는다.

```text
Read Flow
→ 실제 데이터 조회가 필요한 기능

Guidance Flow
→ Business Policy 안내만 필요한 기능

Read + Policy Flow
→ 실제 데이터와 Policy를 함께 사용해야 하는 기능

Write Flow
→ 실제 데이터 변경이 필요한 기능
```

기능의 요구사항에 필요하지 않은 Component는
불필요하게 추가하지 않는다.

예를 들어 `delivery_status`는
현재 저장된 배송 상태라는 객관적인 사실을 조회하는 기능이므로
별도의 Business Policy를 추가하지 않는다.

```text
delivery_status
→ Delivery Service
→ Response
```

---

## 7. 향후 확장 방향

현재 Architecture를 기준으로 다음 기능을 확장할 예정이다.

```text
CS
├─ 회원/계정
├─ 주문/결제
├─ 교환/환불
├─ 배송
│   ├─ delivery_status
│   └─ delivery_eta
└─ 상품 정보

상품 추천
↓
추천 조건 추출
↓
조건 충분 여부 판단
├─ 부족 → 추가 질문
└─ 충분 → 상품 조회
             ↓
          후보 선정
             ↓
          추천 응답
```

현재 주문 수량 감소에 연결한 Refund Service는
향후 다음 Flow에서도 재사용할 수 있도록 확장할 수 있다.

```text
주문 수량 감소
→ 부분 환불
        │
        ▼
    Refund Service
        ▲
        │
주문 취소 / 직접 환불 요청
```

현재 주문 취소 Flow는 기존 환불 처리 구조를 유지하고 있으므로,
향후 Interface가 안정화된 뒤
중복되는 환불 책임을 Refund Service로 통합하는 것을 검토한다.

또한 현재 서버 메모리에 저장되는 State는
실제 서비스 통합 시 사용자 또는 Session 단위의
영속 State 저장 구조로 교체할 수 있다.

기능이 추가되더라도
각 Component의 책임과 Input / Output을 명확히 분리하면서
전체 Orchestration 구조를 확장한다.