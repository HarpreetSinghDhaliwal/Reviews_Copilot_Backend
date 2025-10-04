# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app
import random
import json

client = TestClient(app)
API_KEY = {"x-api-key": "supersecret"}

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ingest_and_suggest_flow():
    unique_id = random.randint(1000000, 9999999)
    sample = [
        {"id": unique_id, "location": "NYC", "rating": 2, "text": "Waited 40 min for pickup; staff seemed overwhelmed.", "date": "2025-06-12"}
    ]
    r = client.post("/ingest", json=sample, headers=API_KEY)
    print("Status code:", r.status_code)
    print("Response JSON:", r.json())
    assert r.status_code == 200
    body = r.json()
    assert body["ingested"] == 1

    # fetch review
    r2 = client.get(f"/reviews/{unique_id}", headers=API_KEY)
    assert r2.status_code == 200
    data = r2.json()
    assert data["id"] == unique_id

    # suggest reply
    r3 = client.post(f"/reviews/{unique_id}/suggest-reply", headers=API_KEY)
    assert r3.status_code == 200
    resp = r3.json()
    assert "reply" in resp
    assert "tags" in resp

def test_missing_review():
    r = client.post("/reviews/9999999/suggest-reply", headers=API_KEY)
    assert r.status_code == 404
