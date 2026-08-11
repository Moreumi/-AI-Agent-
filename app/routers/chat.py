from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.orchestrator import route_request
from app.services.state_service import state

from app.data.sample_data import orders, payments


# =========================================================
# Chat Router 생성
# =========================================================

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


# =========================================================
# POST /chat/
# =========================================================

@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):

    result = route_request(
        user_input=request.message,
        customer_id=request.customer_id,
        orders=orders,
        state=state,
        payments=payments
    )

    return ChatResponse(
        route=result["route"],
        response=result["response"]
    )