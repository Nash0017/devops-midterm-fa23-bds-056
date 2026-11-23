"""Independently recompute the reference result and audit the running API."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--output', default='artifacts/verification.json')
    args = parser.parse_args()
    config = json.loads(Path('config.json').read_text())
    raw = Path('dataset/train.csv').read_bytes()
    data = pd.read_csv('dataset/train.csv')
    features = config['features']
    x = data.loc[:, features].apply(pd.to_numeric, errors='coerce')
    y = data['label'].astype(int)
    seed = int(config['seed'])
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=seed, stratify=y)

    def fresh_model():
        return Pipeline([
            ('missing_values', SimpleImputer(strategy='median')),
            ('scaling', StandardScaler()),
            ('classifier', LogisticRegression(max_iter=700, random_state=seed)),
        ])

    evaluation = fresh_model().fit(x_train, y_train)
    accuracy = round(float(accuracy_score(y_test, evaluation.predict(x_test))), 6)
    digest = hashlib.sha256(raw).hexdigest()
    expected_commit = os.environ['GIT_COMMIT']
    with urllib.request.urlopen(args.url.rstrip('/') + '/metrics', timeout=15) as response:
        actual = json.load(response)
    expected = {
        'student_id': config['student_id'], 'training_rows': len(data),
        'dataset_sha256': digest, 'model_version': digest[:12],
        'git_sha': expected_commit,
    }
    for field, value in expected.items():
        if actual.get(field) != value:
            raise AssertionError(f'{field} differs: expected {value!r}, served {actual.get(field)!r}')
    if abs(float(actual['accuracy']) - accuracy) > 0.000001:
        raise AssertionError(f'Independent accuracy {accuracy} differs from served {actual["accuracy"]}')

    production_reference = fresh_model().fit(x, y)
    sample = x.head(3).fillna(0)
    expected_probabilities = production_reference.predict_proba(sample)[:, 1]
    request = urllib.request.Request(
        args.url.rstrip('/') + '/predict',
        data=json.dumps({'records': sample.to_dict(orient='records')}).encode(),
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        predictions = json.load(response)
    np.testing.assert_allclose(predictions['probabilities'], expected_probabilities, atol=0.000001, rtol=0)
    assert predictions['predictions'] == (expected_probabilities >= 0.5).astype(int).tolist()
    proof = {
        'verified_at': datetime.now(timezone.utc).isoformat(),
        'independent_reference_accuracy': accuracy,
        'expected': expected, 'served_metrics': actual,
        'prediction_reference_matches': True, 'result': 'PASS',
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(proof, indent=2))
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
