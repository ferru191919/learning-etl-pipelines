import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "5.0_orders_branching.db"
CUSTOMERS_TABLE = "customers"


def create_database_and_tables():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {CUSTOMERS_TABLE} (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                country TEXT NOT NULL,
                signup_date TEXT NOT NULL
            )
        """)

        logger.info(f"Table '{CUSTOMERS_TABLE}' is ready.")


def seed_customers():
    customers_data = [
        (1, "Alice Johnson", "alice.johnson@example.com", "USA", "2024-01-15"),
        (2, "Bob Smith", "bob.smith@example.com", "Canada", "2024-02-20"),
        (3, "Carla Rossi", "carla.rossi@example.com", "Italy", "2024-03-10"),
        (4, "David Lee", "david.lee@example.com", "UK", "2024-04-05"),
        (5, "Emma Brown", "emma.brown@example.com", "Germany", "2024-05-12"),
        (6, "Frank Martin", "frank.martin@example.com", "France", "2024-06-01"),
        (7, "Giulia Bianchi", "giulia.bianchi@example.com", "Italy", "2024-06-18"),
        (8, "Henry Walker", "henry.walker@example.com", "USA", "2024-07-07"),
        (9, "Isabel Garcia", "isabel.garcia@example.com", "Spain", "2024-08-14"),
        (10, "Jack Wilson", "jack.wilson@example.com", "Australia", "2024-09-03")
    ]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(f"DELETE FROM {CUSTOMERS_TABLE}")

        cursor.executemany(f"""
            INSERT INTO {CUSTOMERS_TABLE}
            (customer_id, customer_name, email, country, signup_date)
            VALUES (?, ?, ?, ?, ?)
        """, customers_data)

        logger.info(f"Seeded {len(customers_data)} rows into '{CUSTOMERS_TABLE}'.")


def main():
    logger.info("Starting database setup...")
    create_database_and_tables()
    seed_customers()
    logger.info(f"Database setup complete: {DB_PATH}")


if __name__ == "__main__":
    main()