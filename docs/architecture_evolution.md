# Architecture Evolution

이 문서는 온라인 쇼핑몰 AI Agent를 구현하면서
챗봇의 처리 구조에서 어떤 문제를 발견했고,
어떤 판단을 통해 Architecture를 변경했는지 기록한다.

단순한 코드 작성 순서가 아니라
**문제 → 설계 결정 → 구조 변화 → 결과**를 중심으로 기록한다.

---

## 1. 주문/결제 기능을 End-to-End Flow로 연결

### 초기 구조

처음에는 주문·결제와 관련된 개별 기능을
각각 구현하는 수준에서 시작했다.

```text
사용자 질문
→ Intent Classification
→ Service 조회
→ 응답
```

### 문제

개별 함수가 동작하는 것만으로는
실제 챗봇이라고 보기 어려웠다.

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
단일 함수 수준이 아니라 Multi-turn을 포함한
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
그리고 고객에게 **자연어로 표현하는 책임**이
명확하게 분리되어 있지 않았다.

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

주문 완료 여부와 결제 완료 여부를
각각 독립적으로 판단했다.

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

Multi-turn 승인 과정을 유지하기 위해
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
Refund 처리
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

## 7. 배송 예상 시기 문의를 조건부 Flow로 확장

### 초기 설계

배송 예상 시기 문의는 쇼핑몰의 일반 배송기간을 안내하는
Guidance Flow로 처리하는 것을 우선 고려했다.

```text
사용자 질문
→ Intent Classification
→ Delivery ETA Policy
→ 일반 배송기간 안내
→ Flow 종료
```

예를 들어 다음과 같은 질문은
특정 주문 데이터를 조회할 필요가 없다.

```text
"배송은 보통 얼마나 걸려?"
"배송 시작하면 며칠 걸려?"
"제주도는 배송 얼마나 걸려?"
```

이 경우 쇼핑몰의 일반 배송 기준만으로
사용자에게 필요한 정보를 제공할 수 있다.

---

### 문제

배송 예상 시기와 관련된 실제 사용자 질문에는
일반적인 배송기간 문의뿐 아니라
특정 주문의 도착 시기를 묻는 질문도 존재한다.

예:

```text
"내 주문 언제 와?"
"10004번 주문 언제 도착해?"
```

이 질문에 일반 배송 Policy만 바로 적용하면
현재 주문이

```text
배송 준비 중인지
배송 중인지
이미 배송 완료되었는지
취소된 주문인지
```

확인하지 않은 상태에서 동일한 배송기간을 안내하게 된다.

따라서 같은 `delivery_eta` 질문이라도
필요한 정보와 처리 과정이 서로 다르다는 문제가 발생했다.

---

### 결정

`delivery_eta`라는 하나의 `sub_intent`는 유지하되,
질문의 대상 범위를 나타내는
`delivery_eta_scope`를 Structured Output에 추가했다.

```text
delivery_eta_scope

├─ general
│   → 일반적인 배송기간 문의
│
└─ order_specific
    → 실제 사용자 주문의 도착 시기 문의
```

Intent를 다음과 같이 과도하게 분리하지 않았다.

```text
delivery_eta_general
delivery_eta_order
```

두 질문 모두 핵심 목적은
배송 예상 시기를 확인하는 것이기 때문이다.

대신 동일 Intent 내부에서
필요한 정보의 범위를 별도 필드로 표현하도록 설계했다.

---

### 변경된 구조

#### General

```text
사용자 질문
→ Intent Classification
→ delivery_eta
→ delivery_eta_scope = general
→ Delivery ETA Policy
→ 일반 배송기간 안내
→ Flow 종료
```

특정 주문 데이터가 필요하지 않으므로
주문 조회나 State를 사용하지 않는다.

#### Order Specific

```text
사용자 질문
→ Intent Classification
→ delivery_eta
→ delivery_eta_scope = order_specific
→ 주문 조회 / 선택
→ Delivery Service
→ order_status / delivery_status 확인
→ Delivery ETA Policy
→ 실제 배송 상태 + 일반 배송 기준 조합
→ 최종 응답
```

