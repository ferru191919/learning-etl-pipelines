# Fifth Pipeline
#
# The goal is to learn:
# - How to design a database for analytics (Data Warehouse - star schema)
# - How to build the DB star schema using SQL --> See '5.0_setup_dw.py'
# - How to join two tables --> enrich fact table
# - How to perform SQL queries on clean, transformed data


import sqlite3
import pandas as pd
import logging
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SOURCE_DB_PATH = "5.1_customers_data_source.db"
TARGET_DW_PATH = "5.0_retail_dw.db"
URL = "https://fakeapi.net/orders"


# Extract customers raw data from SQLite table
def extract_customers(db_conn):
    df_customers = pd.read_sql_query("SELECT * FROM customers", db_conn)
    logger.info("Extracted %d customers", df_customers.shape[0])
    return df_customers


# Validate customers raw data
#
# Validation checks must match target DW's structure
#
def validate_customers(df_customers):

    if df_customers is None or df_customers.empty:
        logger.warning("Customers data is missing, skipping")
        return pd.DataFrame(), pd.DataFrame()   # downstream ETL steps always receive a consistent dataframe type and can safely check .empty without extra None handling.

    logger.info("Validating %d customers", df_customers.shape[0])

    df = df_customers.copy()
    df["validation_errors"] = ""

    # Row-level validation
    #
    # A. customer_id should not be null, empty, duplicated, or a type different from integer
    mask_dup_id = df["customer_id"].duplicated(keep=False)  # duplicated values = True
    customer_id_as_int = pd.to_numeric(df["customer_id"], errors="coerce")  # id must be convertible to integer, otherwise turns it into NaN
    mask_invalid_id = (
            df["customer_id"].isnull()
            | (df["customer_id"].astype(str).str.strip() == "")
            | customer_id_as_int.isna()
    )
    mask_not_positive_id = customer_id_as_int <= 0 # Negative = True

    # B. first_name should not be null or empty
    mask_missing_fname = df["first_name"].isnull() | (df["first_name"].astype(str).str.strip() == "") # first name null or missing = True

    # C. same goes for last_name
    mask_missing_lname = df["last_name"].isnull() | (df["last_name"].astype(str).str.strip() == "")  # last name null or missing = True

    # D. email should not be without @
    mask_invalid_email = (
            df["email"].notna()
            & ~df["email"].astype(str).str.strip().str.contains("@", na=False)) # ~ flips True/False values --> if row does not contain @ = True

    # E. country code should not be null, empty, or different formats than two letters
    mask_missing_country = (df["country"].isnull() | (df["country"].astype(str).str.strip() == ""))  # country missing = True
    mask_length_country = ~mask_missing_country & (df["country"].astype(str).str.len() != 2)  # country not missing but different length = True

    # F. created_at should not be null, empty, or invalid date
    parsed_dates = pd.to_datetime(df["created_at"], errors="coerce")  # must be convertible to date, otherwise is NaN
    mask_invalid_date = (
            df["created_at"].isnull()
            | (df["created_at"].astype(str).str.strip() == "")
            | parsed_dates.isna() # is NaN = True
    )


    # For each row (condition = True), concatenate the error code ("" string) in "validation_errors" column
    df.loc[mask_dup_id, "validation_errors"] += ";duplicate_customer_id "
    df.loc[mask_not_positive_id, "validation_errors"] += ";negative_customer_id "
    df.loc[mask_invalid_id, "validation_errors"] += ";invalid_customer_id "
    df.loc[mask_missing_fname, "validation_errors"] += ";missing_first_name "
    df.loc[mask_missing_lname, "validation_errors"] += ";missing_last_name "
    df.loc[mask_invalid_email, "validation_errors"] += ";invalid_email "
    df.loc[mask_missing_country, "validation_errors"] += ";missing_country_code "
    df.loc[mask_length_country, "validation_errors"] += ";invalid_country_code "
    df.loc[mask_invalid_date, "validation_errors"] += ";invalid_date "


# Split valid vs. invalid rows
    invalid_customers = df[df["validation_errors"] != ""]
    valid_customers = df[df["validation_errors"] == ""]

    logger.info(
        "Customer validation completed: %d valid, %d invalid",
        valid_customers.shape[0],
        invalid_customers.shape[0],
    )

    return invalid_customers, valid_customers


# Extract purchases raw data from API
def extract_purchases():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
        raw_purchases = raw_data["data"]
        df_purchases = pd.DataFrame(raw_purchases)

        logger.info(
            "Extracted %d purchases from API %s with status %s",
            df_purchases.shape[0],
            URL,
            response.status_code
        )

        return df_purchases

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return pd.DataFrame()


