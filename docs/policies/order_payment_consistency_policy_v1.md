# 주문-결제 상태 일관성 Policy v1

## 1. Policy 기본 정보

- policy_id: `order_payment_consistency_v1`
- policy_category: `order_payment`
- policy_name: `order_payment_consistency`
- 적용 기능:
  - 주문 완료 확인
  - 결제 완료 확인
- 정책 상태: MVP v1

---

## 2. 목적

주문 상태와 결제 상태를 함께 조회했을 때
두 데이터가 서로 일관된 상태인지 판정하기 위한 정책이다.

개별 주문 상태와 결제 상태는 각각 다음 Policy에서 먼저 판정한다.

- `order_completion_check`
- `payment_completion_check`

본 Policy는 두 판정 결과를 함께 비교하여
정상 조합인지, 취소 상태인지, 데이터 확인이 필요한 상태인지 판단한다.

LLM이 주문과 결제 상태의 관계를 임의로 해석하지 않는다.

---

## 3. 현재 MVP에서 사용하는 상태값

### order_status

- `order_completed`
- `order_canceled`
- `order_failed`

### payment_status

- `payment_completed`
- `payment_failed`
- `payment_canceled`

---

## 4. 기본 판단 원칙

### 원칙 1

주문 완료와 결제 완료는 서로 다른 상태로 관리한다.

`order_status = order_completed`라고 해서
자동으로 결제가 완료된 것으로 판단하지 않는다.

### 원칙 2

`payment_status = payment_completed`라고 해서
자동으로 주문이 정상 완료된 것으로 판단하지 않는다.

### 원칙 3

주문과 결제 상태가 서로 모순되는 경우
Agent가 임의로 어느 한쪽을 정상 상태로 선택하지 않는다.

### 원칙 4

데이터 불일치 상태는 `needs_review`로 처리한다.

### 원칙 5

현재 데이터만으로 판단할 수 없는 과거 이력은 추론하지 않는다.

---

## 5. 상태 조합별 판정 규칙

### 5-1. 정상 주문 완료 + 정상 결제 완료

```text
order_status = order_completed
payment_status = payment_completed
```

판정:

`consistent_completed`

의미:

주문과 결제가 모두 정상적으로 완료된 상태이다.

Agent 처리:

- 주문 완료 문의에서는 정상 주문 완료로 안내
- 결제 완료 문의에서는 정상 결제 완료로 안내
- 필요한 경우 확인된 주문/결제 상세정보 제공

---

### 5-2. 주문 완료 + 결제 실패

```text
order_status = order_completed
payment_status = payment_failed
```

판정:

`needs_review`

의미:

주문은 완료 상태이지만 결제는 실패 상태로 기록되어 있어
두 데이터가 서로 일치하지 않는다.

Agent 처리:

- 정상 주문 또는 정상 결제라고 단정하지 않음
- 주문과 결제 상태가 일치하지 않아 추가 확인이 필요함을 안내
- 재조회 또는 상담원 확인 대상으로 처리

금지:

- 주문 완료 상태만 보고 정상 주문이라고 최종 확정하지 않음
- 결제 실패 원인을 추측하지 않음

---

### 5-3. 주문 완료 + 결제 취소

```text
order_status = order_completed
payment_status = payment_canceled
```

판정:

`needs_review`

의미:

주문은 완료 상태이지만 현재 결제가 취소된 상태이므로
현재 데이터만으로 정상적인 주문 진행 상태라고 판단하기 어렵다.

Agent 처리:

- 주문과 결제 상태가 일치하지 않음을 안내
- 결제 취소 이후 주문 상태 갱신 여부에 대한 추가 확인 필요
- 자동으로 주문 취소 또는 환불 완료라고 판단하지 않음

---

### 5-4. 주문 취소 + 결제 취소

```text
order_status = order_canceled
payment_status = payment_canceled
```

판정:

`consistent_canceled`

의미:

주문과 결제가 모두 현재 취소 상태로 기록되어 있다.

Agent 처리:

- 현재 주문이 취소된 상태임을 안내
- 현재 결제가 취소된 상태임을 안내
- 환불 완료 여부는 별도 데이터 없이 추론하지 않음

---

### 5-5. 주문 취소 + 결제 완료

```text
order_status = order_canceled
payment_status = payment_completed
```

판정:

`needs_review`

의미:

주문은 취소 상태이지만 결제는 완료 상태로 남아 있다.

가능한 원인은 현재 데이터만으로 판단하지 않는다.

Agent 처리:

- 주문과 결제 상태가 일치하지 않음을 안내
- 환불 진행 여부 등 추가 확인 필요
- `payment_completed`라는 이유만으로 현재 정상 결제 상태라고 안내하지 않음

---

### 5-6. 주문 취소 + 결제 실패

```text
order_status = order_canceled
payment_status = payment_failed
```

판정:

`consistent_not_completed`

의미:

주문이 취소되었으며 결제 또한 정상 완료되지 않은 상태이다.

Agent 처리:

- 현재 주문은 취소 상태임을 안내
- 결제는 정상 완료되지 않았음을 안내
- 실패 또는 취소의 상세 원인은 추측하지 않음

---

### 5-7. 주문 실패 + 결제 실패

```text
order_status = order_failed
payment_status = payment_failed
```

판정:

`consistent_failed`

의미:

주문과 결제가 모두 정상적으로 완료되지 않은 상태이다.

Agent 처리:

