import re


# =========================================================
# State 초기값
# =========================================================

state = {
    "pending_action": None,
    "candidate_orders": [],
    "selected_order_id": None,
    "pending_data":{},
}


# =========================================================
# State 초기화
# =========================================================

def reset_state(state: dict) -> None:
    state["pending_action"] = None
    state["candidate_orders"] = []
    state["selected_order_id"] = None
    state["pending_data"] = {}


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

# =========================================================
# 배송지 정보 추출
# =========================================================

def extract_delivery_address(user_input: str) -> str | None:
    """
    배송지 변경 과정에서 사용자가 입력한 새 주소를 추출한다.

    현재 MVP에서는 주소 자체의 유효성을 외부 주소 API로 검증하지 않고,
    공백이 아닌 문자열인지 여부만 확인한다.
    """

    address = user_input.strip()

    if not address:
        return None

    return address

# =========================================================
# 주문 수량 변경 요청 추출
# =========================================================

def extract_quantity_change_request(
    user_input: str,
) -> dict | None:
    """
    주문 수량 변경 Multi-turn 과정에서
    사용자의 후속 수량 입력을 해석한다.

    예:
    "3개로 바꿔줘" → set / 3
    "1개 추가해줘" → increase / 1
    "2개 줄여줘" → decrease / 2
    """

    normalized_input = user_input.strip().lower()

    # 한글 수량 표현 지원
    korean_numbers = {
        "한": 1,
        "하나": 1,
        "두": 2,
        "둘": 2,
        "세": 3,
        "셋": 3,
        "네": 4,
        "넷": 4,
        "다섯": 5,
        "여섯": 6,
        "일곱": 7,
        "여덟": 8,
        "아홉": 9,
        "열": 10,
    }

    # -----------------------------------------------------
    # 1. "N개" 형태 추출
    # -----------------------------------------------------

    quantity_matches = re.findall(
        r"(\d+|한|하나|두|둘|세|셋|네|넷|다섯|여섯|일곱|여덟|아홉|열)\s*개",
        normalized_input,
    )

    # 하나의 수량만 명확하게 입력되어야 함
    if len(quantity_matches) != 1:

        # 사용자가 숫자 하나만 입력한 경우
        if re.fullmatch(r"\d+", normalized_input):
            return {
                "quantity_change_type": "set",
                "quantity_value": int(normalized_input),
            }

        return None

    quantity_token = quantity_matches[0]

    if quantity_token.isdigit():
        quantity_value = int(quantity_token)
    else:
        quantity_value = korean_numbers[quantity_token]

    # -----------------------------------------------------
    # 2. 최종 수량 지정
    #    "2개로 줄여줘"도 최종 수량 2개로 해석
    # -----------------------------------------------------

    if re.search(r"개\s*로", normalized_input):
        quantity_change_type = "set"

    # -----------------------------------------------------
    # 3. 수량 증가
    # -----------------------------------------------------

    elif any(
        keyword in normalized_input
        for keyword in [
            "추가",
            "더",
            "늘려",
            "증가",
        ]
    ):
        quantity_change_type = "increase"

    # -----------------------------------------------------
    # 4. 수량 감소
    # -----------------------------------------------------

    elif any(
        keyword in normalized_input
        for keyword in [
            "줄여",
            "빼",
            "감소",
        ]
    ):
        quantity_change_type = "decrease"

    # -----------------------------------------------------
    # 5. "3개"처럼 수량만 말한 경우
    #    현재는 수량 입력을 기다리는 State이므로
    #    최종 수량 지정으로 처리
    # -----------------------------------------------------

    else:
        quantity_change_type = "set"

    return {
        "quantity_change_type": quantity_change_type,
        "quantity_value": quantity_value,
    }