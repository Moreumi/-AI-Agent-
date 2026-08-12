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

현재 구현된 CS Flow는 다음과 같다.

```text
User
↓
FastAPI Router
↓
Intent Classification
↓
Orchestrator
↓
Service / Data
↓
Policy Layer
↓
Order-Payment Consistency Check
↓
Response Mode Selection
├─ fact_summary
└─ narrative_guidance
↓
Output Prompt + LLM
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
```

분류 결과는 Orchestrator가 다음 처리 경로를 결정하는 데 사용한다.

---

### Orchestrator

전체 Agent Flow의 중심 Component이다.

주요 역할은 다음과 같다.

- Intent 결과에 따른 Routing
- 필요한 정보가 충분한지 확인
- State 확인
- Service 호출
- Policy 결과 확인
- Consistency 결과 확인
- Response Mode 결정
- 최종 응답 생성 Component 호출

즉 개별 기능을 직접 수행하기보다
**각 Component를 어떤 순서로 호출할지 결정하는 역할**을 담당한다.

---

### State

멀티턴 대화에서 이전 처리 상태를 유지한다.

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

현재 MVP에서는 Python Dictionary 기반 State를 사용한다.

---

### Service / Data

고객의 실제 주문·결제 데이터를 조회하는 역할을 담당한다.

예:

```text
order_id
order_status
order_date
total_price

payment_status
payment_method
payment_amount
payment_date
```

Service는 데이터를 조회하고
Policy 판단에 필요한 결과를 반환한다.

---

### Policy Layer

조회된 상태값의 업무적 의미를 판단한다.

예:

```text
order_status = order_completed
↓
Order Completion Policy
↓
judgment = completed
```

```text
payment_status = payment_completed
↓
Payment Completion Policy
↓
judgment = completed
```

Business Rule은 LLM이 아니라
Python 코드에서 명시적으로 관리한다.

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
- 쇼핑몰 정책
- 데이터 불일치 해결 방법

즉 현재 구조에서 LLM은

```text
판단
```

보다

```text
표현
```

을 담당한다.

---

## 4. Multi-turn Flow

정보가 부족한 경우 바로 Service를 호출하지 않는다.

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
→ Consistency
→ Response
```

정보가 부족한 경우:

```text
State 저장
→ 추가 질문
→ 다음 사용자 입력
→ State 복원
→ 기존 Flow 계속 처리
```

---

## 5. 현재 구현 범위

현재 End-to-End로 구현된 기능은 다음과 같다.

```text
CS
├─ 주문/결제
│  ├─ 주문 완료 확인
│  └─ 결제 완료 확인
```

지원되는 주요 처리 방식:

- Intent Classification
- Routing
- 주문/결제 데이터 조회
- 멀티턴 주문 선택
- State 관리
- Policy 판단
- 주문-결제 Consistency 검증
- Response Mode 선택
- LLM 기반 최종 응답 생성
- End-to-End 테스트

---

## 6. 현재 Architecture의 핵심 원칙

### 판단과 표현을 분리한다

```text
Business 판단
→ Python / Policy

자연어 표현
→ LLM
```

### Agent 흐름은 Orchestrator가 제어한다

LLM이 임의로 다음 행동을 선택하기보다
Orchestrator가 명시적인 Routing 기준에 따라
다음 Component를 호출한다.

### 관련 데이터의 일관성을 확인한다

하나의 데이터만 보고 최종 결과를 확정하지 않고,
관련된 주문과 결제 상태를 함께 검증한다.

### 정보가 부족하면 추가 질문한다

필요한 정보가 없는 상태에서 추측하지 않고
State를 유지한 채 사용자에게 추가 정보를 요청한다.

---

## 7. 향후 확장 방향

현재 Architecture를 기준으로 다음 기능을 확장할 예정이다.

```text
CS
├─ 회원/계정
├─ 주문/결제
├─ 교환/환불
├─ 배송
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