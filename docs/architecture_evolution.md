# Architecture Evolution

이 문서는 온라인 쇼핑몰 AI Agent를 구현하면서  
챗봇의 처리 구조가 어떤 문제를 발견했고, 어떤 판단을 통해 변경되었는지 기록한다.

단순한 코드 작성 순서가 아니라  
**문제 → 설계 결정 → 구조 변화 → 결과**를 중심으로 기록한다.

---

## 1. 주문/결제 기능을 End-to-End Flow로 연결

### 초기 구조

처음에는 주문·결제와 관련된 개별 기능을 각각 구현하는 수준에서 시작했다.

```text
사용자 질문
→ Intent Classification
→ Service 조회
→ 응답
```

### 문제

개별 함수가 동작하는 것만으로는 실제 챗봇이라고 보기 어려웠다.

사용자의 질문이 들어온 이후

- 어떤 기능으로 Routing할지
- 필요한 정보가 부족하면 어떻게 처리할지
- 여러 주문 중 어떤 주문을 확인할지
- 이전 대화의 정보를 어떻게 이어갈지

와 같은 전체 흐름이 필요했다.

### 결정

개별 기능을 직접 호출하는 구조가 아니라  
`Orchestrator`가 전체 처리 순서를 관리하도록 구성했다.

또한 주문번호가 부족한 경우에는
State에 현재 처리 중인 기능과 후보 주문을 저장하고,
다음 사용자 입력에서 이어서 처리하도록 했다.

### 변경된 구조

```text
사용자 질문
→ Intent Classification
→ Orchestrator
→ 정보 충분 여부 확인

정보 부족
→ State 저장
→ 추가 질문
→ 다음 사용자 입력
→ State 확인
→ 기존 Flow 계속 처리

정보 충분
→ Service 조회
→ 응답 생성
```

### 결과

주문 완료 확인과 결제 완료 확인 기능이  
단일 함수 수준이 아니라 멀티턴을 포함한
End-to-End 챗봇 Flow로 동작하게 되었다.

---

## 2. Policy Layer 분리

### 초기 구조

Service에서 조회한 주문·결제 상태를 기준으로  
바로 고객 응답을 생성하는 구조였다.

```text
Service 조회
→ 상태 확인
→ 응답 생성
```

### 문제

조회된 데이터와 그 데이터의 **업무적 의미를 판단하는 책임**,  
그리고 고객에게 **자연어로 표현하는 책임**이 명확하게 분리되어 있지 않았다.

예를 들어

```text
order_status = order_completed
```

라는 값을 보고 실제로 "주문 완료"라고 판단하는 것은  
쇼핑몰의 Business Rule에 해당한다.

이 판단까지 LLM에게 맡기면
동일한 상태에서도 판단이 달라질 가능성이 있고,
쇼핑몰 정책과 LLM의 일반 지식이 섞일 수 있다.

### 결정

주문·결제 상태의 업무적 판단을 담당하는
`Policy Layer`를 별도로 분리했다.

```text
order_status
→ Order Completion Policy
→ judgment

payment_status
→ Payment Completion Policy
→ judgment
```

LLM은 상태를 판단하지 않고,  
Policy에서 이미 확정된 결과를 고객에게
자연스럽게 설명하는 역할만 담당하도록 했다.

### 변경된 구조

```text
Service / Data
→ Policy
→ 확정된 judgment
→ Response Generation
```

### 결과

다음과 같이 책임이 분리되었다.

```text
Service
→ 실제 데이터 조회

Policy
→ 업무적 의미 판단

LLM
→ 확정된 결과 표현
```

이를 통해 쇼핑몰의 Business Rule과
자연어 생성 책임을 분리할 수 있게 되었다.

---

## 3. 주문-결제 Consistency 검증 추가

### 초기 구조

주문 완료 여부와 결제 완료 여부를 각각 독립적으로 판단했다.

```text
주문 조회
→ Order Policy
→ 주문 결과

결제 조회
→ Payment Policy
→ 결제 결과
```

### 문제

각각의 상태만 보면 정상이어도  
관련 데이터와 함께 확인하면 모순되는 상황이 발생할 수 있다.

예:

```text
order_status = order_completed
payment_status = payment_failed
```

주문 상태만 확인하면 정상적으로 접수된 주문이지만,  
결제 상태까지 함께 보면 추가 확인이 필요한 상황이다.

반대로 다음과 같은 경우도 발생할 수 있다.

```text
order_status = order_failed
payment_status = payment_completed
```

따라서 하나의 상태만으로 고객에게 정상 완료 응답을 제공하면  
잘못된 안내가 발생할 가능성이 있었다.

### 결정

주문 상태와 결제 상태를 함께 검사하는  
`Order-Payment Consistency Policy`를 추가했다.

예:

