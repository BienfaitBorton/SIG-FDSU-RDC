from pathlib import Path
import os
os.environ['PYTHONPATH'] = str(Path.cwd())
from fastapi.testclient import TestClient
from api.main import app
from tests.test_site_crud import SITE_PAYLOAD

client = TestClient(app)
response = client.post('/sites', json={**SITE_PAYLOAD, 'village_id': 1})
print(response.status_code)
print(response.json())
