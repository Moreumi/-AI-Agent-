# =========================================================
# 주문 테스트용 Sample Data
# =========================================================

orders = [
    {
        "order_id": 10001,
        "customer_id": 1,
        "delivery_address": "서울시 성동구",
        "order_date": "2026-08-08",
        "total_price": 49000,
        "delivery_status": "before_shipping",
        "order_status": "order_completed"
    },
    {
        "order_id": 10002,
        "customer_id": 1,
        "delivery_address": "서울시 성동구",
        "order_date": "2026-08-10",
        "total_price": 32000,
        "delivery_status": "before_shipping",
        "order_status": "order_completed"
    },
    {
        "order_id": 10003,
        "customer_id": 2,
        "delivery_address": "서울시 강남구",
        "order_date": "2026-08-09",
        "total_price": 65000,
        "delivery_status": "shipping",
        "order_status": "order_canceled"
    }
]

# =========================================================
# 결제 테스트용 Sample Data
# =========================================================

payments = [
    {
        "payment_id": 50001,
        "order_id": 10001,
        "payment_method": "card",
        "payment_amount": 49000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-08"
    },
    {
        "payment_id": 50002,
        "order_id": 10002,
        "payment_method": "card",
        "payment_amount": 32000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-10"
    },
    {
        "payment_id": 50003,
        "order_id": 10003,
        "payment_method": "card",
        "payment_amount": 65000,
        "payment_status": "payment_canceled",
        "payment_date": "2026-08-09"
    }
]