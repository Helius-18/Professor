import pyodbc

def get_connection():
    """
    Create and return a MSSQL database connection.
    """
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=your_server.database.windows.net;"
        "DATABASE=your_database;"
        "UID=your_username;"
        "PWD=your_password;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

from agno.tools import tool

@tool
def get_tables():
    """
    Get the list of tables in the database.
    """
    print("Fetching table names from database...")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)

    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return tables

@tool
def get_table_columns(table_name: str):
    """
    Get columns for a specific table.
    """
    print(f"Fetching columns for table: {table_name}")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, table_name)

    columns = [
        {
            "column": row.COLUMN_NAME,
            "type": row.DATA_TYPE,
            "nullable": row.IS_NULLABLE
        }
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return columns

@tool
def execute_query(query: str):
    """
    Execute a SQL query and return results.
    """
    print(f"Executing query:\n{query}")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)

        if cursor.description:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            result = [
                dict(zip(columns, row))
                for row in rows
            ]
        else:
            conn.commit()
            result = "Query executed successfully."

    except Exception as e:
        result = f"Error executing query: {str(e)}"

    finally:
        cursor.close()
        conn.close()

    return result

@tool
def get_foreign_keys():
    """
    Get foreign key relationships between tables.
    """
    print("Fetching foreign key relationships...")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            fk.name AS fk_name,
            tp.name AS parent_table,
            cp.name AS parent_column,
            tr.name AS referenced_table,
            cr.name AS referenced_column
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc
            ON fk.object_id = fkc.constraint_object_id
        JOIN sys.tables tp
            ON fkc.parent_object_id = tp.object_id
        JOIN sys.columns cp
            ON fkc.parent_object_id = cp.object_id
           AND fkc.parent_column_id = cp.column_id
        JOIN sys.tables tr
            ON fkc.referenced_object_id = tr.object_id
        JOIN sys.columns cr
            ON fkc.referenced_object_id = cr.object_id
           AND fkc.referenced_column_id = cr.column_id
        ORDER BY parent_table
    """)

    fks = [
        {
            "from_table": row.parent_table,
            "from_column": row.parent_column,
            "to_table": row.referenced_table,
            "to_column": row.referenced_column
        }
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return fks
