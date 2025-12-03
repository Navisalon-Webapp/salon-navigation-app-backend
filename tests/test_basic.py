import pytest
from app import app as current_app

@pytest.fixture
def client():
    current_app.testing = True
    return current_app.test_client()

def test_hello_route(client):
    res = client.get('/uptime/health')
    assert res.status_code == 200
    assert b"healthy" in res.data
