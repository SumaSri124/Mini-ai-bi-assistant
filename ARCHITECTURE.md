##Architecture — Mini AI Business Intelligence Assistant

This document focuses on component boundaries and how requests and data move through the application. General setup instructions, feature descriptions, example questions, and detailed test results remain in `README.md`.

## Component responsibilities

| Component | Responsibility |
|---|---|
| Browser dashboard (`frontend/`) | Collects a natural-language question and displays the answer, generated SQL, and supporting result data. |
| FastAPI (`app/main.py`) | Handles the `POST /ask` request, coordinates query generation, validation, database execution, and response formatting. Also exposes `GET /health`. |
| Google Gemini | Proposes a SQL query using the user's question, relevant schema, and business rules. Its output is untrusted until validated. |
| SQL guard (`app/sql_guard.py`, using SQLGlot) | Parses and checks the proposed SQL against the application's restrictions before execution. |
| SQLite (`data/sales.db`) | Stores ingested sales records and computes results by executing permitted queries with read-only access. |
| Ingestion script (`scripts/load_data.py`) | Reads `data/sales_data.csv`, validates records, skips invalid rows, and builds or refreshes the local database. |
| Tests (`tests/`) | Exercise SQL validation, API behaviour, and analytics logic. |

## Query request flow

1. The user submits a question in the browser dashboard.
2. The frontend sends the question to `POST /ask`.
3. FastAPI provides Gemini with the question, relevant database schema, and business rules.
4. Gemini returns a proposed SQL query, or indicates that the question cannot be handled.
5. The SQL guard parses and validates the proposed query.
6. If the query is rejected, the backend returns an error and does not execute it.
7. If accepted, the backend executes the query against SQLite with read-only access and execution/result limits.
8. FastAPI returns a structured response containing the answer and supporting query/result information.
9. The dashboard displays the response.

**Trust boundary:** Gemini proposes a query; it does not supply the trusted numerical result. SQLite computes the result from the stored data. SQL validation reduces risk but does not guarantee that a query correctly captures the user's intended meaning.

## Data ingestion flow

1. `scripts/load_data.py` reads `data/sales_data.csv`.
2. The loader validates records and skips invalid rows.
3. Accepted records are written to `data/sales.db`.
4. The API reads from this local database when answering questions.

The database is generated locally and should not need to be committed to the repository.

## Important boundaries and safeguards

- Only a single permitted SQL query should proceed to execution.
- The SQL guard restricts query type and table access; SQLite is also configured for read-only/query-only access.
- Query execution time and returned result size are limited.
- Model output and user input should be treated as untrusted.
- Keep credentials in local `.env` configuration; commit only placeholder variable names in `.env.example`.
- Tests should cover the SQL guard, API request/error paths, and analytical calculations separately.
