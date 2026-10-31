# Mini AI Business Intelligence Assistant

A lightweight business intelligence application that allows users to ask questions about sales data in natural language and receive answers backed by SQL queries and database results.

The application combines **Google Gemini, FastAPI, SQLite, SQLGlot, HTML, CSS, and JavaScript** to provide an AI-assisted sales analytics experience.

**Repository:** https://github.com/SumaSri124/AI-bi-assistant

## 1. Problem Statement

Business data is often stored in tables that require users to understand SQL before they can investigate trends or compare performance. This project provides a simple interface for asking common sales-analysis questions in plain English.

The application uses an AI model to interpret a question and propose a query, but generated SQL is not automatically trusted. A validation layer checks the query before database execution, and the response includes supporting results so users can inspect the basis of an answer.

## 2. Features

- **CSV ingestion:** Loads the supplied sales dataset into SQLite.
- **Data validation:** Checks records during ingestion and skips invalid rows.
- **Natural-language questions:** Accepts business questions through a web interface.
- **AI-assisted query generation:** Uses Google Gemini to generate SQL based on the question, available schema, and business rules.
- **SQL validation:** Uses SQLGlot to parse and restrict generated SQL before execution.
- **Read-only analytics:** Executes permitted queries against SQLite using read-only access and query restrictions.
- **Business metrics:** Supports revenue totals, product and regional comparisons, monthly trends, and month-to-month changes.
- **Transparent responses:** Returns answers alongside SQL and supporting result data.
- **REST API:** Provides endpoints for asking questions and checking application health.
- **Automated tests:** Covers SQL safety, API behavior, and analytical calculations.

## 3. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Programming language | Python | Backend logic, ingestion, and tests |
| API framework | FastAPI | Handles requests and returns structured responses |
| Language model | Google Gemini | Interprets questions and proposes SQL |
| Database | SQLite | Stores the prepared sales records |
| SQL validation | SQLGlot | Parses and validates generated SQL |
| Frontend | HTML, CSS, JavaScript | Provides the user-facing dashboard |
| Testing | pytest, FastAPI TestClient | Tests validation, API behavior, and analytics |

## 4. System Architecture

```text
                  User asks a business question
                              |
                              v
                    Browser-based dashboard
                              |
                              v
                       FastAPI backend
                              |
                              v
                       Google Gemini
                    Proposes a SQL query
                              |
                              v
                        SQLGlot guard
                  Validates the generated SQL
                              |
                    Valid query only
                              |
                              v
                         SQLite database
                    Executes read-only query
                              |
                              v
                     Structured API response
                    Answer + SQL + result data
                              |
                              v
                     Dashboard displays results
```

### Request Flow

1. The user submits a business question through the dashboard.
2. The frontend sends the question to the FastAPI `POST /ask` endpoint.
3. The backend provides the question, relevant database schema, and business rules to Gemini.
4. Gemini proposes a SQL query or indicates that the question cannot be handled.
5. The SQL validation layer checks the generated query against the application's restrictions.
6. If validation succeeds, the query is executed against SQLite using read-only access and execution/result limits.
7. The backend builds a structured response using the database result.
8. The frontend displays the answer and supporting data.

The language model proposes a query, while the database computes the numerical result. This keeps analytical calculations grounded in the stored dataset instead of relying on the model to invent figures.

## 5. Project Structure

```text
mini-ai-bi-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── sql_guard.py
├── data/
│   └── sales_data.csv
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── scripts/
│   └── load_data.py
├── tests/
│   ├── conftest.py
│   ├── test_analytics.py
│   ├── test_api.py
│   └── test_sql_guard.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The SQLite database is generated locally by the ingestion script and does not need to be committed to the repository.

## 6. Dataset and Data Ingestion

The application uses `data/sales_data.csv`.

The dataset contains the following fields:

- `Transaction_Id`
- `Order_date`
- `Product`
- `Category`
- `Region`
- `Sales_channel`
- `Quantity`
- `Unit_price`
- `Discount_amount`
- `Status`

The ingestion script validates records and loads accepted records into `data/sales.db`.

During the reported dataset load:

- **51** records were read.
- **49** records were imported.
- **2** invalid records were skipped.
- The imported records included **48 completed transactions** and **1 returned transaction**.

The skipped records included a transaction with zero quantity and a transaction with a missing unit price.

This validation prevents those invalid records from silently entering the analytical dataset.

To create or refresh the local database, run:

```bash
python scripts/load_data.py
```

Run this command whenever you need to rebuild the database from the CSV.

## 7. Setup and Execution

### Prerequisites

- Python 3.10 or a compatible version
- A Google Gemini API key with access to a supported model
- Internet access for model requests

### Step 1: Clone the repository

```bash
git clone https://github.com/SumaSri124/AI-bi-assistant.git
cd AI-bi-assistant
```

### Step 2: Create a virtual environment

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the environment

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` and configure the Gemini settings required by the application.

Example:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Use the variable names expected by `.env.example` and the application configuration. Replace the example values with your own valid configuration.

**Security:** Keep API keys private. Never commit `.env` or hard-code secrets in source files.

### Step 5: Load the dataset

```bash
python scripts/load_data.py
```

This prepares the local SQLite database from the supplied CSV file.

### Step 6: Start the application

