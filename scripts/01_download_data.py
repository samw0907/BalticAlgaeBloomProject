# scripts/01_download_data.py
# Baltic Sea Algal Bloom Monitoring - Sentinel-2 data download
# Queries and downloads scenes from Copernicus Data Space Ecosystem (CDSE)

import os
from sentinelsat import SentinelAPI
from pathlib import Path
from dotenv import load_dotenv

# --- Path configuration ---

# Raw data download destination
RAW_DATA = Path(r"C:\QGIS Projects\Baltic Algae Blooms\raw_data")

# --- Credentials ---
# Replace with your Copernicus Data Space Ecosystem account credentials

load_dotenv()
CDSE_USER = os.getenv("CDSE_USER")
CDSE_PASSWORD = os.getenv("CDSE_PASSWORD")

if not CDSE_USER or not CDSE_PASSWORD:
    raise ValueError("CDSE_USER and CDSE_PASSWORD must be set in .env file")

# --- Authenticate with CDSE ---

print("Connecting to Copernicus Data Space Ecosystem...")

api = SentinelAPI(
    CDSE_USER,
    CDSE_PASSWORD,
    api_url="https://catalogue.dataspace.copernicus.eu/odata/v1",
)

print("Connected successfully.")