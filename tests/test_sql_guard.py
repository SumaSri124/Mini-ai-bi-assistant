import pytest

from app.sql_guard import SQLValidationError, validate_sql


def test_valid_select_query():
    sql = "SELECT COUNT(*) FROM sales"

    result = validate_sql(sql)

    assert "SELECT" in result.upper()
    assert "SALES" in result.upper()


def test_valid_revenue_query():
    sql = """
        SELECT SUM(quantity * unit_price - discount_amount) AS total_revenue
        FROM sales
        WHERE LOWER(TRIM(status)) = 'completed'
    """

    result = validate_sql(sql)

    assert "SUM" in result.upper()
    assert "TOTAL_REVENUE" in result.upper()


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "   ",
    ],
)
def test_rejects_empty_sql(sql):
    with pytest.raises(SQLValidationError, match="empty"):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM sales",
        "DROP TABLE sales",
        "UPDATE sales SET quantity = 0",
        "INSERT INTO sales VALUES ('test')",
        "CREATE TABLE example (id INTEGER)",
    ],
)
def test_rejects_modification_queries(sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_rejects_multiple_statements():
    sql = "SELECT * FROM sales; DELETE FROM sales"

    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_rejects_other_tables():
    sql = "SELECT * FROM customers"

    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql(sql)


def test_rejects_join_with_another_table():
    sql = """
        SELECT sales.product
        FROM sales
        JOIN customers ON sales.transaction_id = customers.id
    """

    with pytest.raises(SQLValidationError, match="not permitted"):
        validate_sql(sql)


def test_rejects_qualified_table_names():
    sql = "SELECT * FROM other_database.sales"

    with pytest.raises(SQLValidationError, match="Qualified table names"):
        validate_sql(sql)


def test_rejects_invalid_sql():
    sql = "SELECT FROM sales WHERE"

    with pytest.raises(SQLValidationError):
        validate_sql(sql)


def test_allows_aggregation_and_grouping():
    sql = """
        SELECT region, SUM(quantity * unit_price - discount_amount) AS revenue
        FROM sales
        GROUP BY region
        ORDER BY revenue DESC
    """

    result = validate_sql(sql)

    assert "GROUP BY" in result.upper()
    assert "ORDER BY" in result.upper()