- 주문이 정상 완료되지 않았음을 안내
- 결제 역시 실패 상태임을 안내
- 실패 원인은 데이터 없이 추측하지 않음

---

### 5-8. 주문 실패 + 결제 완료

```text
order_status = order_failed
payment_status = payment_completed
```

판정:

`needs_review`

의미:

주문은 실패 상태이지만 결제는 완료 상태로 기록되어 있다.

고객에게 금전적인 영향을 줄 수 있는 데이터 불일치 상태이다.

Agent 처리:

- 정상적인 주문 상태라고 안내하지 않음
- 결제 완료 사실은 확인되지만 주문 상태와 일치하지 않음을 안내
- 재조회 또는 상담원 확인 대상으로 처리

---

### 5-9. 주문 실패 + 결제 취소

```text
order_status = order_failed
payment_status = payment_canceled
```

판정:

`consistent_not_completed`

의미:

주문이 정상 완료되지 않았으며
결제 역시 현재 취소 상태이다.

Agent 처리:

- 주문이 정상 완료되지 않았음을 안내
- 결제가 현재 취소 상태임을 안내
- 과거 결제 승인 여부는 추론하지 않음

---

## 6. 상태 조합 요약

| order_status | payment_status | consistency 판정 |
|---|---|---|
| `order_completed` | `payment_completed` | `consistent_completed` |
| `order_completed` | `payment_failed` | `needs_review` |
| `order_completed` | `payment_canceled` | `needs_review` |
| `order_canceled` | `payment_completed` | `needs_review` |
| `order_canceled` | `payment_failed` | `consistent_not_completed` |
| `order_canceled` | `payment_canceled` | `consistent_canceled` |
| `order_failed` | `payment_completed` | `needs_review` |
| `order_failed` | `payment_failed` | `consistent_failed` |
| `order_failed` | `payment_canceled` | `consistent_not_completed` |

---

## 7. 결제 데이터가 존재하지 않는 경우

주문은 존재하지만 연결된 결제 데이터가 없는 경우:

판정:

`payment_not_found`

Agent 처리:

- 결제 완료 또는 실패를 임의로 판단하지 않음
- 결제 정보를 확인할 수 없음을 안내
- 필요 시 재조회 또는 상담원 확인 대상으로 처리

---

## 8. 주문 데이터가 존재하지 않는 경우

결제 데이터가 존재하더라도
현재 customer_id에 속한 주문을 확인할 수 없는 경우:

판정:

`order_not_found`

Agent 처리:

- 해당 결제 정보를 고객의 정상 주문으로 연결하지 않음
- 주문 정보를 확인할 수 없음을 안내
- 필요 시 추가 확인 대상으로 처리

---

## 9. 정의되지 않은 상태값

다음과 같은 경우:

- 정의되지 않은 order_status
- 정의되지 않은 payment_status
- 필수 상태값 누락

판정:

`needs_review`

Agent 처리:

- 정상/실패/취소 여부를 임의로 판정하지 않음
- 추가 확인이 필요한 상태로 처리

---

## 10. Agent 우선 행동

`needs_review`가 발생한 경우
Agent는 사용자의 질문에 대해 정상 완료 여부를 확정적으로 답하지 않는다.

응답 방향:

1. 현재 확인된 상태를 설명한다.
2. 주문과 결제 상태가 일치하지 않는다는 사실을 안내한다.
3. 확인되지 않은 원인을 추측하지 않는다.
4. 재조회 또는 상담원 확인이 필요함을 안내한다.

---

## 11. 고객에게 공개 가능한 정보

일관성 확인 과정에서 고객에게 사용할 수 있는 정보:

- order_id
- order_status
- payment_status
- payment_amount
- payment_method
- payment_date
- order_date
- total_price

단, 현재 질문과 관계없는 정보는 불필요하게 노출하지 않는다.

---

## 12. 금지 규칙

AI Agent는 다음 행동을 하지 않는다.

- 주문 상태만 보고 결제 상태를 추론하지 않는다.
- 결제 상태만 보고 주문 상태를 추론하지 않는다.
- 불일치 상태에서 어느 한쪽 데이터를 임의로 정답으로 선택하지 않는다.
- `payment_canceled`를 환불 완료와 동일하게 판단하지 않는다.
- 주문 취소 상태에서 환불 여부를 추측하지 않는다.
- 결제 실패 또는 주문 실패 원인을 추측하지 않는다.
- 데이터 불일치가 존재하는 경우 정상 처리된 것으로 답변하지 않는다.
- 다른 customer_id의 주문 또는 결제 데이터를 연결하지 않는다.

---

## 13. 현재 MVP의 한계

현재 주문 및 결제 상태는 각각 세 가지 상태만 사용한다.

향후 다음과 같은 상태가 추가될 경우
Consistency Policy를 함께 확장해야 한다.

예:

주문:
- pending
- confirmed
- preparing
- shipped
- delivered

결제:
- payment_pending
- refunded
- partial_refunded

특히 환불 상태가 추가되면
주문 취소와 결제 환불 간의 일관성 규칙을 별도로 정의해야 한다.

---

## 14. 다른 Policy와의 관계

처리 순서는 다음과 같다.

`order_completion_check`
→ 주문 상태 개별 판정

`payment_completion_check`
→ 결제 상태 개별 판정

`order_payment_consistency`
→ 두 상태의 관계 판정

따라서 본 Policy는
개별 상태 판정을 대체하지 않고
두 결과를 종합적으로 검증하는 역할을 담당한다.