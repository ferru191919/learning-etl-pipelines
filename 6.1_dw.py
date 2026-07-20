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
# Differently from 5.1 db, here order_id DOES NOT have UNIQUE constraint because of SCD Type 2
# it keeps history of changes.
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

        FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk)
    );
    """
    conn.execute(sql)


## DIMENSION TABLE ##
# customer_sk = Surrogate Primary Key
#
# For the same reason, customer_source_id is not unique --> SCD Type 2.
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
    created_at         TEXT
);
    """
    conn.execute(sql)


# STAGING customer table
#
def staging_customer(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS stg_customer (
    stg_customer_sk    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id        INTEGER,
    first_name         TEXT,
    last_name          TEXT,
    email              TEXT,
    country            TEXT,
    created_at         TEXT,
    etl_loaded_at      TEXT NOT NULL,
    batch_id           TEXT NOT NULL
);
    """
    conn.execute(sql)

# STAGING order table
#
def staging_order(conn):
    sql = """
    CREATE TABLE IF NOT EXISTS stg_order (
    stg_order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER,
    customer_id         INTEGER,
    order_date          TEXT,
    amount              REAL,
    quantity            REAL,
    currency            TEXT,
    sales_channel       TEXT,
    etl_loaded_at       TEXT NOT NULL,
    batch_id            TEXT NOT NULL
);
    """
    conn.execute(sql)


def main():
    with sqlite3.connect(TARGET_DB) as conn:
        conn.execute(
            "PRAGMA foreign_keys = ON;")  # SQLite does not enforce foreign keys unless enabled on the connection
        create_dim_customer(conn)
        create_fact_order(conn)
        staging_customer(conn)
        staging_order(conn)
        conn.commit()


if __name__ == "__main__":
    main()