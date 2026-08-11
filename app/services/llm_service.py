from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.chat import UserRequest


# 환경변수 로드
load_dotenv()


# LLM 연결
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


# Structured Output 설정
structured_llm = llm.with_structured_output(
    UserRequest,
    method="json_schema"
)


# 사용자 질문 분류 프롬프트
classification_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
너는 온라인 쇼핑몰 고객 질문을 분류하는 역할을 한다.

사용자 질문을 읽고 다음 기준에 따라 분류한다.

[intent]
- cs: 쇼핑몰 이용, 주문, 결제, 배송, 상품 정보 등에 대한 고객 문의
- recommendation: 사용자의 조건이나 상황에 맞는 상품 선택 또는 추천 요청
- other: 인사 또는 쇼핑몰 cs/상품 추천 범위를 벗어난 요청

[cs_category]
- member_account: 회원/계정
- order_payment: 주문/결제
- exchange_refund: 교환/환불
- delivery: 배송
- product_info: 상품 정보

[order_payment의 sub_intent]
- order_confirmation: 주문 완료 여부 확인
- payment_confirmation: 결제 완료 여부 확인
- payment_method_change: 결제 방식 변경
- delivery_address_change: 주문 후 배송지 변경
- order_cancel: 주문 취소
- order_change: 주문 수량 변경
- unknown: 위 세부 유형으로 판단할 수 없음

[order_id]
- 사용자 질문에 주문번호가 명확하게 제시된 경우에만 추출한다.
- 주문번호가 없으면 null로 반환한다.
- 다른 숫자를 임의로 주문번호라고 판단하지 않는다.
"""
    ),
    (
        "human",
        "{user_input}"
    )
])


# Prompt → Structured LLM 연결
classification_chain = classification_prompt | structured_llm