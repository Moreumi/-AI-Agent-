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

또한 주문번호가 부족한 경우에는 State에 현재 처리 중인 기능과 후보 주문을 저장하고, 다음 사용자 입력에서 이어서 처리하도록 했다.

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
단일 함수 수준이 아니라 멀티턴을 포함한 End-to-End 챗봇 Flow로 동작하게 되었다.

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

이 판단까지 LLM에게 맡기면 동일한 상태에서도 판단이 달라질 가능성이 있고,  
쇼핑몰 정책과 LLM의 일반 지식이 섞일 수 있다.

### 결정

주문·결제 상태의 업무적 판단을 담당하는 `Policy Layer`를 별도로 분리했다.

```text
order_status
→ Order Completion Policy
→ judgment

payment_status
→ Payment Completion Policy
→ judgment
```

LLM은 상태를 판단하지 않고,  
Policy에서 이미 확정된 결과를 고객에게 자연스럽게 설명하는 역할만 담당하도록 했다.

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

이를 통해 쇼핑몰의 Business Rule과 자연어 생성 책임을 분리할 수 있게 되었다.

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
정책이나 예외 상황에 대한 설명이 동일한 응답 방식으로 처리될 수 있었다.

### 문제

응답의 목적에 따라 적합한 표현 방식이 달랐다.

예를 들어 주문 완료 여부처럼 객관적인 정보를 확인하는 질문은

```text
주문 상태
주문 날짜
주문 금액
```

등을 빠르게 확인할 수 있는 구조가 적합하다.

반면 주문과 결제 상태가 서로 다른 경우에는  
단순 정보 나열보다 상황 설명과 후속 안내가 필요하다.

### 결정

Orchestrator가 상황에 따라 `response_mode`를 명시적으로 선택하도록 했다.

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

또한 **어떤 응답 방식을 사용할지 LLM이 임의로 결정하지 않고 Orchestrator가 결정**하도록 하여, Agent의 처리 흐름을 명시적으로 제어할 수 있게 되었다.

---

## Current Architecture

현재까지의 구조는 다음과 같다.

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

앞으로 Architecture 수준의 변경이 발생하면  
동일하게 **초기 구조 → 문제 → 결정 → 변경된 구조 → 결과** 기준으로 이 문서에 추가한다.