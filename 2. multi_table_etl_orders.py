# IMPORTANT DISCLAIMER!!!
# Before running this pipeline, you must run the '2.0 setup_database.py' (ONLY ONCE)
# '2.0 ecommerce.db' file will be generated
# this is the SQLite database where this pipeline will extract data from!


from datetime import datetime
import pandas as pd
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)  # production best practices
logger = logging.getLogger(__name__)     # production best practices

DB_PATH = "2.0 ecommerce.db"
USD_TO_EUR = 0.92


# 1. EXTRACT
# Data source: 'users' & 'orders' tables in ecommerce.db file
# To create the ecommerce.db file, run the setup_database.py first

def extract(conn):      # conn = connection object between Python and the SQLite .db file
                        # created with sqlite3.connect(DB_PATH) in main()

    df_users = pd.read_sql("SELECT * FROM users", conn)     # pd function to read sql tables
                                                                 # it returns a DataFrame
    df_orders = pd.read_sql("SELECT * FROM orders", conn)

    logger.info(f"Extracted {df_users.shape} rows x columns successfully from users table")
    logger.info(f"Extracted {df_orders.shape} rows x columns successfully from orders table")
    return df_users, df_orders


# 2. TRANSFORMATION
# a. Join df_users and df_orders
# b. Filter out cancelled orders
# c. Add full_name column
# d. Add order_value_eur column
# e. Flag high-value orders: is_high_value = True if order_value_eur > 100

def transform(df_users, df_orders):
    df_merged = df_orders.merge(df_users, on="user_id")  # a.
    df_merged = df_merged[df_merged["status"] != "cancelled"]  # b.
    df_merged["full_name"] = df_merged["first_name"] + " " + df_merged["last_name"]  # c.
    df_merged = df_merged.drop(["first_name", "last_name"], axis=1)  # axis=1 refer to drop columns
    df_merged["order_value_eur"] = df_merged["amount_usd"] * USD_TO_EUR  # d.
    df_merged["is_high_value"] = df_merged["order_value_eur"] > 100   # e.

    logger.info(f"Successfully transformed 2 sql tables")
    return df_merged


# 3. LOAD
# Load the transformed data into a CSV file

def load(df_merged):
    date = datetime.today().strftime('%Y-%m-%d')
    output_file = f"Outputs/orders_clean_{date}.csv"
    df_merged.to_csv(output_file, index=False)  # avoids index extra column
    logger.info(f"{output_file} loaded successfully!")
    return output_file


def main():
    conn = sqlite3.connect(DB_PATH)  # defined conn object
    df_users, df_orders = extract(conn)
    df_merged = transform(df_users, df_orders)
    output_file = load(df_merged)

if __name__ == "__main__":
    main()















