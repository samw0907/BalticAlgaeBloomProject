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

### Tile-wide statistics

| Date | Mean NDCI | P95 NDCI | Max NDCI |
|---|---|---|---|
| 5 June 2024 | -0.00589 | 0.00141 | 1.00000* |
| 10 July 2024 | -0.00072 | 0.00987 | 1.00000* |
| 29 August 2024 | -0.00425 | 0.00365 | 0.32437 |

*Tile-wide max values of 1.0 for June and July are noise pixels at mask boundaries and are not representative of bloom intensity. The August max of 0.32 is more representative. P95 is used as the primary peak intensity metric.

### HELCOM MPA zonal statistics

Three MPAs fall substantially within the tile extent and were retained for zonal analysis using a 20% minimum area coverage threshold: Kirkkonummi Archipelago (100%), Tammisaari and Hanko Archipelago (45%), and Hangon itäinen selkä (23%). Söderskärin ja Långörenin saaristo (1.4%) and Pakri (2.4%) fell below the threshold and were excluded.

| MPA | Date | Mean NDCI | P95 NDCI | Max NDCI |
|---|---|---|---|---|
| Kirkkonummi Archipelago | 5 June 2024 | -0.00742 | 0.00094 | 0.22521 |
| Kirkkonummi Archipelago | 10 July 2024 | 0.00203 | 0.01489 | 0.24167 |
| Kirkkonummi Archipelago | 29 August 2024 | -0.00402 | 0.00503 | 0.23852 |
| Tammisaari and Hanko Archipelago | 5 June 2024 | -0.00611 | 0.02250 | 0.22315 |
| Tammisaari and Hanko Archipelago | 10 July 2024 | 0.00002 | 0.02698 | 0.26975 |
| Tammisaari and Hanko Archipelago | 29 August 2024 | -0.00039 | 0.02491 | 0.22261 |
| Hangon itäinen selkä | 5 June 2024 | -0.00616 | 0.00000 | 0.03100 |
| Hangon itäinen selkä | 10 July 2024 | -0.00166 | 0.00621 | 0.16610 |
| Hangon itäinen selkä | 29 August 2024 | -0.00503 | 0.00139 | 0.04478 |

All three MPAs follow the same June baseline → July peak → August decline temporal pattern as the tile-wide figures. Tammisaari and Hanko Archipelago consistently shows the highest P95 values, indicating more intense localised bloom conditions. Hangon itäinen selkä shows notably lower values across all metrics, consistent with its smaller size and more open water exposure. The June P95 of 0.000 for Hangon itäinen selkä reflects near-zero chlorophyll activity across 95% of valid pixels in pre-bloom conditions.

### Averaged across retained MPAs by date

| Date | Mean NDCI | P95 NDCI | Max NDCI |
|---|---|---|---|
| 5 June 2024 | -0.00656 | 0.00781 | 0.15979 |
| 10 July 2024 | 0.00013 | 0.01602 | 0.22584 |
| 29 August 2024 | -0.00315 | 0.01044 | 0.16864 |

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
