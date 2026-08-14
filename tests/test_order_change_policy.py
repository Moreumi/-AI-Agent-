from app.policies.order_change_policy import judge_order_change


# =========================================================
# 변경 가능
# =========================================================

def test_order_change_is_changeable_when_all_conditions_are_valid():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="preparing_shipment",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "changeable",
        "reason": None,
    }


# =========================================================
# 주문 상태
# =========================================================

def test_order_change_not_changeable_when_order_is_canceled():
    result = judge_order_change(
        order_status="order_canceled",
        delivery_status="preparing_shipment",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "order_canceled",
    }


def test_order_change_not_changeable_when_order_is_failed():
    result = judge_order_change(
        order_status="order_failed",
        delivery_status="preparing_shipment",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "order_failed",
    }


def test_order_change_needs_review_for_unknown_order_status():
    result = judge_order_change(
        order_status="unknown_status",
        delivery_status="preparing_shipment",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "needs_review",
        "reason": "unknown_order_status",
    }


# =========================================================
# 배송 상태
# =========================================================

def test_order_change_not_changeable_when_in_transit():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="in_transit",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "in_transit",
    }


def test_order_change_not_changeable_when_delivered():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="delivered",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "delivered",
    }


def test_order_change_needs_review_for_unknown_delivery_status():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="unknown_status",
        payment_status="payment_completed",
    )

    assert result == {
        "change_judgment": "needs_review",
        "reason": "unknown_delivery_status",
    }


# =========================================================
# 결제 상태
# =========================================================

def test_order_change_not_changeable_when_payment_failed():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="preparing_shipment",
        payment_status="payment_failed",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "payment_failed",
    }


def test_order_change_not_changeable_when_payment_canceled():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="preparing_shipment",
        payment_status="payment_canceled",
    )

    assert result == {
        "change_judgment": "not_changeable",
        "reason": "payment_canceled",
    }


def test_order_change_needs_review_for_unknown_payment_status():
    result = judge_order_change(
        order_status="order_completed",
        delivery_status="preparing_shipment",
        payment_status="unknown_status",
    )

    assert result == {
        "change_judgment": "needs_review",
        "reason": "unknown_payment_status",
    }