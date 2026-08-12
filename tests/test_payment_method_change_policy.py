from app.policies.payment_method_change_policy import (
    judge_payment_method_change,
)


def test_payment_method_change_is_not_changeable():

    result = judge_payment_method_change()

    assert (
        result["payment_method_change_judgment"]
        == "not_changeable"
    )

    assert (
        result["recommended_action"]
        == "cancel_and_reorder"
    )