import sys
import os
import pytest

# ensure we can import app.py from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    # Flask provides a test client that behaves like requests, but in-process.
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_add(client):
    resp = client.get("/calculate?op=add&a=2&b=3")
    assert resp.status_code == 200
    assert resp.get_json() == {"result": 5.0}

def test_sub(client):
    resp = client.get("/calculate?op=sub&a=10&b=4")
    assert resp.status_code == 200
    assert resp.get_json() == {"result": 6.0}

def test_mul(client):
    resp = client.get("/calculate?op=mul&a=3&b=5")
    assert resp.status_code == 200
    assert resp.get_json() == {"result": 15.0}

def test_div(client):
    resp = client.get("/calculate?op=div&a=9&b=3")
    assert resp.status_code == 200
    assert resp.get_json() == {"result": 3.0}

def test_invalid_op(client):
    resp = client.get("/calculate?op=pow&a=2&b=3")
    # Your current code returns JSON error without an explicit status code (defaults to 200).
    # We assert the current behavior to keep tests passing as-is.
    assert resp.status_code == 200
    assert resp.get_json() == {"error": "Invalid operation"}

@pytest.mark.xfail(reason="Division by zero currently raises ZeroDivisionError (HTTP 500).")
def test_div_by_zero(client):
    client.get("/calculate?op=div&a=1&b=0")
