from fastapi import APIRouter


# =========================================================
# Health Router 생성
# =========================================================

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


# =========================================================
# GET /health/
# =========================================================

@router.get("/")
def health_check():
    return {
        "status": "ok"
    }