# Baltic Sea Algal Bloom Monitoring

Sentinel-2 imagery analysis of algal bloom conditions in the Gulf of Finland across three dates in 2024, using the Normalised Difference Chlorophyll Index (NDCI).

This is one of two linked projects. The other is a desktop analysis of the same data in QGIS. The Python scripts here reproduce that workflow programmatically.

---

## Study area and data

**Tile:** T35VLG, Gulf of Finland  
**Dates:** 5 June, 10 July, 29 August 2024  
**Source imagery:** Sentinel-2 Level-2A (surface reflectance), downloaded from the Copernicus Data Space Ecosystem  
**Vector data:** HELCOM Marine Protected Area boundaries, 2019, from the HELCOM Map and Data Service

The three dates were selected to capture pre-bloom baseline conditions (June), peak bloom (July), and post-peak decline (August). The July scene has significant cloud cover in the northern portion of the tile, which is handled by the SCL mask.

---

## Method

NDCI is calculated from the red and red-edge bands:

```
NDCI = (B05 - B04) / (B05 + B04)
```

B05 is at 20m resolution and is resampled to 10m before calculation (bilinear). The Sentinel-2 Scene Classification Layer (SCL) is used to mask cloud, cloud shadow, and land pixels, retaining only confirmed water and unclassified pixels (classes 6 and 7). The colour stretch applied is -0.015 to 0.08, tuned to the actual data range for this tile and dataset.

No NDWI water mask is applied - SCL masking alone is used to avoid losing valid coastal pixels.

---

## Scripts

Scripts are numbered in recommended run order:

| Script | Purpose |
|---|---|
| `01_download_data.py` | Authenticate with CDSE, query catalogue, download scenes |
| `02_process_imagery.py` | Load bands, apply SCL mask, calculate NDCI, save GeoTIFFs |
| `03_spatial_analysis.py` | Tile-wide statistics and zonal statistics per HELCOM MPA |
| `04_generate_maps.py` | Three-panel Matplotlib map output (PNG and PDF) |

---

## Results

Tile-wide mean NDCI values show a clear temporal pattern:

| Date | Mean NDCI | Interpretation |
|---|---|---|
| 5 June 2024 | -0.00589 | Pre-bloom baseline, low chlorophyll |
| 10 July 2024 | -0.00072 | Peak bloom, elevated chlorophyll |
| 29 August 2024 | -0.00425 | Post-peak decline |

Three HELCOM MPAs fall substantially within the tile extent and were retained for zonal analysis: Kirkkonummi Archipelago (100% within tile), Tammisaari and Hanko Archipelago (45%), and Hangon itäinen selkä (23%). MPAs were included where at least 20% of their total area fell within the tile boundary. A higher total area % would be preffered, however higher cloud coverage over the areas on July 10, required a lower threshold to be used. Zonal mean NDCI values for these areas follow the same temporal pattern as the tile-wide figures:

| Date | Mean NDCI across retained MPAs |
|---|---|
| 5 June 2024 | -0.00656 |
| 10 July 2024 | 0.00013 |
| 29 August 2024 | -0.00315 |

Söderskärin ja Långörenin saaristo (1.4%) and Pakri (2.4%) fell below the 20% threshold and were excluded from the MPA analysis.
---

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Copernicus Data Space credentials:

```
CDSE_USER=your_email@example.com
CDSE_PASSWORD=your_password
```

The download script runs in dry-run mode by default (`DRY_RUN = True`). Set this to `False` to trigger actual downloads. Each scene is approximately 900MB.

---

## Known data characteristics

- A detector seam banding artefact is visible as diagonal striping across water in all three scenes. This is a known Sentinel-2 sensor characteristic and does not affect data validity.
- The July scene has significant cloud coverage in the northern portion, correctly masked by the SCL layer.
- The bloom signal in this dataset is subtle. NDCI values range from approximately 0.002 in clear open water to around 0.08-0.10 in bloom pixels. The colour stretch is tuned accordingly.
- The August scene is used in place of a more typical post bloom period in September due to incomplete tile coverage in the September acquisition.

---

## Data sources

- Sentinel-2 L2A imagery: [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu)
- HELCOM MPA boundaries: [HELCOM Map and Data Service](https://maps.helcom.fi)
- Coordinate system: EPSG:32635 (WGS84 UTM Zone 35N)
