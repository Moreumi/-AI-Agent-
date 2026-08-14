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
        "quantity": 1,
        "unit_price": 49000,
        "delivery_status": "preparing_shipment",
        "order_status": "order_completed",
    },
    {
        "order_id": 10002,
        "customer_id": 1,
        "delivery_address": "서울시 성동구",
        "order_date": "2026-08-10",
        "total_price": 32000,
        "quantity": 1,
        "unit_price": 32000,
        "delivery_status": "preparing_shipment",
        "order_status": "order_completed",
    },

    # 이미 취소된 주문 테스트
    {
        "order_id": 10003,
        "customer_id": 2,
        "delivery_address": "서울시 강남구",
        "order_date": "2026-08-09",
        "total_price": 65000,
        "quantity": 1,
        "unit_price": 65000,
        "delivery_status": "preparing_shipment",
        "order_status": "order_canceled",
    },

    # 배송중 주문 취소 불가 테스트
    {
        "order_id": 10004,
        "customer_id": 3,
        "delivery_address": "서울시 마포구",
        "order_date": "2026-08-11",
        "total_price": 57000,
        "quantity": 1,
        "unit_price": 57000,
        "delivery_status": "in_transit",
        "order_status": "order_completed",
    },

    # 배송완료 주문 취소 불가 테스트
    {
        "order_id": 10005,
        "customer_id": 4,
        "delivery_address": "서울시 송파구",
        "order_date": "2026-08-07",
        "total_price": 41000,
        "quantity": 1,
        "unit_price": 41000,
        "delivery_status": "delivered",
        "order_status": "order_completed",
    },

    # 계좌이체 주문 취소 테스트
    {
        "order_id": 10006,
        "customer_id": 5,
        "delivery_address": "서울시 종로구",
        "order_date": "2026-08-12",
        "total_price": 73000,
        "quantity": 1,
        "unit_price": 73000,
        "delivery_status": "preparing_shipment",
        "order_status": "order_completed",
    },

    # 수량 증감 테스트
    {
    "order_id": 10007,
    "customer_id": 6,
    "delivery_address": "서울시 서대문구",
    "order_date": "2026-08-13",
    "quantity": 3,
    "unit_price": 20000,
    "total_price": 60000,
    "delivery_status": "preparing_shipment",
    "order_status": "order_completed",
},
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
        "payment_date": "2026-08-08",
    },
    {
        "payment_id": 50002,
        "order_id": 10002,
        "payment_method": "card",
        "payment_amount": 32000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-10",
    },
    {
        "payment_id": 50003,
        "order_id": 10003,
        "payment_method": "card",
        "payment_amount": 65000,
        "payment_status": "payment_canceled",
        "payment_date": "2026-08-09",
    },
    {
        "payment_id": 50004,
        "order_id": 10004,
        "payment_method": "card",
        "payment_amount": 57000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-11",
    },
    {
        "payment_id": 50005,
        "order_id": 10005,
        "payment_method": "card",
        "payment_amount": 41000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-07",
    },
    {
        "payment_id": 50006,
        "order_id": 10006,
        "payment_method": "cash",
        "payment_amount": 73000,
        "payment_status": "payment_completed",
        "payment_date": "2026-08-12",
    },
    {
    "payment_id": 50007,
    "order_id": 10007,
    "payment_method": "card",
    "payment_amount": 60000,
    "payment_status": "payment_completed",
    "payment_date": "2026-08-13",
    },
]


# =========================================================
# 환불 테스트용 Sample Data
# =========================================================

refunds = [
    {
        "refund_id": 70001,
        "payment_id": 50003,
        "order_id": 10003,
        "refund_amount": 65000,
        "refund_status": "refund_completed",
        "bank_name": None,
        "account_number": None,
        "account_holder": None,
    }
]

# =========================================================
# 주문 수량 변경 결제 차액 테스트용 Sample Data
# =========================================================

payment_adjustments = []