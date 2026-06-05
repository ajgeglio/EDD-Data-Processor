import math
import json
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1) Input data (edit as needed)
# -----------------------------
df = pd.read_excel("C:\\Users\\ageglio\\OneDrive - TRC\\Documents\\GFL Riverview\\GFL Riverview 2-24-12 coords.xlsx")
df = df[["Boring ID", "Longitude", "Latitude"]]
# ---------------------------------------
# 3) Create GeoJSON (WGS84 / EPSG:4326)
# ---------------------------------------
features = []
for _, r in df.iterrows():
    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["Longitude"], r["Latitude"]]},
        "properties": {"id": r["Boring ID"]}
    })

geojson = {
    "type": "FeatureCollection",
    "name": "boring_locations",
    "features": features,
    "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}
}

geojson_path = "boring_locations.geojson"
with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

# -----------------------------
# 4) Make a quick static map
# -----------------------------
fig, ax = plt.subplots(figsize=(18, 10))

# Category symbology
cats = {
    "MW": {"mask": df["Boring ID"].str.startswith("MW"), "color": "#1f77b4", "marker": "o", "label": "MW"},
    "OW": {"mask": df["Boring ID"].str.startswith("OW"), "color": "#ff7f0e", "marker": "s", "label": "OW"},
    "VP": {"mask": df["Boring ID"].str.startswith("VP"), "color": "#2ca02c", "marker": "^", "label": "VP"},
}
other_mask = ~(cats["MW"]["mask"] | cats["OW"]["mask"] | cats["VP"]["mask"])

# Plot categorized points
for key, spec in cats.items():
    d = df[spec["mask"]]
    ax.scatter(
        d["Longitude"], d["Latitude"],
        s=36, c=spec["color"], marker=spec["marker"],
        label=f"{spec['label']} (n={len(d)})", zorder=3
    )

# Plot others (numeric IDs)
other = df[other_mask]
if not other.empty:
    ax.scatter(other["Longitude"], other["Latitude"], s=36, c="#7f7f7f", marker="D",
               label=f"Other (n={len(other)})", zorder=3)

# Labels
for _, r in df.iterrows():
    ax.annotate(r["Boring ID"], (r["Longitude"], r["Latitude"]),
                xytext=(3, 3), textcoords="offset points",
                fontsize=8, color="#222", zorder=4)

# Extent & axes
pad_lon = 0.00025
pad_lat = 0.00025
ax.set_xlim(df["Longitude"].min() - pad_lon, df["Longitude"].max() + pad_lon)
ax.set_ylim(df["Latitude"].min() - pad_lat,  df["Latitude"].max() + pad_lat)
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linestyle="--", alpha=0.3)
ax.set_xlabel("Longitude (°)")
ax.set_ylabel("Latitude (°)")
ax.set_title("Hypothetical Boring Locations (NAD83 / EPSG:4269)")
ax.legend(loc="upper left", frameon=True)

# North arrow (simple)
x0, x1 = ax.get_xlim()
y0, y1 = ax.get_ylim()
arr_x = x0 + 0.12 * (x1 - x0)
arr_y = y0 + 0.12 * (y1 - y0)
ax.annotate("N",
            xy=(arr_x, arr_y + 0.00012),
            xytext=(arr_x, arr_y - 0.00012),
            arrowprops=dict(arrowstyle="-|>", color="black"),
            ha="center", va="center", fontsize=9)

# Approximate 50 m scale bar (longitude direction)
lat0 = df["Latitude"].mean()
meters_per_deg_lon = 111_320 * math.cos(math.radians(lat0))  # rough but fine for small extents
scale_m = 50
scale_deg_lon = scale_m / meters_per_deg_lon if meters_per_deg_lon else 0
sb_x0 = x0 + 0.05 * (x1 - x0)
sb_y  = y0 + 0.05 * (y1 - y0)
ax.plot([sb_x0, sb_x0 + scale_deg_lon], [sb_y, sb_y], color="k", lw=2)
ax.text(sb_x0 + scale_deg_lon / 2, sb_y + 0.00004, f"{scale_m} m (approx)",
        ha="center", va="bottom", fontsize=8)

# Save figure
out_png = "boring_locations_map.png"
fig.tight_layout()
fig.savefig(out_png, dpi=180)
plt.close(fig)

print("Wrote files:")
print(f" - {geojson_path}")
print(f" - {out_png}")