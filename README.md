# ETL Pipelines — Python Portfolio

A collection of ETL (Extract, Transform, Load) pipeline projects built in Python,
demonstrating data engineering best practices including logging, error handling,
data quality, and modular pipeline design.

---

## Project 1 — Users ETL Pipeline (level of complexity: EASY)

### Overview
A simple ETL pipeline that extracts user data from a public REST API,
applies data cleaning and transformation, and loads the result into a structured CSV file.

### Pipeline Architecture
Extract → Transform → Load
↓ ↓ ↓
REST API Clean Data CSV File

### What It Does
- **Extract**: Fetches 10 users from [JSONPlaceholder API](https://jsonplaceholder.typicode.com/users)
- **Transform**:
  - Splits full name into `first_name` and `last_name`
  - Flattens nested address into `street`, `city`, `zipcode`
  - Normalizes strings (`.strip()`, `.title()`, `.lower()`)
  - Splits phone number into `phone` and `extension`
  - Guards against `None` values at each stage
- **Load**: Saves cleaned data as a date-stamped CSV file in `Outputs/`

---

## Project 2 — 