```text
order_completed + payment_completed
→ consistent_completed

order_completed + payment_failed
→ needs_review
```

### 변경된 구조

```text
Service 조회
→ 개별 Policy 판단
→ Order-Payment Consistency Check
→ 최종 판단
→ Response Generation
```

### 결과

개별 상태가 정상으로 보이더라도  
관련 데이터와 불일치하면 바로 정상 응답을 생성하지 않고  
`needs_review` 상태로 Routing할 수 있게 되었다.

---

## 4. Output Response 방식 분리

### 초기 구조

최종 고객 응답은 하나의 방식으로 생성했다.

따라서 단순한 주문·결제 조회 결과와  
정책이나 예외 상황에 대한 설명이
동일한 응답 방식으로 처리될 수 있었다.

### 문제

응답의 목적에 따라 적합한 표현 방식이 달랐다.

예를 들어 주문 완료 여부처럼
객관적인 정보를 확인하는 질문은

```text
주문 상태
주문 날짜
주문 금액
```

등을 빠르게 확인할 수 있는 구조가 적합하다.

반면 주문과 결제 상태가 서로 다른 경우에는  
단순 정보 나열보다 상황 설명과 후속 안내가 필요하다.

### 결정

Orchestrator가 상황에 따라
`response_mode`를 명시적으로 선택하도록 했다.

```text
fact_summary
→ 객관적인 조회 결과

narrative_guidance
→ Policy / 예외 / 데이터 불일치 설명
```

### 변경된 구조

```text
Service / Data
→ Policy
→ Consistency Check
→ Orchestrator
→ response_mode 결정
    ├─ fact_summary
    └─ narrative_guidance
→ Output Prompt
→ LLM
→ 최종 고객 응답
```

### 결과

객관적인 조회 결과와 설명이 필요한 상황을  
서로 다른 응답 전략으로 처리할 수 있게 되었다.

또한 **어떤 응답 방식을 사용할지 LLM이 임의로 결정하지 않고
Orchestrator가 결정**하도록 하여,
Agent의 처리 흐름을 명시적으로 제어할 수 있게 되었다.

---

## 5. 사용자 승인 기반 Write Action 구조 추가

### 초기 구조

기존 주문 완료 확인과 결제 완료 확인 기능은
데이터를 조회하고 판단한 뒤
사용자에게 결과를 제공하는 Read 중심 구조였다.

```text
Read
→ Judge
→ Respond
```

이 구조에서는 실제 데이터를 변경하지 않기 때문에
사용자의 추가 승인을 확인하는 단계가 필요하지 않았다.

---

### 문제

주문 취소 기능을 추가하면서
기존 Read Flow와는 다른 문제가 발생했다.

주문 취소는 단순히 현재 상태를 조회하는 기능이 아니라
실제 주문 및 결제 데이터를 변경하는 Write Action이다.

예를 들어 Policy에서 다음과 같이 판단했다고 하더라도

```text
order_status = order_completed
delivery_status = preparing_shipment

→ cancelable
```

이 결과는

```text
"이 주문은 취소할 수 있다"
```

는 의미이지,

```text
"지금 바로 주문을 취소해도 된다"
```

는 의미는 아니다.

사용자가 취소 가능 여부만 물어본 것인지,
실제로 취소를 원하는 것인지 구분하지 않고
Action을 실행하면 의도하지 않은 데이터 변경이 발생할 수 있었다.

---

### 결정

Policy 판단과 실제 Write Action 사이에
**사용자 최종 승인 단계**를 추가했다.

```text
Read
→ Judge
→ Confirm
→ Act
→ Verify / Follow-up
→ Respond
```

주문 취소 가능 여부를 먼저 판단한 뒤
사용자가 명확하게 취소를 승인한 경우에만
실제 주문 및 결제 상태를 변경하도록 했다.

승인 여부가 불명확한 경우에는
LLM이 사용자의 의도를 추측하여 Action을 실행하지 않고,
State를 유지한 상태에서 다시 확인한다.

---

### State 확장

멀티턴 승인 과정을 유지하기 위해
다음 State를 사용하도록 했다.

```text
pending_action
→ 현재 이어서 처리해야 하는 Action 단계

candidate_orders
→ 사용자가 선택할 수 있는 주문 목록

selected_order_id
→ 현재 처리 중인 주문번호
```

예를 들어 주문 취소 최종 승인을 기다리는 경우:

```python
state = {
    "pending_action": "confirm_cancel",
    "candidate_orders": [],
    "selected_order_id": 10001,
}
```

이 State를 통해 다음 사용자 입력인

```text
"예"
"아니오"
```

를 새로운 Intent로 다시 분류하지 않고
기존 주문 취소 Flow의 후속 입력으로 처리할 수 있게 했다.

---

### 결제 방식에 따른 Refund Flow 분리

