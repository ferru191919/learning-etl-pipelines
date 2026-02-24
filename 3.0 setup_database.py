import sqlite3
import pandas as pd

DB_PATH = "3.0 cities.db"

cities_data = [
    {"city_id": 1, "city_name": "Milan",        "country": "Italy",          "latitude": 45.4654,  "longitude": 9.1859},
    {"city_id": 2, "city_name": "London",       "country": "United Kingdom", "latitude": 51.5074,  "longitude": -0.1278},
    {"city_id": 3, "city_name": "New York",     "country": "United States",  "latitude": 40.7128,  "longitude": -74.0060},
    {"city_id": 4, "city_name": "Tokyo",        "country": "Japan",          "latitude": 35.6762,  "longitude": 139.6503},
    {"city_id": 5, "city_name": "Sydney",       "country": "Australia",      "latitude": -33.8688, "longitude": 151.2093},
    {"city_id": 6, "city_name": "Dubai",        "country": "UAE",            "latitude": 25.2048,  "longitude": 55.2708},
    {"city_id": 7, "city_name": "São Paulo",    "country": "Brazil",         "latitude": -23.5505, "longitude": -46.6333},
    {"city_id": 8, "city_name": "Toronto",      "country": "Canada",         "latitude": 43.6510,  "longitude": -79.3470},
]

def setup():
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame(cities_data)
    df.to_sql("cities", conn, if_exists="replace", index=False)
    print(f"✅ Created 'cities' table with {len(df)} rows in {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    setup()
