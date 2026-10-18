import json
import unittest
from studio.core import evaluate

class CostOverflowTests(unittest.TestCase):
    def test_overflow_is_recorded_as_case_error_and_json_stays_valid(self):
        result = evaluate([{'id': 'a', 'input': 'x', 'expected': 'ok'}], {'name': 'p', 'template': '{input}'}, lambda *args: {'text': 'ok', 'usage': {'input_tokens': 10, 'output_tokens': 0}}, input_price=1e308)
        self.assertEqual(result['error_count'], 1)
        self.assertFalse(result['cases'][0]['passed'])
        self.assertIsNone(result['estimated_cost_usd'])
        json.dumps(result, allow_nan=False)

    def test_normal_cost_is_preserved(self):
        result = evaluate([{'id': 'a', 'input': 'x', 'expected': 'ok'}], {'name': 'p', 'template': '{input}'}, lambda *args: {'text': 'ok', 'usage': {'input_tokens': 10, 'output_tokens': 0}}, input_price=2)
        self.assertEqual(result['error_count'], 0)
        self.assertAlmostEqual(result['estimated_cost_usd'], .00002)
