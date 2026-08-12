# 결제 완료 확인 Policy v1

## 1. Policy 기본 정보

- policy_id: `payment_completion_check_v1`
- policy_category: `order_payment`
- policy_name: `payment_completion_check`
- 적용 기능: CS > 주문/결제 > 결제 완료 확인
- 정책 상태: MVP v1

---

## 2. 목적

사용자가 자신의 주문에 대한 결제가 정상적으로 완료되었는지 문의했을 때,
AI Agent가 결제 데이터를 기준으로 결제 완료 여부를 일관되게 판정하기 위한 정책이다.

LLM이 결제 상태를 임의로 판단하지 않으며,
Service / DB에서 조회된 데이터와 본 Policy를 이용해 판정한다.

---

## 3. 결제 완료의 정의

현재 MVP에서는 다음과 같이 정의한다.

> `payment_status = payment_completed`인 경우
> 해당 주문의 결제가 정상적으로 완료된 것으로 판단한다.

결제 완료 여부와 주문 완료 여부는 별도로 판단한다.

예:

`order_status = order_completed`
`payment_status = payment_failed`

인 경우 주문 데이터는 존재하더라도
결제가 정상적으로 완료된 것으로 판단하지 않는다.

이와 같은 주문·결제 상태 간 불일치는 별도의
`order_payment_consistency` Policy에서 처리한다.

---

## 4. 조회에 필요한 데이터

### 고객 및 주문 식별 정보

- customer_id
- order_id

### 결제 정보

- payment_id
- payment_status
- payment_method
- payment_amount
- payment_date

### 주문 확인을 위해 사용하는 정보

- order_date
- total_price

---

## 5. 조회 대상 결정 규칙

### 사용자가 order_id를 입력한 경우

먼저 해당 `order_id`가 현재 `customer_id`의 주문인지 확인한다.

해당 고객의 주문이 아니라면 결제 정보를 제공하지 않고
`not_found`로 처리한다.

주문 소유 관계가 확인된 후
해당 `order_id`와 연결된 결제 데이터를 조회한다.

---

### 사용자가 order_id를 입력하지 않은 경우

고객의 주문이 없는 경우:

- `not_found`

고객의 주문이 1건인 경우:

- 해당 주문을 자동으로 선택
- 연결된 결제 데이터를 조회

고객의 주문이 여러 건인 경우:

- Agent가 임의로 주문을 선택하지 않음
- 사용자에게 결제를 확인할 주문번호를 요청
- `selection_required` 상태로 처리
- candidate_orders를 State에 저장

---

## 6. 상태별 판정 규칙

### payment_status = payment_completed

판정:

`completed`

의미:

해당 주문의 결제가 정상적으로 완료되었다.

Agent 처리:

- 결제 완료 사실 안내
- 필요한 경우 주문번호, 결제금액, 결제수단, 결제일 등
  확인된 정보 제공

---

### payment_status = payment_failed

판정:

`failed`

의미:

결제가 정상적으로 완료되지 않았다.

Agent 처리:

- 결제가 완료되지 않았음을 안내
- 확인되지 않은 결제 실패 원인은 추측하지 않음
- 필요 시 후속 결제 절차가 존재하는 경우 해당 Policy에 따라 안내

---

### payment_status = payment_canceled

판정:

`canceled`

의미:

현재 해당 결제는 취소된 상태이다.

Agent 처리:

- 현재 결제가 취소 상태임을 우선 안내
- 결제가 과거에 정상 승인되었다가 취소되었는지는
  현재 데이터만으로 추론하지 않음
- 환불 여부 역시 별도의 환불 데이터나 Policy 없이 추론하지 않음

---

### 결제 데이터 없음

판정:

`not_found`

의미:

선택된 주문과 연결된 결제 정보를 확인할 수 없다.

Agent 처리:

- 결제 정보를 확인할 수 없음을 안내
- 결제 성공 또는 실패 여부를 임의로 판단하지 않음

---

