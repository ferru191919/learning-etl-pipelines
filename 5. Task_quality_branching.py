# Branching = when a pipeline splits the flow of data into two or more paths based on some condition.
#
# Extract → Transform → Decision → Path A
#                                → Path B
from contextlib import nullcontext

import pandas as pd
import requests
import sqlite3
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "5.0_orders_branching.db"
CUSTOMERS_TABLE = "customers"
REPORT_TABLE = "order_report"
REJECTED_TABLE = "order_report_rejected"
URL = "https://dummyjson.com/carts"


## Extraction of customers from SQLite table ##
def extract_db_customers(conn):
    df_customers = pd.read_sql_query(f"SELECT * FROM {CUSTOMERS_TABLE}", conn)
    logger.info(f"Extracted {df_customers.shape[0]} rows and {df_customers.shape[1]} columns")
    return df_customers

## Extraction of orders from API call ##
def extract_api_orders():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        raw_data = response.json()
        raw_orders = raw_data["carts"]
        logger.info(f"Extracted {len(raw_orders)} orders")
        time.sleep(1)
        return raw_orders

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError: {e}")


## Validate raw_orders data (list of dictionaries) ##

# Validate these 6 things:
# 1.raw_orders is not empty
# 2.id exists
# 4.total exists
# 5.total is numeric
# 6.products exists and is a list

def validate_raw_orders(raw_orders):
    valid_orders = []

    # validation n.1
    if not raw_orders:
        raise ValueError("raw_orders is empty!")

    for i, order in enumerate(raw_orders):
        if order == {}:
            logger.warning(f"Empty order at index {i} - skipping")
            continue

    # validation n.2
        if "id" not in order or order["id"] is None:
            logger.warning(f"Missing id for order {i} - skipping")
            continue

    # validation n.4
        if "total" not in order or order["total"] is None:
            logger.warning(f"Missing total for order {i} - skipping")
            continue

    # validation n.5
        if not isinstance(order["total"], (int, float)):
            logger.warning(f"Total for order {i} is not a number - skipping")
            continue

    # validation n.6
        if "products" not in order or not isinstance(order["products"], list):
            logger.warning(f"Invalid products for order {i} - skipping")
            continue

        valid_orders.append(order)

    logger.info(f"Validated: {len(valid_orders)} orders passed all checks")
    return valid_orders


## Validate raw_customers data (dataframe) ##

# Validate these 5 things:
# 1.DataFrame is not empty.
# 2.Customer_id has no nulls.
# 3.Customer_id is unique.
# 4.Customer_name has no nulls.
# 5.Email has no nulls.

def validate_raw_customers(df_customers):

    # validation n.1
    if df_customers.empty:
        raise ValueError("df_customers is empty!")

    # validation n.2
    if df_customers["customer_id"].isnull().any():
        raise ValueError("Null values found in customer_id!")

    # validation n.3
    if df_customers["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id values found!")

    # validation n.4
    if df_customers["customer_name"].isnull().any():
        raise ValueError("Null values found in customer_name!")

    # validation n.5
    if df_customers["email"].isnull().any():
        raise ValueError("Null values found in email!")

# If at least one of the validation rules fail, the whole DataFrame is invalid.
# The reason of this choice is that customers is Master data.
# For transaction/event data, we could just remove invalid rows.

    logger.info(f"Validated: {df_customers.shape[0]} rows passed all checks")
    return df_customers


## Transformation ##

#1. Receive validated inputs
#2. Transform dictionary input into DataFrame
#3. Join the two DataFrames including all the orders row
#4. Branching based on condition (orders with and without customer)

def transform_validated_orders(valid_orders, df_customers):
    clean_orders = []

    for order in valid_orders:
        order_id = order["id"]
        total = order["total"]
        discounted_total = order["discountedTotal"]
        user_id = order["userId"]
        count_products = order["totalProducts"]

        clean_orders.append({
            "order_id": order_id,
            "total": total,
            "discounted_total": discounted_total,
            "user_id": user_id,
            "count_products": count_products,
        })

    #2
    df_orders = pd.DataFrame(clean_orders)

    #3
    df_merged = df_orders.merge(
        df_customers,
        how="left",
        left_on="user_id",
        right_on="customer_id"
    )

    #4
    accepted_df = df_merged[df_merged["customer_name"].notnull()].copy() # Keep rows where customer_name exists after the join.
    rejected_df = df_merged[df_merged["customer_name"].isnull()].copy()   # Keep rows where customer_name is missing after the join.

    accepted_df = accepted_df.drop(columns=["user_id"])
    rejected_df = rejected_df.drop(columns=["user_id"])  # dropping user_id column because we already have customer_id

    accepted_df["customer_id"] = accepted_df["customer_id"].astype("Int64")
    rejected_df["customer_id"] = rejected_df["customer_id"].astype("Int64")  # changing customer_id values in integer (e.g. customer_id = 1 instead of 1.0)

    if rejected_df.shape[0] > 0:
        rejected_df["rejection_reason"] = "customer_not_found"  # creating new column in rejected_df

    return accepted_df, rejected_df


## LOAD ##

# Two different loadings based on branching
# accepted_df loaded into order_report
# rejected_df loaded into rejected_order_report

def load_accepted_df(accepted_df, conn):
    accepted_df.to_sql("order_report", conn, index=False, if_exists="replace")
    logger.info("✅ Loaded accepted rows into order_report SQLite table")

def load_rejected_df(accepted_df, conn):
    accepted_df.to_sql("rejected_order_report", conn, index=False, if_exists="replace")
    logger.info("✅ Loaded rejected rows into rejected_order_report SQLite table")


#main
def main():
    with sqlite3.connect(DB_PATH) as conn:
        df_customers = extract_db_customers(conn)
        logger.info(f"Raw data count: {len(df_customers)}")

        raw_orders = extract_api_orders()
        logger.info(f"Raw data count: {len(raw_orders)}")

        valid_orders = validate_raw_orders(raw_orders)
        logger.info(f"Validated raw orders: {len(valid_orders)}")

        df_customers = validate_raw_customers(df_customers)
        logger.info(f"Validated customers: {len(df_customers)}")

        accepted_df, rejected_df = transform_validated_orders(valid_orders, df_customers)
        logger.info(f"Accepted rows: {len(accepted_df)} | Rejected rows: {len(rejected_df)}")

        load_accepted_df(accepted_df, conn)
        load_rejected_df(rejected_df, conn)



if __name__ == "__main__":
    main()















