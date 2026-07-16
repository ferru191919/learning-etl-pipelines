### RUN THIS TO SET UP TARGET DATA WAREHOUSE ###

## The goal is to learn:
#   - How to design and build a star schema DB

## Structure:
#   - Fact table --> orders
#   - Dimension table --> customers


import sqlite3
import logging


TARGET_DB = "5.1_retail_dw.db"


## FACT TABLE ##
# fact_order_sk = Surrogate Primary Key  --> artificially created key with no business meaning --> safe design
# UNIQUE constraint because I want only one order_id per row (no SCD)
# customer_sk = Foreign Key
#
def create_fact_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS fact_order (
        fact_order_sk       INTEGER PRIMARY KEY,  
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
# customer_sk = Surrogate Primary Key
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