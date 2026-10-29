import pytest
from fastapi.testclient import TestClient
from studio import api

@pytest.mark.parametrize('price', [10**400, -(10**400), True, '1'])
def test_invalid_price_is_a_client_error_without_creating_run(tmp_path, monkeypatch, price):
    monkeypatch.setattr(api, 'DB', str(tmp_path / 'eval.sqlite'))
    with TestClient(api.app) as client:
        dataset = client.post('/api/datasets', json={'name': 'd', 'cases': [{'id': 'one', 'input': 'Q', 'expected': 'A', 'outputs': {'p': 'A'}}]}).json()
        prompt = client.post('/api/prompts', json={'name': 'p', 'template': '{input}'}).json()
        response = client.post('/api/runs', json={'dataset_id': dataset['id'], 'prompt_ids': [prompt['id']], 'input_price': price})
        assert response.status_code == 400
        assert 'finite nonnegative' in response.json()['detail']
        assert client.get('/api/runs').json() == []
        assert not api.LOCK.locked()
