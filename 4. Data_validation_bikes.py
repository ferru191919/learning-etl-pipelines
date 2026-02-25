# Validation rules = e.g. ensuring data is not missing, ensuring ID uniqueness,
#                         ensuring referential integrity, minimum row count, etc...

# It's important to do so BEFORE transformation to avoid waisting resources for transform data that
# is not valid.


import pandas as pd
import requests
import sqlite3
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract...