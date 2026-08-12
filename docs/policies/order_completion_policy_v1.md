# 주문 완료 확인 Policy v1

## 1. Policy 기본 정보

- policy_id: `order_completion_check_v1`
- policy_category: `order_payment`
- policy_name: `order_completion_check`
- 적용 기능: CS > 주문/결제 > 주문 완료 확인
- 정책 상태: MVP v1

---

## 2. 목적

사용자가 자신의 주문이 정상적으로 접수되었는지 문의했을 때,
AI Agent가 주문 데이터를 기준으로 주문 완료 여부를 일관되게 판정하기 위한 정책이다.

LLM이 주문 상태를 임의로 판단하지 않으며,
Service / DB에서 조회된 데이터와 본 Policy를 이용해 판정한다.

---

## 3. 주문 완료의 정의

현재 MVP에서는 다음과 같이 정의한다.

> `order_status = order_completed`인 경우
> 주문 요청이 시스템에 정상적으로 접수된 주문으로 판단한다.

배송 상태는 주문 완료 여부와 별도로 관리한다.

예:

`order_status = order_completed`
`delivery_status = shipping`

인 경우에도 주문 자체는 정상적으로 완료된 것으로 판단한다.

---

## 4. 조회에 필요한 데이터

### 필수 식별 정보

- customer_id

### 주문 식별 정보

- order_id

### 주문 상태 및 응답 정보

- order_status
- order_date
- total_price
- delivery_status

---

## 5. 조회 대상 결정 규칙

### 사용자가 order_id를 입력한 경우

해당 `order_id`가 현재 `customer_id`의 주문인지 확인한다.

해당 고객의 주문이 아니라면 주문 정보를 제공하지 않고 `not_found`로 처리한다.

### 사용자가 order_id를 입력하지 않은 경우

고객의 주문이 없는 경우:

- `not_found`

고객의 주문이 1건인 경우:

- 해당 주문을 자동으로 조회

고객의 주문이 여러 건인 경우:

- Agent가 임의로 주문을 선택하지 않음
- 사용자에게 확인할 주문번호를 요청
- `selection_required` 상태로 처리
- candidate_orders를 State에 저장

---

## 6. 상태별 판정 규칙

### order_status = order_completed

판정:

`completed`

의미:

주문이 정상적으로 접수되었다.

Agent 처리:

- 주문 완료 사실 안내
- 필요한 경우 주문번호, 주문일, 주문금액 등 확인된 정보 제공

---

### order_status = order_canceled

판정:

`canceled`

의미:

현재 해당 주문은 취소된 상태이다.

Agent 처리:

- 현재 주문이 취소 상태임을 우선 안내
- 과거에 주문이 정상 완료되었는지는 현재 데이터만으로 추론하지 않음

---

### order_status = order_failed

판정:

`failed`

의미:

주문이 정상적으로 완료되지 않았다.

Agent 처리:

- 주문이 정상적으로 완료되지 않았음을 안내
- 확인되지 않은 실패 원인은 추측하지 않음

---

### 주문 데이터 없음

판정:

`not_found`

의미:

현재 고객 정보와 조건으로 확인 가능한 주문이 없다.

Agent 처리:

- 확인 가능한 주문이 없음을 안내
- 존재하지 않는 주문 정보를 생성하지 않음

---

### 정의되지 않은 order_status 또는 필수 데이터 이상

판정:

`needs_review`

예:

- 정의되지 않은 order_status
- 주문 데이터의 필수 필드 누락
- 정상적인 자동 판정이 어려운 데이터 상태

Agent 처리:

- 정상/실패 여부를 임의로 결정하지 않음
- 재조회 또는 상담원 확인이 필요한 상태로 처리

---

## 7. 고객에게 공개 가능한 정보

현재 MVP에서 주문 완료 확인 응답에 사용할 수 있는 정보는 다음과 같다.

- order_id
- order_status
- order_date
- total_price
- 필요한 경우 delivery_status

고객 질문과 관계없는 정보는 불필요하게 노출하지 않는다.

---

## 8. 금지 규칙

AI Agent는 다음 행동을 하지 않는다.

- `order_id`가 존재한다는 이유만으로 주문 완료로 판단하지 않는다.
- `order_canceled` 상태에서 과거 주문 완료 여부를 임의로 추론하지 않는다.
- `order_failed`의 실패 원인을 데이터 없이 생성하지 않는다.
- 배송 예정일 등 조회되지 않은 정보를 생성하지 않는다.
- 다른 customer_id에 속한 주문 정보를 제공하지 않는다.
- 정의되지 않은 상태를 임의로 completed 또는 failed로 분류하지 않는다.

---

## 9. 현재 MVP의 한계

현재 `order_status`는 다음 세 상태만 사용한다.

- `order_completed`
- `order_canceled`
- `order_failed`

향후 실제 쇼핑몰 시스템과 연동할 경우 다음 상태가 추가될 수 있다.

예:

- pending
- confirmed
- preparing
- shipped
- delivered

새로운 상태가 추가되면 본 Policy의 상태별 판정 규칙도 함께 수정해야 한다.

또한 현재는 주문 상태 이력이 존재하지 않으므로,
취소된 주문이 과거에 정상적으로 완료되었던 주문인지 여부는 판정하지 않는다.

---

## 10. 다른 Policy와의 관계

본 Policy는 주문 자체의 완료 여부만 판정한다.

결제 완료 여부는 별도의:

`payment_completion_check`

Policy에서 판정한다.

주문 상태와 결제 상태가 서로 모순되는 경우에는 별도의:

`order_payment_consistency`

Policy에서 처리한다.

즉 역할을 다음과 같이 분리한다.

`order_completion_check`
→ 주문 상태 판정

`payment_completion_check`
→ 결제 상태 판정

`order_payment_consistency`
→ 주문·결제 상태 간 불일치 판정