주문이 여러 건 존재하면
기존 Multi-turn State 구조를 이용하여
사용자에게 확인할 주문번호를 추가로 입력받는다.

```text
pending_action = delivery_eta_selection
```

다음 사용자 입력은 새로운 Intent로 다시 분류하지 않고
기존 `delivery_eta` Flow의 후속 입력으로 처리한다.

---

### 기존 Component 재사용

특정 주문의 배송 예상 시기를 확인하기 위해
새로운 주문 조회 Service를 별도로 만들지 않았다.

기존 `delivery_status`에서 사용하는

```text
check_delivery_status()
```

를 그대로 재사용하여

```text
order_status
delivery_status
```

를 조회한다.

두 기능의 차이는 조회 이후의 처리에 있다.

```text
delivery_status
→ 현재 배송 상태 자체를 응답

delivery_eta / order_specific
→ 현재 배송 상태 조회
→ Delivery ETA Policy 적용
→ 현재 상태를 고려한 배송 예상 안내
```

이를 통해 동일한 데이터 조회 책임을 중복 구현하지 않고,
기능별 Business 판단만 분리했다.

---

### 정확한 ETA를 생성하지 않는 이유

현재 MVP 데이터에는 다음 정보가 존재하지 않는다.

```text
shipping_started_at
estimated_delivery_date
tracking_number
택배사 실시간 Tracking 정보
```

따라서 현재 배송 상태와 일반 배송 Policy만으로
정확한 도착 날짜를 임의로 계산하거나 생성하지 않는다.

예를 들어 배송 중인 주문에는

```text
현재 배송 중이라는 실제 상태
+
일반적인 배송 소요 기준
+
정확한 도착일은 현재 데이터로 확인할 수 없다는 제한
```

을 함께 안내한다.

향후 배송 시작 시각이나 택배사 Tracking Tool이 추가되면
보다 구체적인 ETA 기능으로 확장할 수 있다.

---

### 결과

`delivery_eta`를 구현하면서
기존의 단순한

```text
Read Flow
Guidance Flow
Write Flow
```

구분에 더해,

```text
Read + Policy Flow
```

가 명확하게 드러났다.

또한 동일한 사용자 목적이라도
필요한 정보의 범위에 따라 처리 경로를 다르게 선택할 수 있도록

```text
Intent
+
Scope
→ Routing
```

구조를 적용했다.

이를 통해 불필요한 데이터 조회는 피하면서도,
특정 주문을 대상으로 하는 질문에서는
실제 주문 상태를 반영한 응답을 제공할 수 있게 되었다.

---

## 8. 주문 변경과 실제 결제·환불 처리를 분리

### 초기 구조

기존 Write Flow에서는
주문 취소나 배송지 변경처럼 하나의 Action을 수행한 뒤
해당 데이터의 상태를 직접 변경하는 구조를 사용했다.

예를 들어 배송지 변경은 다음과 같이 처리할 수 있었다.

```text
배송지 변경 요청
→ Policy 판단
→ 사용자 승인
→ Action 직전 재검증
→ delivery_address 변경
```

주문 수량 변경도 처음에는
비슷한 Write Flow로 처리할 수 있다고 생각했다.

```text
수량 변경 요청
→ 변경 가능 여부 판단
→ 사용자 승인
→ quantity 변경
→ total_price 변경
```

---

### 문제 1. 주문금액과 실제 결제금액의 의미가 달라짐

주문 수량이 변경되면
단순히 주문 데이터 하나만 변경되는 것이 아니라
결제 금액과의 관계도 함께 달라진다.

예를 들어 기존 주문이 다음과 같은 경우:

```text
quantity = 3
unit_price = 20,000
total_price = 60,000

payment_amount = 60,000
```

사용자가 수량을 2개로 변경하면
새로운 주문금액은 다음과 같다.

