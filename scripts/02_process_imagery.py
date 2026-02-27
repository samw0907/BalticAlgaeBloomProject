# scripts/02_process_imagery.py
# Baltic Sea Algal Bloom Monitoring - Sentinel-2 imagery processing
# Loads B04, B05, SCL bands, applies SCL mask, calculates NDCI, saves output rasters

import rasterio
import numpy as np
from pathlib import Path
from rasterio.enums import Resampling


# --- Path configuration ---

# Root of raw Sentinel-2 data
RAW_DATA = Path(r"C:\QGIS Projects\Baltic Algae Blooms\raw_data")

# Output directory for processed NDCI rasters
OUTPUT_DIR = Path(r"C:\Users\swill\dev\BalticAlgaeBloomProject\outputs")

# Scene definitions - SAFE folder, then granule subfolder, then filenames
SCENES = {
    "june": {
        "safe": "S2B_MSIL2A_20240605T094549_N0510_R079_T35VLG_20240605T112203.SAFE",
        "granule": "L2A_T35VLG_A037857_20240605T094757",
        "b04": "T35VLG_20240605T094549_B04_10m.jp2",
        "b05": "T35VLG_20240605T094549_B05_20m.jp2",
        "scl": "T35VLG_20240605T094549_SCL_20m.jp2",
    },
        "july": {
        "safe": "S2A_MSIL2A_20240710T095031_N0510_R079_T35VLG_20240710T154753.SAFE",
        "granule": "L2A_T35VLG_A047266_20240710T095042",
        "b04": "T35VLG_20240710T095031_B04_10m.jp2",
        "b05": "T35VLG_20240710T095031_B05_20m.jp2",
        "scl": "T35VLG_20240710T095031_SCL_20m.jp2",
    },
    "august": {
        "safe": "S2A_MSIL2A_20240829T095031_N0511_R079_T35VLG_20240829T134149.SAFE",
        "granule": "L2A_T35VLG_A047981_20240829T095026",
        "b04": "T35VLG_20240829T095031_B04_10m.jp2",
        "b05": "T35VLG_20240829T095031_B05_20m.jp2",
        "scl": "T35VLG_20240829T095031_SCL_20m.jp2",
    }
}

# --- Read band arrays for June scene ---

def process_scene(name, scene):
    """Load bands, apply SCL mask, calculate NDCI, save output raster."""

    print(f"\nProcessing: {name}")
    granule_path = RAW_DATA / scene["safe"] / "GRANULE" / scene["granule"] / "IMG_DATA"

    b04_path = granule_path / "R10m" / scene["b04"]
    b05_path = granule_path / "R20m" / scene["b05"]
    scl_path = granule_path / "R20m" / scene["scl"]

    # Read B04 at native 10m resolution
    with rasterio.open(b04_path) as src:
        b04 = src.read(1).astype("float32")
        profile = src.profile  # save metadata for writing outputs later

    # Read B05, resampled from 20m to 10m using bilinear (continuous data)
    with rasterio.open(b05_path) as src:
        b05 = src.read(
            1,
            out_shape=(10980, 10980),
            resampling=Resampling.bilinear
        ).astype("float32")

    # Read SCL, resampled from 20m to 10m using nearest neighbour (categorical data)
    with rasterio.open(scl_path) as src:
        scl = src.read(
            1,
            out_shape=(10980, 10980),
            resampling=Resampling.nearest
        )

    print(f"B04 shape: {b04.shape}")
    print(f"B05 shape (resampled to 10m): {b05.shape}")
    print(f"SCL shape (resampled to 10m): {scl.shape}")

    # --- Apply SCL cloud/land mask ---

    # Retain only water-valid pixels: class 5 (bare soil/coastal), 6 (water), 7 (unclassified)
    # Everything else (clouds, cloud shadow, saturated pixels etc.) becomes NaN
    valid_mask = (scl == 5) | (scl == 6) | (scl == 7)

    # --- Calculate NDCI ---

    # Suppress divide-by-zero warnings - we handle them via NaN masking below
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ndci = (b05 - b04) / (b05 + b04)

    # Apply mask - invalid pixels set to NaN (not a number = no data)
    ndci_masked = np.where(valid_mask, ndci, np.nan)

    # Print a summary of the resulting values
    valid_pixels = np.sum(valid_mask)
    total_pixels = ndci_masked.size
    print(f"Valid pixels: {valid_pixels:,} of {total_pixels:,} ({100 * valid_pixels / total_pixels:.1f}%)")
    print(f"NDCI min: {np.nanmin(ndci_masked):.4f}")
    print(f"NDCI max: {np.nanmax(ndci_masked):.4f}")
    print(f"NDCI mean: {np.nanmean(ndci_masked):.4f}")

    # --- Save NDCI output raster ---

    # Update the profile from B04 for float32 output with NaN no-data value
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=float("nan")
    )

    output_path = OUTPUT_DIR / f"{name}_ndci.tif"

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(ndci_masked, 1)

    print(f"Saved: {output_path}")

# --- Run for all three scenes ---

for name, scene in SCENES.items():
    process_scene(name, scene)

print("\nAll scenes processed.")