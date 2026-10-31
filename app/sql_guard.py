import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    """Raised when generated SQL violates our safety rules."""


def validate_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise SQLValidationError("The generated SQL is empty.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError("The generated SQL is invalid.") from exc

    # Only one SQL statement is allowed.
    statements = [statement for statement in statements if statement is not None]

    if len(statements) != 1:
        raise SQLValidationError("Only one SQL statement is allowed.")

    tree = statements[0]

    # Only SELECT queries are permitted.
    if not isinstance(tree, exp.Select):
        raise SQLValidationError("Only SELECT queries are permitted.")

    # Queries may reference only the sales table.
    for table in tree.find_all(exp.Table):
        if table.name.lower() != "sales":
            raise SQLValidationError(
                f"Access to table '{table.name}' is not permitted."
            )

        # Reject database/schema-qualified table references.
        if table.db or table.catalog:
            raise SQLValidationError(
                "Qualified table names are not permitted."
            )

    # Block SELECT INTO, which can create a table in some SQL dialects.
    if tree.args.get("into") is not None:
        raise SQLValidationError("SELECT INTO is not permitted.")

    return tree.sql(dialect="sqlite")