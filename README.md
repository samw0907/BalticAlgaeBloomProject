# Baltic Sea Algal Bloom Monitoring

Sentinel-2 multispectral imagery analysis of algal bloom development in the Gulf of Finland, June–August 2024.

## Overview

This project automates the detection and monitoring of cyanobacterial blooms using the Normalized Difference Chlorophyll Index (NDCI) derived from Sentinel-2 Level-2A imagery. It accompanies a desktop GIS analysis completed in QGIS.

**Study area:** Gulf of Finland, tile T35VLG  
**Time periods:** June 5, July 10, August 29 2024  
**Index:** NDCI = (B05 - B04) / (B05 + B04)

## Scripts

| Script | Purpose |
|---|---|
| `scripts/02_process_imagery.py` | Band loading, SCL masking, NDCI calculation |
| `scripts/03_spatial_analysis.py` | GeoPandas zonal statistics against HELCOM MPAs |
| `scripts/04_generate_maps.py` | Three-panel Matplotlib map output |
| `scripts/01_download_data.py` | Copernicus CDSE API download automation |

## Installation
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Data Sources

- Sentinel-2 L2A imagery: Copernicus Data Space Ecosystem (dataspace.copernicus.eu)
- HELCOM MPA boundaries: HELCOM Map and Data Service (maps.helcom.fi)
