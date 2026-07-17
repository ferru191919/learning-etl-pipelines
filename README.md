# learning-etl-pipelines

This project is a hands‑on playground for learning how to build small, realistic ETL pipelines in Python step by step.
Each of the four scripts is one “mini‑pipeline” that focuses on a specific set of skills:
- The *first pipeline* introduces the core ETL flow (extract → transform → load), pulling data from an API, adding logging, and using simple production guards. 
- The *second pipeline* works with SQLite as a data source, using a connection object and joining multiple tables. 
- The *third pipeline* combines multiple data sources (database + dynamic API), and shows how to handle nested JSON and flatten it with json_normalize. 
- The *fourth pipeline* adds data validation on top of ETL: presence checks, type checks, row‑level validation using boolean masks, and branching into “valid” vs “invalid” tables.
- The *fifth pipeline* expands the project into a small warehouse-style ETL flow. It introduces a star schema design by transforming raw data to match data warehouse fields, enriching the fact table with dimension table attributes, and loading the results into the warehouse.
------------------------------------------------------------

## Project 1 — REST API - Users ETL

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

## Project 2 — Multi-table SQLite - Orders ETL

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
- Filters out canceled orders 
- Splits `complete_name` into `first_name` and `last_name`
- Converts orders' amount from USD to Euro 
- Flags high-value orders (is_high_value = True if order_value_eur > 100)

**Load**:
- Saves transformed data as a date-stamped CSV file in Outputs/

-----------------------------------------------------------------------------

## Project 3 - Multi-Source (API + SQLite) - Weather ETL

### Overview
A multi-source ETL pipeline that extracts city data from a local SQLite database and live weather data 
from a public API, transforms and merges both sources, and loads the result into a structured SQLite reporting table.

### Pipeline Architecture
Extract (SQLite DB + API) → Transform → Load (SQLite Report Table)

