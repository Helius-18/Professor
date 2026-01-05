from agno.tools import tool


@tool
def get_tables():
    """
    Get the list of tables

    Returns:
        list: A list of table names.
    """
    print("Fetching table names...")
    return ["Property", "Unit", "Tenants", "Lease", "Payments"]


@tool
def get_table_columns(table_name: str):
    """
    Get the columns of a specific table.

    Args:
        table_name (str): The name of the table.

    Returns:
        list: A list of column names for the specified table.
    """
    print(f"Fetching columns for table: {table_name}")
    tables = {
        "Property": ["id", "name", "address", "city", "state", "zip_code"],
        "Unit": ["id", "property_id", "unit_number", "bedrooms", "bathrooms", "rent"],
        "Tenants": ["id", "first_name", "last_name", "email", "phone_number"],
        "Lease": ["id", "tenant_id", "unit_id", "start_date", "end_date", "rent_amount"],
        "Payments": ["id", "lease_id", "payment_date", "amount", "payment_method"],
    }
    return tables.get(table_name, [])

@tool
def execute_query(query: str):
    """
    Execute a SQL query against the property management database.

    Args:
        query (str): The SQL query to execute.

    Returns:
        str: The result of the query execution.
    """
    print(f"Executing query: {query}")
    # Placeholder implementation
    return f"Executed query: {query}"