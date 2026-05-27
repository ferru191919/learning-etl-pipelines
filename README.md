# ETL Pipelines — Python Portfolio

A collection of ETL (Extract, Transform, Load) pipeline projects built in Python,
demonstrating data engineering best practices including logging, error handling,
data quality, and modular pipeline design.

---

## Project 1 — Users ETL Pipeline

### Overview
A simple ETL pipeline that extracts user data from a public REST API,
applies data cleaning and transformation, and loads the result into a structured CSV file.

### Pipeline Architecture
Extract (RestAPI) → Transform → Load (CSV file)

### What It Does
- **Extract**: Fetches 10 users from [JSONPlaceholder API](https://jsonplaceholder.typicode.com/users)
- **Transform**:
  - Splits full name into `first_name` and `last_name`
  - Flattens nested address into `street`, `city`, `zipcode`
  - Normalizes strings (`.strip()`, `.title()`, `.lower()`)
  - Splits phone number into `phone` and `extension`
  - Guards against `None` values at each stage
- **Load**: Saves cleaned data as a date-stamped CSV file in `Outputs/`

-----------------------------------------------------------------------------

## Project 2 — Multi Table Orders ETL Pipeline

## Overview
A multi-source ETL pipeline that extracts relational data from a local SQLite database, 
joins and transforms two tables, and loads the result into a structured CSV file.

## Pipeline Architecture
Extract (SQLite DB two tables) → Transform → Load (CSV file)

## What It Does
**Extract**:
- Reads users and orders tables from a local SQLite database (ecommerce.db) using pandas.read_sql()

**Transform**:
- Joins two sql tables: df_orders and df_users 
- Filters out cancelled orders 
- Creates full_name column by concatenating first_name and last_name, then drops the originals 
- Converts orders' amount from USD to Euro 
- Flags high-value orders (is_high_value = True if order_value_eur > 100)

**Load**:
- Saves transformed data as a date-stamped CSV file in Outputs/

-----------------------------------------------------------------------------

## Project 3 - Multi-Source Weather ETL Pipeline

### Overview
A multi-source ETL pipeline that extracts city data from a local SQLite database and live weather data from a public API, transforms and merges both sources, and loads the result into a structured SQLite reporting table.

### Pipeline Architecture
Extract (SQLite DB + API) → Transform → Load (SQLite Report Table)

## What It Does
**Extract**
- Reads city data from a local SQLite database (`3.0 cities.db`) using `pandas.read_sql_query()`
- Calls the [Open-Meteo API](https://open-meteo.com/) for each city using latitude and longitude
- Collects current weather data for multiple cities through dynamic API requests

**Transform**
- Parses raw JSON responses into a flat weather DataFrame
- Adds `city_name` to each weather record
- Merges weather data with city metadata on `city_name`
- Flags extreme weather conditions (`is_extreme = True` if temperature > 35 or temperature < 0)

**Load**
- Saves the final transformed dataset into the `weather_report` table in SQLite


-----------------------------------------------------------------------------

## Project 4 — Stock Market ETL Pipeline with Validation Rules

### Overview
A multi-step ETL pipeline that extracts stock market data from a public financial API,
validates data quality before and after transformation, and loads the result into a 
structured SQLite reporting table.

### Pipeline Architecture
Extract → Validate Raw → Transform → Validate Clean → Load

## What It Does

**Extract**
- Calls the Alpha Vantage API for multiple stock tickers (AAPL, GOOGL, MSFT, AMZN, TSLA)
- Collects raw market data through repeated API requests with a short delay between calls

**Validate Raw**
- Ensures each response contains the Global Quote key
- Skips empty API responses
- Checks that price values exist and can be converted to numeric format

**Transform**
- Flattens nested JSON into a clean pandas DataFrame
- Renames fields into analysis-friendly snake_case columns
- Converts price and volume fields to numeric types
- Adds an extracted_at timestamp column
- Flags high-volume stocks (is_high_volume = True if volume > 20,000,000)

**Validate Clean**
- Ensures the transformed DataFrame is not empty
- Checks for null values in critical columns such as ticker and current_price
- Verifies that stock prices are positive
- Confirms the final row count matches the expected number of tickers

**Load**
- Saves the final validated dataset into the stock_report table in SQLite

-----------------------------------------------------------------------------

## Project 5 — Multi-Source Orders ETL Pipeline with Branching Logic

### Overview
A multi-source ETL pipeline that extracts customer master data from SQLite and order/cart
data from a public API, validates both sources with different rules, transforms and enriches 
the data through a join, and branches the output into accepted and rejected reporting tables.

### Pipeline Architecture
Extract → Validate Raw → Transform → Branch → Load

### What It Does

**Extract**
- Reads customer data from a SQLite customers table (master data)
- Fetches raw cart/order data from the DummyJSON carts API (transaction data).

**Validate Raw**
- DataFrame is not empty
- customer_id has no null
- customer_id is unique
- required descriptive fields such as customer_name and email are present

**Transform**
1. Receive validated inputs
2. Transform order dictionary input into DataFrame
3. Join the two DataFrames (order row fine-grained)
4. Branching based on condition (orders with and without customer)
5. Apply final cleaning transformation to tables before loading

**Branch**
- Rows with a matched customer go to the accepted dataset.
- Rows with missing customer_name after the join are routed to a rejected dataset.

**Load**
Loads accepted rows into the order_report SQLite table and rejected rows into the order_report_rejected table. This branching pattern preserves useful data for reporting while keeping failed records available for debugging, auditing, and possible reprocessing.