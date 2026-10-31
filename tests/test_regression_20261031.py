import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from studio import api

class RunIdBoundsTests(unittest.TestCase):
    def test_invalid_ids_are_rejected_before_storage(self):
        with patch.object(api.store, 'run') as lookup:
            client = TestClient(api.app)
            for value in ('0', '-1', str(2**63), str(10**100)):
                with self.subTest(value=value):
                    self.assertEqual(client.get('/api/runs/' + value).status_code, 422)
            lookup.assert_not_called()

    def test_valid_missing_id_still_returns_404(self):
        with patch.object(api.store, 'run', return_value=None):
            self.assertEqual(TestClient(api.app).get('/api/runs/1').status_code, 404)
