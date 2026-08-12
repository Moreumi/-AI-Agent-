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

현재 구현된 CS Flow는 기능의 성격에 따라
Read Flow, Guidance Flow, Write Flow로 구분된다.

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
    │   ├─ order_confirmation
    │   └─ payment_confirmation
    │
    │   ↓
    │   Service / Data
    │   ↓
    │   Policy Layer
    │   ↓
    │   Order-Payment Consistency Check
    │   ↓
    │   Response Generation
    │
    ├─ Guidance Flow
    │   └─ payment_method_change
    │       ↓
    │       Payment Method Change Policy
    │       ↓
    │       결제수단 직접 변경 불가 판단
    │       ↓
    │       취소 후 재주문 안내
    │       ↓
    │       Guidance Response
    │       ↓
    │       State 생성 없이 Flow 종료
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
        │       Refund Flow
        │       ├─ card → refund_processing
        │       └─ cash
        │           → refund_account_required
        │           → 환불계좌 입력
        │           → refund_processing
        │   ↓
        │   Final Response
        │
        └─ delivery_address_change
            ↓
            주문 조회
            ↓
            Delivery Address Change Policy
            ↓
            새 배송지 수집
            ↓
            State 임시 저장
            ↓
            사용자 최종 승인
            ↓
            Action 직전 상태 재검증
            ↓
            Delivery Address Change Action
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
delivery_address_change
```

분류 결과는 Orchestrator가 다음 처리 경로를 결정하는 데 사용한다.

---

### Orchestrator

전체 Agent Flow의 중심 Component이다.

주요 역할은 다음과 같다.

- Intent 결과에 따른 Routing
- 필요한 정보가 충분한지 확인
- Pending State 확인
- Service 호출
- Policy 결과 확인
- Consistency 결과 확인
- Response Mode 결정
- 최종 응답 생성 Component 호출
- Write Action 실행 전 사용자 최종 승인 확인
- 주문 취소 이후 결제 방식에 따른 Refund Flow 분기
- 배송지 변경 과정에서 주문 선택, 새 주소 수집, 최종 승인 흐름 제어
- 진행 중인 Action에 따라 Multi-turn State 계속 처리
- 결제수단 변경과 같은 Policy 안내형 CS의 Guidance Flow Routing

즉 개별 기능을 직접 수행하기보다
**각 Component를 어떤 순서로 호출할지 결정하는 역할**을 담당한다.

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
향후 다른 Multi-turn Write Flow에서도
임시 데이터를 저장하기 위한 공통 Interface로 사용한다.

현재 MVP에서는 Python Dictionary 기반 State를 사용한다.

State는 서버 메모리에 저장되므로
서버가 재시작되면 진행 중인 State가 초기화된다.

향후 실제 서비스에서는
사용자 또는 Session 단위의 State 관리와
영속 저장 방식이 필요하다.

---

### Service / Data

고객의 주문·결제·환불 데이터를 조회하고,
Policy 판단에 필요한 결과를 반환한다.

또한 Orchestrator에서 확정된 Write Action 요청이 전달되면
실제 데이터 상태 변경을 수행한다.

주요 조회 데이터 예시는 다음과 같다.

```text
order_id
order_status
order_date
total_price
delivery_status
delivery_address

payment_status
payment_method
payment_amount
payment_date

refund_status
```

현재 주요 Write Action은 다음과 같다.

```text
cancel_order()
→ 주문 상태 변경
→ 결제 상태 변경
→ 환불 상태 생성

register_refund_account()
→ 환불계좌 정보 저장
→ refund_status를 refund_processing으로 변경

change_delivery_address()
→ Action 직전 주문/배송 상태 재검증
→ 주문의 delivery_address 변경
```

Service는 데이터를 조회하여
Policy 판단에 필요한 결과를 반환하고,
확정된 Action 요청이 전달되면 데이터 상태 변경을 수행한다.

Write Action은 Orchestrator가
필요한 조건과 사용자의 명확한 승인을 확인한 이후에만 호출한다.

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

Delivery Address Change Policy
→ 배송지 변경 가능 여부 판단

Payment Method Change Policy
→ 결제 완료 후 결제수단 변경 가능 여부 및 대안 판단
```

---

#### Action 가능 여부를 판단하는 Policy

주문 취소나 배송지 변경처럼
실제 데이터를 변경할 가능성이 있는 기능에서는
Policy가 **Action을 실행해도 되는 조건인지** 먼저 판단한다.

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

