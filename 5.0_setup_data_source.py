### RUN THIS BEFORE THE PIPELINE ###

import sqlite3
from pathlib import Path

DB_PATH = Path("5.0_retail_data_source.db")


def get_connection():
    """
    Create a connection to the SQLite database.
    If the file does not exist, it will be created.
    """
    conn = sqlite3.connect(DB_PATH)
    # Foreign keys must be enabled per connection in SQLite
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
        email           TEXT NOT NULL,
        country         TEXT,
        created_at      TEXT,
        CHECK (length(country) = 2)
    );
    """
    conn.execute(create_table_sql)


def create_orders_table(conn: sqlite3.Connection) -> None:
    """
    Create the orders table.
    Includes a foreign key to customers, but leaves room for messy values
    that are still technically valid at the source level.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS orders (
        order_id         INTEGER PRIMARY KEY,
        customer_id      INTEGER NOT NULL,
        order_date       TEXT NOT NULL,
        product_name     TEXT NOT NULL,
        quantity         INTEGER,
        unit_price       REAL,
        currency         TEXT,
        order_status     TEXT,
        shipping_country TEXT,
        sales_channel    TEXT,
        notes            TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """
    conn.execute(create_table_sql)


def seed_customers(conn: sqlite3.Connection) -> None:
    """
    Insert a small but realistic customer dataset.
    Uses INSERT OR IGNORE so re-running the script is idempotent.
    """
    customers = [
        (1, "Luca", "Rossi", "luca.rossi@example.com", "IT", "2022-01-15T10:30:00"),
        (2, "Maria", "Bianchi", None, "IT", "2021-11-03T09:15:00"),
        (3, "Hans", "Müller", "hans.mueller@example.de", "DE", "2020-06-20T14:45:00"),
        (4, "John", "Smith", "john.smith@example.com", "US", "2018-03-12T08:00:00"),
        (5, "Sofia", "Verdi", "sofia.verdi@example.com", "IT", "2024-12-31T23:59:59"),
    ]

    insert_sql = """
    INSERT OR IGNORE INTO customers (
        customer_id, first_name, last_name, email, country, created_at
    ) VALUES (?, ?, ?, ?, ?, ?);
    """

    conn.executemany(insert_sql, customers)


def seed_orders(conn: sqlite3.Connection) -> None:
    """
    Insert a deliberately messy orders dataset for pipeline practice.

    Examples of messy-but-valid source data:
    - inconsistent date formats
    - product naming variations
    - nulls in optional fields
    - different casing / whitespace in categorical fields
    - negative quantity (return/correction style data)
    - zero price
    - country mismatches between customer and shipping destination
    """
    orders = [
        # Clean-ish row
        (1001, 1, "2025-01-10", "Tennis Balls", 2, 7.99, "EUR", "shipped", "IT", "online", None),

        # Different date format, upper-case status/channel
        (1002, 1, "10/01/2025", "tennis balls", 1, 7.99, "EUR", "SHIPPED", "IT", "ONLINE", "repeat order"),

        # Null quantity, trailing spaces in product, mixed-case country
        (1003, 2, "2025-02-03T14:22:00", "Protein Bar   ", None, 2.49, "EUR", "pending", "it", "store", None),

        # Different product spelling, blank notes
        (1004, 3, "2025/02/15", "protein-bar", 6, 2.39, "EUR", "Pending", "DE", "Store", ""),

        # Negative quantity to simulate return/correction
        (1005, 4, "2025-03-01", "Energy Drink", -1, 1.99, "USD", "returned", "US", "retail", "customer return"),

        # Zero unit price
        (1006, 4, "2025-03-05", "Shaker Bottle", 1, 0.0, "USD", "completed", "US", "Retail", "promo item"),

        # Leading/trailing spaces in status and channel
        (1007, 5, "2025-04-20 09:30:00", "Whey Protein", 1, 29.90, "EUR", " delivered ", "IT", " online ", None),

        # Shipping country differs from customer country
        (1008, 5, "2025-04-21", "Creatine Monohydrate", 2, 18.50, "EUR", "delivered", "FR", "online", "gift shipment"),

        # Null currency
        (1009, 3, "2025-05-01", "Electrolyte Tabs", 3, 5.75, None, "shipped", "DE", "marketplace", None),

        # Duplicate-like business record with formatting differences
        (1010, 1, "2025-01-10", "TENNIS BALLS", 2, 7.990, "EUR", "Shipped", "IT", "Online", "possible duplicate style row"),
    ]

    insert_sql = """
    INSERT OR IGNORE INTO orders (
        order_id, customer_id, order_date, product_name, quantity,
        unit_price, currency, order_status, shipping_country,
        sales_channel, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    conn.executemany(insert_sql, orders)


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        create_customers_table(conn)
        create_orders_table(conn)

        seed_customers(conn)
        seed_orders(conn)

        conn.commit()

        # Simple smoke tests
        print("Customers in source DB:")
        cur = conn.execute("SELECT * FROM customers;")
        for row in cur.fetchall():
            print(row)

        print("\nOrders in source DB:")
        cur = conn.execute("SELECT * FROM orders;")
        for row in cur.fetchall():
            print(row)

    finally:
        conn.close()


if __name__ == "__main__":
    main()