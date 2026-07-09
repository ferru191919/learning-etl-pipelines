# Fifth Pipeline
#
# The goal is to learn:
# - How to design a database for analytics (Data Warehouse - star schema)
# - How to build the DB star schema using SQL --> See '5.0_setup_dw.py'
# - How to perform SQL queries on clean, transformed data


import sqlite3
import pandas as pd
import logging
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DB_PATH = "retail_dw.db"
URL = "https://fakeapi.net/orders"


# Extract customers raw data from SQLite table
#
def extract_customers(conn):
    df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
    logger.info("Extracting %d customers", df_customers.shape[0])
    return df_customers


# Validate customers raw data
#
# Validation checks must match target DW's structure
#
def validate_customers(df_customers):

    if df_customers is None:
        logger.warning("Customers data is missing, skipping")
        return None

    logger.info("Validating %d customers", df_customers.shape[0])

    df = df_customers.copy()
    df["validation_errors"] = ""

    # Row-level validation
    #
    # A. customer_id should not be null, empty, duplicated, or a type different from integer --> going to be 'customer' dimension table PK
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
    mask_invalid_email = ~df["email"].astype(str).str.contains("@", na=False)  # ~ flips True/False values --> if row does not contain @ = True

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
        return None


# Validate purchases raw data
def validate_purchases(df_purchases):

    if df_purchases is None:
        logger.warning("No purchases data extracted, skipping")
        return None

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

    # E. status (is_delivered in target DW) must be a flag 0/1
    mask_invalid_is_delivered = ~df["status"].isin([0, 1])


    df.loc[mask_dup_id, "validation_errors"] += ";orderId not unique "
    df.loc[mask_invalid_id, "validation_errors"] += ";orderId invalid "
    df.loc[mask_not_positive_id, "validation_errors"] += ";orderId negative "
    df.loc[mask_invalid_user_id, "validation_errors"] += ";userId invalid "
    df.loc[mask_not_positive_user_id, "validation_errors"] += ";userId negative "
    df.loc[mask_invalid_order_date, "validation_errors"] += ";orderDate invalid "
    df.loc[mask_invalid_amount, "validation_errors"] += "; amount not numeric"
    df.loc[mask_non_positive_amount, "validation_errors"] += "; amount negative"
    df.loc[mask_invalid_is_delivered, "validation_errors"] += "; is_delivered not a boolean"


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
# - Value normalization and cleaning
#
def transform(valid_customers):

    if valid_customers is None:
        logger.warning("No valid customers data extracted, skipping")
        return None

    logger.info("Transforming %d customers and %d purchases",
                valid_customers.shape[0])

    df = valid_customers.copy()

    # Match columns names of target DW
    df = df.rename(columns={
        "customer_id": "customer_source_id",
        "first_name": "first_name",
        "last_name": "last_name",
        "email": "email",
        "country": "country",
        "created_at": "created_at"
    })

    # Normalize and clean values
    df["first_name"] = df["first_name"].astype(str).str.strip().str.title()
    df["last_name"] = df["last_name"].astype(str).str.strip().str.title()

    # Normalize email (only non-null)
    df["email"] = df["email"].astype(str).str.strip().str.lower()

    # Normalize country code to upper-case 2 letters
    df["country"] = df["country"].astype(str).str.strip().str.upper()

    df_clean_customers = df
    return df_clean_customers


# Transform purchases data
#
# - Match names of target DW columns
# - Value normalization and cleaning
#
def transform_purchases(valid_purchases):

    if valid_purchases is None:
        logger.warning("No valid purchases data extracted, skipping")
        return None

    logger.info("Transforming %d purchases", valid_purchases.shape[0])
    df = valid_purchases.copy()

    # Rename columns to match DW semantics
    df = df.rename(columns={
        "id": "order_id",
        "userId": "customer_source_id",  # will later join to dim_customer on this
        "orderDate": "order_date",
        "totalAmount": "amount",
        "status": "is_delivered",
    })

    # Normalize is_delivered
    df["is_delivered"] = df["is_delivered"].map({"delivered": 1}).fillna(0)

    df_clean_purchases = df
    return df_clean_purchases


# Assume dim_customer_df loaded from DW (with customer_sk and customer_source_id)
fact_staging_df = transform_purchases(valid_purchases)
dim_customer_df = transform_customers(valid_customers)  # or read back from DW

orders_with_sk = fact_staging_df.merge(
    dim_customer_df[["customer_source_id", "customer_sk"]],
    on="customer_source_id",
    how="left",
    validate="many_to_one",  # many orders per one customer
)





def main():
    with sqlite3.connect(DB_PATH) as conn:
        df_customers = extract_customers(conn)
        invalid_customers, valid_customers = validate_customers(df_customers)
        df_purchases = extract_purchases()
        invalid_purchases, valid_purchases = validate_purchases(df_purchases)
        df_clean_customers = transform_customers(valid_customers)
        df_clean_purchases = transform_purchases(valid_purchases)





if __name__ == "__main__":
    main()