# Validate purchases raw data
def validate_purchases(df_purchases):

    if df_purchases is None or df_purchases.empty:
        logger.warning("No purchases data extracted, skipping")
        return pd.DataFrame(), pd.DataFrame()

    logger.info("Validating %d purchases", df_purchases.shape[0])


    df = df_purchases.copy()
    df["validation_errors"] = ""

    # A. (order_)id should not be null, empty, duplicated, or a type different from integer --> It's going to be our fact table PK
    mask_dup_id = df["id"].duplicated(keep=False)  # duplicated values = True
    order_id_as_int = pd.to_numeric(df["id"], errors="coerce")  # id must be convertible to integer, otherwise turns it into NaN
    mask_invalid_id = (
            df["id"].isnull()
            | (df["id"].astype(str).str.strip() == "")
            | order_id_as_int.isna()
    )
    mask_not_positive_id = order_id_as_int <= 0  # Negative = True

    # B. user_id should not be null, empty, or a type different from integer
    user_id_as_int = pd.to_numeric(df["userId"], errors="coerce")  # id must be convertible to integer, otherwise turns it into NaN
    mask_invalid_user_id = (
            df["userId"].isnull()
            | (df["userId"].astype(str).str.strip() == "")
            | user_id_as_int.isna()
    )
    mask_not_positive_user_id = user_id_as_int <= 0  # Negative = True

    # C. order_date should not be null, empty, or different from text
    parsed_order_date = pd.to_datetime(df["orderDate"], errors="coerce")
    mask_invalid_order_date = (
            df["orderDate"].isnull()
            | (df["orderDate"].astype(str).str.strip() == "")
            | parsed_order_date.isna()
    )

    # D. amount must be a float
    amount_as_float = pd.to_numeric(df["totalAmount"], errors="coerce")
    mask_invalid_amount = amount_as_float.isna()
    mask_non_positive_amount = amount_as_float <= 0

    # E. status (is_delivered in target DW) must be an acceptable value
    mask_invalid_is_delivered = ~df["status"].astype(str).str.strip().str.lower().isin(
        ["delivered", "processing", "cancelled"])


    df.loc[mask_dup_id, "validation_errors"] += ";orderId not unique "
    df.loc[mask_invalid_id, "validation_errors"] += ";orderId invalid "
    df.loc[mask_not_positive_id, "validation_errors"] += ";orderId negative "
    df.loc[mask_invalid_user_id, "validation_errors"] += ";userId invalid "
    df.loc[mask_not_positive_user_id, "validation_errors"] += ";userId negative "
    df.loc[mask_invalid_order_date, "validation_errors"] += ";orderDate invalid "
    df.loc[mask_invalid_amount, "validation_errors"] += "; amount not numeric"
    df.loc[mask_non_positive_amount, "validation_errors"] += "; amount negative"
    df.loc[mask_invalid_is_delivered, "validation_errors"] += "; status invalid"


    invalid_purchases = df[df["validation_errors"] != ""]
    valid_purchases = df[df["validation_errors"] == ""]

    logger.info(
        "Purchases validation completed: %d valid, %d invalid",
        valid_purchases.shape[0],
        invalid_purchases.shape[0],
    )

    return invalid_purchases, valid_purchases


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
    df["email"] = df["email"].where(df["email"].notna(), None)  # email can be Null in star schema design
    df["email"] = df["email"].apply(lambda x: x.strip().lower() if isinstance(x, str) else None) # for each value in the email column, strip spaces and convert it to lowercase, but only if the value is actually a string; otherwise set it to None
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


