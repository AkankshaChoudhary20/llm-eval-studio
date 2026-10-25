import pytest
from studio.core import evaluate

def test_unrepresentable_token_price_is_validation_error():
    with pytest.raises(ValueError, match="Token prices"):
        evaluate([{"id": "a", "input": "", "expected": ""}],
                 {"name": "p", "template": "{input}"}, lambda *args: {"text": ""},
                 input_price=10 ** 1000)
