# Fourth Pipeline
#
# The goal is to learn:
# - What validation is
# - Validation checks
# - Row level validation


# DATA VALIDATION = Data validation is the process of verifying that data is clean, accurate and ready for use.
#                   It avoids inconsistent formats and discrepancies, duplicate data, incomplete data fields,
#                   data entry errors, missing data.

# VALIDATION CHECKS = e.g. specific operations that ensure data is not missing, ensuring ID uniqueness,
#                         ensuring referential integrity, minimum row count, etc...

# ROW-LEVEL VALIDATION: I don't want to invalid whole DB because of some invalid rows. Therefore, I'll build
#                       a boolean mask (condition = True/False) that identifies which rows respect that condition.
#                       The rows that respect the condition will create a 'valid' db.


from datetime import datetime
import pandas as pd
import requests
import sqlite3
import logging
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_KEY = "WHQYM3ZFLN98YR7Y"
BASE_URL = "https://www.alphavantage.co/query?"
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
DB_PATH = "4.0 stocks.db"


# 1. EXTRACT
#
# Loop through tickers, call API for each, collect raw responses.
#
def extract():
    raw_stock_data = []

    for ticker in TICKERS:
        try:
            url = f"{BASE_URL}function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            raw_data = response.json()
            raw_stocks = raw_data["Global Quote"]  # indexing for Global_Quote
            raw_stock_data.append(raw_stocks)
            logger.info(f"Successfully extracted {ticker}")
            time.sleep(1)  # recommended

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")

    return raw_stock_data


# 2. VALIDATE raw data:
#
#    a) PRESENCE CHECK: did you get one quote per ticker?
#    b) PRESENCE CHECK: did you get the required columns? (symbol, price, volume)
#    c) FORMAT CHECK: are "05. price" and "06. volume" numeric?
#
def validate_raw(raw_stock_data):
    if raw_stock_data is None:
        logger.warning("Empty raw data, skipping")
        return None


    # I will convert lists of JSONs into DF before validation
    df_raw = pd.DataFrame(raw_stock_data)   # I'm not using json.normalize because JSON has no nested values
    df_raw["validation_errors"] = ""       # Creating a new column to differentiate valid vs. invalid rows


    # a) One quote per ticker
    if df_raw.shape[0] != len(TICKERS):
        logger.warning(
            "Row count mismatch: got %d rows, expected %d (len(TICKERS))",
            df_raw.shape[0],
            len(TICKERS),
        )

    # Building a boolean mask (condition = True/False) per row
    #
    # b) Required columns
    mask_missing_symbol = df_raw["01. symbol"].isnull() | (df_raw["01. symbol"].astype(str).str.strip() == "")
    mask_missing_price = df_raw["05. price"].isnull() | (df_raw["05. price"].astype(str).str.strip() == "")
    mask_missing_volume = df_raw["06. volume"].isnull() | (df_raw["06. volume"].astype(str).str.strip() == "")

    # c) FORMAT CHECK
    price_as_num = pd.to_numeric(df_raw["05. price"], errors="coerce")  # price must be convertible to numeric, otherwise it's NaN
    mask_price_not_num = price_as_num.isna() # if price is NaN, then condition = True
    mask_price_not_positive = price_as_num <= 0 # if price <= 0, then True

    volume_as_num = pd.to_numeric(df_raw["06. volume"], errors="coerce")
    mask_volume_not_num = volume_as_num.isna()
    mask_volume_not_positive = volume_as_num <= 0


    # For each row (condition = True), concatenate the error code ("" string) in "validation_errors" column
    df_raw.loc[mask_missing_symbol, "validation_errors"] += "; missing symbol"
    df_raw.loc[mask_missing_price, "validation_errors"] += "; missing price"
    df_raw.loc[mask_missing_volume, "validation_errors"] += "; missing volume"
    df_raw.loc[mask_price_not_num, "validation_errors"] += "; price not numeric"
    df_raw.loc[mask_price_not_positive, "validation_errors"] += "; price not positive"
    df_raw.loc[mask_volume_not_num, "validation_errors"] += "; volume not numeric"
    df_raw.loc[mask_volume_not_positive, "validation_errors"] += "; volume not positive"


# Split valid vs. invalid rows
    invalid_quotes = df_raw[df_raw["validation_errors"] != ""]
    valid_quotes = df_raw[df_raw["validation_errors"] == ""]

    logger.info(
        "Quotes validation completed: %d valid, %d invalid",
        valid_quotes.shape[0],
        invalid_quotes.shape[0],
    )

    return valid_quotes, invalid_quotes


# 3. TRANSFORM validated data
#
#    - Create a "quote_id" column
#    - Convert columns names & Convert price into float, and convert volume into integer
#    - Remove "validation_errors" column
#    - Flag is_high_volume = True if volume > 20,000,000
#
def transform(valid_quotes):
    if valid_quotes is None:
        logger.warning("Validated data is missing, skipping")
        return None

    # a) Create a quote_id column
    df_clean = valid_quotes.copy()
    df_clean.reset_index(drop=True, inplace=True)   # drop old index but modifies original DataFrame
    df_clean["quote_id"] = df_clean.index + 1       # 1, 2, 3, ...

    # b) Convert columns names
    df_clean = df_clean.rename(columns={
        "01. symbol": "symbol",
        "05. price": "price",
        "06. volume": "volume",
    })

    # b) Convert price into float, and volume into integer
    df_clean["price"] = pd.to_numeric(df_clean["price"], errors="raise")  # errors=raise because I already validated it
    df_clean["volume"] = pd.to_numeric(df_clean["volume"], errors="raise").astype("Int64")

    # c) Remove validation_errors column
    df_clean = df_clean.drop(columns=["validation_errors"])

    # d) Add is_high_volum column
    df_clean["is_high_volume"] = df_clean["volume"] > 20000000

    logger.info(f"Successfully transformed {df_clean.shape[0]} rows and {df_clean.shape[1]} columns")
    return df_clean


# 5. LOAD
#
# Loading valid and invalid tables into '4.0 stocks.db' database
#
def load(df_clean, invalid_quotes, conn):

    if df_clean is None or invalid_quotes is None:
        logger.warning("Data is missing, skipping")
        return None

    df_clean.to_sql("valid_stock_report", conn, index=False, if_exists="replace")  # transforming df_clean into stock_report sql table
    logger.info("✅ Loaded 'valid_stock_report' into %s database",
                "4.0 stocks.db")

    invalid_quotes.to_sql("invalid_stocks", conn, index=False,
                    if_exists="replace")  # transforming invalid_quotes into invalid_stocks sql table
    logger.info("✅ Loaded 'invalid_stocks' into %s database",
                "4.0 stocks.db")


# MAIN
def main():
    with sqlite3.connect(DB_PATH) as conn:
        raw_stock_data = extract()
        logger.info(
            "Raw data count: %d",
            len(raw_stock_data))

        valid_quotes, invalid_quotes = validate_raw(raw_stock_data)
        logger.info(
            "Valid quotes data count: %d; Invalid quotes data count: %d",
            valid_quotes.shape[0], invalid_quotes.shape[0])

        df_clean = transform(valid_quotes)
        logger.info(
            "Transformed %d rows and %d columns",
            df_clean.shape[0],
            df_clean.shape[1])

        load(df_clean, invalid_quotes, conn)


if __name__ == "__main__":
    main()