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

- order_confirmation:
  주문 완료 여부 확인

- payment_confirmation:
  결제 완료 여부 확인

- payment_method_change:
  결제 방식 변경

- delivery_address_change:
  주문 후 배송지 변경

- order_cancel:
  주문 취소

- order_change:
  주문 수량 변경


[delivery의 sub_intent]

- delivery_status:
  현재 주문의 배송 상태 또는 배송 진행 현황을 확인하려는 질문

- delivery_eta:
  배송에 일반적으로 얼마나 시간이 걸리는지,
  또는 사용자의 실제 주문이 언제쯤 도착하는지 묻는 질문


[delivery_eta_scope]

sub_intent가 delivery_eta인 경우에만 다음 기준으로 판단한다.

- general:
  특정 주문이 아니라 쇼핑몰의 일반적인 배송기간이나
  지역별 배송 소요기간을 묻는 경우

- order_specific:
  사용자의 실제 주문 또는 특정 주문의 도착 시기를 묻는 경우

예:

"배송은 보통 얼마나 걸려?"
→ delivery_eta_scope = general

"배송 시작하면 며칠 걸려?"
→ delivery_eta_scope = general

"제주도는 배송 얼마나 걸려?"
→ delivery_eta_scope = general

"내 주문 언제 와?"
→ delivery_eta_scope = order_specific

"내가 주문한 거 언제쯤 받을 수 있어?"
→ delivery_eta_scope = order_specific

"10004번 주문 언제 도착해?"
→ delivery_eta_scope = order_specific

"내 주문은 보통 며칠 걸려?"
→ delivery_eta_scope = order_specific

특정 주문을 가리키는 표현과 일반적인 표현이 함께 존재하면
order_specific을 우선한다.

sub_intent가 delivery_eta가 아닌 경우
delivery_eta_scope는 반드시 null로 반환한다.


[delivery_status와 delivery_eta 구분]

- 현재 배송이 어느 단계인지 묻는 질문
  → delivery_status

- 배송에 얼마나 걸리는지 또는 언제 도착하는지 묻는 질문
  → delivery_eta

예:

"내 주문 지금 어디까지 왔어?"
→ delivery_status

"내 주문 배송 중이야?"
→ delivery_status

"10004번 주문 배송 상태 알려줘"
→ delivery_status

"내 주문 언제 와?"
→ delivery_eta

"10004번 주문 언제 도착해?"
→ delivery_eta

"배송은 보통 며칠 걸려?"
→ delivery_eta


[unknown]

- 위 세부 유형으로 판단할 수 없으면 unknown으로 반환한다.


[cs_category와 sub_intent 일관성 규칙]

- delivery_status 또는 delivery_eta로 판단한 경우
  cs_category는 반드시 delivery로 반환한다.

- 사용자 질문에 "주문", "주문번호", 특정 order_id가 포함되어 있더라도
  질문의 핵심 목적이 배송 상태, 배송 진행 상황,
  배송 소요기간 또는 도착 시기 확인이면 delivery로 분류한다.

- "내 주문", "주문번호"라는 표현만으로
  order_payment로 분류하지 않는다.

- order_payment는 주문 완료, 결제 완료, 결제수단 변경,
  배송지 변경, 주문 취소, 주문 변경 문의에 사용한다.


[order_id]

- 사용자 질문에 주문번호가 명확하게 제시된 경우에만 추출한다.
- 주문번호가 없으면 null로 반환한다.
- 다른 숫자를 임의로 주문번호라고 판단하지 않는다.


[전체 분류 예시]

"내 주문 지금 어디까지 왔어?"
→ intent = cs
→ cs_category = delivery
→ sub_intent = delivery_status
→ delivery_eta_scope = null
→ order_id = null

"10004번 주문 배송 상태 알려줘"
→ intent = cs
→ cs_category = delivery
→ sub_intent = delivery_status
→ delivery_eta_scope = null
→ order_id = 10004

"배송은 보통 얼마나 걸려?"
→ intent = cs
→ cs_category = delivery
→ sub_intent = delivery_eta
→ delivery_eta_scope = general
→ order_id = null

"내 주문 언제 와?"
→ intent = cs
→ cs_category = delivery
→ sub_intent = delivery_eta
→ delivery_eta_scope = order_specific
→ order_id = null

"10004번 주문 언제 도착해?"
→ intent = cs
→ cs_category = delivery
→ sub_intent = delivery_eta
→ delivery_eta_scope = order_specific
→ order_id = 10004

"내 주문 제대로 들어갔어?"
→ intent = cs
→ cs_category = order_payment
→ sub_intent = order_confirmation
→ delivery_eta_scope = null
→ order_id = null
"""
    ),
    (
        "human",
        "{user_input}"
    )
])


# Prompt → Structured LLM 연결
classification_chain = classification_prompt | structured_llm