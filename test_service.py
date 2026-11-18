import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)
config = json.loads(Path('config.json').read_text())

def test_metrics_match_current_training_data():
    response = client.get('/metrics')
    assert response.status_code == 200
    result = response.json()
    raw = Path('dataset/train.csv').read_bytes()
    assert result['student_id'] == 'FA23-BDS-056'
    assert result['training_rows'] == len(pd.read_csv('dataset/train.csv'))
    assert result['training_rows'] >= 100
    assert result['dataset_sha256'] == hashlib.sha256(raw).hexdigest()
    assert result['model_version'] == hashlib.sha256(raw).hexdigest()[:12]
    assert 0.5 <= result['accuracy'] <= 1.0
    expected_sha = os.environ.get('GIT_COMMIT')
    if expected_sha:
        assert result['git_sha'] == expected_sha

def test_prediction_uses_assigned_features():
    records = pd.read_csv('dataset/train.csv')[config['features']].head(3).fillna(0).to_dict('records')
    response = client.post('/predict', json={'records': records})
    assert response.status_code == 200
    result = response.json()
    assert len(result['predictions']) == len(records)
    assert all(x in (0, 1) for x in result['predictions'])
    assert all(0 <= x <= 1 for x in result['probabilities'])

@pytest.mark.parametrize('records', [[], [{}] * 101])
def test_invalid_batch_size_is_rejected(records):
    assert client.post('/predict', json={'records': records}).status_code == 422
