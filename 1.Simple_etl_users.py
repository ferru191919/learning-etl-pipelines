# First Pipeline
#
# The goal is to learn:
# - General concept of Extraction, Transformation, Loading
# - Production best practices (logging, production guards, ...)
# - API as data source


from datetime import datetime
import requests
import pandas as pd
import os
import logging


logging.basicConfig(level=logging.INFO)  # production best practices
logger = logging.getLogger(__name__)     # production best practices


# GLOBAL VARIABLES
API_URL = "https://jsonplaceholder.typicode.com/users"
TIMEOUT = 10
OUTPUT_DIR = "Outputs/"


# EXTRACTION
def extract_users():
    try:
        response = requests.get(API_URL, timeout=TIMEOUT)   # API call
        response.raise_for_status()     # check response status code == 200
        raw_data = response.json()      # get data from API call in JSON format
        logger.info(f"Extracted {len(raw_data)} users successfully")  # == 10
        return raw_data
    except requests.exceptions.HTTPError as e:  # API call failed
        logger.error(f"HTTP error: {e}")
        return None


# Transformation processes:
# a. Splitting name into first and last name
# b. Including in address only Street, City, and Zip code
# c. Ensuring data quality (no Null, whitespaces, etc...) with string methods
# d. Splitting phone in phone_number and extension

def transform_users(raw_data):

    # Production Guard
    # If it does not receive raw data, it skips transformation
    if raw_data is None:
        logger.warning("No raw data received, skipping transforming")
        return None

    clean_users = []      # where I will append dictionaries of clean users data

    for user in raw_data:
        name_parts = user["name"].split(" ", maxsplit=1)  # maxsplit=1 allows to split the full name in 1 first name + multiple last names
        first_name = name_parts[0].strip().title()
        last_name = name_parts[1].strip().title()
        city = user["address"]["city"].strip().title()      # nested value
        street = user["address"]["street"].strip().title()
        zipcode = user["address"]["zipcode"].strip()
        email = user["email"].strip().lower()
        phone_parts = user["phone"].split(" x")
        phone_number = phone_parts[0].strip()
        extension = phone_parts[1].strip() if len(phone_parts) > 1 else None

        clean_users.append({"user_id" : user["id"],     # Building dictionaries with clean users data
                            "first_name" : first_name,
                            "last_name" : last_name,
                            "city" : city,
                            "street" : street,
                            "zipcode" : zipcode,
                            "email" : email,
                            "phone" : phone_number,
                            "extension" : extension})

    logger.info(f"Sample record: {clean_users[3]}")
    logger.info(f"Transformed {len(clean_users)} users successfully")
    df = pd.DataFrame(clean_users)  # converts dictionaries into df
    return df


# Loading processes:
# Save the DataFrame as a CSV file inside an output/ folder.

def load_users(df):
    if df is None:  # Production guard
        logger.warning("No transformed data received, skipping loading")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)   # Creates new folder for output (if it does not exist)
    date = datetime.today().strftime('%Y-%m-%d')
    output_file = f'{OUTPUT_DIR}simple_etl_users_output_{date}.csv'  # Output file name
    df.to_csv(output_file, index=False)  # Transforms df into csv file
    logger.info(f"{output_file} loaded successfully!")
    return output_file


# LOGIC
def main():
    raw_data = extract_users()
    df = transform_users(raw_data)
    load_users(df)


if __name__ == "__main__":         # Guard block ← only runs when YOU run this file
                                    # (e.g. avoids automatic run when imported)
    main()




