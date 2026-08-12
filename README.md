# Online Shopping Mall AI Agent

온라인 쇼핑몰에서 고객의 문의를 이해하고,  
CS 응대와 상품 추천을 처리할 수 있는 AI Agent를 개발하는 프로젝트입니다.

현재는 CS 기능 중 **주문 완료 확인 / 결제 완료 확인 / 주문 취소**를 중심으로
사용자 입력부터 최종 응답까지 End-to-End 처리 흐름을 구현하고 있습니다.

---

## 1. Project Goal

단순히 LLM에게 사용자 질문을 전달해 답변을 생성하는 것이 아니라,

```text
사용자 질문
→ 질문 이해
→ Intent 판단
→ 필요한 기능 선택
→ 데이터 조회
→ Policy 판단
→ 결과 검증
→ 응답 방식 결정
→ 최종 응답 생성
```
까지 이어지는 전체 Chatbot Flow를 설계하고 구현하는 것을 목표로 합니다.

최종적으로 다음 두 기능을 지원하는 AI Agent를 개발합니다.

- 고객 CS 응대
- 고객 조건·상황·스타일에 따른 상품 추천

---

## 2. My Role

### Chatbot Flow / Agent Logic / Orchestration 설계 및 구현

사용자의 질문이 들어온 이후 최종 답변이 생성될 때까지의
전체 처리 흐름을 설계하고 각 Component를 연결하는 역할을 담당합니다.

주요 담당 영역:

- Intent Classification 및 Routing 구조 설계
- CS / 상품추천 처리 흐름 설계
- Component 간 Input / Output 정의
- 멀티턴 대화를 위한 State 관리
- Service / Policy / LLM 호출 순서 설계
- Policy 기반 Business Rule 적용
- 기능 간 Orchestration 구현
- End-to-End 테스트 및 개선

---

## 3. Current Implementation

현재 구현된 CS 기능은 다음과 같습니다.

### 주문 완료 확인

```text
사용자 질문
→ Intent Classification
→ 주문 조회
→ Order Completion Policy
→ 주문-결제 Consistency 검증
→ Response Mode 결정
→ 최종 응답
```

### 결제 완료 확인

```text
사용자 질문
→ Intent Classification
→ 결제 조회
→ Payment Completion Policy
→ 주문-결제 Consistency 검증
→ Response Mode 결정
→ 최종 응답
```

주문이 여러 건 존재하는 경우에는
Agent가 임의로 주문을 선택하지 않고 사용자에게 주문번호를 추가로 확인합니다.

### 주문 취소

```text
사용자 질문
→ Intent Classification
→ 주문 조회
→ Order Cancel Policy
→ 취소 가능 여부 판단
→ 사용자 최종 승인
→ 주문 / 결제 취소 Action
→ 결제 방식에 따른 Refund Flow
→ 최종 응답
```

주문 취소처럼 실제 데이터를 변경하는 기능은 
Policy에서 취소 가능하다고 판단되더라도 바로 실행하지 않습니다.

사용자의 명확한 최종 승인을 확인한 이후에만
Write Action을 실행합니다.

카드 결제는 취소 후 refund_processing 상태로 전환하고,
계좌이체는 환불계좌 정보를 추가로 입력받은 뒤
refund_processing 상태로 전환합니다.

## 4. Current Architecture

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

### 역할 분리

**Service / Data**
- 고객의 실제 주문·결제 데이터 조회

**Policy**
- 조회된 상태값의 업무적 의미 판정

**Consistency Policy**
- 주문 상태와 결제 상태 간 불일치 검증

**Orchestrator**
- 다음 처리 단계와 응답 방식을 결정

**Output LLM**
- 확정된 사실과 Policy를 고객이 이해하기 쉬운 자연어로 표현

LLM은 주문 상태나 쇼핑몰 Policy 자체를 임의로 판단하지 않습니다.

---

## 5. Key Design Decisions

