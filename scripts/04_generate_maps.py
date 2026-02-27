# scripts/04_generate_maps.py
# Baltic Sea Algal Bloom Monitoring - three-panel NDCI map output
# Produces PNG and PDF map matching QGIS print layout

import numpy as np
import rasterio
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon, Rectangle
from pyproj import Transformer
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

# --- Graticule helper ---

# Transformer from geographic (lat/lon) to UTM Zone 35N
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32635", always_xy=True)

def add_graticule(ax):
    """Add lat/lon grid lines and labels to a UTM-projected axis."""

    # Grid lines at 0.5 degree intervals
    lons = [23.5, 24.0, 24.5, 25.0]
    lats = [59.5, 60.0]

    # Vertical lines (longitude)
    for lon in lons:
        x, _ = transformer.transform(lon, 60.0)
        ax.axvline(x, color="black", linewidth=0.6, linestyle="-", alpha=0.7)
        ax.text(x, 6588500, f"{lon}°", color="white", fontsize=6,
            ha="center", va="top", clip_on=False)

    # Horizontal lines (latitude)
    for lat in lats:
        _, y = transformer.transform(24.0, lat)
        ax.axhline(y, color="black", linewidth=0.6, linestyle="-", alpha=0.7)
        ax.text(298000, y, f"{lat}°", color="white", fontsize=6,
            ha="right", va="center", clip_on=False)

    # Remove default UTM tick labels
    ax.set_xticks([])
    ax.set_yticks([])

# --- Build three-panel figure ---

fig, axes = plt.subplots(1, 3, figsize=(20, 8))
fig.patch.set_facecolor("black")

# Colour map and normalisation - consistent across all three panels
cmap = plt.cm.Spectral_r.copy()
cmap.set_bad("white")
norm = mcolors.Normalize(vmin=NDCI_MIN, vmax=NDCI_MAX)

# MPA style categories
mpa_styles = {
    "Designated":                 {"edgecolor": "black",  "linewidth": 0.8},
    "Designated and managed":     {"edgecolor": "red",    "linewidth": 0.8},
}

for ax, (name, date_label) in zip(axes, SCENES.items()):
    ax.set_facecolor("black")

    # Display NDCI raster
    img = ax.imshow(
        ndci_data[name],
        cmap=cmap,
        norm=norm,
        extent=ndci_extent[name],
        origin="upper",
        interpolation="none"
    )

    # Overlay MPA boundaries by category
    for status, style in mpa_styles.items():
        subset = mpas[mpas["MPA_status"] == status]
        if not subset.empty:
            subset.plot(
                ax=ax,
                facecolor="none",
                edgecolor=style["edgecolor"],
                linewidth=style["linewidth"]
            )

    # Lock view to raster tile extent
    ax.set_xlim(300000, 410000)
    ax.set_ylim(6590220, 6665000)

    add_graticule(ax)

    # Date label
    ax.text(
        0.02, 0.97, date_label,
        transform=ax.transAxes,
        color="black", fontsize=11, fontweight="bold",
        va="top", ha="left"
    )

    # Axis styling
    ax.tick_params(colors="white", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("white")

    # Panel border
    for spine in ax.spines.values():
        spine.set_edgecolor("white")

    # --- North arrow - cartographic split style, top right ---
    arrow_x = 403000
    arrow_top = 6663000
    arrow_bottom = 6655000
    arrow_mid = (arrow_top + arrow_bottom) / 2
    arrow_width = 2500

    # Left half - black
    left = Polygon([
        [arrow_x, arrow_top],
        [arrow_x - arrow_width, arrow_bottom],
        [arrow_x, arrow_mid]
    ], closed=True, facecolor="black", edgecolor="black", linewidth=0.5)
    ax.add_patch(left)

    # Right half - white
    right = Polygon([
        [arrow_x, arrow_top],
        [arrow_x + arrow_width, arrow_bottom],
        [arrow_x, arrow_mid]
    ], closed=True, facecolor="white", edgecolor="black", linewidth=0.5)
    ax.add_patch(right)

    # --- Scale bar - alternating black/white segments, bottom right ---
    scale_x_start = 388000
    segment_width = 5000  # 5km per segment
    scale_y = 6592000
    scale_height = 1000
    colours = ["black", "white", "black"]
    for i, col in enumerate(colours):
        rect = Rectangle(
            (scale_x_start + i * segment_width, scale_y),
            segment_width, scale_height,
            facecolor=col, edgecolor="black", linewidth=0.5
        )
        ax.add_patch(rect)

    # Labels above the bar
    ax.text(scale_x_start, scale_y + scale_height + 500, "0", color="black", fontsize=6, ha="center")
    ax.text(scale_x_start + segment_width, scale_y + scale_height + 500, "5", color="black", fontsize=6, ha="center")
    ax.text(scale_x_start + segment_width * 3, scale_y + scale_height + 500, "15 km", color="black", fontsize=6, ha="center")

# --- Shared colour bar ---
cbar_ax = fig.add_axes([0.92, 0.25, 0.012, 0.5])
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_ticks([NDCI_MIN, 0, 0.02, 0.04, 0.06, NDCI_MAX])
cbar.set_ticklabels([str(NDCI_MIN), "0", "0.02", "0.04", "0.06", str(NDCI_MAX)])
cbar.set_label("NDCI", color="white", fontsize=9)
cbar.ax.yaxis.set_tick_params(color="white")
cbar.ax.tick_params(labelcolor="white", labelsize=7)

# --- MPA legend ---
legend_elements = [
    mpatches.Patch(facecolor="none", edgecolor="black", label="Designated"),
    mpatches.Patch(facecolor="none", edgecolor="red",   label="Designated and managed"),
]
legend = fig.legend(
    handles=legend_elements,
    loc="lower right",
    bbox_to_anchor=(0.91, 0.02),
    fontsize=7,
    framealpha=0.2,
    labelcolor="white",
    title="HELCOM MPAs",
    title_fontsize=8,
)
legend.get_title().set_color("white")

# Title
fig.suptitle(
    "Algae Bloom Monitoring, Baltic Sea  |  NDCI Index Analysis  |  June - August 2024",
    color="white", fontsize=12, fontweight="bold", y=0.98
)

plt.subplots_adjust(left=0.04, right=0.91, top=0.93, bottom=0.07, wspace=0.08)

# --- Save outputs ---

png_path = MAPS_DIR / "ndci_map.png"
pdf_path = MAPS_DIR / "ndci_map.pdf"

fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="black")
fig.savefig(pdf_path, dpi=300, bbox_inches="tight", facecolor="black")

print(f"\nSaved: {png_path}")
print(f"Saved: {pdf_path}")

plt.show()