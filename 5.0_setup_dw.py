# Design a DB schema for loading transformed data to perform analytics
# Star schema with a fact table and two dimension tables


import sqlite3
import logging

logger = logging.getLogger(__name__)
TARGET_DB = "5.0_retail_dw.db"


# Fact Table
#
# References customer surrogate key
#
def create_fact_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS fact_order (
        order_id            INTEGER PRIMARY KEY,
        customer_sk         INTEGER NOT NULL,
        order_date          TEXT NOT NULL,
        amount              REAL,
        is_delivered        INTEGER,
        FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk)
    );
    """
    conn.execute(sql)


# Dimensional table
#
# I'm using customer_sk as Surrogate Key
# UNIQUE constraint because I want only one customer_source_id per row (no SCD)
#
def create_dim_customer(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk        INTEGER PRIMARY KEY,
    customer_source_id INTEGER NOT NULL UNIQUE,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    email              TEXT,
    country            TEXT NOT NULL,
    created_at         TEXT NOT NULL
);
    """
    conn.execute(sql)



# Dimensional table
def create_dq_rejected_orders(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS dq_rejected_orders (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id          INTEGER,
        customer_sk       INTEGER,
        raw_payload       TEXT NOT NULL,
        validation_errors TEXT NOT NULL,
        rejected_at       TEXT NOT NULL
    );
    """
    conn.execute(sql)


def main():
    with sqlite3.connect(TARGET_DB) as conn:
        create_dim_customer(conn)
        create_fact_order(conn)
        create_dq_rejected_orders(conn)
        conn.commit()


if __name__ == "__main__":
    main()