```text
quantity = 2
total_price = 40,000
```

하지만 실제 PG에서 부분 환불을 수행하지 않은 상태에서
결제 데이터까지 다음과 같이 변경하면 문제가 발생한다.

```text
payment_amount
60,000 → 40,000
```

이 값은 실제로 40,000원만 결제되었다는 의미처럼 보이지만,
실제 고객은 아직 60,000원을 결제한 상태이다.

반대로 수량을 증가시킨 경우에도
추가 결제가 실제로 수행되지 않았는데
`payment_amount`를 증가시키면
완료되지 않은 결제를 완료된 사실처럼 기록하게 된다.

즉 주문 수량 변경에서는 다음 세 값을
하나의 값으로 취급할 수 없었다.

```text
현재 주문의 금액
≠
실제로 이미 결제된 금액
≠
앞으로 처리해야 할 결제 차액
```

---

### 결정 1. Payment Adjustment 분리

주문 데이터의 변경과
실제 결제 처리를 서로 다른 책임으로 분리했다.

```text
orders.total_price
→ 변경된 주문의 현재 금액

payments.payment_amount
→ 실제로 이미 결제된 금액

payment_adjustments
→ 추가 결제 또는 부분 환불이 필요한 결제 차액
```

주문 수량 변경이 승인되면
`quantity`와 `total_price`는
실제 주문 상태에 맞게 변경한다.

하지만 외부 PG 추가 결제 또는 환불이 아직 수행되지 않았으므로
`payments.payment_amount`는 변경하지 않는다.

대신 결제 차액을 별도의
`payment_adjustments`에 기록한다.

예:

```text
기존
quantity = 3
total_price = 60,000
payment_amount = 60,000

↓

2개로 변경

↓

orders
quantity = 2
total_price = 40,000

payments
payment_amount = 60,000

payment_adjustments
adjustment_type = partial_refund_required
adjustment_amount = 20,000
adjustment_status = pending
```

수량이 증가하는 경우에도 동일한 원칙을 적용한다.

```text
기존 3개
→ 변경 후 5개

주문금액
60,000 → 100,000

실제 결제금액
60,000 유지

결제 차액
40,000
additional_payment_required
pending
```

---

### 계산 책임도 분리

사용자가 말한 수량 표현과
실제 목표 수량 계산 역시 분리했다.

LLM은 다음 정보만 Structured Output으로 추출한다.

```text
"5개로 바꿔줘"
→ set / 5

"2개 더 추가해줘"
→ increase / 2

"1개 줄여줘"
→ decrease / 1
```

LLM이 실제 주문의 현재 수량을 추측하거나
최종 목표 수량을 계산하지 않는다.

```text
사용자 표현
↓
LLM
→ quantity_change_type
→ quantity_value

↓

실제 주문 조회

↓

Python Business Logic
→ current_quantity 확인
→ target_quantity 계산
→ new_total_price 계산
→ adjustment 계산
```

이를 통해 자연어 해석과
실제 데이터에 기반한 계산 책임을 분리했다.

---

### 1차 변경 구조

처음에는 주문 수량 변경 이후
발생한 결제 차액을 기록하는 것까지를
MVP의 처리 범위로 두었다.

```text
주문 수량 변경
↓
Order Change Action
↓
quantity / total_price 변경
↓
Payment Adjustment 생성
↓
additional_payment_required
또는
partial_refund_required
↓
pending
↓
최종 응답
```

이 구조에서는 실제 외부 PG 처리를 하지 않으면서도
주문 데이터와 결제 데이터의 의미를
잘못 섞지 않을 수 있었다.

---

### 문제 2. 부분 환불 필요 상태만 기록하면 CS Flow가 끝나지 않음

수량 감소 Flow를 End-to-End 관점에서 다시 확인하면서
추가적인 문제가 발견되었다.

예를 들어 고객이

```text
"10007번 주문 1개 줄여줘"
```

라고 요청하여

```text
3개 → 2개
60,000원 → 40,000원
부분 환불 필요 금액 = 20,000원
```

