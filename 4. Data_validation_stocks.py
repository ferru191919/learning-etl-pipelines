# Validation Rules = e.g. ensuring data is not missing, ensuring ID uniqueness,
#                         ensuring referential integrity, minimum row count, etc...

# It's important to do so after each step of the ETL pipeline --> Pipeline Observability!!

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

# 1. EXTRACT: Loop through tickers, call API for each, collect raw responses.

def extract():
    raw_stock_data = []

    for ticker in TICKERS:
        try:
            url = f"{BASE_URL}function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            raw_data = response.json()
            raw_stock_data.append(raw_data)
            logger.info(f"Successfully extracted {ticker}")
            time.sleep(1)  # recommended

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")

    return raw_stock_data

# 2. VALIDATE raw data:
#    - Response must contain "Global Quote" key
#    - "Global Quote" must not be empty {}
#    - Price must exist and be convertible to float

def validate_raw(raw_stock_data):
    valid_data = []

    for i, dictionary in enumerate(raw_stock_data):
        # response must contain "Global Quote" key
        if "Global Quote" not in dictionary:
            logger.warning(f"No Global Quote for item {i} - skipping")  # can't use dictionary['symbol'] because it does not exist
            continue   # skips other validations and goes to next dictionary

        # "Global Quote" must not be empty {}
        if dictionary["Global Quote"] == {}:
            logger.warning(f"Empty Global Quote for item {i} - skipping")
            continue

        # Price must exist
        if "05. price" not in dictionary["Global Quote"]:
            logger.warning(f"Empty price for {dictionary['symbol']} - skipping")
            continue

        # Price must be convertible to float (i.e. it's not N/A)
        try:
            float(dictionary["Global Quote"]["05. price"])
        except (ValueError, TypeError):
            logger.warning(f"Invalid price for {dictionary['Global Quote']['01. symbol']} - skipping")
            continue

        valid_data.append(dictionary)

    return valid_data

# 3. TRANSFORM validated data
#    - Flatten JSON → clean DataFrame
#    - Rename fields to snake_case (open_price, close_price, etc.)
#    - Convert price columns from string → float
#    - Add extracted_at timestamp column
#    - Flag is_high_volume = True if volume > 20,000,000

def transform(valid_data):
    clean_rows = []
    for dictionary in valid_data:
        ticker = dictionary["Global Quote"]["01. symbol"]
        open_price = float(dictionary["Global Quote"]["02. open"])
        highest_price = float(dictionary["Global Quote"]["03. high"])
        lowest_price = float(dictionary["Global Quote"]["04. low"])
        current_price = float(dictionary["Global Quote"]["05. price"])
        volume = int(dictionary["Global Quote"]["06. volume"])
        latest_trading_day = dictionary["Global Quote"]["07. latest trading day"]
        previous_close = float(dictionary["Global Quote"]["08. previous close"])
        change = dictionary["Global Quote"]["09. change"]
        change_percent = dictionary["Global Quote"]["10. change percent"]

        clean_rows.append({
            "ticker" : ticker,
            "open_price" : open_price,
            "highest_price" : highest_price,
            "lowest_price" : lowest_price,
            "current_price" : current_price,
            "volume" : volume,
            "latest_trading_day" : latest_trading_day,
            "previous_close" : previous_close,
            "change" : change,
            "change_percent" : change_percent,
        })

    df_clean = pd.DataFrame(clean_rows)
    df_clean["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_clean["is_high_volume"] = df_clean["volume"] > 20000000
    logger.info(f"Successfully transformed {df_clean.shape[0]} rows and {df_clean.shape[1]} columns")
    return df_clean

# 4. Post-Transformation VALIDATION

def validate_clean(df_clean):
    # 1. Check DataFrame is not empty
    if df_clean.empty:
        raise ValueError("Transformed DataFrame is empty!")

    # 2. Check no nulls in critical columns
    critical_columns = ["ticker", "current_price"]
    if df_clean[critical_columns].isnull().any().any():   # .any().any() returns one True/False for previous condition
        raise ValueError("Null values found in critical columns!")

    # 3. Check price > 0
    if not (df_clean["current_price"] > 0).all():      # .all() returns True only if every value in the Series is True
        raise ValueError("Prices must be positive!")

    # 4. Check row count matches expected
    expected_count = len(TICKERS)
    if df_clean.shape[0] != expected_count:
        raise ValueError(f"Expected {expected_count} rows, got {df_clean.shape[0]}")

    logger.info(f"Validated: {df_clean.shape[0]} rows passed all checks")
    return df_clean

# 5. LOAD → stock_report table in SQLite

def load(df_clean, conn):
    df_clean.to_sql("stock_report", conn, index=False, if_exists="replace")  # transforming df_clean into stock_report sql table
    logger.info("✅ Loaded stock_report table to SQLite")


def main():
    with sqlite3.connect(DB_PATH) as conn:
        raw_stock_data = extract()
        logger.info(f"Raw data count: {len(raw_stock_data)}")

        valid_data = validate_raw(raw_stock_data)
        logger.info(f"Valid raw data count: {len(valid_data)}")

        df_clean = transform(valid_data)
        logger.info(f"Transformed df_clean shape: {df_clean.shape}")

        df_clean = validate_clean(df_clean)
        load(df_clean, conn)



if __name__ == "__main__":
    main()







