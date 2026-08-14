from app.services.order_payment_service import (
    calculate_order_quantity_change,
)


# =========================================================
# 수량 증가
# =========================================================

def test_quantity_increase_calculation():
    result = calculate_order_quantity_change(
        current_quantity=2,
        quantity_change_type="increase",
        quantity_value=1,
        unit_price=20000,
        current_total_price=40000,
    )

    assert result == {
        "result_type": "change_preview",
        "current_quantity": 2,
        "target_quantity": 3,
        "unit_price": 20000,
        "current_total_price": 40000,
        "new_total_price": 60000,
        "adjustment_type": "additional_payment_required",
        "adjustment_amount": 20000,
    }


# =========================================================
# 수량 감소
# =========================================================

def test_quantity_decrease_calculation():
    result = calculate_order_quantity_change(
        current_quantity=3,
        quantity_change_type="decrease",
        quantity_value=1,
        unit_price=20000,
        current_total_price=60000,
    )

    assert result == {
        "result_type": "change_preview",
        "current_quantity": 3,
        "target_quantity": 2,
        "unit_price": 20000,
        "current_total_price": 60000,
        "new_total_price": 40000,
        "adjustment_type": "partial_refund_required",
        "adjustment_amount": 20000,
    }


# =========================================================
# 최종 수량 지정
# =========================================================

def test_quantity_set_calculation():
    result = calculate_order_quantity_change(
        current_quantity=2,
        quantity_change_type="set",
        quantity_value=4,
        unit_price=15000,
        current_total_price=30000,
    )

    assert result["result_type"] == "change_preview"
    assert result["target_quantity"] == 4
    assert result["new_total_price"] == 60000
    assert result["adjustment_type"] == "additional_payment_required"
    assert result["adjustment_amount"] == 30000


# =========================================================
# 수량 0 → 주문 취소 필요
# =========================================================

def test_quantity_zero_requires_order_cancel():
    result = calculate_order_quantity_change(
        current_quantity=1,
        quantity_change_type="decrease",
        quantity_value=1,
        unit_price=30000,
        current_total_price=30000,
    )

    assert result == {
        "result_type": "cancel_required",
        "reason": "target_quantity_zero",
        "current_quantity": 1,
        "target_quantity": 0,
    }


# =========================================================
# 목표 수량이 음수
# =========================================================

def test_quantity_below_zero_is_invalid():
    result = calculate_order_quantity_change(
        current_quantity=1,
        quantity_change_type="decrease",
        quantity_value=2,
        unit_price=30000,
        current_total_price=30000,
    )

    assert result == {
        "result_type": "invalid_quantity",
        "reason": "target_quantity_below_zero",
        "current_quantity": 1,
        "target_quantity": -1,
    }


# =========================================================
# 동일 수량
# =========================================================

def test_same_quantity_returns_no_change():
    result = calculate_order_quantity_change(
        current_quantity=2,
        quantity_change_type="set",
        quantity_value=2,
        unit_price=25000,
        current_total_price=50000,
    )

    assert result == {
        "result_type": "no_change",
        "reason": "same_quantity",
        "current_quantity": 2,
        "target_quantity": 2,
    }


# =========================================================
# 기존 주문금액 불일치
# =========================================================

def test_total_price_mismatch_is_detected():
    result = calculate_order_quantity_change(
        current_quantity=2,
        quantity_change_type="increase",
        quantity_value=1,
        unit_price=20000,
        current_total_price=50000,
    )

    assert result == {
        "result_type": "data_inconsistent",
        "reason": "total_price_mismatch",
        "current_quantity": 2,
        "unit_price": 20000,
        "current_total_price": 50000,
        "expected_total_price": 40000,
    }


# =========================================================
# 정의되지 않은 수량 변경 방식
# =========================================================

def test_unknown_quantity_change_type_is_invalid():
    result = calculate_order_quantity_change(
        current_quantity=2,
        quantity_change_type="unknown",
        quantity_value=1,
        unit_price=20000,
        current_total_price=40000,
    )

    assert result == {
        "result_type": "invalid_request",
        "reason": "unknown_quantity_change_type",
    }