### 정의되지 않은 payment_status 또는 필수 데이터 이상

판정:

`needs_review`

예:

- 정의되지 않은 payment_status
- payment_id 누락
- payment_status 누락
- 결제 데이터의 구조가 정상적인 자동 판정을 수행하기 어려운 상태

Agent 처리:

- 결제 완료/실패 여부를 임의로 결정하지 않음
- 재조회 또는 상담원 확인이 필요한 상태로 처리

---

## 7. 고객에게 공개 가능한 정보

현재 MVP에서 결제 완료 확인 응답에 사용할 수 있는 정보는 다음과 같다.

- order_id
- payment_status
- payment_method
- payment_amount
- payment_date

필요한 경우 주문 식별을 위해 다음 정보를 사용할 수 있다.

- order_date
- total_price

고객 질문과 관계없는 정보는 불필요하게 노출하지 않는다.

---

## 8. 금지 규칙

AI Agent는 다음 행동을 하지 않는다.

- 주문 데이터가 존재한다는 이유만으로 결제 완료로 판단하지 않는다.
- `payment_id`가 존재한다는 이유만으로 결제 완료로 판단하지 않는다.
- `payment_failed`의 실패 원인을 데이터 없이 생성하지 않는다.
- `payment_canceled` 상태에서 과거 결제 승인 여부를 임의로 추론하지 않는다.
- 결제 취소를 환불 완료와 동일하게 판단하지 않는다.
- 환불 여부 또는 환불 일정을 데이터 없이 생성하지 않는다.
- 다른 customer_id에 속한 주문의 결제 정보를 제공하지 않는다.
- 정의되지 않은 상태를 임의로 completed 또는 failed로 분류하지 않는다.
- 결제수단별 정책이 제공되지 않은 경우 임의의 처리 기준을 생성하지 않는다.

---

## 9. 현재 MVP의 한계

현재 `payment_status`는 다음 세 상태만 사용한다.

- `payment_completed`
- `payment_failed`
- `payment_canceled`

현재 MVP에는 다음 상태를 별도로 관리하지 않는다.

예:

- payment_pending
- refunded
- partial_refunded

따라서 현재 데이터만으로는 다음과 같은 상황을 세부적으로 판정할 수 없다.

- 결제 승인 대기
- 결제 후 전액 환불
- 결제 후 일부 환불
- 결제 취소와 환불 완료의 구분

향후 실제 쇼핑몰 시스템과 연동하여 상태값이 추가될 경우
본 Policy의 상태별 판정 규칙을 함께 확장해야 한다.

---

## 10. 결제수단에 대한 현재 MVP 기준

현재 MVP에서 지원하는 결제수단은 다음과 같다.

- `card`

카드 결제의 완료 여부는 다음 기준으로 판단한다.

`payment_status = payment_completed`
→ 결제 완료

`payment_status = payment_failed`
→ 결제 실패

`payment_status = payment_canceled`
→ 결제 취소

현재 MVP에서는 다음 결제수단을 지원 범위에 포함하지 않는다.

- 계좌이체
- 무통장입금
- 간편결제

따라서 위 결제수단에 대한 완료 기준을 현재 Policy에서 임의로 정의하지 않는다.

향후 해당 결제수단을 지원할 경우,
각 결제수단의 실제 결제 완료 시점을 먼저 정의한 뒤
payment_completion_check Policy를 확장한다.

---

## 11. 다른 Policy와의 관계

본 Policy는 결제 자체의 완료 여부만 판정한다.

주문 완료 여부는 별도의:

`order_completion_check`

Policy에서 판정한다.

주문 상태와 결제 상태가 서로 모순되는 경우에는 별도의:

`order_payment_consistency`

Policy에서 처리한다.

역할은 다음과 같이 분리한다.

`order_completion_check`
→ 주문 상태 판정

`payment_completion_check`
→ 결제 상태 판정

`order_payment_consistency`
→ 주문·결제 상태 간 불일치 판정