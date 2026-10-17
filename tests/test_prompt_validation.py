import unittest
from studio.core import evaluate
class PromptValidationTests(unittest.TestCase):
    def test_invalid_prompt_fails_before_provider_calls(self):
        for prompt in [None,[],{}, {'name':'p'}, {'name':' ','template':'x'}, {'name':'p','template':42}]:
            calls=[]
            with self.assertRaisesRegex(ValueError,'Prompt'):
                evaluate([{'id':'1','input':'Q','expected':'A'}],prompt,lambda *args:calls.append(args))
            self.assertEqual(calls,[])