```bash
uvicorn app.main:app --reload
```

Keep the server running while using the dashboard.

| Resource | Address |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| API documentation | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/health |

The dashboard requires the backend server to be running.

## 8. Example Business Questions

The application is designed to answer questions such as:

1. What is the total revenue?
2. Which product generated the highest revenue?
3. What is the monthly revenue trend?
4. Which region generated the highest sales?
5. How did revenue change from January to February?

### Revenue Calculation

Revenue is calculated using the following rule:

```text
Revenue = Quantity × Unit Price − Discount Amount
```

The reported completed-sales revenue metrics exclude returned transactions.

### Reference Results

The following results were reported for the supplied dataset:

| Metric | Result |
|---|---:|
| Total completed revenue | 1,439,200 |
| Highest-revenue product | Monitor |
| Highest-revenue region | South |
| Highest monthly revenue | May 2026 — 318,500 |
| Lowest monthly revenue | January 2026 — 210,250 |
| January-to-February revenue change | +24,350 (+11.58%) |

These values apply to the current sample data and the business rules described above. Results may change if the dataset or calculation rules change.

## 9. API Overview

### `POST /ask`

Accepts a natural-language business question and returns a structured response containing the answer and supporting query information.

Example request:

```json
{
  "question": "What is the total revenue?"
}
```

The response structure includes fields for:

- Request status
- Answer
- Generated SQL
- Result columns
- Result rows

The exact response and error formats depend on the application's request-handling and validation paths.

### `GET /health`

Returns application and database health information.

For the precise request and response schemas, start the application and open:

```text
http://127.0.0.1:8000/docs
```

## 10. SQL Safety and Validation

AI-generated SQL is treated as untrusted input.

The application includes several safeguards:

- SQLGlot parses the generated query before execution.
- Only one SQL statement is accepted.
- The top-level statement must be a `SELECT`.
- Queries are restricted to the authorized `sales` table.
- Qualified table names and `SELECT INTO` are rejected.
- SQLite is opened in read-only mode.
- SQLite query-only mode is enabled.
- Query execution time and result size are limited.

These safeguards reduce the risk of destructive queries and limit the amount of work a query can perform.

However, **syntactically safe SQL is not necessarily semantically correct SQL**. A query can pass validation but still use an incorrect filter, grouping, or interpretation of the user's question. Semantic validation and better handling of ambiguous requests remain important areas for improvement.

## 11. Automated Testing

Run the test suite from the project root with the virtual environment activated:

```bash
pytest -v
```

The reported development test run completed with **27 passing tests**.

The tests cover:

### SQL Guard Tests

Check accepted queries and rejection of disallowed or malformed SQL.

### API Tests

Check request handling, valid and invalid inputs, and error-handling paths.

### Analytics Tests

Check expected results for core sales questions and analytical calculations.

The API and analytics tests use controlled query-generation behavior so backend logic can be tested without depending on a live model response for every test. This makes the tests more repeatable, but it does not prove that the live model will interpret every possible question correctly.

Run the test suite again after making changes and use the latest test output as the authoritative result.

## 12. Key Engineering Decisions

### Separate Query Generation from Execution

Allowing a language model to generate SQL and executing it immediately would introduce unnecessary risk.

The application separates query generation from database execution. The generated query must pass validation before it can be executed.

### Use the Database for Numerical Calculations

The model helps translate natural language into a query, while SQLite calculates the result from the stored data.

This separation makes results reproducible for a given dataset, query, and set of business rules.

### Use a Lightweight Architecture

FastAPI provides the API layer, SQLite avoids requiring a separate database server for this sample, and a plain HTML/CSS/JavaScript frontend keeps the interface simple to run.

### Test Components Separately

The SQL guard has dedicated tests separate from API and analytics tests. This makes it easier to identify whether a failure originates in query validation, request handling, or analytical calculations.

## 13. Limitations

- Answer quality depends on the SQL proposed by the language model.
- SQL validation checks query structure and permitted access but cannot guarantee semantic correctness.
- Ambiguous questions and questions outside the available schema may not always be interpreted as intended.
- The dataset is a small sample rather than a production data warehouse.
- Forecasting and external data integration are not implemented.
- Authentication and multi-user access controls are not implemented.
- Model requests require valid API configuration and model availability.
- The application is a demonstration project and has not been hardened for production use.

## 14. Future Improvements

With additional development time, the following improvements would be valuable:

1. **Semantic validation:** Check the generated query against the requested metric, grouping, filters, and date range.
2. **Clarification flow:** Ask follow-up questions when a request is ambiguous instead of guessing.
3. **Expanded negative tests:** Add more unsupported-question, malformed-output, timeout, and unusual-data cases.
4. **Improved visualizations:** Select appropriate chart types based on the returned data and make trends easier to compare.
5. **Observability:** Add structured logs and clearer error categories without exposing secrets or internal details.
6. **Production readiness:** Add authentication, deployment configuration, and operational monitoring if the project is extended beyond a local demonstration.

## 15. Security Notes

- Keep API keys in local environment configuration.
- Do not commit `.env` files, generated databases, or virtual-environment directories.
- Validate model-generated SQL before execution.
- Keep analytical database access read-only.
- Return useful error messages without exposing credentials or sensitive internal details.

---
