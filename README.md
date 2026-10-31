# Mini AI Business Intelligence Assistant

A lightweight AI-powered business intelligence application that allows users to ask natural-language questions about sales data and receive answers supported by SQL queries and actual database results.

The application uses Google Gemini to interpret questions and generate SQL, SQLite to store and query sales data, FastAPI to provide the backend API, and HTML, CSS, and JavaScript for the user interface.

## Features

- **CSV Data Ingestion:** Loads sales data from a CSV file into an SQLite database.
- **Data Validation:** Handles invalid records and tracks skipped rows during ingestion.
- **Natural-Language Queries:** Allows users to ask business questions in plain English.
- **AI-Assisted SQL Generation:** Uses Google Gemini to interpret questions and generate SQL queries.
- **SQL Validation:** Restricts queries to a single `SELECT` statement against the authorized `sales` table.
- **Read-Only Database Access:** Executes queries using a read-only SQLite connection.
- **Business Analytics:** Supports revenue calculations, product comparisons, regional analysis, and monthly trends.
- **Supporting Data:** Displays answers, query results, and the SQL used to generate them.
- **Automated Testing:** Includes tests for SQL validation, API behavior, and analytical results.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend framework | FastAPI |
| AI model | Google Gemini |
| Database | SQLite |
| SQL validation | SQLGlot |
| Frontend | HTML, CSS, JavaScript |
| Testing | pytest |
| API testing | FastAPI TestClient |

## Project Structure

```text
mini-ai-bi-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── sql_guard.py
├── data/
│   ├── sales_data.csv
│   └── sales.db
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

## Architecture

The application follows a simple request-processing pipeline:

1. The user enters a natural-language question in the web interface.
2. The frontend sends the question to the FastAPI `/ask` endpoint.
3. The backend sends the question and database schema to Gemini.
4. Gemini returns a SQL query plan or a clarification response.
5. The SQL validation layer checks the generated query.
6. Valid queries execute against the SQLite database using read-only access.
7. The backend constructs an answer from the query results.
8. The frontend displays the answer, supporting data, and SQL query.

The `/health` endpoint reports application and database status.

## Dataset and Data Ingestion

The source dataset is `data/sales_data.csv`.

It contains the following columns:

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

The ingestion script validates records and loads accepted data into `data/sales.db`.

To load the dataset:

```bash
python scripts/load_data.py
```

The current dataset contains 49 imported records, including 48 completed transactions and one returned transaction. Two invalid records were skipped during ingestion.

## Setup and Installation

### Prerequisites

- Python 3.10 or a compatible version.
- Internet connectivity to access the configured Google Gemini API.
- A valid Gemini API key.
- Campus proxy configuration, if required by the network.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd mini-ai-bi-assistant
```

Replace the placeholder with the actual repository URL.

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and provide the required Gemini configuration. For example:

```text
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model
```

Use a model supported by your Gemini API account. Never commit your real API key or other credentials to Git.

If your network requires an authenticated proxy, configure the proxy in the environment before starting the application. Do not put proxy passwords in the README or commit them to the repository.

### 5. Prepare the database

If the database needs to be created or refreshed, run:

```bash
python scripts/load_data.py
```

**Note:** Running the loader may replace or refresh existing database contents, depending on its implementation. Back up any data you need to preserve before rerunning it.

## Running the Application

Activate the virtual environment and start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open the dashboard in a browser:

```text
http://127.0.0.1:8000
```

The interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The health endpoint is:

```text
http://127.0.0.1:8000/health
```

Keep the terminal running while using the dashboard.

## Example Business Questions

The application supports the following analytical questions:

1. What is the total revenue?
2. Which product generated the highest revenue?
3. What is the monthly revenue trend?
4. Which region generated the highest sales?
5. How did revenue change from January to February?

Revenue is calculated as:

```text
Revenue = Quantity × Unit Price − Discount Amount
```

Revenue calculations use completed transactions.

### Reference Results

For the current dataset:

| Metric | Expected result |
|---|---:|
| Total revenue | 1,439,200 |
| Highest-revenue product | Monitor |
| Highest-revenue region | South |
| Highest monthly revenue | May 2026: 318,500 |
| Lowest monthly revenue | January 2026: 210,250 |
| January-to-February change | Increase of 24,350 (+11.58%) |

These figures are reference results for the current dataset and business rules.

## SQL Safety

The application uses several safeguards for generated SQL:

- SQLGlot parses and validates the generated query.
- Only one SQL statement is allowed.
- Only `SELECT` statements are permitted.
- Queries may reference only the authorized `sales` table.
- Qualified table names are rejected.
- SQLite is opened in read-only mode.
- SQLite query-only mode is enabled.
- Query execution has resource and result-size limits.

These controls reduce the risk of destructive database operations. They do not guarantee that every generated query correctly represents the user's intent. Business-rule validation and unsupported-question handling remain important.

## Running Tests

Activate the virtual environment, then run:

```bash
pytest -v
```

The test suite covers:

- SQL validation and rejection of unsafe statements.
- API input validation and error handling.
- Expected results for the required analytical questions.

The current test suite contains 27 tests, which passed during development.

## Limitations

- Answers depend on the accuracy of the generated SQL.
- Incorrect SQL can produce incorrect analytical results even when the query is safe.
- Questions requiring unavailable information, such as profit margins without cost data, cannot be answered reliably.
- Forecasting and external data sources are not currently implemented.
- Gemini availability depends on network connectivity, proxy configuration, API access, and model availability.
- The application is a demonstration project and has not been hardened for production deployment.

## Future Improvements

- Add stronger validation that checks whether generated SQL matches the original question.
- Expand tests for unsupported and ambiguous questions.
- Improve query timeouts and user-facing error messages.
- Add richer charts for trends and comparisons.
- Improve handling of missing data and unusual business cases.
- Add user authentication and deployment hardening if required.

## Security Notes

- Never commit `.env` files containing secrets.
- Keep API keys and proxy credentials private.
- Use read-only database access for analytical queries.
- Validate all generated SQL before execution.
- Avoid exposing internal exceptions or sensitive configuration details to users.
