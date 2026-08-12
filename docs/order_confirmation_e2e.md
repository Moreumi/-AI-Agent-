# 주문 완료 확인 기능 End-to-End 검증 기록

## 1. 검증 대상

CS > 주문/결제 > 주문 완료 확인 기능

사용자가 자신의 주문이 정상적으로 완료되었는지 확인하는 흐름을 검증한다.

---

## 2. 내부 로직 테스트

### 테스트 시나리오

1턴 사용자 입력

"내 주문 제대로 들어갔어?"

- customer_id: 1
- 주문번호는 입력하지 않음
- 해당 고객의 주문이 여러 건 존재

### 예상 처리

- 주문 완료 확인 기능으로 Routing
- 고객의 주문 목록 조회
- 여러 주문이 존재하므로 주문 선택 요청
- State에 다음 정보 저장
  - pending_action = order_confirmation
  - candidate_orders

2턴 사용자 입력

"10002번"

### 예상 처리

- 새로운 Intent Classification을 수행하지 않고 기존 State 확인
- 입력에서 주문번호 10002 추출
- candidate_orders에 포함된 주문인지 확인
- 주문번호 10002의 주문 상태 조회
- 주문 완료 응답 생성
- 처리 완료 후 State 초기화

### 결과

정상 동작 확인

---

## 3. 서버 API 테스트

### Health Check

GET /health/

결과

- HTTP Status Code: 200
- Response:

```json
{
  "status": "ok"
}
```

FastAPI 서버와 Router가 정상적으로 연결되어 있음을 확인했다.

### Chat API - 1턴

POST /chat/

Request:

```json
{
  "message": "내 주문 제대로 들어갔어?",
  "customer_id": 1
}
```

결과

- HTTP Status Code: 200
- route: order_confirmation
- 여러 주문 중 확인할 주문을 선택하도록 요청하는 응답 반환

### Chat API - 2턴

POST /chat/

Request:

```json
{
  "message": "10002번",
  "customer_id": 1
}
```

결과

- HTTP Status Code: 200
- route: order_confirmation
- 주문번호 10002가 정상적으로 완료되었다는 응답 반환
- 이전 요청에서 저장한 State가 다음 HTTP 요청에서도 정상적으로 사용됨

---

## 4. 확인된 End-to-End 처리 흐름

사용자 입력  
→ FastAPI POST /chat/  
→ Chat Router  
→ Orchestrator  
→ LLM Intent Classification  
→ 주문 완료 확인 Service  
→ 주문 데이터 조회  
→ 정보가 부족한 경우 State 저장  
→ 추가 사용자 입력  
→ State 기반 후속 처리  
→ 주문 확인  
→ 응답 생성  
→ ChatResponse 반환

---

## 5. 검증 결과

주문 완료 확인 기능에 대해 다음 두 단계의 검증을 완료했다.

1. Python 내부에서 챗봇 처리 로직 및 멀티턴 State 동작 확인
2. FastAPI 서버 환경에서 HTTP 요청·응답 및 멀티턴 흐름 확인

따라서 주문 완료 확인 기능의 현재 MVP 범위에 대한 End-to-End 연결이 정상적으로 동작함을 확인했다.

---

## 6. pytest 자동 테스트

### 테스트 파일

`tests/test_order_confirmation_flow.py`

### 검증 항목

1턴에서 다음 내용을 자동 검증한다.

- `order_confirmation` 경로로 Routing 되었는지
- 여러 주문이 존재하여 `need_order_selection` 결과가 발생했는지
- `pending_action`이 `order_confirmation`으로 저장되었는지
- 선택 가능한 주문번호가 10001, 10002인지

2턴에서 다음 내용을 자동 검증한다.

- 기존 State를 이용해 주문 확인 흐름이 이어지는지
- 주문번호 10002 조회가 성공했는지
- `order_status`가 `order_completed`인지
- 처리 완료 후 State가 초기화되었는지

### 실행 명령어

```bash
python -m pytest -v
```

### 실행 결과

```text
tests/test_order_confirmation_flow.py::test_order_confirmation_multiturn_flow PASSED [100%]

1 passed in 2.81s
```

### 최종 결과

주문 완료 확인 멀티턴 흐름에 대한 pytest 자동 테스트가 정상적으로 통과하였다.

---

## 현재 구현 구조 업데이트

초기 주문 완료 확인 기능은 주문 데이터를 조회한 뒤
Python 고정 응답을 반환하는 구조로 구현하였다.

이후 Policy Layer와 공통 Output Response 구조를 추가하여
현재는 다음 흐름으로 동작한다.

```text
사용자 질문
↓
Intent Classification
↓
order_confirmation
↓
주문 데이터 조회
↓
Order Completion Policy
↓
judgment 생성
↓
Order-Payment Consistency 검사
↓
Orchestrator 응답 방식 결정
↓
최종 응답
```

### 주문 완료 Policy

현재 MVP에서는 다음 기준으로 주문 상태를 판단한다.

```text
order_completed
→ completed

order_canceled
→ canceled

order_failed
→ failed

정의되지 않은 상태
→ needs_review
```

LLM이 주문 상태를 직접 해석하지 않고,
Python Business Rule에서 먼저 `judgment`를 확정한다.

### 주문-결제 Consistency 검증

주문 자체가 완료 상태라도 연결된 결제 상태와 모순되는 경우
정상 주문 완료 응답을 바로 생성하지 않는다.

예:

```text
order_status = order_completed
payment_status = payment_failed

↓
consistency_judgment = needs_review
```

이 경우 정상 조회 결과용 `fact_summary`를 사용하지 않고
설명이 필요한 `narrative_guidance` 응답으로 분기한다.

### Response Mode

정상적인 주문 완료 확인:

```text
response_mode = fact_summary
```

출력 예:

```text
주문이 정상적으로 접수되었습니다.

- 주문 번호: 10002
- 주문 상태: 완료
- 주문 날짜: 2026년 8월 10일
- 주문 금액: 32,000원

추가로 궁금한 점이 있으시면 언제든지 문의해 주세요.
```

주문과 결제 상태가 불일치하는 경우:

```text
response_mode = narrative_guidance
```

### Hybrid Response

주문 선택 등 대화 흐름을 제어하는 응답은
결정적인 Python 응답을 유지한다.

```text
주문 선택 요청
→ Python

확정된 주문 결과 설명
→ Output Prompt + LLM
```

이를 통해 LLM은 업무 상태를 판단하지 않고,
확정된 결과를 고객 친화적으로 표현하는 역할만 담당한다.