주문 취소 후 환불 과정은
결제 방식에 따라 추가 분기가 필요했다.

```text
주문 취소
↓
결제 취소
↓
결제 방식 확인

├─ card
│   → refund_processing
│
└─ cash
    → refund_account_required
    → 환불계좌 입력
    → refund_processing
```

카드 결제는 주문 및 결제 취소 이후
환불 처리 상태로 전환한다.

계좌이체는 환불을 진행하기 위해
사용자로부터 환불계좌 정보를 추가로 입력받아야 하므로
다시 Multi-turn State를 사용한다.

또한

```text
payment_canceled
≠
refund_completed
```

로 구분했다.

결제가 취소되었다는 사실만으로
실제 환불까지 완료되었다고 판단하지 않는다.

---

### 변경된 구조

```text
주문 취소 요청
↓
Intent Classification
↓
주문 조회
↓
Order Cancel Policy
↓
취소 가능 여부 판단

├─ 취소 불가
│   → 사유 안내
│
└─ 취소 가능
    ↓
사용자 최종 승인

├─ 거절
│   → Action 실행하지 않음
│
├─ 불명확
│   → State 유지 후 다시 확인
│
└─ 승인
    ↓
Write Action
↓
주문 상태 변경
↓
결제 상태 변경
↓
Refund Flow
↓
최종 응답
```

---

### 결과

기존 Read 중심 Agent 구조에
실제 데이터를 안전하게 변경할 수 있는
Write Flow가 추가되었다.

핵심 원칙은 다음과 같이 정리했다.

```text
Policy 판단
≠
사용자 승인
≠
Action 실행
```

이를 통해 LLM이나 Policy의 판단만으로
실제 고객 데이터를 변경하지 않고,
사용자의 명확한 승인 이후에만
Write Action을 수행하도록 처리 흐름을 분리할 수 있게 되었다.

주문 취소 Flow는 Policy, Service, State, Action,
Multi-turn Flow 및 FastAPI Swagger 기반
End-to-End 테스트를 통해 검증했다.

---

## 6. Multi-turn Write Flow를 재사용 가능한 구조로 확장

### 기존 구조

주문 취소 기능을 구현하면서
사용자의 승인을 받은 이후 실제 데이터를 변경하는
Write Action 구조를 처음 도입했다.

```text
조회
→ Policy 판단
→ 사용자 승인
→ Write Action
→ 결과 응답
```

주문 취소에서는 다음 State를 중심으로
Multi-turn Flow를 관리했다.

```text
pending_action
candidate_orders
selected_order_id
```

---

### 문제

배송지 변경 기능을 추가하면서
Write Action 전에 단순히 승인 여부만 유지하는 것으로는
충분하지 않은 경우가 발생했다.

배송지 변경은 다음과 같이
추가 정보 수집 과정이 필요하다.

```text
배송지 변경 요청
→ 주문 선택
→ 변경 가능 여부 확인
→ 새 배송지 입력
→ 새 배송지 임시 보관
→ 사용자 최종 승인
→ 실제 배송지 변경
```

특히 사용자가 입력한 새 배송지는
다음 사용자 입력까지 유지해야 하지만,
최종 승인 전에는 실제 주문 데이터에 반영하면 안 된다.

따라서 **실제 데이터와 분리된 임시 Action 데이터**를
저장할 구조가 필요했다.

배송지 변경 기능만을 위해

```text
pending_delivery_address
```

와 같은 전용 State를 추가할 수도 있었지만,
향후 다른 정보 수집형 Write Flow에서도
유사한 임시 데이터가 필요할 수 있다.

---

### 결정

특정 기능에 종속된 State를 계속 추가하는 대신
Multi-turn Action 과정에서 필요한 임시 데이터를 저장하는
공통 State Interface인 `pending_data`를 추가했다.

```python
state = {
    "pending_action": None,
    "candidate_orders": [],
    "selected_order_id": None,
    "pending_data": {},
}
```

배송지 변경 과정에서는 다음과 같이 사용한다.

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

새 배송지는 사용자 승인 전까지
`pending_data`에만 저장한다.

실제 주문 데이터의 `delivery_address`는
사용자의 최종 승인이 확인된 이후에만 변경한다.

---

### Action 직전 상태 재검증

배송지 변경 가능 여부를 처음 확인한 이후
사용자가 새 주소를 입력하고 최종 승인하기까지
시간이 발생할 수 있다.

그 사이 실제 주문 상태가 변경될 가능성이 있다.

예:

```text
최초 Policy 판단
delivery_status = preparing_shipment
→ 배송지 변경 가능

↓

사용자 새 배송지 입력

↓

배송 시작
delivery_status = in_transit

↓

사용자 최종 승인
```

최초 Policy 결과만 사용하면
이미 배송이 시작된 주문의 배송지를
변경하는 문제가 발생할 수 있다.