이 계산되었는데,

Agent가

```text
부분 환불이 필요합니다.
현재 pending 상태입니다.
```

라고 답변하고 Flow를 종료하면
사용자 입장에서는 실제 환불 처리가
어디까지 진행되는지 알 수 없다.

즉

```text
partial_refund_required
```

는 **환불이 필요하다는 판단 결과**이지,
**환불 절차 자체의 상태**를 의미하지 않았다.

다음 두 데이터의 책임을
다시 구분할 필요가 생겼다.

```text
payment_adjustments
→ 왜 얼마의 차액 처리가 필요한가

refunds
→ 실제 환불 절차가 현재 어떤 상태인가
```

---

### 대안 검토. 새로운 사용자 입력처럼 환불 요청을 다시 만들지 않음

부분 환불이 필요한 경우
내부적으로 다음과 같은 새로운 사용자 입력을 만들어

```text
"환불해줘"
```

다시 Intent Classification부터 실행하는 방법도 고려할 수 있었다.

하지만 이미 Order Change Flow에서 다음 정보가 확정되어 있다.

```text
order_id
payment_id
refund_amount
refund_type
refund_reason
adjustment_id
```

이미 알고 있는 정보를 버리고
가상의 사용자 질문을 만들어 다시 LLM에 전달하면

```text
불필요한 Intent Classification
+
이미 확정된 Context의 재해석
+
기존 Flow와 새로운 Flow 사이의 연결 관계 불명확
```

문제가 생길 수 있다.

따라서 새로운 사용자 입력을 만드는 방식은 사용하지 않았다.

---

### 결정 2. Refund Service를 별도 Component로 분리하고 Orchestrator에서 연결

부분 환불 처리 책임을
Order Change Service 내부에 직접 넣는 대신
별도의 `Refund Service`로 분리했다.

```text
Order Change
↓
partial_refund_required
↓
Orchestrator
↓
Refund Service
```

Order Change Service는

```text
주문 수량 변경
주문금액 변경
결제 차액 계산
```

까지 담당하고,

Refund Service는

```text
환불 데이터 생성
결제수단 확인
환불 상태 관리
환불계좌 등록
```

을 담당하도록 책임을 분리했다.

두 Component 사이의 연결은
Orchestrator가 담당한다.

이렇게 구성한 이유는
Service가 다른 Service의 실행 순서까지 결정하게 하지 않고,
**기능 간 연결과 실행 순서는 Orchestrator가 관리한다는
기존 Architecture 원칙을 유지하기 위해서이다.**

---

### 결제수단에 따른 Refund 분기

부분 환불이라는 결과는 같아도
실제 다음 단계는 결제수단에 따라 달랐다.

#### 카드

카드는 기존 결제정보가 존재하므로
별도의 환불계좌를 사용자에게 받을 필요가 없다.

```text
partial_refund_required
↓
Refund Service
↓
payment_method = card
↓
Refund 데이터 생성
↓
refund_processing
```

#### 계좌이체

계좌이체는 환불을 진행하기 위해
사용자의 환불계좌 정보가 추가로 필요하다.

```text
partial_refund_required
↓
Refund Service
↓
payment_method = cash
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
```

따라서 동일한 부분 환불 Flow 안에서도
**다음 단계에 필요한 정보가 서로 다르기 때문에 조건 분기**를 적용했다.

---

### Refund State에서 refund_id를 사용

계좌이체 부분 환불에서는
다음 사용자 입력까지 현재 환불 건을 유지해야 했다.

처음에는 주문번호인 `order_id`만으로
환불 데이터를 다시 찾는 방법도 가능했지만,
하나의 주문에서 여러 부분 환불이 발생할 가능성을 고려하면
어떤 환불 건을 처리하고 있는지 모호해질 수 있다.

따라서 Pending State에
현재 환불 건의 `refund_id`를 저장하도록 했다.

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

사용자가 다음 턴에