실제 배송지 변경
```

`changeable`은 현재 상태에서 배송지 변경이 가능하다는
Business 판단 결과일 뿐이다.

실제 배송지 변경은 이후 Orchestrator에서

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
- 배송지 변경 가능 여부
- 쇼핑몰 정책
- 데이터 불일치 해결 방법
- Write Action 실행 여부

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
Write Action 관련 고정 응답은
현재 Python 코드에서 직접 생성하고 있다.

---

## 4. Multi-turn Flow

정보가 부족하거나
Write Action 수행을 위해 추가 정보가 필요한 경우
State를 이용해 다음 사용자 입력까지 Flow를 유지한다.

기본 구조는 다음과 같다.

```text
사용자 질문
↓
Intent Classification
↓
Orchestrator
↓
필요 정보 확인
```

정보가 충분한 경우:

```text
Service
→ Policy
→ 필요한 추가 검증
→ Response
```

정보가 부족한 경우:

```text
State 저장
→ 추가 질문
→ 다음 사용자 입력
→ Pending State 확인
→ 기존 Flow 계속 처리
```

배송지 변경의 경우 다음과 같이 여러 턴을 사용한다.

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
Write Action 실행
↓
State 초기화
```

---

## 5. 현재 구현 범위

현재 End-to-End로 구현된 기능은 다음과 같다.

```text
CS
└─ 주문/결제
   ├─ 주문 완료 확인
   ├─ 결제 완료 확인
   ├─ 결제수단 변경
   │   ├─ Payment Method Change Policy
   │   ├─ 직접 변경 불가 안내
   │   ├─ 취소 후 재주문 안내
   │   └─ State 없이 Flow 종료
   ├─ 주문 취소
   │   ├─ 주문 취소 가능 여부 판단
   │   ├─ 사용자 최종 승인
   │   ├─ 주문/결제 취소 Action
   │   └─ 환불 처리
   │       ├─ 카드
   │       │   → refund_processing
   │       └─ 계좌이체
   │           → 환불계좌 수집
   │           → refund_processing
   │
   └─ 배송지 변경
       ├─ 주문 선택
       ├─ 배송지 변경 가능 여부 판단
       ├─ 새 배송지 수집
       ├─ State 임시 저장
       ├─ 사용자 최종 승인
       ├─ Action 직전 상태 재검증
       └─ 배송지 변경 Action
```

현재 전체 자동 테스트 58개가 통과한다.

배송지 변경 Flow는 FastAPI Swagger를 통해
Multi-turn End-to-End 동작을 추가로 검증했다.

---

## 6. 현재 Architecture의 핵심 원칙

### 판단과 표현을 분리한다

```text
Business 판단
→ Python / Policy

자연어 표현
→ LLM 또는 Response Layer
```

### Agent 흐름은 Orchestrator가 제어한다

LLM이 임의로 다음 행동을 선택하기보다
Orchestrator가 명시적인 Routing 기준과 State를 기반으로
다음 Component를 호출한다.

### 관련 데이터의 일관성을 확인한다

하나의 데이터만 보고 최종 결과를 확정하지 않고,
필요한 경우 관련된 주문과 결제 상태를 함께 검증한다.

### 정보가 부족하면 추가 질문한다

필요한 정보가 없는 상태에서 추측하지 않고
State를 유지한 채 사용자에게 추가 정보를 요청한다.

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

### Write Action 직전에 상태를 재검증한다

최초 Policy 판단 이후
사용자와의 Multi-turn 대화가 진행되는 동안
실제 데이터 상태가 변경될 수 있다.

따라서 배송지 변경처럼
현재 상태에 따라 실행 가능 여부가 달라지는 Action은
실제 실행 직전에 상태를 다시 확인한다.

### 기능의 성격에 따라 필요한 Component만 사용한다

모든 CS 기능에 동일한 처리 단계를 적용하지 않는다.

```text
Read Flow
→ 실제 데이터 조회가 필요한 기능

Guidance Flow
→ Business Policy 안내만 필요한 기능

Write Flow
→ 실제 데이터 변경이 필요한 기능
```

기능의 요구사항에 필요하지 않은 Component는
불필요하게 추가하지 않는다.

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

기능이 추가되더라도
각 Component의 책임과 Input / Output을 명확히 분리하면서
전체 Orchestration 구조를 확장한다.