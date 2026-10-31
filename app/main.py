import json
import os
import sqlite3
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.sql_guard import SQLValidationError, validate_sql


load_dotenv()

ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = Path(
    os.getenv("DATABASE_PATH", str(ROOT / "data" / "sales.db"))
).resolve()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = FastAPI(
    title="Mini AI Business Intelligence Assistant",
    description="Answer business questions using Gemini, validated SQL, and SQLite.",
    version="1.0.0",
)
app.mount(
    "/frontend",
    StaticFiles(directory=ROOT / "frontend"),
    name="frontend"
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


def get_client():
    """Create a Gemini client using the API key from .env."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is missing from your .env file.",
        )

    return genai.Client(api_key=api_key)


def ask_gemini(prompt: str, json_response: bool = False) -> str:
    """Send a prompt to Gemini and return its text response."""

    client = get_client()

    config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json" if json_response else "text/plain",
        http_options=types.HttpOptions(timeout=60000),
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=config,
        )

        print("Gemini response received.", flush=True)

        if not response.text:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response.",
            )

        return response.text

    except HTTPException:
        raise

    except Exception as exc:
        # Avoid exposing API credentials or internal request details.
        print(f"Gemini error type: {type(exc).__name__}")
        print(f"Gemini error details: {exc}")


        raise HTTPException(
            status_code=502,
            detail=f"Gemini request failed: {type(exc).__name__}: {exc}",
        ) from exc


def generate_sql(question: str) -> dict:
    """Interpret a business question and generate SQL or request clarification."""

    prompt = f"""
You are the query planner for a business intelligence application.

The database contains exactly this table:

sales(
    transaction_id TEXT,
    order_date TEXT,
    product TEXT,
    category TEXT,
    region TEXT,
    sales_channel TEXT,
    quantity INTEGER,
    unit_price REAL,
    discount_amount REAL,
    status TEXT
)

Business rules:
1. Revenue = quantity * unit_price - discount_amount.
2. Revenue calculations must include only rows where
   LOWER(TRIM(status)) = 'completed'.
3. Other questions about transaction status must use the relevant status.
4. Do not invent columns, tables, data, or business facts.
5. Use SQLite-compatible SQL.
6. Generate exactly one read-only SELECT statement.
7. Reference only the sales table.
8. Use explicit columns rather than SELECT * when practical.
9. Use GROUP BY for aggregations and ORDER BY for rankings.
10. Use LIMIT for rankings when appropriate.
11. Dates are stored as YYYY-MM-DD strings.
12. If the requested information cannot be determined from the available
    columns, ask for clarification.
13. Do not reject a question merely because it is not a predefined example.
    Interpret any business question that can reasonably be answered using
    the available sales data.
14. If the question is unrelated to the sales dataset, explain the limitation.
15. Return a query plan, not the final business answer.

Return a JSON object in one of these formats:

{{"kind":"sql","sql":"SELECT ..."}}

or

{{"kind":"clarification","message":"Explain what is missing or unsupported."}}

User question:
{question}
"""
    print("DEBUG: Sending SQL-generation prompt to Gemini", flush=True)

    raw_response = ask_gemini(prompt, json_response=True)

    print("DEBUG: Gemini returned the SQL-generation response", flush=True)

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid JSON query plan.",
        ) from exc

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid query plan.",
        )

    if result.get("kind") == "clarification":
        message = result.get("message")

        if not isinstance(message, str) or not message.strip():
            message = "Please clarify your question."

        return {
            "kind": "clarification",
            "message": message,
        }

    if result.get("kind") != "sql":
        raise HTTPException(
            status_code=502,
            detail="Gemini did not return a supported query plan.",
        )

    sql = result.get("sql")

    if not isinstance(sql, str) or not sql.strip():
        raise HTTPException(
            status_code=502,
            detail="Gemini did not provide a SQL query.",
        )

    return {
        "kind": "sql",
        "sql": sql,
    }


def execute_read_only_sql(sql: str) -> tuple[list[str], list[dict]]:
    """Validate and execute a read-only query against SQLite."""

    try:
        safe_sql = validate_sql(sql)

    except SQLValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Generated SQL was rejected: {exc}",
        ) from exc

    if not DATABASE_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="The sales database does not exist. Load the CSV first.",
        )

    database_uri = DATABASE_PATH.as_uri() + "?mode=ro"

    try:
        with sqlite3.connect(
            database_uri,
            uri=True,
            timeout=5,
        ) as connection:

            connection.row_factory = sqlite3.Row

            # Prevent database modifications even if another safeguard fails.
            connection.execute("PRAGMA query_only = ON")

            # Limit the work performed by a generated query.
            connection.set_progress_handler(
                lambda: 1,
                1_000_000,
            )

            cursor = connection.execute(safe_sql)

            rows = cursor.fetchmany(201)

            if len(rows) > 200:
                raise HTTPException(
                    status_code=400,
                    detail="Too many results. Narrow your question.",
                )

            columns = [
                description[0]
                for description in (cursor.description or [])
            ]

            results = [
                dict(row)
                for row in rows
            ]

            return columns, results

    except HTTPException:
        raise

    except sqlite3.Error as exc:
        raise HTTPException(
            status_code=400,
            detail=f"The generated query could not be executed: {exc}",
        ) from exc


# def explain_results(
#     question: str,
#     columns: list[str],
#     rows: list[dict],
# ) -> str:
#     """Explain actual database results without inventing figures."""

#     prompt = f"""
# You are explaining results from a business intelligence database.

# Business question:
# {question}

# Database result columns:
# {json.dumps(columns)}

# Actual database result rows:
# {json.dumps(rows, default=str)}

# Instructions:
# - Use only the supplied question and database results.
# - Never invent numbers, totals, products, dates, or explanations.
# - If there are no rows, clearly say that no matching records were found.
# - Explain the results in simple language for a business user.
# - If the result is a number, state the number exactly as returned.
# - Do not claim a comparison or calculation that the results do not support.
# - Be concise.
# """

#     try:
#         return ask_gemini(prompt)

#     except HTTPException:
#         # Preserve the actual database results if Gemini is unavailable.
#         return (
#             "The database query succeeded, but an explanation could not "
#             "be generated. Inspect the returned columns and rows."
#         )


@app.get("/")
def root():
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database_exists": DATABASE_PATH.exists(),
        "model": MODEL,
        "provider": "Gemini",
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    """Answer a business question using database-backed results."""
    print("DEBUG 1: /ask endpoint reached", flush=True)

    question = request.question.strip()

    if len(question) < 3:
        raise HTTPException(
            status_code=422,
            detail="Please enter a meaningful business question.",
        )

    # Step 1: Ask Gemini to interpret the business question.
    print("DEBUG 2: Starting SQL generation", flush=True)
    plan = generate_sql(question)
    print("DEBUG 3: SQL generation finished", flush=True)

    # Step 2: Handle questions that need clarification.
    if plan["kind"] == "clarification":
        return {
            "question": question,
            "status": "needs_clarification",
            "answer": plan["message"],
            "sql": None,
            "columns": [],
            "rows": [],
        }

    # Step 3: Validate and execute the generated SQL.
    sql = plan["sql"]
    columns, rows = execute_read_only_sql(sql)

    # Step 4: Generate a deterministic answer from database results.
    if not rows:
        answer = "No matching records were found."

    elif (
        len(rows) == 2
        and "month" in rows[0]
        and any(key in rows[0] for key in ("revenue", "total_revenue"))
    ):
        # Explain a comparison between two months.
        revenue_key = (
            "revenue" if "revenue" in rows[0] else "total_revenue"
        )

        first_month = rows[0]["month"]
        second_month = rows[1]["month"]

        first_revenue = float(rows[0][revenue_key] or 0)
        second_revenue = float(rows[1][revenue_key] or 0)

        change = second_revenue - first_revenue

        if first_revenue != 0:
            percentage = change / abs(first_revenue) * 100
        else:
            percentage = None

        if change > 0:
            direction = "increased"
        elif change < 0:
            direction = "decreased"
        else:
            direction = "remained unchanged"

        answer = (
            f"Revenue {direction} by {abs(change):,.2f} "
            f"from {first_month} to {second_month}."
        )

        if percentage is not None:
            answer += f" Percentage change: {percentage:+.2f}%."

    elif (
        len(rows) == 1
        and len(columns) == 1
    ):
        value = rows[0][columns[0]]
        answer = f"{columns[0].replace('_', ' ').title()}: {value}"

    elif len(rows) == 1:
        details = ", ".join(
            f"{column.replace('_', ' ').title()}: {rows[0][column]}"
            for column in columns
        )
        answer = details

    elif (
        "month" in rows[0]
        and any(key in rows[0] for key in ("revenue", "total_revenue"))
    ):
        # Summarize a monthly revenue trend.
        revenue_key = (
            "revenue" if "revenue" in rows[0] else "total_revenue"
        )

        highest_month = max(
            rows,
            key=lambda row: float(row[revenue_key] or 0),
        )

        lowest_month = min(
            rows,
            key=lambda row: float(row[revenue_key] or 0),
        )

        answer = (
            f"Monthly revenue is available for {len(rows)} months. "
            f"The highest was {highest_month['month']} "
            f"({float(highest_month[revenue_key]):,.2f}), "
            f"and the lowest was {lowest_month['month']} "
            f"({float(lowest_month[revenue_key]):,.2f})."
        )

    else:
        answer = (
            f"The query returned {len(rows)} rows. "
            "See the returned rows for the supporting data."
        )
    return {
        "question": question,
        "status": "success",
        "answer": answer,
        "sql": sql,
        "columns": columns,
        "rows": rows,
    }