```text
"국민은행 / 1234567890 / 홍길동"
```

을 입력하면 새로운 Intent로 분류하지 않고,

```text
Pending State
↓
refund_id 확인
↓
해당 Refund 데이터 조회
↓
계좌정보 저장
↓
refund_processing
```

으로 기존 부분 환불 Flow를 이어서 처리한다.

---

### 외부 PG와 내부 환불 상태의 경계

Refund Service를 추가했지만
실제 외부 PG(Payment Gateway) 환불 API가
연결된 것은 아니다.

따라서 Agent가

```text
환불이 완료되었습니다.
```

라고 응답하거나

```text
refund_completed
```

상태를 생성하면
실제로 수행되지 않은 금융 거래를
완료된 사실처럼 기록하게 된다.

현재 MVP에서는 다음과 같이 구분한다.

```text
partial_refund_required
→ 환불 필요 금액이 발생했다는 사실

refund_account_required
→ 환불 진행을 위해 추가 계좌정보가 필요한 상태

refund_processing
→ 내부 환불 절차를 시작한 상태

refund_completed
→ 실제 외부 환불 완료
→ 현재 MVP에서는 생성하지 않음
```

즉 Refund Service가 추가되었더라도
현재 시스템이 보장할 수 있는 범위는
`refund_processing`까지이다.

---

### 최종 변경 구조

주문 수량 변경 Flow는 최종적으로 다음과 같이 확장되었다.

```text
사용자 주문 수량 변경 요청
↓
Intent Classification
↓
quantity_change_type / quantity_value 추출
↓
Orchestrator
↓
주문 / 결제 조회
↓
Order Change Policy
↓
변경 가능 여부 판단
↓
실제 current_quantity 조회
↓
Python Business Logic
├─ target_quantity 계산
├─ new_total_price 계산
└─ Payment Adjustment 계산
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
payment_amount 유지
↓
Payment Adjustment 생성
↓
adjustment_type 확인
│
├─ additional_payment_required
│   ↓
│   추가 결제 필요 상태
│   ↓
│   pending
│
└─ partial_refund_required
    ↓
    Orchestrator
    ↓
    Refund Service
    ↓
    결제수단 확인
    │
    ├─ card
    │   ↓
    │   Refund 데이터 생성
    │   ↓
    │   refund_processing
    │
    └─ cash
        ↓
        Refund 데이터 생성
        ↓
        refund_account_required
        ↓
        Pending State
        ↓
        환불계좌 입력
        ↓
        refund_processing
↓
Final Response
```

---

### 결과

기존 Write Flow의

```text
Policy 판단
≠
사용자 승인
≠
Write Action
```

원칙에 더해,
주문 수량 변경을 구현하면서 다음 책임 경계가 추가되었다.

```text
LLM의 자연어 해석
≠
실제 데이터 기반 계산

주문 데이터 변경
≠
실제 결제 데이터

결제 차액
≠
환불 절차의 진행 상태

Order Change Service
≠
Refund Service
```

또한 기능 간 연결 책임은 다음과 같이 유지했다.

```text
Order Change Service
→ 주문 변경 책임

Refund Service
→ 환불 처리 책임

Orchestrator
→ 두 Component의 실행 순서와 조건 분기 연결
```

이를 통해 외부 결제 시스템이 아직 연결되지 않은 MVP에서도
실제로 발생하지 않은 결제·환불 완료 상태를 생성하지 않으면서,
주문 수량 감소 이후의 부분 환불 절차까지
하나의 사용자 요청에서 End-to-End로 연결할 수 있게 되었다.

현재 추가 결제는

```text
additional_payment_required
→ payment_adjustments
→ pending
```

까지 구현되어 있고,

부분 환불은

```text
partial_refund_required
→ Refund Service
→ refund_processing
```

까지 확장되어 있다.

향후 실제 PG 또는 결제 Tool이 연결되면
각 상태를 기준으로

```text
additional_payment_required
→ 추가 결제 Tool

refund_processing
→ 실제 환불 API
→ 성공 시 refund_completed
```

