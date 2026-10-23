import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from studio import api


class RunIdTests(unittest.TestCase):
    def test_invalid_dataset_ids_return_client_errors(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api, 'DB', str(Path(directory) / 'eval.sqlite')):
            with TestClient(api.app) as client:
                client.post('/api/datasets', json={
                    'name': 'ids', 'cases': [{'id': 'one', 'input': 'Q', 'expected': 'A'}]
                })
                prompt = client.post('/api/prompts', json={'name': 'p', 'template': '{input}'}).json()
                for value in (None, True, False, "1", 1.0, [], {}, 0, -1, 2**63):
                    with self.subTest(value=value):
                        response = client.post('/api/runs', json={'dataset_id': value, 'prompt_ids': [prompt['id']]})
                        self.assertEqual(response.status_code, 400)
                self.assertEqual(client.get('/api/runs').json(), [])

    def test_invalid_prompt_ids_return_client_errors(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(api, 'DB', str(Path(directory) / 'eval.sqlite')):
            with TestClient(api.app) as client:
                dataset = client.post('/api/datasets', json={
                    'name': 'ids', 'cases': [{'id': 'one', 'input': 'Q', 'expected': 'A'}]
                }).json()
                for value in (True, "1", 1.0, [], {}, 0, -1, 2**63):
                    with self.subTest(value=value):
                        response = client.post('/api/runs', json={
                            'dataset_id': dataset['id'], 'prompt_ids': [value]
                        })
                        self.assertEqual(response.status_code, 400)
                self.assertEqual(client.get('/api/runs').json(), [])