따라서 실제 Write Action 실행 직전에
현재 주문 상태와 배송 상태를 다시 확인하도록 했다.

```text
최초 Policy 판단
→ 정보 수집
→ 사용자 승인
→ Action 직전 Policy 재검증
→ Write Action
```

현재 상태가 더 이상 변경 가능한 조건이 아니라면
사용자가 승인했더라도 Write Action을 실행하지 않는다.

배송지 변경에서 이 문제를 확인한 이후,
동일하게 배송 상태에 따라 실행 가능 여부가 달라지는
주문 취소 Action에도 같은 원칙을 적용했다.

```text
주문 취소 가능 여부 최초 판단
→ 사용자 승인
→ Action 직전 Order Cancel Policy 재검증
→ 결제 상태 재검증
→ Write Action
```

따라서 현재 상태 의존적인 Write Flow에서는
최초 Policy 결과를 Action 시점까지 그대로 신뢰하지 않고,
실제 Action 직전의 최신 상태를 다시 기준으로 판단한다.

---

### 변경된 구조

Write Flow를 다음과 같은 공통 구조로 확장했다.

```text
Write 요청
↓
대상 데이터 조회
↓
Policy 판단
↓
필요 정보 확인

├─ 정보 부족
│   ↓
│   State 저장
│   ↓
│   추가 정보 수집
│
└─ 정보 충분
    ↓

Action 예정 데이터
필요 시 State에 임시 저장
↓
사용자 최종 승인

├─ 거절
│   → Action 실행하지 않음
│
├─ 불명확
│   → State 유지 후 재확인
│
└─ 승인
    ↓
Action 직전 상태 재검증
↓
Write Action
↓
결과 확인
↓
State 초기화
↓
최종 응답
```

---

### 결과

배송지 변경 기능이 다음과 같은
End-to-End Flow로 동작하게 되었다.

```text
사용자 배송지 변경 요청
→ Intent Classification
→ 주문 조회 / 선택
→ Delivery Address Change Policy
→ 새 배송지 수집
→ pending_data 임시 저장
→ 사용자 최종 승인
→ Action 직전 상태 재검증
→ Delivery Address Change Action
→ 최종 응답
```

또한 State가 단순히 현재 처리 단계와 주문번호만 유지하는 구조에서

```text
현재 어떤 작업을 진행 중인가
+
어떤 주문을 처리하고 있는가
+
다음 턴까지 어떤 임시 데이터를 유지해야 하는가
```

를 표현할 수 있는 구조로 확장되었다.

이를 통해 향후 다른 Multi-turn Write 기능에서도
동일한 State 및 Orchestration 패턴을 재사용할 수 있게 되었다.

배송지 변경 Flow는 단위 및 통합 테스트와
FastAPI Swagger 기반 Multi-turn End-to-End 테스트를 통해 검증했다.

---

## Current Architecture

현재까지의 구조는 다음과 같다.

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
    │   ├─ 주문 완료 확인
    │   └─ 결제 완료 확인
    │
    │   ↓
    │   Service / Data
    │   ↓
    │   Policy Layer
    │   ↓
    │   필요한 경우 Consistency Check
    │   ↓
    │   Response Mode Selection
    │   ├─ fact_summary
    │   └─ narrative_guidance
    │   ↓
    │   Output Prompt + LLM
    │   ↓
    │   Final Response
    │
    ├─ Guidance Flow
    │   └─ 결제수단 변경
    │       ↓
    │       Payment Method Change Policy
    │       ↓
    │       직접 변경 불가 판단
    │       ↓
    │       취소 후 재주문 안내
    │       ↓
    │       State 생성 없이 Flow 종료
    │
    └─ Write Flow
        │
        ├─ 주문 취소
        │   ↓
        │   Service / Data 조회
        │   ↓
        │   Order Cancel Policy
        │   ↓
        │   사용자 최종 승인
        │   ↓
        │   Action 직전 Policy 재검증
        │   ↓
        │   결제 상태 재검증
        │   ↓
        │   Write Action
        │   ├─ Order Cancel
        │   └─ Payment Cancel
        │       ↓
        │       Refund Flow
        │       ├─ card
        │       │   → refund_processing
        │       │
        │       └─ cash
        │           → refund_account_required
        │           → 환불계좌 입력
        │           → refund_processing
        │   ↓
        │   State 초기화
        │   ↓
        │   Final Response
        │
        └─ 배송지 변경
            ↓
            Service / Data 조회
            ↓
            Delivery Address Change Policy
            ↓
            필요 시 주문 선택
            ↓
            새 배송지 수집
            ↓
            pending_data 임시 저장
            ↓
            사용자 최종 승인
            ↓
            Action 직전 Policy 재검증
            ↓
            Delivery Address Change Action
            ↓
            State 초기화
            ↓
            Final Response
```