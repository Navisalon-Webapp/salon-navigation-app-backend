import os
import sys
import pytest

# Ensure the backend package root is on sys.path so `from app import app` works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as current_app

@pytest.fixture
def client():
    current_app.testing = True
    return current_app.test_client()

# def test_hello_route(client):
#     res = client.get('/uptime/health')
#     assert res.status_code == 200
#     assert b"healthy" in res.data
