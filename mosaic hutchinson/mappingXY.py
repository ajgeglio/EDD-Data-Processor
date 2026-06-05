import math
import json
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1) Input data (edit as needed)
# -----------------------------
df = pd.read_csv("MosaicWellCoordinates_all_sampled.csv")
df = df[["WellName", "XCoord", "YCoord", "LAT", "LONG", "Aquifer"]]

# -----------------------------
# 2) Filter wells inside plotted boundary
# -----------------------------
x_min = 1.4840e6
x_max = 1.491e6
y_min = 1.812e6
y_max = 1.820e6

filtered_df = df[(df['XCoord'] >= x_min) & (df['XCoord'] <= x_max) & (df['YCoord'] >= y_min) & (df['YCoord'] <= y_max)]

print("Filtered wells inside the plotted boundary:")
print(len(filtered_df), "wells")
filtered_df.WellName.to_csv("MosaicWellNames_Filtered.csv", index=False, header=False)
# ---------------------------------------
# 3) Create GeoJSON (WGS84 / EPSG:4326)
# ---------------------------------------
features = []
for _, r in df.iterrows():
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["LONG"], r["LAT"]]},
        "properties": {"id": r["WellName"]}
    })

geojson = {
    "type": "FeatureCollection",
    "name": "WellLocations",
    "features": features,
    "crs": {"type": "name", "properties": {"name": "EPSG:4269"}}  # NAD83, which is close enough for this purpose
}

geojson_path = "MosaicWellLocations.geojson"
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

# -----------------------------
# 4) Make a quick static map
# -----------------------------
fig, ax = plt.subplots(figsize=(18, 10))

# Category symbology
cats = {
    "Shallow": {
        "mask": df["Aquifer"].str.contains("S"),
        "color": "#ff7f0e",
        "marker": "s",
        "label": "S",
        # annotate to the bottom-left of the point
        "text_offset": (-24, -12),
    },
    "Deep": {
        "mask": df["Aquifer"].str.contains("D"),
        "color": "#1f77b4",
        "marker": "o",
        "label": "D",
        # annotate to the top-right of the point
        "text_offset": (3, 3),
    },
}

# Plot categorized points
for key, spec in cats.items():
    d = df[spec["mask"]]
    ax.scatter(
        d["XCoord"], d["YCoord"],
        s=36, c=spec["color"], marker=spec["marker"],
        label=f"{spec['label']} (n={len(d)})", zorder=4
    )

for _, r in df.iterrows():
    # Use category-specific text offset to reduce overlap
    # (top-right for Deep, bottom-left for Shallow)
    cat = "Deep" if "D" in r["Aquifer"] else "Shallow"
    offset = cats[cat]["text_offset"]
    ax.annotate(r["WellName"], (r["XCoord"], r["YCoord"]),
                xytext=offset, textcoords="offset points",
                fontsize=8, color="#222", zorder=3)

# Extent & axes
pad_lon = 0.00025
pad_lat = 0.00025
# ax.set_xlim(df["XCoord"].min() - pad_lon, df["XCoord"].max() + pad_lon)
# ax.set_ylim(df["YCoord"].min() - pad_lat,  df["YCoord"].max() + pad_lat)
ax.set_xlim(x_min, x_max)  # fixed extent for better map layout
ax.set_ylim(y_min, y_max)  # fixed extent for better map layout

ax.set_aspect("equal", adjustable="box")
ax.grid(True, linestyle="--", alpha=0.3)
ax.set_xlabel("X (SPCS NAD83 / EPSG:26910)")
ax.set_ylabel("Y (SPCS NAD83 / EPSG:26910)")
ax.set_title("Hypothetical Boring Locations (NAD83 / EPSG:4269)")
ax.legend(loc="upper left", frameon=True)

# North arrow (simple)
x0, x1 = ax.get_xlim()
y0, y1 = ax.get_ylim()
arr_x = x0 + 0.12 * (x1 - x0)
arr_y = y0 + 0.12 * (y1 - y0)
# Use a fixed fraction of the Y dimension for arrow length (coordinates are in feet)
arr_len = 0.02 * (y1 - y0)
ax.annotate("N",
            xy=(arr_x, arr_y + arr_len / 2),
            xytext=(arr_x, arr_y - arr_len / 2),
            arrowprops=dict(arrowstyle="-|>", color="black"),
            ha="center", va="center", fontsize=9)

# Approximate 5280 ft scale bar (X direction)
scale_ft = 5280
sb_x0 = x0 + 0.05 * (x1 - x0)
sb_y = y0 + 0.05 * (y1 - y0)
ax.plot([sb_x0, sb_x0 + scale_ft], [sb_y, sb_y], color="k", lw=2)
ax.text(sb_x0 + scale_ft / 2, sb_y + 0.01 * (y1 - y0), f"1 mile (5280 ft) (approx)",
        ha="center", va="bottom", fontsize=8)

# Save figure
out_png = "WellLocations_Mosaic2.png"
fig.tight_layout()
fig.savefig(out_png, dpi=180)
plt.close(fig)

print("Wrote files:")
print(f" - {geojson_path}")
print(f" - {out_png}")