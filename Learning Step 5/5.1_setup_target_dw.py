### RUN THIS TO SET UP TARGET DATA WAREHOUSE ###

## The goal is to learn:
#   - How to design and build a star schema DB
#   - Surrogate Keys
#   - Slowly Changing Dimensions Type 1 --> UNIQUE constraints

## Structure:
#   - Fact table --> orders
#   - Dimension table --> customers


import sqlite3
import logging


TARGET_DB = "5.1_retail_dw.db"


## FACT TABLE ##
# order_sk = Surrogate PK --> artificial key with no business value --> protects you if business key changes.
# customer_sk = Foreign Key
# order_id = Business Key --> granularity = 1 row per order --> UNIQUE constraint.
#
def create_fact_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS fact_order (  
        order_sk            INTEGER PRIMARY KEY,
        order_id            INTEGER NOT NULL UNIQUE,
        customer_sk         INTEGER NOT NULL,
        order_date          TEXT,
        amount              REAL NOT NULL,
        quantity            REAL NOT NULL,
        currency            TEXT NOT NULL,
        sales_channel       TEXT,
    
        FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk)
    );
    """
    conn.execute(sql)


## DIMENSION TABLE ##
# customer_sk = Surrogate PK
# customer_source_id = business key --> UNIQUE constraint because SCD Type 1.
# SCD Type 1 == if customer attributes change, new ones overwrite the old ones --> No history of changes.
#
def create_dim_customer(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk        INTEGER PRIMARY KEY,
    customer_source_id INTEGER NOT NULL UNIQUE,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    email              TEXT NOT NULL,
    country            TEXT,
    created_at         TEXT
);
    """
    conn.execute(sql)


def main():
    with sqlite3.connect(TARGET_DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")  # SQLite does not enforce foreign keys unless enabled on the connection
        create_dim_customer(conn)
        create_fact_order(conn)
        conn.commit()


if __name__ == "__main__":
    main()
