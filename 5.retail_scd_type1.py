# Fifth Pipeline
#
# The goal is to learn:
# - How to design and build a star schema db --> See '5.1_setup_target_dw.py'
# - How to populate DW tables using SQL
# - Slowly Changing Dimensions Type 1 --> overwrites history changes.


import sqlite3
import pandas as pd
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SOURCE_DB_PATH = "5.0_retail_data_source.db"
TARGET_DW_PATH = "5.1_retail_dw.db"


# Extract customers raw data from SQLite table
#
def extract_customers(db_conn):
    df_customers = pd.read_sql_query("SELECT * FROM customers", db_conn)
    logger.info("Extracted %d customers", df_customers.shape[0])
    return df_customers


# Validate customers raw data
# Validation checks must match target DW's structure
#
def validate_customers(df_customers):
    if df_customers is None or df_customers.empty:
        logger.warning("Customers data is missing, skipping")
        return pd.DataFrame(), pd.DataFrame()   # downstream ETL steps always receive a consistent dataframe type and
                                                # can safely check .empty without extra None handling.

    logger.info("Validating %d customers", df_customers.shape[0])

    df = df_customers.copy()
    df["validation_errors"] = ""

    # Row-level validation
    #
    # A. customer_id should not be null, empty, duplicated, or a type different from integer
    mask_dup_id = df["customer_id"].duplicated(keep=False)  # duplicated values = True condition
    customer_id_as_int = pd.to_numeric(df["customer_id"], errors="coerce")  # id must be convertible to integer,
                                                                            # otherwise turns it into NaN
    mask_invalid_id = (
            df["customer_id"].isnull()
            | (df["customer_id"].astype(str).str.strip() == "")
            | customer_id_as_int.isna()
    )
    mask_not_positive_id = customer_id_as_int <= 0 # Value Negative = True condition

    # B. first_name should not be null or empty
    mask_missing_fname = df["first_name"].isnull() | (df["first_name"].astype(str).str.strip() == "") # first name null or missing = True

    # C. same goes for last_name
    mask_missing_lname = df["last_name"].isnull() | (df["last_name"].astype(str).str.strip() == "")  # last name null or missing = True

    # D. email should not be null, empty, or without @
    mask_invalid_email = (
            df["email"].isna()
            | (df["email"].astype(str).str.strip() == "")
            | (~df["email"].astype(str).str.strip().str.contains("@", na=False))
    ) # ~ flips True/False values --> if row does not contain @ = True

    # E. country code should not be different formats than two letters (can be null)
    country_clean = df["country"].astype(str).str.strip()
    mask_invalid_country = (
            df["country"].notna()
            & (country_clean != "")
            & ((country_clean.str.len() != 2) | (~country_clean.str.match(r"^[A-Z]{2}$", na=False)))
    )

    # F. created_at should be a date (can be null)
    parsed_dates = pd.to_datetime(df["created_at"], errors="coerce")  # must be convertible to date, otherwise is NaN
    mask_invalid_date = (
            df["created_at"].isna()
            | (df["created_at"].astype(str).str.strip() == "")
            | (parsed_dates.isna())
    )


    # For each row (condition = True), concatenate the error code ("" string) in "validation_errors" column
    df.loc[mask_dup_id, "validation_errors"] += ";duplicate_customer_id "
    df.loc[mask_not_positive_id, "validation_errors"] += ";negative_customer_id "
    df.loc[mask_invalid_id, "validation_errors"] += ";invalid_customer_id "
    df.loc[mask_missing_fname, "validation_errors"] += ";missing_first_name "
    df.loc[mask_missing_lname, "validation_errors"] += ";missing_last_name "
    df.loc[mask_invalid_email, "validation_errors"] += ";invalid_email "
    df.loc[mask_invalid_country, "validation_errors"] += ";invalid_country_code "
    df.loc[mask_invalid_date, "validation_errors"] += ";invalid_date "


# Split valid vs. invalid rows
    invalid_customers = df[df["validation_errors"] != ""]
    valid_customers = df[df["validation_errors"] == ""]

    logger.info(
        "Customer validation completed: %d valid, %d invalid",
        valid_customers.shape[0],
        invalid_customers.shape[0],
    )

    return valid_customers, invalid_customers


# Extract orders raw data from API
def extract_orders(db_conn):
    df_orders = pd.read_sql_query("SELECT * FROM orders", db_conn)
    logger.info("Extracted %d orders", df_orders.shape[0])
    return df_orders


