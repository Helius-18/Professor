"""Create a small sample database with one DB tool and one API tool for testing.

Run this script to initialize `app.db` in the `Professor` folder and insert sample rows.
"""
from models import init_db, get_session, Connection, Tool


def create_samples(db_url: str = "sqlite:///app.db"):
    init_db(db_url)
    session = get_session(db_url)
    try:
        # DB connection (uses the same sqlite file)
        db_conn = Connection(
            connection_type="DB",
            server_name=db_url,
        )
        session.add(db_conn)
        session.flush()

        db_tool = Tool(
            tool_name="sample_select",
            tool_type="DB",
            connection_id=db_conn.id,
            content="SELECT 1 as sample_value",
        )
        session.add(db_tool)

        # API connection example (httpbin)
        api_conn = Connection(
            connection_type="API",
            endpoint="https://httpbin.org",
            request_type="GET",
        )
        session.add(api_conn)
        session.flush()

        api_tool = Tool(
            tool_name="httpbin_get",
            tool_type="API",
            connection_id=api_conn.id,
            content="get",
        )
        session.add(api_tool)

        session.commit()
        print("Sample data created.")
    finally:
        session.close()


if __name__ == "__main__":
    create_samples()
