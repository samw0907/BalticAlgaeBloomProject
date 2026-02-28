# scripts/01_download_data.py
# Baltic Sea Algal Bloom Monitoring - Sentinel-2 data download
# Queries and downloads scenes from Copernicus Data Space Ecosystem (CDSE)

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# --- Path configuration ---

# Raw data download destination
RAW_DATA = Path(r"C:\QGIS Projects\Baltic Algae Blooms\raw_data")

# --- Credentials ---
# Credentials are loaded from .env file - never hardcode these

load_dotenv()
CDSE_USER = os.getenv("CDSE_USER")
CDSE_PASSWORD = os.getenv("CDSE_PASSWORD")

if not CDSE_USER or not CDSE_PASSWORD:
    raise ValueError("CDSE_USER and CDSE_PASSWORD must be set in .env file")

# --- Authenticate with CDSE ---

print("Authenticating with Copernicus Data Space Ecosystem...")

token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

response = requests.post(token_url, data={
    "grant_type": "password",
    "username": CDSE_USER,
    "password": CDSE_PASSWORD,
    "client_id": "cdse-public",
})

if response.status_code != 200:
    raise ConnectionError(f"Authentication failed: {response.status_code} {response.text}")

access_token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print("Authenticated successfully.")

# --- Query CDSE OData catalogue ---

print("\nQuerying Copernicus catalogue...")

base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

date_ranges = [
    ("2024-06-01T00:00:00Z", "2024-06-15T00:00:00Z", "June"),
    ("2024-07-05T00:00:00Z", "2024-07-15T00:00:00Z", "July"),
    ("2024-08-25T00:00:00Z", "2024-09-01T00:00:00Z", "August"),
]

for start, end, label in date_ranges:
    params = {
        "$filter": (
            f"Collection/Name eq 'SENTINEL-2' "
            f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' "
            f"and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A') "
            f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'tileId' "
            f"and att/OData.CSC.StringAttribute/Value eq '35VLG') "
            f"and ContentDate/Start gt {start} "
            f"and ContentDate/Start lt {end}"
        ),
        "$top": 10,
    }

    response = requests.get(base_url, params=params, headers=headers)
    results = response.json()
    products = results.get("value", [])
    print(f"  {label}: {len(products)} scene(s) found")
    for p in products:
        print(f"    {p['Name']}")