## What It Does
**Extract**
- Reads city data from a local SQLite database (`3.0 cities.db`) using `pandas.read_sql_query()`
- Calls the [Open-Meteo API](https://open-meteo.com/) for each city using latitude and longitude
- Collects current weather data for multiple cities through dynamic API requests

**Transform**
- Parses raw JSON responses into a flat weather DataFrame using json_normalize
- Adds `city_name` to each weather record
- Merges weather data with city metadata on `city_name`
- Flags extreme weather conditions (`is_extreme = True` if temperature > 35 or temperature < 0)

**Load**
- Saves the final transformed dataset into the `weather_report` table in SQLite


-----------------------------------------------------------------------------
## Project 4 — Validation Rules - Stock Market ETL

### Overview
A multi-step ETL pipeline that extracts stock market data from a public financial API, 
applies row-level validation rules to identify bad records, transforms the valid data 
into a clean schema, and saves both valid and invalid rows into separate SQLite tables.

### Pipeline Architecture
Extract → Validate Raw → Transform → Load (Branch to valid_stocks & invalid_stocks)

### What It Does

**Extract**
- Calls the Alpha Vantage `GLOBAL_QUOTE` endpoint for multiple stock tickers (AAPL, GOOGL, MSFT, AMZN, TSLA)
- Extracts the `"Global Quote"` block from each API response
- Collects one raw quote dictionary per ticker with a short delay between requests

**Validate (row-level)**
- Converts the list of quote dictionaries into a pandas DataFrame
- Adds a `validation_errors` column to store row-level error codes
- Checks required fields:
  - `01. symbol` (stock symbol) is present and not empty
  - `05. price` (latest price) is present and not empty
  - `06. volume` (trading volume) is present and not empty
- Checks numeric format and business rules:
  - `05. price` and `06. volume` can be converted to numeric values
  - `price` and `volume` are strictly positive
- Logs a warning if the number of returned rows does not match the number of requested tickers
- Splits the dataset into:
  - `valid_quotes` (rows with an empty `validation_errors` string)
  - `invalid_quotes` (rows where one or more validation rules failed)

**Transform**
- Copies `valid_quotes` into a clean working DataFrame
- Resets the index and creates a sequential `quote_id`
- Renames Alpha Vantage fields to analysis-friendly names:
  - `"01. symbol"` → `symbol`
  - `"05. price"` → `price`
  - `"06. volume"` → `volume`
- Converts `price` to float and `volume` to integer types
- Drops the `validation_errors` column (since only valid rows are kept here)
- Flags high-volume stocks with:
  - `is_high_volume = True` if `volume > 20_000_000`

**Load (Branching)**
- Writes the clean, validated quotes to a `valid_stocks` table in the SQLite database
- Writes all invalid or rejected rows (with their `validation_errors`) to an `invalid_stocks` table

-----------------------------------------------------------------------------
## Project 5 — Data Warehouse Design - Orders fact table, Customers dimension table

### Overview
A multi-step ETL pipeline that extracts retail customer and order data from a SQLite source database, 
applies row-level validation rules to identify bad records, transforms valid records into a dimensional 
warehouse-friendly format, and loads them into a star schema with one customer dimension and one order fact table.

### Pipeline Architecture
Extract → Validate Raw → Transform → Load Dimension → Enrich Fact → Load Fact

### What It Does

**Extract**
- Connects to a SQLite operational source database
- Extracts raw customer data from the `customers` table
- Extracts raw order data from the `orders` table
- Loads both datasets into pandas DataFrames for validation and transformation

**Validate Customers (row-level)**
- Adds a `validation_errors` column to store row-level error codes
- Checks `customer_id`:
  - is present and not empty
  - can be converted to an integer
  - is positive
  - is not duplicated
- Checks `first_name` and `last_name`:
  - are present and not empty
- Checks `email`:
  - is present and not empty
  - contains `@`
- Checks `country`:
  - if present, must be a 2-letter uppercase country code
- Checks `created_at`:
  - must be parseable as a date/time value
- Splits the dataset into:
  - `valid_customers`
  - `invalid_customers`

**Validate Orders (row-level)**
- Adds a `validation_errors` column to store row-level error codes
- Checks `order_id`:
  - is present and not empty
  - can be converted to an integer
  - is positive
  - is not duplicated
- Checks `customer_id`:
  - is present and not empty
  - can be converted to an integer
  - is positive
- Checks `order_date`:
  - must be parseable as a date
- Checks `amount`:
  - is present and not empty
  - can be converted to numeric
  - is strictly positive
- Checks `quantity`:
  - is present and not empty
  - can be converted to numeric
  - is not negative
- Checks `currency`:
  - is present and not empty
- Splits the dataset into:
  - `valid_orders`
  - `invalid_orders`

**Transform Customers**
- Copies `valid_customers` into a clean working DataFrame
- Renames and standardizes the source business key:
  - `customer_id` → `customer_source_id`
- Cleans text fields:
  - trims spaces from names
  - converts names to title case
  - lowercases and trims email values
  - uppercases country codes
- Converts `created_at` to a standard datetime string format
- Drops duplicate customers by `customer_source_id`
- Produces a clean customer dataset ready for the dimension table

**Transform Orders**
- Copies `valid_orders` into a clean working DataFrame
- Renames and standardizes the foreign business key:
  - `customer_id` → `customer_source_id`
- Standardizes fields:
  - converts `order_id` to integer
  - converts `order_date` to `YYYY-MM-DD`
  - converts `amount` to float
  - converts `quantity` to float
  - uppercases `currency`
  - lowercases and trims `sales_channel`
- Produces a clean orders dataset ready for dimensional enrichment

**Load Customer Dimension**
- Loads clean customer records into the `dim_customer` table
- Uses `customer_source_id` as the business key for upsert logic
- Updates existing customer rows when the same source customer already exists
- Inserts new customer rows when the source customer is new

**Enrich Fact Orders**
- Reads `customer_sk` and `customer_source_id` from `dim_customer`
- Joins clean orders to the customer dimension on `customer_source_id`
- Replaces the source business key with the warehouse surrogate key `customer_sk`
- Keeps only matched rows for fact loading
- Produces the final `fact_df` dataset for the fact table

**Load Order Fact**
- Loads enriched order rows into the `fact_order` table
- Stores:
  - `order_id`
  - `customer_sk`
  - `order_date`
  - `amount`
  - `quantity`
  - `currency`
  - `sales_channel`
- Uses upsert logic so repeated runs update existing fact rows instead of duplicating them

### Star Schema Design
- **Dimension table:** `dim_customer`
- **Fact table:** `fact_order`
- **Business key:** `customer_source_id`
- **Surrogate key:** `customer_sk`

### Learning Goals
- Practice building a star schema from an operational source
- Apply row-level validation before transformation
- Separate valid and invalid business records logically in the pipeline
- Standardize messy source data before loading a warehouse
- Use surrogate keys and dimension lookups to populate fact tables
- Implement idempotent loads with SQLite upsert logic

-----------------------------------------------------------------------------