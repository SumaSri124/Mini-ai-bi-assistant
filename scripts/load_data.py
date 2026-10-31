import argparse
import sqlite3
from pathlib import Path

import pandas as pd


# Project root directory
ROOT = Path(__file__).resolve().parents[1]

# Default SQLite database location
DEFAULT_DB = ROOT / "data" / "sales.db"

# Expected columns in the assignment CSV
REQUIRED_COLUMNS = [
    "Transaction_Id",
    "Order_date",
    "Product",
    "Category",
    "Region",
    "Sales_channel",
    "Quantity",
    "Unit_price",
    "Discount_amount",
    "Status",
]


def clean_sales_csv(csv_path):
    """
    Read the CSV, validate records, and return cleaned data
    along with an import report.
    """

    df = pd.read_csv(csv_path)

    # Check whether all required columns exist.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    # Keep only the expected columns.
    df = df[REQUIRED_COLUMNS].copy()

    rows_read = len(df)

    # Remove unnecessary spaces from text columns.
    text_columns = [
        "Transaction_Id",
        "Product",
        "Category",
        "Region",
        "Sales_channel",
        "Status",
    ]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    # Convert dates and numeric columns into appropriate types.
    df["Order_date"] = pd.to_datetime(
        df["Order_date"],
	format="%d-%m-%Y",
        errors="coerce",
    )

    numeric_columns = [
        "Quantity",
        "Unit_price",
        "Discount_amount",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Begin by assuming all rows are valid.
    valid = pd.Series(True, index=df.index)

    # Required text fields cannot be empty.
    for column in text_columns:
        valid &= df[column].notna()
        valid &= df[column].str.len().fillna(0).gt(0)

    # The date must be valid.
    valid &= df["Order_date"].notna()

    # Quantity must be positive.
    valid &= df["Quantity"].notna()
    valid &= df["Quantity"] > 0

    # Unit price and discount cannot be negative.
    valid &= df["Unit_price"].notna()
    valid &= df["Unit_price"] >= 0

    valid &= df["Discount_amount"].notna()
    valid &= df["Discount_amount"] >= 0

    # A discount cannot exceed the gross transaction amount.
    gross_amount = df["Quantity"] * df["Unit_price"]

    valid &= df["Discount_amount"] <= gross_amount

    # Keep the first occurrence of each transaction ID.
    valid &= ~df["Transaction_Id"].duplicated(keep="first")

    # Remove invalid records.
    cleaned = df.loc[valid].copy()

    # Convert dates to ISO format for SQLite.
    cleaned["Order_date"] = (
        cleaned["Order_date"].dt.strftime("%Y-%m-%d")
    )

    # Quantity represents a count of items, so require whole numbers.
    whole_quantity = (
        cleaned["Quantity"] % 1 == 0
    )

    cleaned = cleaned.loc[whole_quantity].copy()

    cleaned["Quantity"] = cleaned["Quantity"].astype(int)
    cleaned["Unit_price"] = cleaned["Unit_price"].astype(float)
    cleaned["Discount_amount"] = (
        cleaned["Discount_amount"].astype(float)
    )

    # Generate an import report.
    report = {
        "rows_read": rows_read,
        "rows_imported": len(cleaned),
        "rows_skipped": rows_read - len(cleaned),
        "completed_rows": int(
            cleaned["Status"].str.casefold().eq("completed").sum()
        ),
        "non_completed_rows": int(
            cleaned["Status"].str.casefold().ne("completed").sum()
        ),
    }

    return cleaned, report


def load_csv(csv_path, db_path=DEFAULT_DB):
    """
    Load validated CSV records into SQLite.
    """

    csv_path = Path(csv_path)
    db_path = Path(db_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {csv_path}"
        )

    # Validate the CSV before modifying the database.
    cleaned, report = clean_sales_csv(csv_path)

    # Create the data directory if it doesn't exist.
    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Open the SQLite database.
    with sqlite3.connect(db_path) as connection:

        # Create a fresh sales table for this initial ingestion.
        connection.execute("DROP TABLE IF EXISTS sales")

        connection.execute(
            """
            CREATE TABLE sales (
                transaction_id TEXT PRIMARY KEY,
                order_date TEXT NOT NULL,
                product TEXT NOT NULL,
                category TEXT NOT NULL,
                region TEXT NOT NULL,
                sales_channel TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                discount_amount REAL NOT NULL
                    CHECK (discount_amount >= 0),
                status TEXT NOT NULL
            )
            """
        )

        # Rename the CSV columns to database-friendly names.
        cleaned = cleaned.rename(
            columns={
                "Transaction_Id": "transaction_id",
                "Order_date": "order_date",
                "Product": "product",
                "Category": "category",
                "Region": "region",
                "Sales_channel": "sales_channel",
                "Quantity": "quantity",
                "Unit_price": "unit_price",
                "Discount_amount": "discount_amount",
                "Status": "status",
            }
        )

        # Insert the cleaned records into SQLite.
        cleaned.to_sql(
            "sales",
            connection,
            if_exists="append",
            index=False,
        )

        # Add indexes to help common queries run faster.
        connection.execute(
            "CREATE INDEX idx_sales_order_date ON sales(order_date)"
        )

        connection.execute(
            "CREATE INDEX idx_sales_product ON sales(product)"
        )

        connection.execute(
            "CREATE INDEX idx_sales_region ON sales(region)"
        )

        connection.execute(
            "CREATE INDEX idx_sales_status ON sales(status)"
        )

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate and load sales CSV data into SQLite."
    )

    parser.add_argument(
        "csv",
        type=Path,
        help="Path to the sales CSV file",
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="SQLite database path",
    )

    args = parser.parse_args()

    report = load_csv(
        csv_path=args.csv,
        db_path=args.db,
    )

    print("\nCSV import completed successfully.")
    print(f"Database: {args.db.resolve()}")

    print("\nImport report:")

    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
