import unittest
from studio.core import evaluate,score,check_dataset,replay_provider
class CoreTests(unittest.TestCase):
    def setUp(self):self.rows=[{'id':'1','input':'Q','expected':'A','outputs':{'p':'A'}},{'id':'2','input':'Q2','contains':['B'],'outputs':{'p':'Wrong'}}];self.prompt={'name':'p','template':'Question: {input}','version':1}
    def test_replay_results(self):
        r=evaluate(self.rows,self.prompt,replay_provider);self.assertEqual(r['pass_rate'],.5);self.assertIsNone(r['estimated_cost_usd'])
    def test_cost_accounting(self):
        r=evaluate([self.rows[0]],self.prompt,lambda *args:{'text':'A','usage':{'input_tokens':100,'output_tokens':50}},2,4)
        self.assertAlmostEqual(r['estimated_cost_usd'],.0004)
    def test_errors_fail_cases(self):
        r=evaluate(self.rows,{**self.prompt,'name':'missing'},replay_provider);self.assertEqual(r['error_count'],2);self.assertEqual(r['pass_rate'],0)
    def test_exact_and_contains_are_both_required(self):
        self.assertFalse(score({'expected':'A','contains':['B']},'A')['passed']);self.assertTrue(score({'expected':' A '},'A')['passed'])
    def test_invalid_dataset(self):
        for rows in [[],[{'id':'1','input':'Q'}],[{'id':'1','input':'Q','contains':[]}],self.rows+self.rows]:
            with self.assertRaises(ValueError):check_dataset(rows)
    def test_invalid_provider_usage_fails_case_without_corrupting_cost(self):
        for usage in [{}, {'input_tokens': -1, 'output_tokens': 2},
                      {'input_tokens': True, 'output_tokens': 2},
                      {'input_tokens': 1.5, 'output_tokens': 2},
                      {'input_tokens': float('nan'), 'output_tokens': 2}]:
            with self.subTest(usage=usage):
                result = evaluate([self.rows[0]], self.prompt,
                                  lambda *args: {'text': 'A', 'usage': usage}, 2, 4)
                self.assertEqual(result['error_count'], 1)
                self.assertIsNone(result['estimated_cost_usd'])
                self.assertIn('token counts', result['cases'][0]['error'])

    def test_zero_usage_has_zero_cost(self):
        result = evaluate([self.rows[0]], self.prompt,
                          lambda *args: {'text': 'A', 'usage': {'input_tokens': 0, 'output_tokens': 0}}, 2, 4)
        self.assertEqual(result['estimated_cost_usd'], 0)
        self.assertEqual(result['error_count'], 0)

if __name__=='__main__':unittest.main()
