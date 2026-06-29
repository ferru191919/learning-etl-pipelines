# learning-etl-pipelines

This project is a hands‑on playground for learning how to build small, realistic ETL pipelines in Python step by step.
Each of the four scripts is one “mini‑pipeline” that focuses on a specific set of skills:
- The *first pipeline* introduces the core ETL flow (extract → transform → load), pulling data from an API, adding logging, and using simple production guards. 
- The *second pipeline* works with SQLite as a data source, using a connection object and joining multiple tables. 
- The *third pipeline* combines multiple data sources (database + dynamic API), and shows how to handle nested JSON and flatten it with json_normalize. 
- The *fourth pipeline* adds data validation on top of ETL: presence checks, type checks, row‑level validation using boolean masks, and branching into “valid” vs “invalid” tables.

---

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