과 같이 외부 결제 처리 단계로 확장할 수 있다.

이번 구조는 Policy, 수량 계산, Service, State,
사용자 최종 승인, Action-time Recheck,
Write Action, Payment Adjustment, Refund Service,
카드·계좌이체 분기 및 End-to-End 테스트를 통해 검증했다.

전체 Regression Test에서는
**140개 테스트가 모두 통과했다.**

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
    │   │
    │   ├─ order_confirmation
    │   ├─ payment_confirmation
    │   │   ↓
    │   │   Service / Data
    │   │   ↓
    │   │   Policy Layer
    │   │   ↓
    │   │   필요한 경우 Consistency Check
    │   │   ↓
    │   │   Response Mode Selection
    │   │   ├─ fact_summary
    │   │   └─ narrative_guidance
    │   │   ↓
    │   │   Output Prompt + LLM
    │   │   ↓
    │   │   Final Response
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
    │   │   직접 변경 불가 판단
    │   │   ↓
    │   │   취소 후 재주문 안내
    │   │   ↓
    │   │   State 생성 없이 Flow 종료
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
    │       order_status / delivery_status 조회
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
        │       기존 Refund 처리
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
        ├─ delivery_address_change
        │   ↓
        │   Service / Data 조회
        │   ↓
        │   Delivery Address Change Policy
        │   ↓
        │   필요 시 주문 선택
        │   ↓
        │   새 배송지 수집
        │   ↓
        │   pending_data 임시 저장
        │   ↓
        │   사용자 최종 승인
        │   ↓
        │   Action 직전 Policy 재검증
        │   ↓
        │   Delivery Address Change Action
        │   ↓
        │   State 초기화
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
            실제 current_quantity 조회
            ↓
            Python Business Logic
            ├─ target_quantity 계산
            ├─ new_total_price 계산
            └─ Payment Adjustment 계산
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
            payment_amount 유지
            ↓
            Payment Adjustment 생성
            ↓
            차액 유형 분기
            │
            ├─ additional_payment_required
            │   ↓
            │   pending
            │
            └─ partial_refund_required
                ↓
                Orchestrator
                ↓
                Refund Service
                ↓
                결제수단 분기
                │
                ├─ card
                │   ↓
                │   refund_processing
                │
                └─ cash
                    ↓
                    refund_account_required
                    ↓
                    collect_partial_refund_account
                    ↓
                    환불계좌 입력
                    ↓
                    refund_processing
            ↓
            State 초기화
            ↓
            Final Response
```

현재 Architecture에서는 기능의 성격에 따라
모든 요청에 동일한 Component를 적용하지 않는다.

```text
Read Flow
→ 실제 데이터 조회

Guidance Flow
→ Business Policy 안내

Read + Policy Flow
→ 실제 데이터와 Policy 조합

Write Flow
→ 사용자 승인과 Action-time Recheck 이후 실제 데이터 변경
```

또한 현재 Write Flow에서는 다음 원칙을 유지한다.

```text
Policy 판단
≠
사용자 승인
≠
Write Action
```

주문 수량 변경에서는 여기에 다음 책임 경계를 추가했다.

```text
LLM 자연어 해석
≠
실제 데이터 기반 계산

주문 데이터 변경
≠
실제 결제금액 변경

Payment Adjustment
≠
Refund 상태

Order Change Service
≠
Refund Service
```

기능 간 연결은 Orchestrator가 담당한다.

```text
Component A 결과
↓
Orchestrator가 결과 확인
↓
필요한 경우에만 Component B 호출
```

예를 들어:

```text
Order Change
↓
partial_refund_required
↓
Refund Service
```

처럼 앞 단계의 결과가
다음 Component를 실행할 조건이 된다.

이를 기준으로 향후 새로운 CS 기능과 외부 Tool을 연결하더라도
각 Component의 책임과 데이터의 의미를 분리하면서
전체 Orchestration 구조를 확장한다.