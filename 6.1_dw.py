### RUN THIS TO SET UP TARGET DATA WAREHOUSE ###

## The goal is to learn:
#   - Design Data Warehouse for SCD Type 2

## Structure:
#   - Fact table --> orders
#   - Dimension table --> customers


import sqlite3

TARGET_DB = "6.1_retail_dw.db"


## FACT TABLE ##
# fact_order_sk = Surrogate Primary Key  --> artificially created key with no business meaning
# customer_sk = Foreign Key
#
def create_fact_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS fact_order (
        fact_order_sk       INTEGER PRIMARY KEY,  
        order_id            INTEGER NOT NULL,
        customer_sk         INTEGER NOT NULL,
        order_date          TEXT,
        amount              REAL NOT NULL,
        quantity            REAL NOT NULL,
        currency            TEXT NOT NULL,
        sales_channel       TEXT,
        effective_from      TEXT NOT NULL,
        effective_to        TEXT NOT NULL,
        is_current          INTEGER NOT NULL

        FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk)
    );
    """
    conn.execute(sql)


## DIMENSION TABLE ##
# customer_sk = Surrogate Primary Key
#
# Differently from SCD Type 1, here customer_source_id DOES NOT have UNIQUE constraint.
# It keeps history of changes, so we might have multiple Ids as customer has changed attributes over time.
#
# effective_from, effective_to shows the validity window when that version of the value was being active.
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


def main():
    with sqlite3.connect(TARGET_DB) as conn:
        conn.execute(
            "PRAGMA foreign_keys = ON;")  # SQLite does not enforce foreign keys unless enabled on the connection
        create_dim_customer(conn)
        create_fact_order(conn)
        conn.commit()


if __name__ == "__main__":
    main()