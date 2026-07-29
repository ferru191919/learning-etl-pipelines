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


## DIMENSION TABLE ##
# customer_sk = Surrogate Key as PK --> Artificial key with no business meaning
#                                   --> In dim table, used for SCD Type 2 to keep multiple rows of same customer_id
#                                   --> It also protects your data warehouse if a source system changes its natural key
#
# customer_source_id = business key --> UNIQUE constraint because SCD Type 1
# SCD Type 1 = if customer attributes change, new ones overwrite the old ones --> No history of past values
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


## FACT TABLE ##
# In fact table, uniqueness of a row usually comes from the combination of Foreign Keys.
# You choose the combination of FKs depending on the granularity you want for the table.
# Surrogate keys are not usually used as PKs in fact tables, because it can hide dublicate rows (same combination of FKs).
#
# In this Data Warehouse, I want to keep 1 row per order.
# For this reason, I'm going to use order_id as PK.
#
# customer_sk = Foreign Key
#
def create_fact_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS fact_order (  
        order_id            INTEGER PRIMARY KEY,
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


def main():
    with sqlite3.connect(TARGET_DB) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")  # SQLite does not enforce foreign keys unless enabled on the connection
        create_dim_customer(conn)
        create_fact_order(conn)
        conn.commit()


if __name__ == "__main__":
    main()
