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

# --- Select and download target scenes ---

# These are the specific scenes validated and used in this project
TARGET_SCENES = [
    "S2B_MSIL2A_20240605T094549_N0510_R079_T35VLG_20240605T112203.SAFE",
    "S2A_MSIL2A_20240710T095031_N0510_R079_T35VLG_20240710T154753.SAFE",
    "S2A_MSIL2A_20240829T095031_N0511_R079_T35VLG_20240829T134149.SAFE",
]

# Set to False to actually download - data is ~900MB per scene
DRY_RUN = True

print("\nSearching catalogue for target scenes...")

download_session = requests.Session()
download_session.headers.update(headers)

for scene_name in TARGET_SCENES:
    # Query by exact name
    params = {
        "$filter": f"Name eq '{scene_name}'",
        "$top": 1,
    }
    response = requests.get(base_url, params=params, headers=headers)
    products = response.json().get("value", [])

    if not products:
        print(f"  Not found in catalogue: {scene_name}")
        continue

    product = products[0]
    product_id = product["Id"]
    output_path = RAW_DATA / f"{scene_name}.zip"

    if output_path.exists():
        print(f"  Already exists, skipping: {scene_name}")
        continue

    if DRY_RUN:
        print(f"  DRY RUN - would download: {scene_name} (ID: {product_id})")
        continue

    print(f"  Downloading: {scene_name}")
    download_url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"

    with download_session.get(download_url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r    {pct:.1f}%", end="", flush=True)
        print(f"\r    Done - saved to {output_path}")

print("\nDownload script complete.")