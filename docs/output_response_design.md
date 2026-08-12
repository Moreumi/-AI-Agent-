# CS Output Response 설계

## 1. 목적

CS 기능에서 Service / DB / Policy를 통해 확인된 결과를
고객이 이해하기 쉬운 최종 자연어 응답으로 변환하기 위한 구조를 정의한다.

LLM은 고객의 주문 상태나 쇼핑몰 정책을 새롭게 판단하지 않는다.

최종 응답 생성에 필요한 판단은 앞 단계에서 완료하고,
Output LLM은 확인된 사실과 정책을 고객 친화적인 표현으로 전달하는 역할을 담당한다.

---

## 2. 전체 처리 구조

```text
사용자 질문
↓
Intent Classification
↓
Orchestrator
↓
Service / DB 조회
↓
Policy 판단
↓
주문-결제 Consistency 검증
↓
확정 Result
↓
Orchestrator가 response_mode 결정
↓
공통 CS Output Prompt
↓
LLM
↓
최종 고객 응답
```

---

## 3. Component 역할

### Service / DB

고객의 실제 주문 및 결제 데이터를 조회한다.

예:

- order_id
- order_status
- order_date
- total_price
- payment_status
- payment_method
- payment_amount
- payment_date

---

### Policy

조회된 상태값을 기준으로 업무적 의미를 판정한다.

예:

```text
order_status = order_completed
→ judgment = completed
```

```text
payment_status = payment_completed
→ judgment = completed
```

Policy 판정은 LLM이 아니라 Python Business Rule에서 수행한다.

---

### Consistency Policy

주문 상태와 결제 상태가 서로 일관되는지 추가로 검증한다.

예:

```text
order_completed + payment_completed
→ consistent_completed
```

```text
order_completed + payment_failed
→ needs_review
```

개별 상태는 정상으로 보이더라도
관련 데이터와 불일치하는 경우 정상 응답을 바로 생성하지 않는다.

---

### Orchestrator

확정된 결과를 기준으로 어떤 응답 방식을 사용할지 결정한다.

현재 사용하는 response_mode는 다음과 같다.

#### fact_summary

객관적인 조회 결과를 전달할 때 사용한다.

적용 예:

- 주문 완료 확인
- 결제 완료 확인

형식:

```text
핵심 결과

- 항목명: 값
- 항목명: 값

고객 응대 마무리
```

#### narrative_guidance

정책, 예외, 데이터 불일치 등 설명이 필요한 상황에서 사용한다.

적용 예:

- 주문 상태와 결제 상태 불일치
- 향후 환불/교환 정책 안내 등

형식:

```text
핵심 답변
→ 필요한 설명
→ 필요한 경우 후속 행동
→ 고객 응대 마무리
```

---

## 4. Hybrid Response Generation

모든 응답을 LLM으로 생성하지 않는다.

### Python 응답을 사용하는 경우

대화 흐름을 제어하기 위한 메시지에는
결정적인 Python 응답을 사용한다.

예:

- 확인할 주문번호 요청
- 여러 주문 중 선택 요청
- 잘못된 주문번호 재입력 요청
- 조회 대상 없음

예:

```text
"확인할 주문번호를 입력해주세요."
```

---

### Output LLM을 사용하는 경우

Service / Policy에서 결과가 확정된 후
고객에게 자연스럽게 설명해야 하는 최종 응답에 사용한다.

즉 현재 구조는 다음과 같다.

```text
Flow Control
→ Python

Final Customer Response
→ Output Prompt + LLM
```

---

## 5. Output Prompt Input / Output

### Input

#### user_input

고객의 원래 질문

#### sub_intent

현재 처리 중인 CS 기능

예:

- order_confirmation
- payment_confirmation

#### response_mode

Orchestrator가 결정한 응답 형식

예:

- fact_summary
- narrative_guidance

#### result

Service / Policy에서 확정된 결과

예:

```json
{
  "result_type": "success",
  "judgment": "completed",
  "order_id": 10002,
  "order_status": "order_completed",
  "order_date": "2026-08-10",
  "total_price": 32000
}
```

#### policy_context

현재 응답에 필요한 쇼핑몰 운영 Policy

---

### Output

```text
response: str
```

사용자에게 최종적으로 표시되는 자연어 응답이다.

---

## 6. 사실 사용 우선순위

최종 응답에서 사용할 사실의 우선순위는 다음과 같다.

```text
1. Service / DB / Tool에서 조회된 실제 고객 데이터
2. 프로젝트에서 확정한 쇼핑몰 Policy
3. LLM 일반 지식
```

단, LLM 일반 지식은 사실 판단의 근거로 사용하지 않는다.

LLM 일반 지식은 문장을 자연스럽게 표현하는 데만 사용한다.

---

## 7. 금지 원칙

Output LLM은 다음 행동을 하지 않는다.

- 제공되지 않은 주문 상태 추측
- 제공되지 않은 결제 상태 추측
- 실패 원인 생성
- 환불 여부 임의 판단
- 처리 예정일 생성
- 쇼핑몰 정책 생성
- 확인된 주문번호, 금액, 날짜 등의 값 변경
- 데이터 불일치 상태에서 어느 한쪽을 임의로 정상으로 선택

---

## 8. 주문 완료 확인 응답 예시

### 정상 상태

```text
주문이 정상적으로 접수되었습니다.

- 주문 번호: 10002
- 주문 상태: 완료
- 주문 날짜: 2026년 8월 10일
- 주문 금액: 32,000원

추가로 궁금한 점이 있으시면 언제든지 문의해 주세요.
```

response_mode:

```text
fact_summary
```

---

## 9. 결제 완료 확인 응답 예시

### 정상 상태

```text
결제가 정상적으로 완료되었습니다.

- 주문 번호: 10002
- 결제 상태: 완료
- 결제 수단: 카드
- 결제 금액: 32,000원
- 결제 날짜: 2026년 8월 10일

추가로 궁금한 점이 있으시면 언제든지 문의해 주세요.
```

response_mode:

```text
fact_summary
```

---

## 10. 주문-결제 불일치 응답 예시

상태:

```text
order_status = order_completed
payment_status = payment_failed
```

Consistency 판정:

```text
needs_review
```

최종 응답 예:

```text
주문은 정상적으로 접수되었습니다.

다만 결제 상태가 실패로 확인되어 추가 확인이 필요합니다.
결제 문제에 대해서는 고객센터 또는 상담원을 통해 확인해 주세요.

추가로 궁금한 점이 있으시면 언제든지 문의해 주세요.
```

response_mode:

```text
narrative_guidance
```

---

## 11. 현재 설계의 핵심 결정

### 결정 1

LLM은 업무 상태를 판단하지 않고 표현만 담당한다.

### 결정 2

쇼핑몰 Policy는 Prompt에 임의로 작성하지 않고 별도의 Policy Layer에서 관리한다.

### 결정 3

주문 완료와 결제 완료는 별도의 Policy로 판단한다.

### 결정 4

주문과 결제 상태가 서로 모순될 수 있으므로
Consistency Policy를 추가한다.

### 결정 5

객관적인 조회 결과와 설명이 필요한 답변의 출력 형식을 분리한다.

```text
객관적인 조회 결과
→ fact_summary

정책 / 예외 / 불일치 설명
→ narrative_guidance
```

### 결정 6

대화 흐름 제어 메시지는 Python,
최종 고객 응답은 Output LLM을 사용하는 Hybrid 구조를 적용한다.