# Validate orders raw data
def validate_orders(df_orders):

    if df_orders is None or df_orders.empty:
        logger.warning("No orders data extracted, skipping")
        return pd.DataFrame(), pd.DataFrame()

    logger.info("Validating %d orders", df_orders.shape[0])

    df = df_orders.copy()
    df["validation_errors"] = ""

    # A. order_id should not be null, empty, duplicated, or a type different from integer
    mask_dup_id = df["order_id"].duplicated(keep=False)  # duplicated values = True

    order_id_as_int = pd.to_numeric(df["order_id"], errors="coerce")  # id must be convertible to integer, otherwise turns it into NaN
    mask_invalid_id = (
            df["order_id"].isnull()
            | (df["order_id"].astype(str).str.strip() == "")
            | order_id_as_int.isna()
    )

    mask_not_positive_id = order_id_as_int <= 0

    # B. customer_id should not be null, empty, or a type different from integer
    customer_id_as_int = pd.to_numeric(df["customer_id"], errors="coerce")  # id must be convertible to integer,
                                                                       # otherwise turns it into NaN
    mask_invalid_user_id = (
            df["customer_id"].isnull()
            | (df["customer_id"].astype(str).str.strip() == "")
            | customer_id_as_int.isna()
    )

    mask_not_positive_user_id = customer_id_as_int <= 0

    # C. order_date should be a date
    parsed_order_date = pd.to_datetime(df["order_date"], errors="coerce", format="mixed")
    mask_invalid_order_date = (
            df["order_date"].isnull()
            | (df["order_date"].astype(str).str.strip() == "")
            | parsed_order_date.isna()
    )

    # D. amount must be a float and cannot be null or empty
    amount_as_float = pd.to_numeric(df["amount"], errors="coerce")
    mask_invalid_amount = (
            (df["amount"].astype(str).str.strip() == "")
            | (df["amount"].isnull())
            | (amount_as_float.isna())
    )
    mask_non_positive_amount = amount_as_float <= 0

    # E. quantity must be a float and cannot be null or empty
    quantity_as_float = pd.to_numeric(df["quantity"], errors="coerce")
    mask_invalid_quantity = (
            (df["quantity"].astype(str).str.strip() == "")
            | (df["quantity"].isnull())
            | (quantity_as_float.isna())
    )
    mask_non_positive_quantity = quantity_as_float < 0

    # F. currency cannot be null or empty
    mask_invalid_currency = (
            (df["currency"].astype(str).str.strip() == "")
            | (df["currency"].isnull())
    )


    df.loc[mask_dup_id, "validation_errors"] += ";orderId not unique "
    df.loc[mask_invalid_id, "validation_errors"] += ";orderId invalid "
    df.loc[mask_not_positive_id, "validation_errors"] += ";orderId negative "
    df.loc[mask_invalid_user_id, "validation_errors"] += ";userId invalid "
    df.loc[mask_not_positive_user_id, "validation_errors"] += ";userId negative "
    df.loc[mask_invalid_order_date, "validation_errors"] += ";orderDate invalid "
    df.loc[mask_invalid_amount, "validation_errors"] += "; amount not numeric"
    df.loc[mask_non_positive_amount, "validation_errors"] += "; amount negative"
    df.loc[mask_invalid_quantity, "validation_errors"] += "; quantity not numeric"
    df.loc[mask_non_positive_quantity, "validation_errors"] += "; quantity not positive"
    df.loc[mask_invalid_currency, "validation_errors"] += "; currency not valid"


    invalid_orders = df[df["validation_errors"] != ""]
    valid_orders = df[df["validation_errors"] == ""]

    logger.info(
        "Orders validation completed: %d valid, %d invalid",
        valid_orders.shape[0],
        invalid_orders.shape[0],
    )

    return valid_orders, invalid_orders


