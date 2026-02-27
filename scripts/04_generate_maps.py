# scripts/04_generate_maps.py
# Baltic Sea Algal Bloom Monitoring - three-panel NDCI map output
# Produces PNG and PDF map matching QGIS print layout

import numpy as np
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# --- Path configuration ---

# Processed NDCI rasters from 02_process_imagery.py
OUTPUT_DIR = Path(r"C:\Users\swill\dev\BalticAlgaeBloomProject\outputs")

# HELCOM MPA shapefile
VECTORS_DIR = Path(r"C:\Users\swill\dev\BalticAlgaeBloomProject\data\vectors")

# Map output directory
MAPS_DIR = OUTPUT_DIR / "maps"
MAPS_DIR.mkdir(exist_ok=True)

# NDCI colour stretch - validated against QGIS output
NDCI_MIN = -0.015
NDCI_MAX = 0.08

# Scene labels for map panels
SCENES = {
    "june":   "05.06.24",
    "july":   "10.07.24",
    "august": "29.08.24",
}

# --- Load NDCI rasters ---

ndci_data = {}
ndci_extent = {}

for name in SCENES:
    path = OUTPUT_DIR / f"{name}_ndci.tif"
    with rasterio.open(path) as src:
        ndci_data[name] = src.read(1)
        bounds = src.bounds
        # extent format for matplotlib: [left, right, bottom, top]
        ndci_extent[name] = [bounds.left, bounds.right, bounds.bottom, bounds.top]

print("Loaded scenes:")
for name, arr in ndci_data.items():
    print(f"  {name}: shape {arr.shape}, mean NDCI {np.nanmean(arr):.4f}")

# --- Load HELCOM MPA boundaries ---

mpa_path = VECTORS_DIR / "HELCOM_MPAs_2019_2.shp"
mpas = gpd.read_file(mpa_path)

# Reproject from EPSG:4326 to EPSG:32635 to match raster data
mpas = mpas.to_crs("EPSG:32635")

print(f"\nLoaded {len(mpas)} MPA polygons")
print(f"CRS: {mpas.crs}")
print(f"Columns: {list(mpas.columns)}")