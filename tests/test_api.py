from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health_and_info_endpoints():
    r = client.get("/health")
    assert r.status_code == 200
    r = client.get("/info")
    assert r.status_code == 200