### Policy와 LLM의 책임 분리

업무 상태 판정은 Python Business Rule에서 수행하고,
LLM은 확정된 결과를 표현하는 역할만 담당합니다.

```text
Data
→ Policy 판단
→ 확정 Result
→ LLM 표현
```

### 주문과 결제의 Consistency 검증

개별 상태만 정상이라고 해서 최종적으로 정상 처리된 것으로 판단하지 않습니다.

예:

```text
order_status = order_completed
payment_status = payment_failed

→ needs_review
```

이 경우 정상 완료 응답을 차단하고 추가 확인이 필요한 상태로 처리합니다.

### Hybrid Response Generation

모든 메시지를 LLM으로 생성하지 않습니다.

```text
주문번호 선택 요청 등 Flow Control
→ Python

확정된 고객 결과 설명
→ Output Prompt + LLM
```

### 응답 형식 분리

객관적인 조회 결과와 설명이 필요한 상황의 출력 형식을 분리했습니다.

```text
fact_summary
→ 주문/결제 상태 등 객관적인 정보 전달

narrative_guidance
→ Policy, 예외, 데이터 불일치 설명
```

---

## 6. Project Structure

```text
app/
├── data/          # 테스트용 서비스 데이터
├── policies/      # Business Rule / Policy
├── routers/       # FastAPI Endpoint
├── schemas/       # Request / Response Schema
├── services/      # Service, LLM, State, Orchestration
└── main.py

docs/
├── policies/                      # Policy 정의 문서
├── order_confirmation_e2e.md
├── payment_confirmation_e2e.md
└── output_response_design.md

tests/
├── test_order_confirmation_flow.py
├── test_payment_confirmation_flow.py
└── test_order_payment_consistency.py
```

---

## 7. Tech Stack

- Python
- FastAPI
- LangChain
- OpenAI LLM
- Pydantic
- pytest
- Git / GitHub

---

## 8. How to Run

### 패키지 설치

```bash
pip install -r requirements.txt
```

### 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 OpenAI API Key를 설정합니다.

```text
OPENAI_API_KEY=your_api_key
```

`.env` 파일은 Git에 업로드하지 않습니다.

### FastAPI 실행

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## 9. Test

전체 테스트 실행:

```bash
python -m pytest -v
```

현재 테스트에서는 다음 흐름을 검증합니다.

- 주문 완료 확인 멀티턴 Flow
- 결제 완료 확인 멀티턴 Flow
- 주문 완료 + 결제 실패 상태의 Consistency Routing
- 주문 실패 + 결제 완료 상태의 Consistency Routing
- 주문 취소 가능 여부 Policy
- 사용자 승인 / 거절 / 불명확 응답 처리
- 카드 주문 취소 Action
- 계좌이체 주문 취소 및 환불계좌 수집
- 주문 취소 Multi-turn Flow
- FastAPI Swagger 기반 주문 취소 End-to-End Flow

현재 전체 테스트 28개가 통과합니다.

---

## 10. Documentation

상세 설계는 `docs/`에서 확인할 수 있습니다.

- `docs/output_response_design.md`
  - Policy / Consistency / Output Response 구조

- `docs/order_confirmation_e2e.md`
  - 주문 완료 확인 End-to-End 처리 흐름

- `docs/payment_confirmation_e2e.md`
  - 결제 완료 확인 End-to-End 처리 흐름

- `docs/policies/`
  - 주문 / 결제 / Consistency Policy 정의

---

## 11. Next Steps

현재 CS의 주문·결제 확인 기능을 기준으로 전체 Agent 구조를 검증하고 있습니다.

향후 다음 영역으로 확장할 예정입니다.

- 주문/결제 CS 세부 기능 확장
- 배송 / 교환 / 환불 / 상품정보 CS
- 상품 추천 Flow
- 실제 DB 연동
- State 관리 구조 확장
- 전체 End-to-End 테스트 확대