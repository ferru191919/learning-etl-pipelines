# Customer data source (created by AI)
# RUN THIS BEFORE THE PIPELINE


import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("5.1_customers_data_source.db")


def get_connection():
    """
    Create a connection to the SQLite database.
    If the file does not exist, it will be created.
    """
    conn = sqlite3.connect(DB_PATH)
    # Enforce foreign keys if we add more tables later
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_customers_table(conn: sqlite3.Connection) -> None:
    """
    Create the customers table with realistic constraints.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id     INTEGER PRIMARY KEY,
        first_name      TEXT NOT NULL,
        last_name       TEXT NOT NULL,
        email           TEXT UNIQUE,
        country         TEXT NOT NULL,
        created_at      TEXT NOT NULL,
        CHECK (length(country) = 2)
    );
    """
    conn.execute(create_table_sql)


def seed_customers(conn: sqlite3.Connection) -> None:
    """
    Insert a small but realistic customer dataset.
    Uses INSERT OR IGNORE so re-running the script is idempotent.
    """
    customers = [
        # Normal Italian customer
        (1, "Luca", "Rossi", "luca.rossi@example.com", "IT", "2022-01-15T10:30:00"),
        # No email (allowed)
        (2, "Maria", "Bianchi", None, "IT", "2021-11-03T09:15:00"),
        # Non-Italian customer
        (3, "Hans", "Müller", "hans.mueller@example.de", "DE", "2020-06-20T14:45:00"),
        # Older created_at
        (4, "John", "Smith", "john.smith@example.com", "US", "2018-03-12T08:00:00"),
        # Another edge case, still valid
        (5, "Sofia", "Verdi", "sofia.verdi@example.com", "IT", "2024-12-31T23:59:59"),
    ]

    insert_sql = """
    INSERT OR IGNORE INTO customers (
        customer_id, first_name, last_name, email, country, created_at
    ) VALUES (?, ?, ?, ?, ?, ?);
    """

    conn.executemany(insert_sql, customers)


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        create_customers_table(conn)
        seed_customers(conn)
        conn.commit()

        # Simple smoke test: print all customers
        cur = conn.execute("SELECT * FROM customers;")
        rows = cur.fetchall()
        print("Customers in source DB:")
        for row in rows:
            print(row)
    finally:
        conn.close()


if __name__ == "__main__":
    main()