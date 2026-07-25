# learning-etl-pipelines

This project is a hands‑on playground for learning how to build small, realistic ETL pipelines in Python.
Each script is one “mini-pipeline” focused on a specific ETL or data warehousing concept.
It starts from the first pipeline "Learning Step 1" onwards.

------------------------------------------------------------

## Learning Step 1

### Overview
A simple ETL pipeline that extracts user data from a public REST API, applies data cleaning and transformation, 
and loads the result into a structured CSV file.

### Learning Goals
- General concept of Extraction, Transformation, Loading
- Production best practices (logging, production guards, ...)
- API as data source

### Pipeline Architecture
Extract (REST API) → Transform → Load (CSV file)

### What It Does
- Fetches user data from the JSONPlaceholder API
- Cleans and normalizes names, addresses, and phone fields
- Saves the transformed output as a date-stamped CSV file.

-----------------------------------------------------------------------------

## Learning Step 2

### Overview
A multi-source ETL pipeline that extracts relational data from a local SQLite database, joins and 
transforms two tables, and loads the result into a structured CSV file.

### Setup
Before running this pipeline, run the setup script once:
- `2.0_setup_database.py` → creates and populates the SQLite source database used by the pipeline

### Learning Goals
- SQLite tables as data source
- Conn object
- Merge two SQLite tables

### Pipeline Architecture
Extract (SQLite DB two tables) → Transform → Load (CSV file)

### What It Does
- Reads users and orders from a local SQLite database
- Joins both tables and filters out canceled orders
- Converts values, derives simple business flags, and writes the result to CSV.

-----------------------------------------------------------------------------

## Learning Step 3

### Overview
A multi-source ETL pipeline that extracts city data from a local SQLite database and live weather data 
from a public API, transforms and merges both sources, and loads the result into a structured SQLite reporting table.

### Setup
Before running this pipeline, run the setup script once:
- `3.0_setup_database.py` → creates and populates the SQLite source database with the city data used by the pipeline

### Learning Goals
- To manage different data sources
- Dynamic API
- Nested JSON and normalization (`json_normalize`)

### Pipeline Architecture
Extract (SQLite DB + API) → Transform → Load (SQLite Report Table)

### What It Does
- Reads city metadata from SQLite and weather data from an API
- Flattens nested JSON and merges the two datasets
- Loads the final weather report into a SQLite table.

-----------------------------------------------------------------------------

## Learning Step 4

### Overview
A multi-step ETL pipeline that extracts stock market data from a public financial API, applies row-level validation 
rules to identify bad records, transforms the valid data into a clean schema, and saves both valid and invalid rows 
into separate SQLite tables.

### Learning Goals
- What validation is
- Validation checks
- Row level validation
- Branching

### Pipeline Architecture
Extract → Validate Raw → Transform → Load (Branch to valid_stocks & invalid_stocks)

### What It Does
- Collects stock quote data for multiple tickers from an API
- Applies row-level validation checks on required fields and numeric values
- Splits the output into valid and invalid records and stores both in SQLite

-----------------------------------------------------------------------------

## Learning Step 5

### Overview
An ETL pipeline that extracts retail customer and order data from a SQLite source database, applies row-level 
validation rules to identify bad records, transforms valid records into a dimensional warehouse-friendly format, 
and loads them into a star schema with one customer dimension and one order fact table.

### Setup
Before running this pipeline, run the setup scripts once:
- `5.0_setup_data_source.py` → creates and populates the SQLite source database used as the operational data source
- `5.1_setup_target_dw.py` → creates the target data warehouse tables for the star schema

### Learning Goals
- How to design and build a star schema DB → (`5.1_setup_target_dw.py`)
- How to populate DW tables using SQL
- Slowly Changing Dimensions Type 1

### Pipeline Architecture
Extract → Validate Raw → Transform → Load Dimension (SCD Type 1) → Enrich Fact → Load Fact

### What It Does
- Validates and cleans customer and order data from the source database
- Loads customers into a dimension table and links orders to surrogate keys
- Populates a simple star schema with one dimension and one fact table.

-----------------------------------------------------------------------------

## Learning Step 6

### Overview
Takes pipeline 5 functions exepts load dim_customer functions. The goal is to understand the difference between 
SCD Type 1 and Type 2. Also load fact_orders is different to implement incremental loading differently from pipeline 5.

### Setup
Before running this pipeline, run the setup scripts once:
- `5.0_setup_data_source.py` → creates and populates the SQLite source database used as the operational data source
- `6.1_dw_setup.py` → creates the target data warehouse tables used by the SCD Type 2 pipeline

### Learning Goals
- Slowly Changing Dimensions (SCD) Type 2
- Incremental Loading

### Pipeline Architecture
Extract → Validate Raw → Transform → Load Dimension (SCD2) → Enrich Fact → Load Fact (Incremental Loading)

### What It Does
- Validates and standardizes customer and order data from the source database
- Loads the customer dimension with SCD Type 2 logic, preserving historical versions
- Enriches orders with surrogate keys and inserts only new fact rows into the warehouse.

-----------------------------------------------------------------------------