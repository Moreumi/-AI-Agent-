import re


# =========================================================
# State 초기값
# =========================================================

state = {
    "pending_action": None,
    "candidate_orders": []
}


# =========================================================
# State 초기화
# =========================================================

def reset_state(state: dict) -> None:
    state["pending_action"] = None
    state["candidate_orders"] = []


# =========================================================
# 사용자가 선택한 주문번호 추출
# =========================================================

def extract_order_id(user_input: str) -> int | None:

    match = re.search(r"\d+", user_input)

    if match:
        return int(match.group())

    return None