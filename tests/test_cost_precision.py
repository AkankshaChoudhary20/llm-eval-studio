import pytest
from studio.core import evaluate


def test_representable_cost_does_not_overflow_intermediate_product():
    result = evaluate(
        [{'id': 'a', 'input': '', 'expected': 'ok'}],
        {'name': 'p', 'template': '{input}'},
        lambda *args: {'text': 'ok', 'usage': {'input_tokens': 10, 'output_tokens': 10}},
        input_price=1e308, output_price=1e308,
    )
    assert result['error_count'] == 0
    assert result['cases'][0]['passed']
    assert result['estimated_cost_usd'] == pytest.approx(2e303)


def test_small_price_is_not_rounded_to_zero_before_multiplication():
    result = evaluate(
        [{'id': 'a', 'input': '', 'expected': 'ok'}],
        {'name': 'p', 'template': '{input}'},
        lambda *args: {'text': 'ok', 'usage': {'input_tokens': 1_000_000, 'output_tokens': 0}},
        input_price=1e-320,
    )
    assert result['error_count'] == 0
    assert result['estimated_cost_usd'] == 1e-320
