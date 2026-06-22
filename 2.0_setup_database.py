# This will generate a SQLite database
# You must run this file (only once) to create the database for Exercise '2.Multi_table_etl_orders.py'
# This SQLite DB will be the data source for the 'extract' function in Exercise 2

import sqlite3

DB_PATH = "2.0_ecommerce.db"

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            first_name  TEXT,
            last_name   TEXT,
            email       TEXT,
            country     TEXT,
            created_at  TEXT
        );

        INSERT OR IGNORE INTO users VALUES
            (1, 'alice',   'Smith',   'alice@email.com',   ' ',              '2023-01-10'),
            (2, 'Bob',     'Jones',   'bob@email.com',     'US',             '2023-02-15'),
            (3, 'clara',   'brown',   'clara@email.com',   'DE',             '2023-03-20'),
            (4, 'David',   'wilson',  ' ',                 'France',         'April 25th 2023'),
            (5, 'Eva',     'Taylor',  'eva@email.com',     'IT',             '2023-05-30'),
            (6, 'frank',   'Martin',  'frank@email.com',   'United States',  '2023-06-05'),
            (7, 'Georgia', 'Lee',     ' ',                 'UK',             '05.12.2023');

        CREATE TABLE IF NOT EXISTS orders (
            order_id    INTEGER PRIMARY KEY,
            user_id     INTEGER,
            product     TEXT,
            amount_usd  REAL,
            status      TEXT,
            order_date  TEXT
        );

        INSERT OR IGNORE INTO orders VALUES
            (1,  1, 'laptop',     999.99,        'completed',  '2024-01-15'),
            (2,  2, 'Mouse',       25,           'completed',  '2024-01-16'),
            (3,  1, 'Keyboard',    75.00,                ' ',  '2024-01-17'),
            (4,  3, 'monitor',    299.99,        'completed',  '2024-01-18'),
            (5,  2, 'Webcam',      89.99,        'pending',    '2024-01-19'),
            (6,  4, 'headphones', 149.99,        'completed',  '2024-01-20'),
            (7,  5, 'Desk Chair', 399.99,        'cancelled',  '2024-01-21'),
            (8,  3, 'USB Hub',    'thirty-five', 'completed',  '2024-01-22'),
            (9,  6, 'Laptop',     999.99,         'completed', '23.01.2024'),
            (10, 7, 'mouse',      'twenty-five',        ' ',   '24 January 2024');
    """)

    conn.commit()
    conn.close()
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()

