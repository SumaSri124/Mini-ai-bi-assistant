from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_exists" in data


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "  "},
        {"question": "ab"},
    ],
)
def test_ask_rejects_invalid_questions(payload):
    response = client.post("/ask", json=payload)
    assert response.status_code == 422


def test_ask_rejects_missing_question():
    response = client.post("/ask", json={})
    assert response.status_code == 422


def test_ask_accepts_valid_question():
    mock_plan = {
        "kind": "sql",
        "sql": (
            "SELECT SUM(quantity * unit_price - discount_amount) "
            "AS total_revenue FROM sales "
            "WHERE LOWER(TRIM(status)) = 'completed'"
        ),
    }

    with patch("app.main.generate_sql", return_value=mock_plan):
        response = client.post(
            "/ask",
            json={"question": "What is the total revenue?"},
        )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["answer"]
    assert data["sql"]
    assert "total_revenue" in data["columns"]


def test_ask_rejects_unsafe_generated_sql():
    mock_plan = {
        "kind": "sql",
        "sql": "DELETE FROM sales",
    }

    with patch("app.main.generate_sql", return_value=mock_plan):
        response = client.post(
            "/ask",
            json={"question": "Delete all sales"},
        )

    assert response.status_code == 400