# Transform purchases data
#
# - Match names of target DW columns
# - Value normalization and cleaning
#
def transform_purchases(valid_purchases):

    if valid_purchases is None or valid_purchases.empty:
        logger.warning("No valid purchases data extracted, skipping")
        return pd.DataFrame()

    logger.info("Transforming %d purchases", valid_purchases.shape[0])
    df = valid_purchases.copy()

    df["order_id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["customer_source_id"] = pd.to_numeric(df["userId"], errors="coerce").astype("Int64")
    df["order_date"] = pd.to_datetime(df["orderDate"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount"] = pd.to_numeric(df["totalAmount"], errors="coerce")
    df["is_delivered"] = (
        df["status"].astype(str).str.strip().str.lower().eq("delivered").astype(int)
    )

    clean_purchases = df[[
        "order_id",
        "customer_source_id",
        "order_date",
        "amount",
        "is_delivered"
    ]].drop_duplicates(subset=["order_id"], keep=False).copy()

    return clean_purchases


# Load dim_customers
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

    rows = list(clean_customers.itertuples(index=False, name=None))  # converts df rows into a list of tuples
    dw_conn.executemany(sql, rows)     # runs the same SQL statement once for every tuple in rows.
    dw_conn.commit()   # permanently saves the inserts to the database.
    logger.info("Loaded %d customers into dim_customer", len(rows))
    return len(rows)


# Join fact_order with dim_customer
#
def enrich_fact_orders(dw_conn, clean_purchases):

    if clean_purchases is None or clean_purchases.empty:
        logger.warning("No valid purchases to enrich")
        return pd.DataFrame(), pd.DataFrame()

    dim_customer = pd.read_sql_query(
        "SELECT customer_sk, customer_source_id FROM dim_customer",
        dw_conn
    )
    df = clean_purchases.merge(dim_customer, on="customer_source_id", how="left")  # Left join

    unmatched = df[df["customer_sk"].isna()].copy()
    matched = df[df["customer_sk"].notna()].copy()
    matched["customer_sk"] = matched["customer_sk"].astype(int)

    fact_df = matched[[
        "order_id",
        "customer_sk",
        "order_date",
        "amount",
        "is_delivered"
    ]].copy()

    return fact_df, unmatched


# Load fact table
#
def load_fact_order(fact_df, dw_conn):

    if fact_df is None or fact_df.empty:
        logger.warning("No fact rows to load")
        return 0

    sql = """
    INSERT INTO fact_order (
        order_id, customer_sk, order_date, amount, is_delivered
    )
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(order_id) DO UPDATE SET
        customer_sk = excluded.customer_sk,
        order_date = excluded.order_date,
        amount = excluded.amount,
        is_delivered = excluded.is_delivered
    """

    rows = list(fact_df.itertuples(index=False, name=None))
    dw_conn.executemany(sql, rows)
    dw_conn.commit()
    logger.info("Loaded %d fact rows into fact_order", len(rows))
    return len(rows)


# Load rejected orders
#
def load_rejected_orders(unmatched_fact_df, invalid_purchases, dw_conn):
    frames = []

    if invalid_purchases is not None and not invalid_purchases.empty:
        temp = invalid_purchases.copy()
        temp["raw_payload"] = temp.drop(columns=["validation_errors"], errors="ignore").astype(str).agg(" | ", axis=1)
        # This creates a single text field that stores the rejected row in a readable form.
        # It first removes validation_errors so that the error message does not get mixed into the original data,
        # then converts every remaining value to string, and finally joins all column values in that row with | .
        temp["validation_errors"] = temp["validation_errors"]
        temp["rejected_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = temp.rename(columns={"id": "order_id", "userId": "customer_source_id"})
        frames.append(temp[["order_id", "customer_source_id", "raw_payload", "validation_errors", "rejected_at"]])

    if unmatched_fact_df is not None and not unmatched_fact_df.empty:
        temp = unmatched_fact_df.copy()
        temp["raw_payload"] = temp.astype(str).agg(" | ", axis=1)
        temp["validation_errors"] = "unmatched_customer_source_id"
        temp["rejected_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        frames.append(temp[["order_id", "customer_source_id", "raw_payload", "validation_errors", "rejected_at"]])

    if not frames:
        logger.info("No rejected orders to load")
        return 0

    df = pd.concat(frames, ignore_index=True)
    sql = """
       INSERT INTO dq_rejected_orders (
           order_id, customer_sk, raw_payload, validation_errors, rejected_at
       )
       VALUES (?, ?, ?, ?, ?)
       """

    if "customer_sk" not in df.columns:
        df["customer_sk"] = None
    rows = list(
        df[["order_id", "customer_sk", "raw_payload", "validation_errors", "rejected_at"]].itertuples(index=False,
                                                                                                      name=None))
    dw_conn.executemany(sql, rows)
    dw_conn.commit()
    logger.info("Loaded %d rejected rows into dq_rejected_orders", len(rows))
    return len(rows)


# MAIN
def main():
    with sqlite3.connect(SOURCE_DB_PATH) as db_conn, sqlite3.connect(TARGET_DW_PATH) as dw_conn:
        dw_conn.execute("PRAGMA foreign_keys = ON")

        df_customers = extract_customers(db_conn)
        invalid_customers, valid_customers = validate_customers(df_customers)

        df_purchases = extract_purchases()
        invalid_purchases, valid_purchases = validate_purchases(df_purchases)

        df_clean_customers = transform_customers(valid_customers)
        df_clean_purchases = transform_purchases(valid_purchases)

        load_dim_customer(df_clean_customers, dw_conn)

        fact_df, unmatched = enrich_fact_orders(dw_conn, df_clean_purchases)

        load_fact_order(fact_df, dw_conn)
        load_rejected_orders(unmatched, invalid_purchases, dw_conn)

        logger.info("Pipeline completed")


if __name__ == "__main__":
    main()