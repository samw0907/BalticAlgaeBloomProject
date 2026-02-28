# scripts/03_spatial_analysis.py
# Baltic Sea Algal Bloom Monitoring - spatial analysis
# Calculates tile-wide NDCI statistics and zonal statistics per HELCOM MPA

import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import mapping

# --- Path configuration ---

# Processed NDCI rasters from 02_process_imagery.py
OUTPUT_DIR = Path(r"C:\Users\swill\dev\BalticAlgaeBloomProject\outputs")

# HELCOM MPA shapefile
VECTORS_DIR = Path(r"C:\Users\swill\dev\BalticAlgaeBloomProject\data\vectors")

# Statistics output directory
STATS_DIR = OUTPUT_DIR / "statistics"
STATS_DIR.mkdir(exist_ok=True)

# Scene dates for labelling
SCENES = {
    "june":   "2024-06-05",
    "july":   "2024-07-10",
    "august": "2024-08-29",
}

# --- Load HELCOM MPA boundaries ---

mpa_path = VECTORS_DIR / "HELCOM_MPAs_2019_2.shp"
mpas = gpd.read_file(mpa_path)
mpas = mpas.to_crs("EPSG:32635")

print(f"Loaded {len(mpas)} MPA polygons")

# --- Filter MPAs by coverage within tile extent ---

# Get tile extent from June raster as a polygon
with rasterio.open(OUTPUT_DIR / "june_ndci.tif") as src:
    tile_bounds = src.bounds
    from shapely.geometry import box
    tile_polygon = box(tile_bounds.left, tile_bounds.bottom,
                       tile_bounds.right, tile_bounds.top)

tile_gdf = gpd.GeoDataFrame(geometry=[tile_polygon], crs="EPSG:32635")

# Calculate what percentage of each MPA falls within the tile
mpas["mpa_area"] = mpas.geometry.area
mpas["intersection_area"] = mpas.geometry.intersection(tile_polygon).area
mpas["coverage_pct"] = (mpas["intersection_area"] / mpas["mpa_area"]) * 100

# Retain only MPAs with at least 60% of their area within the tile
mpas_filtered = mpas[mpas["coverage_pct"] >= 60].copy()

print(f"MPAs within tile at 60% coverage threshold: {len(mpas_filtered)} of {len(mpas)}")
print("\nRetained MPAs:")
for _, row in mpas_filtered.iterrows():
    print(f"  {row['Name']} ({row['MPA_status']}) - {row['coverage_pct']:.1f}% coverage")

# --- Tile-wide summary statistics ---

print("\nTile-wide NDCI statistics:")
print(f"{'Date':<12} {'Valid pixels':>15} {'Mean NDCI':>12} {'Max NDCI':>12} {'Std dev':>10}")
print("-" * 65)

tile_stats = []

for name, date in SCENES.items():
    path = OUTPUT_DIR / f"{name}_ndci.tif"
    with rasterio.open(path) as src:
        ndci = src.read(1)

    valid = ndci[~np.isnan(ndci)]
    stats = {
        "date": date,
        "valid_pixels": len(valid),
        "mean_ndci": round(float(np.mean(valid)), 5),
        "max_ndci": round(float(np.max(valid)), 5),
        "std_ndci": round(float(np.std(valid)), 5),
    }
    tile_stats.append(stats)
    print(f"{date:<12} {stats['valid_pixels']:>15,} {stats['mean_ndci']:>12.5f} {stats['max_ndci']:>12.5f} {stats['std_ndci']:>10.5f}")

tile_df = pd.DataFrame(tile_stats)
tile_df.to_csv(STATS_DIR / "tile_wide_statistics.csv", index=False)
print(f"\nSaved: {STATS_DIR / 'tile_wide_statistics.csv'}")

# --- Zonal statistics per HELCOM MPA ---

print("\nCalculating zonal statistics per MPA...")

# Open each raster once and store the src object info we need
raster_paths = {name: OUTPUT_DIR / f"{name}_ndci.tif" for name in SCENES}

zonal_rows = []

for idx, mpa_row in mpas_filtered.iterrows():
    geom = [mapping(mpa_row.geometry)]
    mpa_name = mpa_row["Name"]
    mpa_status = mpa_row["MPA_status"]
    mpa_country = mpa_row["Country"]

    for name, date in SCENES.items():
        try:
            with rasterio.open(raster_paths[name]) as src:
                # Clip raster to MPA polygon extent
                out_image, _ = rio_mask(src, geom, crop=True, nodata=np.nan)
                clipped = out_image[0]

            valid = clipped[~np.isnan(clipped)]

            if len(valid) < 10:
                # Skip MPAs with too few valid pixels (outside tile or fully clouded)
                continue

            zonal_rows.append({
                "mpa_name": mpa_name,
                "mpa_status": mpa_status,
                "country": mpa_country,
                "date": date,
                "valid_pixels": len(valid),
                "mean_ndci": round(float(np.mean(valid)), 5),
                "max_ndci": round(float(np.max(valid)), 5),
                "std_ndci": round(float(np.std(valid)), 5),
            })

        except Exception:
            # MPA geometry outside raster extent - skip silently
            continue

zonal_df = pd.DataFrame(zonal_rows)

if not zonal_df.empty:
    zonal_df.to_csv(STATS_DIR / "mpa_zonal_statistics.csv", index=False)
    print(f"Processed {zonal_df['mpa_name'].nunique()} MPAs with valid data")
    print(f"Saved: {STATS_DIR / 'mpa_zonal_statistics.csv'}")

    # Print summary by date
    print("\nMean NDCI across all valid MPAs by date:")
    summary = zonal_df.groupby("date")["mean_ndci"].mean()
    for date, val in summary.items():
        print(f"  {date}: {val:.5f}")
else:
    print("No valid MPA pixels found within tile extent.")