# Second Pipeline
#
# The goal is to learn:
# - SQLite tables as data source
# - Conn object
# - Merge two SQLite tables


# IMPORTANT DISCLAIMER!!!
# Before running this pipeline, you must run the '2.0_setup_database.py' (ONLY ONCE)
# '2.0_ecommerce.db' file will be generated
# this is the SQLite database where this pipeline will extract data from!


from datetime import datetime
import pandas as pd
import sqlite3
import logging


logging.basicConfig(level=logging.INFO)  # production best practices
logger = logging.getLogger(__name__)     # production best practices


DB_PATH = "2.0_ecommerce.db"
USD_TO_EUR = 0.92


# 1. EXTRACT
# Data source: 'users' & 'orders' tables in ecommerce.db file
# To create the ecommerce.db file, run the setup_database.py first

def extract(conn):      # conn = connection object between Python and the SQLite .db file
                        # created with sqlite3.connect(DB_PATH) in main()

    df_users = pd.read_sql("SELECT * FROM users", conn)     # function in Pandas library to read SQL tables --> it returns a DataFrame
    df_orders = pd.read_sql("SELECT * FROM orders", conn)

    logger.info(f"Extracted {df_users.shape} rows x columns successfully from users table")
    logger.info(f"Extracted {df_orders.shape} rows x columns successfully from orders table")

    return df_users, df_orders


# 2. TRANSFORMATION
#
# Perform some cleaning and then merge the two tables.

def transform_merged(df_users, df_orders):
    if df_users is None or df_orders is None:
        logger.warning("No raw users data received, skipping")
        return None

    # SPLIT complete_name into FIRST NAME and LAST NAME
    name_parts = df_users["complete_name"].str.split(" ", n=1, expand=True)
    df_users["first_name"] = name_parts[0]
    df_users["last_name"] = name_parts[1]

    # CONSISTENT UPPERCASE
    df_orders["product"] = df_orders["product"].str.upper()

    # IF STATUS IS EMPTY = CANCELLED
    df_orders["status"] = df_orders["status"].str.strip()  # remove whitespaces
    df_orders["status"] = df_orders["status"].replace("", "cancelled")
    df_orders["status"] = df_orders["status"].replace(" ", "cancelled")

    # MERGE
    df_merged = df_orders.merge(df_users, on="user_id")  # inner join on user_id
    df_merged = df_merged[df_merged["status"] != "cancelled"]  # eliminate "cancelled" rows
    df_merged["order_value_eur"] = df_merged["amount_usd"] * USD_TO_EUR  # add new column
    df_merged["is_high_value"] = df_merged["order_value_eur"] > 100   # add new column with logic

    logger.info(f"Successfully transformed 2 sql tables")
    return df_merged


# 3. LOAD
# Load the transformed data into a CSV file

def load(df_merged):
    if df_merged is None:
        logger.warning("No data received, skipping")
        return None

    date = datetime.today().strftime('%Y-%m-%d')
    output_file = f"Outputs/orders_clean_{date}.csv"
    df_merged.to_csv(output_file, index=False)  # transforms df into csv , avoids index extra column
    logger.info(f"{output_file} loaded successfully!")
    return output_file


def main():
    with sqlite3.connect(DB_PATH) as conn:  # defined conn object (connection between this file and SQL database)
                                            # Context Manager (auto conn.close())
        df_users, df_orders = extract(conn)
        df_merged = transform_merged(df_users, df_orders)
        output_file = load(df_merged)

    logger.info(f"🌟 ETL COMPLETE! Output: {output_file}")


if __name__ == "__main__":
    main()















