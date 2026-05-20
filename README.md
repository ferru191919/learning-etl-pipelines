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
Extract (SQLite DB) → Transform → Load (CSV file)

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

## Project 3 - 

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



