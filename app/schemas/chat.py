from typing import Literal
from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    intent: Literal[
        "cs",
        "recommendation",
        "other"
    ] = Field(
        description="사용자 질문의 최상위 유형"
    )

    cs_category: Literal[
        "member_account",
        "order_payment",
        "exchange_refund",
        "delivery",
        "product_info"
    ] | None = Field(
        default=None,
        description="intent가 cs인 경우의 cs 카테고리"
    )

    sub_intent: Literal[
        "order_confirmation",
        "payment_confirmation",
        "payment_method_change",
        "delivery_address_change",
        "order_cancel",
        "order_change",
        "delivery_status",
        "delivery_eta",
        "unknown"
    ] | None = Field(
        default=None,
        description="세부 처리 목적"
    )

    delivery_eta_scope: Literal[
        "general",
        "order_specific"
    ] | None = Field(
        default=None,
        description=(
            "sub_intent가 delivery_eta인 경우 "
            "일반적인 배송기간 문의인지 특정 주문의 배송시기 문의인지 구분"
        )
    )
    quantity_change_type: Literal[
        "set",
        "increase",
        "decrease"
    ] | None = Field(
        default=None,
        description=(
            "sub_intent가 order_change인 경우 "
            "수량을 특정 값으로 변경하는지, 증가시키는지, 감소시키는지 구분"
        )
    )

    quantity_value: int | None = Field(
        default=None,
        ge=0,
        description=(
            "sub_intent가 order_change인 경우 "
            "사용자가 요청한 수량 또는 증감 수량"
        )
    )
    order_id: int | None = Field(
        default=None,
        description="사용자 질문에 주문번호가 명시된 경우 해당 주문번호"
    )

# =========================================================
# FastAPI Schema
# =========================================================

class ChatRequest(BaseModel):
    message: str
    customer_id: int

class ChatResponse(BaseModel):
    route: str
    response: str