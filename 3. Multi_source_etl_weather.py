# MULTI-SOURCE ETL PIPELINE
#
# First, run the '3.0 setup_database.py' file to create the SQLite database to extract data from


import pandas as pd
import requests
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "3.0 cities.db"
BASE_URL = "https://api.open-meteo.com/v1/forecast"

## ----------------- ##
## 1. EXTRACT ##
## ----------------- ##

# from SQLite database.
def extract_cities(conn):
    df_cities = pd.read_sql_query("select * from cities", conn)  # reads SQL table and converts it into a DF
    logger.info(f"Extracted {df_cities.shape[0]} rows and {df_cities.shape[1]} columns successfully from cities table")
    return df_cities

# from API call.
# NOTE: it's a dynamic API, meaning that it fetches different weather data depending
#       on longitude (lon) and latitude (lat).
def extract_weather(df_cities):
    cities_weather = []  # where I will append a dictionary for each API call for each city

    for _, row in df_cities.iterrows():   # method that loops through a DataFrame row by row
        lat = row["latitude"]
        lon = row["longitude"]
        try:   # inside the loop (if one API call fails, the for loop does not stop)
            url = f"{BASE_URL}?latitude={lat}&longitude={lon}&current_weather=true"   # dynamic URL
            response = requests.get(url)  # API call
            response.raise_for_status()  # check response status code == 200
            raw_data = response.json()  # gets data from API call in JSON format
            cities_weather.append(raw_data)
            logger.info(f"Extracted {row['city_name']} weather successfully")

        except requests.exceptions.HTTPError as e:  # in case API call does not fetch data (inside the loop for same reason as try:)
            logger.error(f"HTTP error: {e}")

    logger.info(f"Extracted {len(cities_weather)} cities successfully")
    return cities_weather

## ----------------- ##
## 2. TRANSFORM ##
## ----------------- ##

# - Parse cities_weather (list of JSONs) → extract only the useful fields into a flat DataFrame df_weather.
# - Add city_name to each row so you know which city the weather belongs to.
# - Merge df_weather with df_cities on city_name.
# - Flag extreme weather: is_extreme = True if temperature > 35 or temperature < 0.

def transformation_weather(df_cities, cities_weather):
    clean_rows = [] # where I will append clean dictionaries for my new df
    for i, city in enumerate(cities_weather):  # cities_weather is a list of dictionaries (need to iterate for each city)
#                                                enumerate() gives both the index (i) and value from a list
        city_name = df_cities.iloc[i]["city_name"]
        temperature_unit = city["current_weather_units"]["temperature"]
        temperature = city["current_weather"]["temperature"]
        windspeed_unit = city["current_weather_units"]["windspeed"]
        windspeed = city["current_weather"]["windspeed"]
        clean_rows.append({  # creating clean dictionary
            "city_name": city_name,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "windspeed": windspeed,
            "windspeed_unit": windspeed_unit,
        })
    df_weather = pd.DataFrame(clean_rows)  # first two transformations done!

#   Transformation #3
    df_merged = df_weather.merge(df_cities, on="city_name")  # inner join (only cities with weather data)

#   Transformation #4
    condition = (df_merged["temperature"] > 35) | (df_merged["temperature"] < 0)
    df_merged["is_extreme"] = condition  # adds new boolean column

    logger.info(f"Transformed: {df_merged.shape[0]} rows, {df_merged.shape[1]} columns")
    return df_merged


## ----------------- ##
## 3. LOAD ##
## ----------------- ##

def load_weather_report(conn, df_merged):
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




