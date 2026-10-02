import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from studio import api
class ApiTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();api.DB=str(Path(self.tmp.name)/'test.sqlite');self.client=TestClient(api.app)
    def tearDown(self):self.tmp.cleanup()
    def test_versioned_batch_and_export(self):
        dataset=self.client.post('/api/datasets',json={'name':'smoke','cases':[{'id':'one','input':'Q','expected':'A','outputs':{'p':'A'}}]}).json()
        prompt=self.client.post('/api/prompts',json={'name':'p','template':'{input}'}).json()
        run=self.client.post('/api/runs',json={'dataset_id':dataset['id'],'prompt_ids':[prompt['id']],'provider':'replay'}).json()
        saved=self.client.get('/api/runs/'+str(run['id'])).json();self.assertEqual(saved['status'],'completed');self.assertEqual(saved['payload']['results'][0]['pass_rate'],1)
        self.assertEqual(len(self.client.get('/api/runs').json()),1)
        self.assertEqual(self.client.post('/api/prompts',json={'name':'p','template':'Again: {input}'}).json()['version'],2)
    def test_invalid_input(self):
        self.assertEqual(self.client.post('/api/datasets',json={'name':'x','cases':[]}).status_code,400)
        self.assertEqual(self.client.post('/api/prompts',json={'name':'p','template':'No placeholder'}).status_code,400)
        self.assertEqual(self.client.get('/api/runs/999').status_code,404)
if __name__=='__main__':unittest.main()
