### RUN THIS TO SET UP TARGET DATA WAREHOUSE ###

## The goal is to learn:
#   - Slowly Changing Dimensions Type 2

## Structure:
#   - Fact table --> orders
#   - Dimension table --> customers


import sqlite3


TARGET_DB = "6.1_retail_dw.db"


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


## DIMENSION TABLE ##
# customer_sk = Surrogate PK
# customer_source_id = business key --> NOT UNIQUE constraint because SCD Type 2.
# SCD Type 2 == if customer attributes change, a new row will be created --> Keeps history of changes.
#
def create_dim_customer(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk        INTEGER PRIMARY KEY,
    customer_source_id INTEGER NOT NULL,
    first_name         TEXT NOT NULL,
    last_name          TEXT NOT NULL,
    email              TEXT NOT NULL,
    country            TEXT,
    created_at         TEXT,
    effective_from     TEXT NOT NULL,
    effective_to       TEXT NOT NULL,
    is_current         INTEGER NOT NULL
);
    """
    conn.execute(sql)

    # effective_from , effective_to define the range of time when the row was the latest version of that customer_id.
    # is_current defines whether that row is the latest version.

def main():
    with sqlite3.connect(TARGET_DB) as conn:
        conn.execute(
            "PRAGMA foreign_keys = ON;")  # SQLite does not enforce foreign keys unless enabled on the connection
        create_dim_customer(conn)
        create_fact_order(conn)
        conn.commit()


if __name__ == "__main__":
    main()
