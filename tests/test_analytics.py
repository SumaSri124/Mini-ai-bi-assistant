from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("question", "sql", "expected_value"),
    [
        (
            "What is the total revenue?",
            """
            SELECT SUM(quantity * unit_price - discount_amount)
            AS total_revenue
            FROM sales
            WHERE LOWER(TRIM(status)) = 'completed'
            """,
            1439200,
        ),
        (
            "Which product generated the highest revenue?",
            """
            SELECT product,
                   SUM(quantity * unit_price - discount_amount) AS revenue
            FROM sales
            WHERE LOWER(TRIM(status)) = 'completed'
            GROUP BY product
            ORDER BY revenue DESC
            LIMIT 1
            """,
            "Monitor",
        ),
        (
            "Which region generated the highest sales?",
            """
            SELECT region,
                   SUM(quantity * unit_price - discount_amount) AS revenue
            FROM sales
            WHERE LOWER(TRIM(status)) = 'completed'
            GROUP BY region
            ORDER BY revenue DESC
            LIMIT 1
            """,
            "South",
        ),
    ],
)
def test_business_analytics(question, sql, expected_value):
    plan = {"kind": "sql", "sql": sql}

    with patch("app.main.generate_sql", return_value=plan):
        response = client.post("/ask", json={"question": question})

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "success"
    assert data["rows"]

    first_row = data["rows"][0]

    if isinstance(expected_value, (int, float)):
        assert round(float(first_row["total_revenue"]), 2) == expected_value
    else:
        assert first_row["product" if expected_value == "Monitor" else "region"] == expected_value


def test_monthly_revenue_trend():
    plan = {
        "kind": "sql",
        "sql": """
            SELECT strftime('%Y-%m', order_date) AS month,
                   SUM(quantity * unit_price - discount_amount) AS revenue
            FROM sales
            WHERE LOWER(TRIM(status)) = 'completed'
            GROUP BY strftime('%Y-%m', order_date)
            ORDER BY month
        """,
    }

    with patch("app.main.generate_sql", return_value=plan):
        response = client.post(
            "/ask",
            json={"question": "What is the monthly revenue trend?"},
        )

    assert response.status_code == 200, response.text

    rows = response.json()["rows"]

    assert [row["month"] for row in rows] == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
    ]

    expected_revenue = [
        210250,
        234600,
        223900,
        240700,
        318500,
        211250,
    ]

    assert [
        round(float(row["revenue"]), 2) for row in rows
    ] == expected_revenue


def test_revenue_change_january_to_february():
    plan = {
        "kind": "sql",
        "sql": """
            SELECT month, revenue
            FROM (
                SELECT strftime('%Y-%m', order_date) AS month,
                       SUM(quantity * unit_price - discount_amount) AS revenue
                FROM sales
                WHERE LOWER(TRIM(status)) = 'completed'
                  AND strftime('%Y-%m', order_date) IN ('2026-01', '2026-02')
                GROUP BY strftime('%Y-%m', order_date)
            )
            ORDER BY month
        """,
    }

    with patch("app.main.generate_sql", return_value=plan):
        response = client.post(
            "/ask",
            json={"question": "How did revenue change from January to February?"},
        )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data["rows"]) == 2
    assert "24,350.00" in data["answer"]
    assert "+11.58%" in data["answer"]
