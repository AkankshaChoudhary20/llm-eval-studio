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
if __name__=='__main__':unittest.main()