# Transform customers data
#
# - Match names of target DW columns
# - Clean values
#
def transform_customers(valid_customers):

    if valid_customers is None or valid_customers.empty:
        logger.warning("No valid customers data extracted, skipping")
        return pd.DataFrame()

    logger.info("Transforming %d customers", valid_customers.shape[0])
    df = valid_customers.copy()

    df["customer_source_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["first_name"] = df["first_name"].astype(str).str.strip().str.title()
    df["last_name"] = df["last_name"].astype(str).str.strip().str.title()
    df["email"] = df["email"].apply(lambda x: x.strip().lower() if isinstance(x, str) else None) # for each value in the
    # email column, strip spaces and convert it to lowercase, but only if the value is actually a string; otherwise set it to None
    df["country"] = df["country"].astype(str).str.strip().str.upper()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

    clean_customers = df[[
        "customer_source_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "created_at"
    ]].drop_duplicates(subset=["customer_source_id"], keep="last").copy()  # UNIQUE in star schema design

    return clean_customers


# Transform orders data
#
# - Match names of target DW columns
# - Value normalization and cleaning
#
def transform_orders(valid_orders):

    if valid_orders is None or valid_orders.empty:
        logger.warning("No valid purchases data extracted, skipping")
        return pd.DataFrame()

    logger.info("Transforming %d orders", valid_orders.shape[0])
    df = valid_orders.copy()

    df["order_id"] = pd.to_numeric(df["order_id"], errors="coerce").astype("Int64")
    df["customer_source_id"] = pd.to_numeric(df["customer_id"], errors="coerce").astype("Int64")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").astype(float)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype(float)
    df["currency"] = df["currency"].astype(str).str.strip().str.upper()
    df["sales_channel"] = df["sales_channel"].astype(str).str.strip().str.lower()

    clean_orders = df[[
        "order_id",
        "customer_source_id",
        "order_date",
        "amount",
        "quantity",
        "currency",
        "sales_channel"
    ]]

    return clean_orders


# Load dim_customers
#
# must overwrite history changes --> SCD Type 1
#
def load_dim_customer(clean_customers, dw_conn):

    if clean_customers is None or clean_customers.empty:
        logger.warning("No valid customer data extracted, skipping")
        return 0

    # inserts a new customer if customer_source_id is new,
    # and updates the existing row if that same customer_source_id already exists.
    #
    sql = """
       INSERT INTO dim_customer (
           customer_source_id, first_name, last_name, email, country, created_at
       )
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(customer_source_id) DO UPDATE SET
           first_name = excluded.first_name,
           last_name  = excluded.last_name,
           email      = excluded.email,
           country    = excluded.country,
           created_at = excluded.created_at
       """
    # ON CONFLICT DO UPDATE is a Slowly Changing Dimensions Type 1.
    # meaning it does not keep history track of dimension, but overwrites changes.
    # customer_source_id must have a UNIQUE constraint in DB design.


    # customer_source_id was saved as byte instead of integer
    clean_customers["customer_source_id"] = pd.to_numeric(clean_customers["customer_source_id"], errors="coerce").astype("Int64")
    clean_customers["customer_source_id"] = clean_customers["customer_source_id"].astype(object).where(clean_customers["customer_source_id"].notna(), None)
    clean_customers["customer_source_id"] = clean_customers["customer_source_id"].apply(lambda x: int(x) if x is not None else None)

    # Insert values from clean_customers df into dim table
    rows = list(clean_customers.itertuples(index=False, name=None))  # converts clean_customers rows into a list of tuples
    dw_conn.executemany(sql, rows)     # runs the same SQL statement once for every tuple in rows.
    dw_conn.commit()   # permanently saves the inserts to the database.
    logger.info("Loaded %d customers into dim_customer", len(rows))
    return len(rows)


# Join fact_order with dim_customer
#
def enrich_fact_orders(dw_conn, clean_orders):

    if clean_orders is None or clean_orders.empty:
        logger.warning("No valid purchases to enrich")
        return pd.DataFrame()

    dim_customer = pd.read_sql_query(
        "SELECT customer_sk, customer_source_id FROM dim_customer",  # Select columns to join into fact table
        dw_conn
    )

    df = clean_orders.merge(dim_customer, on="customer_source_id", how="left")  # Left Join

    # unmatched = df[df["customer_sk"].isna()].copy()  # customer_sk null after left join
    matched = df[df["customer_sk"].notna()].copy()

    fact_df = matched[[
        "order_id",
        "customer_sk",
        "order_date",
        "amount",
        "quantity",
        "currency",
        "sales_channel"
    ]].copy()

    return fact_df


# Load fact table
#
def load_fact_order(fact_df, dw_conn):

    if fact_df is None or fact_df.empty:
        logger.warning("No fact rows to load")
        return 0

    # If facts already exist, I don't want to load duplicates
    existing_orders = pd.read_sql_query(
        "SELECT order_id FROM fact_order",
        dw_conn
    )

    new_fact_df = fact_df[~fact_df["order_id"].isin(existing_orders["order_id"])].copy()

    if new_fact_df.empty:
        logger.info("No new fact rows to load")
        return 0


    # Query for loading
    sql = """
    INSERT INTO fact_order (
        order_id, customer_sk, order_date, amount, quantity, currency, sales_channel
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    # ON CONFLICT does not apply here because it's not a dim table
    # SCD is only for dimensions.


    # order_id was saved as byte instead of integer
    # otherwise it's not saved as integer in dw table
    fact_df["order_id"] = pd.to_numeric(fact_df["order_id"], errors="coerce").astype("Int64")  # should be convertible to int
    fact_df["order_id"] = fact_df["order_id"].astype(object).where(fact_df["order_id"].notna(), None)
    fact_df["order_id"] = fact_df["order_id"].apply(lambda x: int(x) if x is not None else None)  # None if it's not integer

    # Insert fact_df values into fact table
    rows = list(fact_df.itertuples(index=False, name=None)) # converts clean_customers rows into a list of tuples
    dw_conn.executemany(sql, rows)
    dw_conn.commit()
    logger.info("Loaded %d fact rows into fact_order", len(rows))
    return len(rows)


# MAIN
def main():
    with (sqlite3.connect(SOURCE_DB_PATH) as db_conn,
          sqlite3.connect(TARGET_DW_PATH) as dw_conn):
        dw_conn.execute("PRAGMA foreign_keys = ON")

        df_customers = extract_customers(db_conn)
        valid_customers, invalid_customers = validate_customers(df_customers)

        df_orders = extract_orders(db_conn)
        valid_orders, invalid_orders = validate_orders(df_orders)

        clean_customers = transform_customers(valid_customers)
        clean_orders = transform_orders(valid_orders)

        load_dim_customer(clean_customers, dw_conn)
        fact_df = enrich_fact_orders(dw_conn, clean_orders)
        load_fact_order(fact_df, dw_conn)

        logger.info("Pipeline completed")


if __name__ == "__main__":
    main()