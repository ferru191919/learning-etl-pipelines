# Third Pipeline
#
# The goal is to learn:
# - To manage different data sources
# - Dynamic API
# - Nested JSON and normalization (json_normalize)


# DISCLAIMER!
#
# First, run the '3.0_setup_database.py' file to create the SQLite database to extract data from it.


import pandas as pd
import requests
import sqlite3
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DB_PATH = "3.0 cities.db"
BASE_URL = "https://api.open-meteo.com/v1/forecast"


## 1. EXTRACT
#
# from SQLite database.
#
def extract_cities(conn):
    df_cities = pd.read_sql_query("select * from cities", conn)
    logger.info(f"Extracted {df_cities.shape[0]} rows and {df_cities.shape[1]} columns successfully from cities table")
    return df_cities


#
# from API call.
# NOTE: it's a dynamic API:
# meaning that it fetches different weather data depending on longitude (lon) and latitude (lat).
#
def extract_weather(df_cities):
    cities_weather = []

    for _, row in df_cities.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        city_name = row["city_name"]

        try:
            url = f"{BASE_URL}?latitude={lat}&longitude={lon}&current_weather=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw_data = response.json()
            # attach city name into the JSON so it survives normalization
            raw_data["city_name"] = city_name
            cities_weather.append(raw_data)
            logger.info("Extracted %s weather successfully", city_name)

        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", city_name, e)

    logger.info("Extracted %d cities successfully", len(cities_weather))
    return cities_weather


## 2. TRANSFORM ##
#
# We've got a list of dictionaries (cities_weather) and a DataFrame from Extract functions.
#
# I want to transform cities_weather into a DF before transformation. However, JSON has nested values.
#
# There are two common ways to turn nested JSON data into a flat DataFrame:
# a) Loop through each JSON object, manually pick the nested fields you need, and build a list of clean dictionaries (like I did in '1.Simple_etl_users.py').
# b) Use pd.json_normalize to automatically flatten the nested dictionaries into normal columns.
#
def transformation_weather(df_cities, cities_weather):
    if df_cities is None and cities_weather is None:
        logger.warning("No cities data received, skipping")
        return None

    # 1) Flatten the list of JSONs into a DataFrame
    df_raw = pd.json_normalize(cities_weather)

    # 2) Add city_name if it's not already in the JSON
    #    (this assumes cities_weather is in the same order as df_cities)
    if "city_name" not in df_raw.columns:
        df_raw["city_name"] = df_cities["city_name"].values

    # 3) Select and rename only the useful fields into df_weather
    df_weather = pd.DataFrame({
        "city_name": df_raw["city_name"],
        "temperature": df_raw["current_weather.temperature"],  # one of the nested values in previous JSON
        "temperature_unit": df_raw["current_weather_units.temperature"],  # one of the nested values in previous JSON
        "windspeed": df_raw["current_weather.windspeed"],   # one of the nested values in previous JSON
        "windspeed_unit": df_raw["current_weather_units.windspeed"],   # one of the nested values in previous JSON
    })

    # 4) Merge with df_cities on city_name
    df_merged = df_weather.merge(df_cities, on="city_name", how="inner")

    # 5) Flag extreme weather
    condition = (df_merged["temperature"] > 35) | (df_merged["temperature"] < 0)
    df_merged["is_extreme"] = condition

    logger.info(f"Transformed: {df_merged.shape[0]} rows, {df_merged.shape[1]} columns")
    return df_merged


## 3. LOAD
#
def load_weather_report(conn, df_merged):
    if df_merged is None:
        logger.warning("No weather data received, skipping")
        return None

    df_merged.to_sql("weather_report", conn, if_exists="replace", index=False)  # transforms df to "weather_report" SQL table
                                                                                # conn = connecting to existing SQLite file
    logger.info("✅ Loaded weather_report table to SQLite")


def main():
    with sqlite3.connect(DB_PATH) as conn:   # defined conn object (Context Manager)
        df_cities= extract_cities(conn)
        cities_weather = extract_weather(df_cities)
        df_merged = transformation_weather(df_cities, cities_weather)
        load_weather_report(conn, df_merged)

    logger.info("🌤️ Weather ETL COMPLETE!")


if __name__ == "__main__":
    main()