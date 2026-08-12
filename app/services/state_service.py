import re


# =========================================================
# State 초기값
# =========================================================

state = {
    "pending_action": None,
    "candidate_orders": [],
    "selected_order_id": None,
}


# =========================================================
# State 초기화
# =========================================================

def reset_state(state: dict) -> None:
    state["pending_action"] = None
    state["candidate_orders"] = []
    state["selected_order_id"] = None


# =========================================================
# 사용자가 선택한 주문번호 추출
# =========================================================

def extract_order_id(user_input: str) -> int | None:

    match = re.search(r"\d+", user_input)

    if match:
        return int(match.group())

    return None


# =========================================================
# 주문 취소 최종 승인 여부 확인
# =========================================================

def extract_confirmation(user_input: str) -> bool | None:
    """
    사용자의 주문 취소 최종 승인 여부를 확인한다.

    True:
        명확하게 승인한 경우

    False:
        명확하게 거절한 경우

    None:
        승인/거절 여부가 명확하지 않은 경우

    LLM의 추측으로 승인 여부를 판단하지 않는다.
    """

    normalized_input = user_input.strip().lower()

    approve_inputs = {
        "예",
        "네",
        "응",
        "yes",
        "y",
    }

    reject_inputs = {
        "아니오",
        "아니요",
        "아니",
        "no",
        "n",
    }

    if normalized_input in approve_inputs:
        return True

    if normalized_input in reject_inputs:
        return False

    return None

# =========================================================
# 환불계좌 정보 추출
# =========================================================

def extract_refund_account(user_input: str) -> dict | None:
    """
    환불계좌 정보를 다음 형식으로 입력받는다.

    은행명 / 계좌번호 / 예금주

    예:
    국민은행 / 1234567890 / 홍길동
    """

    parts = [
        part.strip()
        for part in user_input.split("/")
    ]

    # 정확히 세 항목이 필요
    if len(parts) != 3:
        return None

    bank_name, account_number, account_holder = parts

    # 빈 값이 있는 경우
    if not bank_name or not account_number or not account_holder:
        return None

    # 계좌번호는 숫자와 '-'만 허용
    normalized_account_number = account_number.replace("-", "")

    if not normalized_account_number.isdigit():
        return None

    return {
        "bank_name": bank_name,
        "account_number": account_number,
        "account_holder": account_holder,
    }